import unittest
import json
from datetime import datetime
from app import create_app, db
from constants import USERNAME_KEY, PASSWORD_KEY, ROLE_KEY, Database, UserRole, TestData, AppConfig, API, StatusCode, Message, JWT
from models.user import User
from models.workout import Workout
from models.progress import Progress
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = AppConfig.TEST_DB_URI

class ProgressRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test users
        self.trainer = User(username=TestData.TRAINER_USERNAME, password=TestData.PASSWORD_123, role=UserRole.TRAINER)
        self.trainee = User(username=TestData.TRAINEE_USERNAME, password=TestData.PASSWORD_123, role=UserRole.TRAINEE)
        db.session.add(self.trainer)
        db.session.add(self.trainee)
        db.session.commit()
        
        # Login as trainer to get JWT token
        response = self.client.post(
            f'{API.AUTH_URL_PREFIX}{API.SIGNIN_ROUTE}',
            data=json.dumps({
                USERNAME_KEY: TestData.TRAINER_USERNAME,
                PASSWORD_KEY: TestData.PASSWORD_123
            }),
            content_type=API.CONTENT_TYPE_JSON
        )
        self.trainer_token = response.headers.getlist('Set-Cookie')[0].split(';')[0].split('=')[1]
        
        # Login as trainee to get JWT token
        response = self.client.post(
            f'{API.AUTH_URL_PREFIX}{API.SIGNIN_ROUTE}',
            data=json.dumps({
                USERNAME_KEY: TestData.TRAINEE_USERNAME,
                PASSWORD_KEY: TestData.PASSWORD_123
            }),
            content_type=API.CONTENT_TYPE_JSON
        )
        self.trainee_token = response.headers.getlist('Set-Cookie')[0].split(';')[0].split('=')[1]
        
        # Create a test workout
        self.workout = Workout(
            name='Test Workout',
            exercise='Push-ups',
            duration=30,
            type='Strength',
            description='Test workout description',
            trainer_id=self.trainer.id
        )
        db.session.add(self.workout)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_log_progress_success(self):
        response = self.client.post(
            f'{API.PROGRESS_URL_PREFIX}{API.LOG_PROGRESS_ROUTE}',
            data=json.dumps({
                Database.WORKOUT_ID_KEY: self.workout.id,
                Database.VALUE_KEY: 10.5,
                Database.DATE_KEY: datetime.utcnow().date().isoformat(),
                Database.DESCRIPTION_KEY: 'Test progress notes'
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainee_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.CREATED)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.PROGRESS_LOGGED)
        self.assertEqual(data['progress'][Database.VALUE_KEY], 10.5)
        self.assertEqual(data['progress'][Database.DESCRIPTION_KEY], 'Test progress notes')
        self.assertEqual(data['progress']['workout'][Database.ID_KEY], self.workout.id)

    def test_log_progress_missing_fields(self):
        response = self.client.post(
            f'{API.PROGRESS_URL_PREFIX}{API.LOG_PROGRESS_ROUTE}',
            data=json.dumps({
                Database.WORKOUT_ID_KEY: self.workout.id,
                # Missing value
                Database.DATE_KEY: datetime.utcnow().date().isoformat(),
                Database.DESCRIPTION_KEY: 'Test progress notes'
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainee_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.BAD_REQUEST)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.MISSING_FIELDS)

    def test_log_progress_workout_not_found(self):
        response = self.client.post(
            f'{API.PROGRESS_URL_PREFIX}{API.LOG_PROGRESS_ROUTE}',
            data=json.dumps({
                Database.WORKOUT_ID_KEY: 999,  # Non-existent workout ID
                Database.VALUE_KEY: 10.5,
                Database.DATE_KEY: datetime.utcnow().date().isoformat(),
                Database.DESCRIPTION_KEY: 'Test progress notes'
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainee_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.NOT_FOUND)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.WORKOUT_NOT_FOUND)

    def test_get_all_progress(self):
        # Create a progress entry first
        progress = Progress(
            user_id=self.trainee.id,
            workout_id=self.workout.id,
            value=10.5,
            date=datetime.utcnow().date(),
            notes='Test progress notes'
        )
        db.session.add(progress)
        db.session.commit()
        
        response = self.client.get(
            f'{API.PROGRESS_URL_PREFIX}{API.LOG_PROGRESS_ROUTE}',
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.OK)
        data = json.loads(response.data)
        self.assertEqual(len(data['progress']), 1)
        self.assertEqual(data['progress'][0][Database.VALUE_KEY], 10.5)
        self.assertEqual(data['progress'][0][Database.DESCRIPTION_KEY], 'Test progress notes')
        self.assertEqual(data['progress'][0]['workout'][Database.ID_KEY], self.workout.id)

    def test_get_progress_success(self):
        # Create a progress entry first
        progress = Progress(
            user_id=self.trainee.id,
            workout_id=self.workout.id,
            value=10.5,
            date=datetime.utcnow().date(),
            notes='Test progress notes'
        )
        db.session.add(progress)
        db.session.commit()
        
        response = self.client.get(
            f'{API.PROGRESS_URL_PREFIX}{API.GET_PROGRESS_ROUTE.replace("<int:progress_id>", str(progress.id))}',
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.OK)
        data = json.loads(response.data)
        self.assertEqual(data['progress'][Database.VALUE_KEY], 10.5)
        self.assertEqual(data['progress'][Database.DESCRIPTION_KEY], 'Test progress notes')
        self.assertEqual(data['progress']['workout'][Database.ID_KEY], self.workout.id)

    def test_get_progress_not_found(self):
        response = self.client.get(
            f'{API.PROGRESS_URL_PREFIX}{API.GET_PROGRESS_ROUTE.replace("<int:progress_id>", "999")}',
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.NOT_FOUND)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.PROGRESS_NOT_FOUND)

    def test_get_user_progress(self):
        # Create a progress entry first
        progress = Progress(
            user_id=self.trainee.id,
            workout_id=self.workout.id,
            value=10.5,
            date=datetime.utcnow().date(),
            notes='Test progress notes'
        )
        db.session.add(progress)
        db.session.commit()
        
        response = self.client.get(
            f'{API.PROGRESS_URL_PREFIX}{API.GET_USER_PROGRESS_ROUTE}',
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainee_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.OK)
        data = json.loads(response.data)
        self.assertEqual(len(data['progress']), 1)
        self.assertEqual(data['progress'][0][Database.VALUE_KEY], 10.5)
        self.assertEqual(data['progress'][0][Database.DESCRIPTION_KEY], 'Test progress notes')
        self.assertEqual(data['progress'][0]['workout'][Database.ID_KEY], self.workout.id)

    def test_get_user_progress_as_trainer(self):
        # Create a progress entry for the trainer
        progress = Progress(
            user_id=self.trainer.id,
            workout_id=self.workout.id,
            value=15.0,
            date=datetime.utcnow().date(),
            notes='Trainer progress notes'
        )
        db.session.add(progress)
        db.session.commit()
        
        response = self.client.get(
            f'{API.PROGRESS_URL_PREFIX}{API.GET_USER_PROGRESS_ROUTE}',
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.OK)
        data = json.loads(response.data)
        self.assertEqual(len(data['progress']), 1)
        self.assertEqual(data['progress'][0][Database.VALUE_KEY], 15.0)
        self.assertEqual(data['progress'][0][Database.DESCRIPTION_KEY], 'Trainer progress notes')
        self.assertEqual(data['progress'][0]['workout'][Database.ID_KEY], self.workout.id)

if __name__ == '__main__':
    unittest.main()
