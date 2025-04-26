import unittest
from app import create_app, db
from constants import USERNAME_KEY, PASSWORD_KEY, ROLE_KEY, Database, UserRole, TestData, AppConfig
from models.user import User
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = AppConfig.TEST_DB_URI

class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username=TestData.TEST_USERNAME, password=TestData.PASSWORD, role=UserRole.TRAINER)
        self.assertTrue(u.check_password(TestData.PASSWORD))
        self.assertFalse(u.check_password(TestData.WRONG_PASSWORD))

    def test_user_creation(self):
        u = User(username=TestData.TEST_USERNAME, password=TestData.PASSWORD, role=UserRole.TRAINER)
        db.session.add(u)
        db.session.commit()

        retrieved_user = User.query.filter_by(username=TestData.TEST_USERNAME).first()
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.username, TestData.TEST_USERNAME)
        self.assertEqual(retrieved_user.role, UserRole.TRAINER)

    def test_to_dict(self):
        u = User(username=TestData.TEST_USERNAME, password=TestData.PASSWORD, role=UserRole.TRAINER)
        db.session.add(u)
        db.session.commit()

        user_dict = u.to_dict()
        self.assertEqual(user_dict[USERNAME_KEY], TestData.TEST_USERNAME)
        self.assertEqual(user_dict[ROLE_KEY], UserRole.TRAINER)
        self.assertIn(Database.ID_KEY, user_dict)
        self.assertIn(Database.CREATED_AT_KEY, user_dict)
        self.assertNotIn(Database.PASSWORD_HASH_KEY, user_dict)

if __name__ == '__main__':
    unittest.main()
