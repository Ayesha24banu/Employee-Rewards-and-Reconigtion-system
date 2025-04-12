from flask_mysqldb import MySQL
from flask import g
from hash_password import hash_password
import MySQLdb.cursors
import os

def get_db():
    if 'db' not in g:
        g.db = MySQLdb.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'xxxxxxxxxxxxx'),
            password=os.getenv('MYSQL_PASSWORD', 'Axxxxxxxxxx'),
            db=os.getenv('MYSQL_DB', 'employee_reward'),
            charset='utf8mb4',
            cursorclass=MySQLdb.cursors.DictCursor
        )
    return g.db
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def insert_db(query, args=()):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(query, args)
        db.commit()
    except Exception as e:
        db.rollback()  # Rollback in case of error
        print(f"Error inserting data: {e}")
    finally:
        cursor.close()

def update_db(query, args=()):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(query, args)
        db.commit()
    except Exception as e:
        db.rollback()  # Rollback in case of error
        print(f"Error inserting data: {e}")
    finally:
        cursor.close()

def query_db(query, args=(), one=False):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(query, args)
    rv = cursor.fetchall()
    cursor.close()
    return (rv[0] if rv else None) if one else rv

def get_top_scorers():
    query = '''
    SELECT u.username, SUM(t.points_send) as total_points_received
    FROM user u
    JOIN transaction t ON u.email_id = t.receiver_email
    GROUP BY u.username
    ORDER BY total_points_received DESC
    LIMIT 20
    '''
    return query_db(query)

def get_most_sending_users():
    query = '''
    SELECT u.username, COUNT(t.points_send) as send_count
    FROM user u
    JOIN transaction t ON u.email_id = t.sender_email
    GROUP BY u.username
    ORDER BY send_count DESC
    LIMIT 20
    '''
    return query_db(query)

def create_admin_user():
    admin_username = "admin"
    admin_password = hash_password("admin123")
    admin_email = "admin@gmail.com"
    picture = "default_admin.jpg"  # Example image file name for the profile picture

    # Check if the admin user already exists to avoid duplicate entries
    existing_admin = query_db('SELECT * FROM user WHERE username = %s', (admin_username,), one=True)
    if not existing_admin:
    # Assuming you have a function `insert_db` to insert into the database
        insert_db('''INSERT INTO user (username, password, picture, first_name, last_name, email_id, department, manager, manager_points, available_points, is_admin)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                 (admin_username, admin_password, picture, 'Ayesha', 'Banu', admin_email, 'Admin', 'no', 0, 0, True))
        print("Admin user created successfully.")
    else:
        print("Admin user already exists.")



