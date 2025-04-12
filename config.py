from dotenv import load_dotenv
import os

load_dotenv()
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'xxxxxx')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'xxxxxxxxxxxx')
    MYSQL_DB = os.getenv('MYSQL_DB', 'employee_reward')
    MYSQL_CURSORCLASS = 'DictCursor'
    FLASK_DEBUG = os.getenv('FLASK_DEBUG')
    
    # Email configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 'xxx'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') 
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'xxxxxxxxxxxx@gmail.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'xxxx xxxx xxxx xxxx ')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'xxxxxxxxx@gmail.com')
    
    # Security
    SECURITY_PASSWORD_SALT = os.getenv('SECURITY_PASSWORD_SALT', 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')

class TestConfig(Config):
    MYSQL_DB = 'test_employee_reward'
    TESTING = True


