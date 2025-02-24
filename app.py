from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from models import query_db, insert_db,get_top_scorers,get_most_sending_users, update_db, create_admin_user
import pandas as pd
import xlsxwriter
from io import BytesIO
import datetime
import os
from hash_password import hash_password, check_password
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, login_required,  logout_user, current_user
from werkzeug.utils import secure_filename

# Flask app initialization
app = Flask(__name__, static_folder='static')
app.config.from_object('config' if os.getenv('FLASK_DEBUG') != 'testing' else 'config.TestConfig')
app.config['SECRET_KEY'] =os.getenv('SECRET_KEY')  # Retrieve the secret key from environment variables
app.config['SECURITY_PASSWORD_SALT'] =os.getenv('SECURITY_PASSWORD_SALT')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS')
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_SSL')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Set the upload folder and allowed extensions
UPLOAD_FOLDER = 'static/uploads/profile_pictures'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Email configuration
mail = Mail(app)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, username, password, is_admin):
        self.username = username
        self.password = password
        self.is_admin = is_admin
 
    def get_id(self):
        return self.username
    
@login_manager.user_loader
def load_user(username):
    user = query_db('SELECT * FROM user WHERE username = %s', (username,), one=True)
    if user:
        return User(user['username'], user['password'], user['is_admin'])
    return None

# Ensure the admin user is created when the app starts
with app.app_context():
    create_admin_user()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    if request.method == 'POST':
        try:
             # Retrieve form data
            data = request.form
            password = hash_password(request.form['password'])
            is_manager = 'manager' in data and data['manager'] == 'yes'
            manager_points = 200 if is_manager else 0
            available_points = 150 if not is_manager else 0
            received_points = 0
            manager = 'yes' if is_manager else 'no'

            # Handle the profile picture
            if 'profile_picture' not in request.files:
                flash('No file part', 'error')
                return redirect(request.url)
            file = request.files['profile_picture']
            if file.filename == '':
                flash('No selected file', 'error')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                picture = filename
            else:
                flash('File type not allowed', 'error')
                return redirect(request.url)

            # Insert user data into the database
            insert_db('INSERT INTO user (username, password, picture, first_name, last_name, email_id, department, manager, manager_points, available_points, received_points) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s)',
                      (data['username'], password, picture, data['first_name'], data['last_name'], data['email_id'], data['department'], manager, manager_points, available_points, received_points))
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            return f"An error occurred: {e}"
    return render_template('sign_in.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            remember_me = 'remember_me' in request.form

            user = query_db('SELECT * FROM user WHERE username = %s', (username,), one=True)
            if user and check_password(user['password'], password):
                user_obj = User(user['username'], user['password'], user['is_admin']) 
                login_user(user_obj, remember=remember_me)
                session['user'] = user
                if user['is_admin']:
                   flash('Login successful!', 'success')
                   return redirect(url_for('admin'))
                return redirect(url_for('send_rewards'))
            else:
                flash('Invalid credentials. please try again.', 'error')
                return redirect(url_for('login'))
                
        except Exception as e:
            return f"An error occurred: {e}"
    return render_template('login.html')

# Password Reset
def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY' ])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except (BadSignature, SignatureExpired):
        return False
    return email
# Forgot password functionality
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email_id']
        user = query_db('SELECT * FROM user WHERE email_id = %s', (email,), one=True)
        if user:
            token =  generate_confirmation_token(email)
            reset_url = url_for('reset_password', token=token, _external=True)
            reset_password_email(email, reset_url)
            flash('A password reset link has been sent to your email.', 'info')
        else:
            flash('Email address not found.', 'error')
    return render_template('forgot_password.html')

# Reset password functionality
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = confirm_token(token)
    if not email:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        form_email = request.form['email_id']
        if form_email != email:
            flash('Email address does not match.', 'error')
            return render_template('reset_password.html', token=token)
        
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)
        hashed_password = hash_password(new_password)
        update_db('UPDATE user SET password = %s WHERE email_id = %s', (hashed_password, email))
        flash('Your password has been updated!', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

def reset_password_email(email, reset_url):
    subject = 'Password Reset Request'
    message = f'Please click the following link to reset your password: {reset_url}'
    msg = Message(subject, recipients=[email], body=message)
    mail.send(msg)

# User account route
@app.route('/user_account', methods=['GET'])
@login_required
def user_account():
    user = query_db('SELECT * FROM user WHERE username = %s', (current_user.get_id(),), one=True)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('login'))
    
    # Query redeem points from the redeem table
    redeem = query_db('SELECT redeem_points FROM redeem WHERE username = %s', (user['username'],), one=True)

    # Ensure redeem points are fetched correctly
    redeem_points = redeem['redeem_points'] if redeem else 0

    return render_template('user_account.html', user=user, redeem={'redeem_points': redeem_points})
   
