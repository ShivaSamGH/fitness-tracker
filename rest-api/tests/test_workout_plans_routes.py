import unittest
import json
from app import create_app, db
from constants import USERNAME_KEY, PASSWORD_KEY, ROLE_KEY, Database, UserRole, TestData, AppConfig, API, StatusCode, Message, JWT
from models.user import User
from models.workout import Workout
from models.workout_plan import WorkoutPlan
from models.group import Group
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = AppConfig.TEST_DB_URI

class WorkoutPlansRoutesTestCase(unittest.TestCase):
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
        
        # Create a test group
        self.group = Group(
            name='Test Group',
            description='Test Group Description',
            trainer_id=self.trainer.id,
            invite_code='test123'
        )
        db.session.add(self.group)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_workout_plan_success(self):
        response = self.client.post(
            f'{API.WORKOUT_PLANS_URL_PREFIX}{API.CREATE_WORKOUT_PLAN_ROUTE}',
            data=json.dumps({
                Database.NAME_KEY: 'Test Workout Plan',
                Database.DESCRIPTION_KEY: 'Test workout plan description'
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.CREATED)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.WORKOUT_PLAN_CREATED)
        self.assertEqual(data['workout_plan'][Database.NAME_KEY], 'Test Workout Plan')
        self.assertEqual(data['workout_plan'][Database.DESCRIPTION_KEY], 'Test workout plan description')

    def test_create_workout_plan_unauthorized_role(self):
        response = self.client.post(
            f'{API.WORKOUT_PLANS_URL_PREFIX}{API.CREATE_WORKOUT_PLAN_ROUTE}',
            data=json.dumps({
                Database.NAME_KEY: 'Test Workout Plan',
                Database.DESCRIPTION_KEY: 'Test workout plan description'
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainee_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.UNAUTHORIZED)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.UNAUTHORIZED_ROLE)

    def test_create_workout_plan_missing_fields(self):
        response = self.client.post(
            f'{API.WORKOUT_PLANS_URL_PREFIX}{API.CREATE_WORKOUT_PLAN_ROUTE}',
            data=json.dumps({
                # Missing name
                Database.DESCRIPTION_KEY: 'Test workout plan description'
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.BAD_REQUEST)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.MISSING_FIELDS)

    def test_get_workout_plans(self):
        # Create a workout plan first
        workout_plan = WorkoutPlan(
            name='Test Workout Plan',
            description='Test workout plan description',
            trainer_id=self.trainer.id
        )
        db.session.add(workout_plan)
        db.session.commit()
        
        response = self.client.get(
            f'{API.WORKOUT_PLANS_URL_PREFIX}{API.CREATE_WORKOUT_PLAN_ROUTE}',
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.OK)
        data = json.loads(response.data)
        self.assertEqual(len(data['workout_plans']), 1)
        self.assertEqual(data['workout_plans'][0][Database.NAME_KEY], 'Test Workout Plan')
        self.assertEqual(data['workout_plans'][0][Database.DESCRIPTION_KEY], 'Test workout plan description')

    def test_get_workout_plan_success(self):
        # Create a workout plan first
        workout_plan = WorkoutPlan(
            name='Test Workout Plan',
            description='Test workout plan description',
            trainer_id=self.trainer.id
        )
        db.session.add(workout_plan)
        db.session.commit()
        
        response = self.client.get(
            f'{API.WORKOUT_PLANS_URL_PREFIX}{API.GET_WORKOUT_PLAN_ROUTE.replace("<int:workout_plan_id>", str(workout_plan.id))}',
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.OK)
        data = json.loads(response.data)
        self.assertEqual(data['workout_plan'][Database.NAME_KEY], 'Test Workout Plan')
        self.assertEqual(data['workout_plan'][Database.DESCRIPTION_KEY], 'Test workout plan description')

    def test_get_workout_plan_not_found(self):
        response = self.client.get(
            f'{API.WORKOUT_PLANS_URL_PREFIX}{API.GET_WORKOUT_PLAN_ROUTE.replace("<int:workout_plan_id>", "999")}',
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.NOT_FOUND)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.WORKOUT_PLAN_NOT_FOUND)

    def test_add_workout_to_plan_success(self):
        # Create a workout plan first
        workout_plan = WorkoutPlan(
            name='Test Workout Plan',
            description='Test workout plan description',
            trainer_id=self.trainer.id
        )
        db.session.add(workout_plan)
        db.session.commit()
        
        response = self.client.post(
            f'{API.WORKOUT_PLANS_URL_PREFIX}{API.ADD_WORKOUT_TO_PLAN_ROUTE.replace("<int:workout_plan_id>", str(workout_plan.id))}',
            data=json.dumps({
                Database.WORKOUT_ID_KEY: self.workout.id,
                Database.ORDER_KEY: 1
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.OK)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.WORKOUT_ADDED_TO_PLAN)
        
        # Verify the workout was added to the plan
        response = self.client.get(
            f'{API.WORKOUT_PLANS_URL_PREFIX}{API.GET_WORKOUT_PLAN_ROUTE.replace("<int:workout_plan_id>", str(workout_plan.id))}',
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        data = json.loads(response.data)
        self.assertEqual(len(data['workout_plan']['workouts']), 1)
        self.assertEqual(data['workout_plan']['workouts'][0]['workout'][Database.ID_KEY], self.workout.id)
        self.assertEqual(data['workout_plan']['workouts'][0]['order'], 1)

    def test_add_workout_to_plan_unauthorized_role(self):
        # Create a workout plan first
        workout_plan = WorkoutPlan(
            name='Test Workout Plan',
            description='Test workout plan description',
            trainer_id=self.trainer.id
        )
        db.session.add(workout_plan)
        db.session.commit()
        
        response = self.client.post(
            f'{API.WORKOUT_PLANS_URL_PREFIX}{API.ADD_WORKOUT_TO_PLAN_ROUTE.replace("<int:workout_plan_id>", str(workout_plan.id))}',
            data=json.dumps({
                Database.WORKOUT_ID_KEY: self.workout.id,
                Database.ORDER_KEY: 1
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainee_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.UNAUTHORIZED)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.UNAUTHORIZED_ROLE)

    def test_add_workout_to_plan_missing_fields(self):
        # Create a workout plan first
        workout_plan = WorkoutPlan(
            name='Test Workout Plan',
            description='Test workout plan description',
            trainer_id=self.trainer.id
        )
        db.session.add(workout_plan)
        db.session.commit()
        
        response = self.client.post(
            f'{API.WORKOUT_PLANS_URL_PREFIX}{API.ADD_WORKOUT_TO_PLAN_ROUTE.replace("<int:workout_plan_id>", str(workout_plan.id))}',
            data=json.dumps({
                Database.WORKOUT_ID_KEY: self.workout.id
                # Missing order
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.BAD_REQUEST)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.MISSING_FIELDS)

    def test_assign_plan_to_group_success(self):
        # Create a workout plan first
        workout_plan = WorkoutPlan(
            name='Test Workout Plan',
            description='Test workout plan description',
            trainer_id=self.trainer.id
        )
        db.session.add(workout_plan)
        db.session.commit()
        
        response = self.client.post(
            f'{API.WORKOUT_PLANS_URL_PREFIX}{API.ASSIGN_PLAN_TO_GROUP_ROUTE.replace("<int:workout_plan_id>", str(workout_plan.id))}',
            data=json.dumps({
                Database.GROUP_ID_KEY: self.group.id
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.OK)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.PLAN_ASSIGNED_TO_GROUP)
        
        # Verify the plan was assigned to the group
        workout_plan = WorkoutPlan.query.get(workout_plan.id)
        self.assertEqual(len(workout_plan.groups), 1)
        self.assertEqual(workout_plan.groups[0].id, self.group.id)

    def test_assign_plan_to_group_unauthorized_role(self):
        # Create a workout plan first
        workout_plan = WorkoutPlan(
            name='Test Workout Plan',
            description='Test workout plan description',
            trainer_id=self.trainer.id
        )
        db.session.add(workout_plan)
        db.session.commit()
        
        response = self.client.post(
            f'{API.WORKOUT_PLANS_URL_PREFIX}{API.ASSIGN_PLAN_TO_GROUP_ROUTE.replace("<int:workout_plan_id>", str(workout_plan.id))}',
            data=json.dumps({
                Database.GROUP_ID_KEY: self.group.id
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainee_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.UNAUTHORIZED)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.UNAUTHORIZED_ROLE)

    def test_assign_plan_to_group_missing_fields(self):
        # Create a workout plan first
        workout_plan = WorkoutPlan(
            name='Test Workout Plan',
            description='Test workout plan description',
            trainer_id=self.trainer.id
        )
        db.session.add(workout_plan)
        db.session.commit()
        
        response = self.client.post(
            f'{API.WORKOUT_PLANS_URL_PREFIX}{API.ASSIGN_PLAN_TO_GROUP_ROUTE.replace("<int:workout_plan_id>", str(workout_plan.id))}',
            data=json.dumps({}),  # Missing group_id
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.BAD_REQUEST)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.MISSING_FIELDS)

if __name__ == '__main__':
    unittest.main()
