from dotenv import load_dotenv
import os

load_dotenv()
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', '\x0f\x0e\x8f\x96\xfaaX+\xbc\x9d+\xbb5\xc9Lo')
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'Ayesha@990')
    MYSQL_DB = os.getenv('MYSQL_DB', 'employee_reward')
    MYSQL_CURSORCLASS = 'DictCursor'
    FLASK_DEBUG = os.getenv('FLASK_DEBUG')
    
    # Email configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') 
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'aneesayesha35@gmail.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'sqei eioy bjcc wywu ')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'aneesayesha35@gmail.com')
    
    # Security
    SECURITY_PASSWORD_SALT = os.getenv('SECURITY_PASSWORD_SALT', '04626b2326b3f38b44ab76a08dbc8bdb')

class TestConfig(Config):
    MYSQL_DB = 'test_employee_reward'
    TESTING = True