# Update profile route
@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    # Get the current user information from the database
    user = query_db('SELECT * FROM user WHERE username = %s', (current_user.get_id(),), one=True)
    # Check if the user exists
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('login'))

    try:
        # Fetch form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email_id = request.form['email_id']
        department = request.form['department']
        
         # Log the incoming email to see if the form data is correct
        print(f"New email from form: {email_id}")
        print(f"Current email in DB: {user['email_id']}")

        # Check if the new email is already in use by another user
        existing_user = query_db('SELECT * FROM user WHERE email_id = %s AND username != %s', (email_id, current_user.get_id()), one=True)
        if existing_user:
            flash('The email is already in use by another account.', 'error')
            return redirect(url_for('user_account'))
        
        # Handle profile picture upload
        file = request.files['profile_picture']
        picture = user['picture']  # Default to current picture
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            picture = filename

        # Update user profile in the database
        update_db('UPDATE user SET picture = %s, first_name = %s, last_name = %s, email_id = %s, department = %s WHERE username = %s',
                  (picture, first_name, last_name, email_id, department, current_user.get_id()))

         # Re-check if the email update went through
        updated_user = query_db('SELECT * FROM user WHERE username = %s', (current_user.get_id(),), one=True)
        print(f"Updated email in DB after query: {updated_user['email_id']}")
        
        # Only update transactions and redeem table if the email has changed
        if email_id != user['email_id']:
            # Update transactions related to the old email
            update_db('UPDATE transaction SET sender_email = %s WHERE sender_email = %s', (email_id, user['email_id']))
            update_db('UPDATE transaction SET receiver_email = %s WHERE receiver_email = %s', (email_id, user['email_id']))

            # Update redeem entries related to the old email
            update_db('UPDATE redeem SET email_id = %s WHERE email_id = %s', (email_id, user['email_id'])) 

        flash('Profile updated successfully!', 'success')

    except Exception as e:
        print(f'Error occurred: {e}')  # Log the error to the console
        flash(f'An error occurred: {e}', 'error')

    return redirect(url_for('user_account'))

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    try:
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('user_account'))
        
        user = query_db('SELECT * FROM user WHERE username = %s', (current_user.get_id(),), one=True)
        if not user or not check_password(user['password'], current_password):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('user_account'))
        
        hashed_password = hash_password(new_password)
        update_db('UPDATE user SET password = %s WHERE username = %s', (hashed_password, current_user.get_id()))
        flash('Password changed successfully!', 'success')
    except Exception as e:
        flash(f'An error occurred: {e}', 'error')

    return redirect(url_for('user_account'))
       
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
   
    if 'user' not in session or not session['user'].get('is_admin', False):
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            if 'reset_points' in request.form:
                # Reset points for all users
                update_db('UPDATE user SET available_points = 150 WHERE manager = "no"')
                update_db('UPDATE user SET manager_points = 200 WHERE manager = "yes"')
                update_db('UPDATE user SET manager_points = 0, available_points = 0 WHERE is_admin = 1')
                flash('Points have been reset.', 'success')
                return redirect(url_for('admin'))

            elif 'manage_users' in request.form:
                return redirect(url_for('manage_users'))    
        except Exception as e:
            return f"An error occurred: {e}"
        
    transactions = query_db('SELECT * FROM transaction')
    redeem_data = query_db('SELECT * FROM redeem')
    user = session.get('user')  # Get user information from session

    return render_template('admin.html', transactions=transactions, redeem_data=redeem_data, user=user)

@app.route('/export_transactions', methods=['POST'])
def export_transactions():
     # Get month and year from the form
    month = request.form['month']
    year = request.form['year']
    # Validate month and year
    if not month or not year:
        flash('Month and Year are required.', 'error')
        return redirect(url_for('admin'))
    
    try:
        # Query transactions for the specified month and year
        transactions = query_db('SELECT * FROM transaction WHERE MONTH(date) = %s AND YEAR(date) = %s', (month, year))
        # Convert transactions to a DataFrame
        df = pd.DataFrame(transactions)
        if not df.empty:
         # Create a BytesIO buffer
            output = BytesIO()
        # Use xlsxwriter to write the Excel file
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Transactions')
            # Get the worksheet object
                worksheet = writer.sheets['Transactions']

            # Set the column widths to the maximum length in each column
                for idx, col in enumerate(df.columns):
                  max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2  # Adding a little extra space
                  worksheet.set_column(idx, idx, max_len)
        # Seek to the beginning of the stream
            output.seek(0)
        # Send the file to the client
            return send_file(output, download_name='transactions.xlsx', as_attachment=True)   
        else:
            flash('No transaction data found  for the specified month and year.', 'warning')
            return redirect(url_for('admin'))
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('admin'))
    

