import unittest
import json
from app import create_app, db
from constants import USERNAME_KEY, PASSWORD_KEY, ROLE_KEY, Database, UserRole, TestData, AppConfig, API, StatusCode, Message, JWT
from models.user import User
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = AppConfig.TEST_DB_URI

class AuthRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_signup_success(self):
        response = self.client.post(
            f'{API.AUTH_URL_PREFIX}{API.SIGNUP_ROUTE}',
            data=json.dumps({
                USERNAME_KEY: TestData.TRAINER_USERNAME,
                PASSWORD_KEY: TestData.PASSWORD_123,
                ROLE_KEY: UserRole.TRAINER
            }),
            content_type=API.CONTENT_TYPE_JSON
        )
        self.assertEqual(response.status_code, StatusCode.CREATED)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.USER_CREATED)
        self.assertEqual(data['user'][USERNAME_KEY], TestData.TRAINER_USERNAME)
        self.assertEqual(data['user'][ROLE_KEY], UserRole.TRAINER)
        response = self.client.post(
            f'{API.AUTH_URL_PREFIX}{API.SIGNUP_ROUTE}',
            data=json.dumps({
                USERNAME_KEY: TestData.TRAINEE_USERNAME,
                PASSWORD_KEY: TestData.PASSWORD_123,
                ROLE_KEY: UserRole.TRAINEE
            }),
            content_type=API.CONTENT_TYPE_JSON
        )
        self.assertEqual(response.status_code, StatusCode.CREATED)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.USER_CREATED)
        self.assertEqual(data['user'][USERNAME_KEY], TestData.TRAINEE_USERNAME)
        self.assertEqual(data['user'][ROLE_KEY], UserRole.TRAINEE)

    def test_signup_invalid_role(self):
        response = self.client.post(
            f'{API.AUTH_URL_PREFIX}{API.SIGNUP_ROUTE}',
            data=json.dumps({
                USERNAME_KEY: TestData.USER_USERNAME,
                PASSWORD_KEY: TestData.PASSWORD_123,
                ROLE_KEY: UserRole.INVALID_ROLE
            }),
            content_type=API.CONTENT_TYPE_JSON
        )
        self.assertEqual(response.status_code, StatusCode.BAD_REQUEST)
        data = json.loads(response.data)
        self.assertIn(Message.INVALID_ROLE, data['message'])

    def test_signup_duplicate_username(self):
        user = User(username=TestData.EXISTING_USERNAME, password=TestData.PASSWORD_123, role=UserRole.TRAINER)
        db.session.add(user)
        db.session.commit()
        response = self.client.post(
            f'{API.AUTH_URL_PREFIX}{API.SIGNUP_ROUTE}',
            data=json.dumps({
                USERNAME_KEY: TestData.EXISTING_USERNAME,
                PASSWORD_KEY: TestData.PASSWORD_123,
                ROLE_KEY: UserRole.TRAINER
            }),
            content_type=API.CONTENT_TYPE_JSON
        )
        self.assertEqual(response.status_code, StatusCode.CONFLICT)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.USERNAME_EXISTS)

    def test_signin_success(self):
        user = User(username=TestData.TEST_USER_USERNAME, password=TestData.PASSWORD_123, role=UserRole.TRAINER)
        db.session.add(user)
        db.session.commit()

        response = self.client.post(
            f'{API.AUTH_URL_PREFIX}{API.SIGNIN_ROUTE}',
            data=json.dumps({
                USERNAME_KEY: TestData.TEST_USER_USERNAME,
                PASSWORD_KEY: TestData.PASSWORD_123
            }),
            content_type=API.CONTENT_TYPE_JSON
        )
        self.assertEqual(response.status_code, StatusCode.OK)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.LOGIN_SUCCESSFUL)
        self.assertEqual(data['user'][USERNAME_KEY], TestData.TEST_USER_USERNAME)
        self.assertEqual(data['user'][ROLE_KEY], UserRole.TRAINER)
        self.assertIn(JWT.COOKIE_NAME, response.headers.getlist('Set-Cookie')[0])

    def test_signin_invalid_credentials(self):
        user = User(username=TestData.TEST_USER_USERNAME, password=TestData.PASSWORD_123, role=UserRole.TRAINER)
        db.session.add(user)
        db.session.commit()

        response = self.client.post(
            f'{API.AUTH_URL_PREFIX}{API.SIGNIN_ROUTE}',
            data=json.dumps({
                USERNAME_KEY: TestData.TEST_USER_USERNAME,
                PASSWORD_KEY: TestData.WRONG_PASSWORD
            }),
            content_type=API.CONTENT_TYPE_JSON
        )
        self.assertEqual(response.status_code, StatusCode.UNAUTHORIZED)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.INVALID_CREDENTIALS)
        response = self.client.post(
            f'{API.AUTH_URL_PREFIX}{API.SIGNIN_ROUTE}',
            data=json.dumps({
                USERNAME_KEY: TestData.NON_EXISTENT_USERNAME,
                PASSWORD_KEY: TestData.PASSWORD_123
            }),
            content_type=API.CONTENT_TYPE_JSON
        )
        self.assertEqual(response.status_code, StatusCode.UNAUTHORIZED)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.INVALID_CREDENTIALS)

if __name__ == '__main__':
    unittest.main()
