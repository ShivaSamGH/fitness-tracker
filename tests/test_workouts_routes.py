import unittest
import json
from app import create_app, db
from constants import USERNAME_KEY, PASSWORD_KEY, ROLE_KEY, Database, UserRole, TestData, AppConfig, API, StatusCode, Message, JWT
from models.user import User
from models.workout import Workout
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = AppConfig.TEST_DB_URI

class WorkoutsRoutesTestCase(unittest.TestCase):
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

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_workout_success(self):
        response = self.client.post(
            f'{API.WORKOUTS_URL_PREFIX}{API.CREATE_WORKOUT_ROUTE}',
            data=json.dumps({
                Database.NAME_KEY: 'Test Workout',
                Database.EXERCISE_KEY: 'Push-ups',
                Database.DURATION_KEY: 30,
                Database.TYPE_KEY: 'Strength',
                Database.DESCRIPTION_KEY: 'Test workout description'
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.CREATED)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.WORKOUT_CREATED)
        self.assertEqual(data['workout'][Database.NAME_KEY], 'Test Workout')
        self.assertEqual(data['workout'][Database.EXERCISE_KEY], 'Push-ups')
        self.assertEqual(data['workout'][Database.DURATION_KEY], 30)
        self.assertEqual(data['workout'][Database.TYPE_KEY], 'Strength')
        self.assertEqual(data['workout'][Database.DESCRIPTION_KEY], 'Test workout description')

    def test_create_workout_unauthorized_role(self):
        response = self.client.post(
            f'{API.WORKOUTS_URL_PREFIX}{API.CREATE_WORKOUT_ROUTE}',
            data=json.dumps({
                Database.NAME_KEY: 'Test Workout',
                Database.EXERCISE_KEY: 'Push-ups',
                Database.DURATION_KEY: 30,
                Database.TYPE_KEY: 'Strength',
                Database.DESCRIPTION_KEY: 'Test workout description'
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainee_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.UNAUTHORIZED)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.UNAUTHORIZED_ROLE)

    def test_create_workout_missing_fields(self):
        response = self.client.post(
            f'{API.WORKOUTS_URL_PREFIX}{API.CREATE_WORKOUT_ROUTE}',
            data=json.dumps({
                Database.NAME_KEY: 'Test Workout',
                Database.EXERCISE_KEY: 'Push-ups',
                # Missing duration
                Database.TYPE_KEY: 'Strength',
                Database.DESCRIPTION_KEY: 'Test workout description'
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.BAD_REQUEST)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.MISSING_FIELDS)

    def test_get_workouts_as_trainer(self):
        # Create a workout first
        workout = Workout(
            name='Test Workout',
            exercise='Push-ups',
            duration=30,
            type='Strength',
            description='Test workout description',
            trainer_id=self.trainer.id
        )
        db.session.add(workout)
        db.session.commit()
        
        response = self.client.get(
            f'{API.WORKOUTS_URL_PREFIX}{API.CREATE_WORKOUT_ROUTE}',
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.OK)
        data = json.loads(response.data)
        self.assertEqual(len(data['workouts']), 1)
        self.assertEqual(data['workouts'][0][Database.NAME_KEY], 'Test Workout')
        self.assertEqual(data['workouts'][0][Database.EXERCISE_KEY], 'Push-ups')

    def test_get_workouts_as_trainee(self):
        # Create a workout first
        workout = Workout(
            name='Test Workout',
            exercise='Push-ups',
            duration=30,
            type='Strength',
            description='Test workout description',
            trainer_id=self.trainer.id
        )
        db.session.add(workout)
        db.session.commit()
        
        response = self.client.get(
            f'{API.WORKOUTS_URL_PREFIX}{API.CREATE_WORKOUT_ROUTE}',
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainee_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.OK)
        data = json.loads(response.data)
        self.assertEqual(len(data['workouts']), 1)  # Trainees can see all workouts
        self.assertEqual(data['workouts'][0][Database.NAME_KEY], 'Test Workout')

    def test_get_workout_success(self):
        # Create a workout first
        workout = Workout(
            name='Test Workout',
            exercise='Push-ups',
            duration=30,
            type='Strength',
            description='Test workout description',
            trainer_id=self.trainer.id
        )
        db.session.add(workout)
        db.session.commit()
        
        response = self.client.get(
            f'{API.WORKOUTS_URL_PREFIX}{API.GET_WORKOUT_ROUTE.replace("<int:workout_id>", str(workout.id))}',
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.OK)
        data = json.loads(response.data)
        self.assertEqual(data['workout'][Database.NAME_KEY], 'Test Workout')
        self.assertEqual(data['workout'][Database.EXERCISE_KEY], 'Push-ups')
        self.assertEqual(data['workout'][Database.DURATION_KEY], 30)
        self.assertEqual(data['workout'][Database.TYPE_KEY], 'Strength')
        self.assertEqual(data['workout'][Database.DESCRIPTION_KEY], 'Test workout description')

    def test_get_workout_not_found(self):
        response = self.client.get(
            f'{API.WORKOUTS_URL_PREFIX}{API.GET_WORKOUT_ROUTE.replace("<int:workout_id>", "999")}',
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.NOT_FOUND)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.WORKOUT_NOT_FOUND)

if __name__ == '__main__':
    unittest.main()