@app.route('/export_redeem_data', methods=['POST'])
def export_redeem_data():
    month = request.form['month']
    year = request.form['year']
    redeem_data = query_db('SELECT * FROM redeem WHERE redeem_points > 0 AND MONTH(date) = %s AND YEAR(date) = %s', (month, year))
    df = pd.DataFrame(redeem_data)
    if not df.empty:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Redeem Data')
            worksheet = writer.sheets['Redeem Data']

            # Set the column widths to the maximum length in each column
            for idx, col in enumerate(df.columns):
                max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2  # Adding a little extra space
                worksheet.set_column(idx, idx, max_len)
        output.seek(0)
        return send_file(output, download_name='redeem_data.xlsx', as_attachment=True)
    else:
        flash('No redeem data found for the specified month and year.', 'warning')
        return redirect(url_for('admin'))

@app.route('/manage_users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if 'user' not in session or not session['user'].get('is_admin', False):
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
       
            if 'delete_user' in request.form:
                username = request.form['original_username']
                user = query_db('SELECT email_id FROM user WHERE username = %s', (username,), one=True)
                if user:
                    try:
                        email_id = user['email_id']
                        # Set sender_email and receiver_email to NULL in transactions before deleting the user
                        update_db('UPDATE transaction SET sender_email = NULL WHERE sender_email = %s', (email_id,))
                        update_db('UPDATE transaction SET receiver_email = NULL WHERE receiver_email = %s', (email_id,))
                        
                        # Then delete the user
                        update_db('DELETE FROM user WHERE username = %s', (username,))
                        flash('User and related transactions deleted successfully.', 'success')
                    except Exception as e:
                         return f"An error occurred: {e}"
                else:
                    flash('User not found.', 'error') 

            elif 'update_user' in request.form:
                username = request.form['username']
                first_name = request.form['first_name']
                last_name = request.form['last_name']
                email_id = request.form['email_id']
                department = request.form['department']
                manager = request.form['manager']
                manager_points = request.form['manager_points']
                available_points = request.form['available_points']
                received_points = request.form['received_points']
                original_username = request.form['original_username']
                
                try:
                    # Check if the user has sent or received any points
                    user = query_db('SELECT * FROM user WHERE username = %s', (original_username,), one=True)
                    if user:
                        update_db('UPDATE user SET username = %s, first_name = %s, last_name = %s, email_id = %s, department = %s, manager = %s, manager_points = %s, available_points = %s, received_points = %s WHERE username = %s',
                                     (username, first_name, last_name, email_id, department, manager, manager_points, available_points, received_points, original_username))
                        flash('User updated successfully.', 'success')
                    else:
                        flash('User not found.', 'error')
                except Exception as e:
                    return f"An error occurred: {e}"

        except Exception as e:
            return f"An error occurred: {e}"

    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page

    if search:
        users = query_db('SELECT * FROM user WHERE username LIKE %s LIMIT %s OFFSET %s', (f'%{search}%', per_page, offset))
    else:
        users = query_db('SELECT * FROM user LIMIT %s OFFSET %s', (per_page, offset))


    return render_template('manage_users.html', users=users, page=page, per_page=per_page, len=len)


@app.route('/send_rewards', methods=['GET', 'POST'])
@login_required
def send_rewards():
    user = session.get('user')
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = session['user']
    # Fetch admin email dynamically from the database
    admin_info = query_db('SELECT email_id FROM user WHERE is_admin = 1', one=True)
    if admin_info:
        admin_email = admin_info['email_id']
    else:
        admin_email = None  # Handle the case where no admin is found

    # Fetch all other email IDs except the admin and current user
    all_emails = [user['email_id'] for user in query_db('SELECT email_id FROM user WHERE email_id != %s',(admin_email,))]
    all_emails.remove(user['email_id'])  # Remove sender's email from the list

    top_scorers = query_db( '''
    SELECT u.username, SUM(t.points_send) as received_points
    FROM user u
    JOIN transaction t ON u.email_id = t.receiver_email
    GROUP BY u.username
    ORDER BY received_points DESC
    LIMIT 3
    ''')
     # Calculate most sending users by aggregating the transaction table
    most_sending_users = query_db('''
        SELECT u.username, COUNT(t.sender_email) AS send_count
        FROM transaction t
        JOIN user u ON t.sender_email = u.email_id
        GROUP BY u.username
        ORDER BY send_count DESC
        LIMIT 3
    ''')

    if request.method == 'POST':
        try:
            sender_email = user['email_id']  # Corrected: use square brackets
            receiver_email = request.form['email_id']
            points_send = int(request.form['points_send'])
            comment = request.form['comment']
            date = datetime.datetime.now()
             
            if receiver_email == sender_email:
                flash('You cannot send points to yourself.', 'error')
                return redirect(url_for('send_rewards'))
            if receiver_email == admin_email:
                flash('You cannot send points to the admin.', 'error')
                return redirect(url_for('send_rewards'))
            
            # Check if the sender has enough points
            if user['manager'] == 'yes':
                manager_points = user['manager_points']
                new_sender_points = manager_points - points_send
                if new_sender_points < 0:
                    flash('Not enough available points to send.', 'warning')
                    return redirect(url_for('send_rewards'))
                update_db('UPDATE user SET manager_points = %s WHERE email_id = %s', (new_sender_points, sender_email))
            else:
                available_points = user['available_points']
                new_sender_points = available_points - points_send
                if new_sender_points < 0:
                    flash('Not enough available points to send.', 'warning')
                    return redirect(url_for('send_rewards'))
                update_db('UPDATE user SET available_points = %s WHERE email_id = %s', (new_sender_points, sender_email))

            # Update receiver's received points
            receiver = query_db('SELECT received_points FROM user WHERE email_id = %s', (receiver_email,), one=True)
            if not receiver:
                flash('Receiver not found.', 'error')
                return redirect(url_for('send_rewards'))
            new_receiver_points = receiver['received_points'] + points_send
            update_db('UPDATE user SET received_points = %s WHERE email_id = %s', (new_receiver_points, receiver_email))

            # Insert the transaction
            insert_db('INSERT INTO transaction (sender_email, receiver_email, points_send, date, comment) VALUES (%s, %s, %s, %s, %s)',
                      (sender_email, receiver_email, points_send, date, comment))

            # Update session
            if user['manager'] == 'yes':
                user['manager_points'] = new_sender_points
            else:
                user['available_points'] = new_sender_points
            session['user'] = user

            flash('Points sent successfully!', 'success')
            return redirect(url_for('send_rewards'))
        except Exception as e:
            return f"An error occurred: {e}"

    return render_template('send_rewards.html', user=user, all_emails=all_emails, top_scorers=top_scorers, most_sending_users=most_sending_users)
 
@app.route('/redeem_points', methods=['POST'])
@login_required
def redeem_points():
    user = session.get('user')
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session['user']
   
    try:
        redeem_points = int(request.form['redeem_points'])

        if redeem_points > user['received_points']:
            flash('You have entered more points than available.', 'warning')
            return redirect(url_for('send_rewards'))
        
        # Calculate new received points
        new_received_points = user['received_points'] - redeem_points

        # Update the received points in the user table
        update_db('UPDATE user SET received_points = %s WHERE email_id = %s',
                  (new_received_points, user['email_id']))
        
        
             # Insert a new record into the redeem table
        insert_db(
                'INSERT INTO redeem (username, email_id, redeem_points, date) VALUES (%s, %s, %s, NOW())',
                (user['username'], user['email_id'], redeem_points))
        
        # Update the user's session data
        user['received_points'] = new_received_points
        session['user'] = user
        
         # Send email to the user
        msg = Message(
            "Points Redeemed",
            recipients=[user['email_id']]
        )
        msg.body = f"Dear {user['username']},\n\nYou have successfully redeemed {redeem_points} points.\n\nHR will transfer the money within a few days.\n\nThank you!"
        mail.send(msg) 

        flash('Points have been successfully redeemed.', 'success')
        return redirect(url_for('send_rewards'))
    except Exception as e:
        return f"An error occurred: {e}"

@app.route('/leaderboard', methods=['GET'])
@login_required
def leaderboard():
    user = session.get('user')
    top_scorers= get_top_scorers()
    most_sending_users = get_most_sending_users()
    return render_template('leaderboard.html', top_scorers=top_scorers, most_sending_users=most_sending_users, is_admin=user['is_admin'])
    

@app.route('/logout')
@login_required
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

