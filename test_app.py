import unittest
from app import app, insert_db, query_db
from werkzeug.security import generate_password_hash
from flask import current_app

class test_app(unittest.TestCase):

    def setUp(self):
        app.config.from_object('config.TestConfig')
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        # Create tables
        insert_db('''
        CREATE TABLE IF NOT EXISTS user (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            email_id VARCHAR(100) NOT NULL UNIQUE,
            department VARCHAR(50) NOT NULL,
            manager ENUM('yes', 'no') NOT NULL,
            manager_points INT DEFAULT 0,
            available_points INT DEFAULT 0,
            is_admin BOOLEAN NOT NULL
        )''')

        insert_db('''
        CREATE TABLE IF NOT EXISTS transaction (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sender_email VARCHAR(100) NOT NULL,
            receiver_email VARCHAR(100) NOT NULL,
            points_send INT NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            comment TEXT,
            FOREIGN KEY (sender_email) REFERENCES user(email_id) ON DELETE CASCADE,
            FOREIGN KEY (receiver_email) REFERENCES user(email_id) ON DELETE CASCADE
        )''')

        # Add a test admin user
        hashed_password = generate_password_hash('$z6R9YAMGv9I5ZFWa$9b99a9b1898a42cc470509163f99b51011b282af8adfe3a623514466298f6c08399ad7d61bfbb6a0015361aa9b24942cd02ddaf736c823ca8178195659f179e7')
        insert_db('INSERT INTO user (username, password, first_name, last_name, email_id, department, manager, manager_points, available_points, is_admin) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                  ('admin',hashed_password , 'Admin', 'User', 'admin@example.com', 'Admin', 'no', 0, 0, True))

    def tearDown(self):
        # Drop tables
        insert_db('DROP TABLE IF EXISTS transaction')
        insert_db('DROP TABLE IF EXISTS user')
        self.app_context.pop()

    def test_sign_in(self):
        response = self.client.post('/sign_in', data={
            'username': 'testuser',
            'password': 'testpassword',
            'first_name': 'Test',
            'last_name': 'User',
            'email_id': 'test@example.com',
            'department': 'IT',
            'manager': 'no'
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)

    def test_login(self):
        response = self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin_password'
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('/send_rewards', response.location)

    def test_send_rewards(self):
        # Login as admin first
        self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin_password'
        })
        response = self.client.post('/send_rewards', data={
            'email': 'test@example.com',
            'points': '50',
            'comment': 'Great job!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('/send_rewards', response.location)

    def test_leaderboard(self):
        response = self.client.get('/leaderboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Admin', response.data)

    def test_admin_reset_points(self):
        # Login as admin first
        self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin_password'
        })
        response = self.client.post('/admin', data={'reset': 'reset'})
        self.assertEqual(response.status_code, 200)
        user = query_db('SELECT * FROM user WHERE username = %s', ('admin',), one=True)
        self.assertEqual(user['available_points'], 0)

if __name__ == '__main__':
    unittest.main()
