import unittest
import json
from app import create_app, db
from constants import USERNAME_KEY, PASSWORD_KEY, ROLE_KEY, Database, UserRole, TestData, AppConfig, API, StatusCode, Message, JWT
from models.user import User
from models.group import Group
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = AppConfig.TEST_DB_URI

class GroupsRoutesTestCase(unittest.TestCase):
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

    def test_create_group_success(self):
        response = self.client.post(
            f'{API.GROUPS_URL_PREFIX}{API.CREATE_GROUP_ROUTE}',
            data=json.dumps({
                'name': 'Test Group',
                'description': 'Test Group Description'
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.CREATED)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.GROUP_CREATED)
        self.assertEqual(data['group']['name'], 'Test Group')
        self.assertEqual(data['group']['description'], 'Test Group Description')
        self.assertIn('invite_code', data['group'])

    def test_create_group_unauthorized_role(self):
        response = self.client.post(
            f'{API.GROUPS_URL_PREFIX}{API.CREATE_GROUP_ROUTE}',
            data=json.dumps({
                'name': 'Test Group',
                'description': 'Test Group Description'
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainee_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.UNAUTHORIZED)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.UNAUTHORIZED_ROLE)

    def test_create_group_missing_fields(self):
        response = self.client.post(
            f'{API.GROUPS_URL_PREFIX}{API.CREATE_GROUP_ROUTE}',
            data=json.dumps({
                'description': 'Test Group Description'
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.BAD_REQUEST)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.MISSING_FIELDS)

    def test_join_group_success(self):
        # Create a group first
        group = Group(name='Test Group', description='Test Group Description', trainer_id=self.trainer.id, invite_code='test123')
        db.session.add(group)
        db.session.commit()
        
        response = self.client.post(
            f'{API.GROUPS_URL_PREFIX}{API.JOIN_GROUP_ROUTE}',
            data=json.dumps({
                'invite_code': 'test123'
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainee_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.OK)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.JOINED_GROUP)
        self.assertEqual(data['group']['name'], 'Test Group')

    def test_join_group_invalid_invite_code(self):
        response = self.client.post(
            f'{API.GROUPS_URL_PREFIX}{API.JOIN_GROUP_ROUTE}',
            data=json.dumps({
                'invite_code': 'invalid_code'
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainee_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.NOT_FOUND)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.INVALID_INVITE_CODE)

    def test_join_group_already_member(self):
        # Create a group first
        group = Group(name='Test Group', description='Test Group Description', trainer_id=self.trainer.id, invite_code='test123')
        db.session.add(group)
        group.members.append(self.trainee)
        db.session.commit()
        
        response = self.client.post(
            f'{API.GROUPS_URL_PREFIX}{API.JOIN_GROUP_ROUTE}',
            data=json.dumps({
                'invite_code': 'test123'
            }),
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainee_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.CONFLICT)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.ALREADY_MEMBER)

    def test_generate_invite_success(self):
        # Create a group first
        group = Group(name='Test Group', description='Test Group Description', trainer_id=self.trainer.id, invite_code='test123')
        db.session.add(group)
        db.session.commit()
        
        response = self.client.post(
            f'{API.GROUPS_URL_PREFIX}{API.GROUP_INVITE_ROUTE.replace("<int:group_id>", str(group.id))}',
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.OK)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.INVITE_CREATED)
        self.assertIn('invite_code', data)
        self.assertNotEqual(data['invite_code'], 'test123')  # New invite code should be different

    def test_generate_invite_unauthorized_role(self):
        # Create a group first
        group = Group(name='Test Group', description='Test Group Description', trainer_id=self.trainer.id, invite_code='test123')
        db.session.add(group)
        db.session.commit()
        
        response = self.client.post(
            f'{API.GROUPS_URL_PREFIX}{API.GROUP_INVITE_ROUTE.replace("<int:group_id>", str(group.id))}',
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainee_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.UNAUTHORIZED)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.UNAUTHORIZED_ROLE)

    def test_generate_invite_group_not_found(self):
        response = self.client.post(
            f'{API.GROUPS_URL_PREFIX}{API.GROUP_INVITE_ROUTE.replace("<int:group_id>", "999")}',
            content_type=API.CONTENT_TYPE_JSON,
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.NOT_FOUND)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.GROUP_NOT_FOUND)

    def test_get_members_success(self):
        # Create a group first
        group = Group(name='Test Group', description='Test Group Description', trainer_id=self.trainer.id, invite_code='test123')
        db.session.add(group)
        group.members.append(self.trainee)
        db.session.commit()
        
        response = self.client.get(
            f'{API.GROUPS_URL_PREFIX}{API.GROUP_MEMBERS_ROUTE.replace("<int:group_id>", str(group.id))}',
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.OK)
        data = json.loads(response.data)
        self.assertEqual(len(data['members']), 1)
        self.assertEqual(data['members'][0]['username'], TestData.TRAINEE_USERNAME)

    def test_get_members_group_not_found(self):
        response = self.client.get(
            f'{API.GROUPS_URL_PREFIX}{API.GROUP_MEMBERS_ROUTE.replace("<int:group_id>", "999")}',
            headers={'Cookie': f'{JWT.COOKIE_NAME}={self.trainer_token}'}
        )
        self.assertEqual(response.status_code, StatusCode.NOT_FOUND)
        data = json.loads(response.data)
        self.assertEqual(data['message'], Message.GROUP_NOT_FOUND)

if __name__ == '__main__':
    unittest.main()
