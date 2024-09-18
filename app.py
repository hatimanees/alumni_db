from flask import Flask, render_template, request, redirect, url_for, session, Response
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'HTMLshow@1234',
    'database': 'alumni_db'
}

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465 # or 587 if using TLS
app.config['MAIL_USE_SSL'] = True  # Use True if using port 465
app.config['MAIL_USE_TLS'] = False  # Use True if using port 587
app.config['MAIL_USERNAME'] = 'hatim.anees@bbadsh.christuniversity.in'
app.config['MAIL_PASSWORD'] = 'htmlshow'
app.config['MAIL_DEFAULT_SENDER'] = 'hatim.anees@bbadsh.christuniversity.in'

mail = Mail(app)


# Database connection
def create_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error: {e}")
    return None

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = user['username']
            session['role'] = user['role']
            session['user_id'] = user['id']

            if user['role'] == 'alumni':
                return redirect(url_for('alumni_dashboard'))
            elif user['role'] == 'student':
                return redirect(url_for('student_dashboard'))
            elif user['role'] == 'faculty':
                return redirect(url_for('faculty_dashboard'))
            elif user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid credentials"

    return render_template('login.html')

def generate_reset_token(user_id):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return s.dumps(user_id, salt='password-reset-salt')

def verify_reset_token(token):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        return None
    return user_id



def send_reset_email(email, token):
    reset_url = url_for('reset_password', token=token, _external=True)
    msg = Message('Password Reset Request', sender='noreply@example.com', recipients=[email])
    msg.body = f'''To reset your password, visit the following link:
   {reset_url}

   If you did not make this request, simply ignore this email.
   '''
    mail.send(msg)
@app.route('/request_reset', methods=['GET', 'POST'])
def request_reset():
    if request.method == 'POST':
        email = request.form['email']
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user:
            # Generate reset token and send email
            token = generate_reset_token(user['id'])
            send_reset_email(user['email'], token)
            return "An email has been sent with instructions to reset your password."
        else:
            return "Email does not exist."

    return render_template('request_reset.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user_id = verify_reset_token(token)
    if not user_id:
        return "Invalid or expired token."

    if request.method == 'POST':
        new_password = request.form['password']
        # hashed_password = generate_password_hash(new_password)  # Hash the new password

        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute("UPDATE users SET password=%s WHERE id=%s", (new_password, user_id))
        conn.commit()

        return "Your password has been reset."

    return render_template('reset_password.html')

# Alumni Dashboard
@app.route('/alumni_dashboard')
def alumni_dashboard():
    if session.get('role') != 'alumni':
        return "Unauthorized Access", 403

    alumni_id = session.get('user_id')
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM alumni WHERE alumni_id = %s", (alumni_id,))
    alumni = cursor.fetchone()
    return render_template('alumni.html', data=get_alumni_data(),alumni=alumni)


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    alumni_id = session.get('user_id')
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        # Retrieve form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        graduation_year = request.form['graduation_year']
        degree = request.form['degree']
        department = request.form['department']
        current_employer = request.form['current_employer']
        job_title = request.form['job_title']
        location = request.form['location']
        linkedin_profile = request.form['linkedin_profile']
        biography = request.form['biography']

        # Handle file upload for profile picture
        profile_picture = request.files['profile_picture']  # Get the file from the form
        profile_picture_data = None
        if profile_picture:
            profile_picture_data = profile_picture.read()  # Read the image as binary

        # Check if alumni record exists
        cursor.execute("SELECT * FROM alumni WHERE alumni_id = %s", (alumni_id,))
        existing_record = cursor.fetchone()

        if existing_record:
            # Update the existing alumni record
            if profile_picture_data:
                cursor.execute("""
                    UPDATE alumni
                    SET first_name=%s, last_name=%s, email=%s, phone_number=%s, 
                        graduation_year=%s, degree=%s, department=%s, 
                        current_employer=%s, job_title=%s, location=%s, 
                        linkedin_profile=%s, profile_picture=%s, biography=%s
                    WHERE alumni_id=%s
                """, (
                    first_name, last_name, email, phone_number,
                    graduation_year, degree, department,
                    current_employer, job_title, location,
                    linkedin_profile, profile_picture_data, biography, alumni_id
                ))
            else:
                # If no new picture, update other fields without changing profile picture
                cursor.execute("""
                    UPDATE alumni
                    SET first_name=%s, last_name=%s, email=%s, phone_number=%s, 
                        graduation_year=%s, degree=%s, department=%s, 
                        current_employer=%s, job_title=%s, location=%s, 
                        linkedin_profile=%s, profile_picture=%s,biography=%s
                    WHERE alumni_id=%s
                """, (
                    first_name, last_name, email, phone_number,
                    graduation_year, degree, department,
                    current_employer, job_title, location,
                    linkedin_profile,profile_picture_data, biography, alumni_id
                ))
        else:
            # Insert a new alumni record
            cursor.execute("""
                INSERT INTO alumni (alumni_id, first_name, last_name, email, phone_number, 
                                    graduation_year, degree, department, current_employer, 
                                    job_title, location, linkedin_profile, profile_picture, 
                                    biography)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                alumni_id, first_name, last_name, email, phone_number,
                graduation_year, degree, department, current_employer,
                job_title, location, linkedin_profile, profile_picture_data, biography
            ))

        conn.commit()
        return redirect(url_for('alumni_dashboard'))

    # Fetch the current profile data (if it exists)
    cursor.execute("SELECT * FROM alumni WHERE alumni_id = %s", (alumni_id,))
    alumni = cursor.fetchone()

    return render_template('alumni_edit_profile.html', alumni=alumni)

@app.route('/profile_picture/<int:alumni_id>')
def get_profile_picture(alumni_id):
    conn = create_connection()
    cursor = conn.cursor()

    # Fetch the profile picture BLOB for the given alumni_id
    cursor.execute("SELECT profile_picture FROM alumni WHERE alumni_id = %s", (alumni_id,))
    row = cursor.fetchone()

    if row and row[0]:
        profile_picture_data = row[0]
        # Send the image data as a response
        return Response(profile_picture_data, mimetype='image/jpeg')  # Assuming the image is a JPEG
    else:
        # Return a placeholder image or handle cases with no profile picture
        return redirect(url_for('static', filename='images/default-profile.png'))  # Example placeholder image

@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if session.get('role') != 'alumni':
        return "Unauthorized Access", 403

    if request.method == 'POST':
        title = request.form['title']
        company = request.form['company']
        location = request.form['location']
        pre_requisites = request.form['pre_requisites']
        alumni_id = session.get('user_id')

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO jobs (title, company, location, pre_requisites, status, alumni_id)
            VALUES (%s, %s, %s, %s, 'pending', %s)
        """, (title, company, location, pre_requisites, alumni_id))
        conn.commit()
        return redirect(url_for('alumni_dashboard'))

    return render_template('alumni-job.html')



@app.route('/post_internship', methods=['GET', 'POST'])
def post_internship():
    if session.get('role') != 'alumni':
        return "Unauthorized Access", 403

    if request.method == 'POST':
        title = request.form['title']
        company = request.form['company']
        location = request.form['location']
        pre_requisites = request.form['pre_requisites']
        alumni_id = session.get('user_id')

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO internships (title, company, location, pre_requisites, status, alumni_id)
            VALUES (%s, %s, %s, %s, 'pending', %s)
        """, (title, company, location, pre_requisites, alumni_id))
        conn.commit()
        return redirect(url_for('alumni_dashboard'))

    return render_template('alumni-internship.html')


@app.route('/events')
def events():
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    return render_template('alumni-events.html', events=events)

@app.route('/apply_event', methods=['POST'])
def apply_event():
    if session.get('role') != 'alumni':
        return "Unauthorized Access", 403

    event_id = request.form['event_id']
    note = request.form.get('note', '')
    alumni_id = session.get('user_id')

    conn = create_connection()
    cursor = conn.cursor(dictionary=True)


    cursor.execute("""
        INSERT INTO event_applications (alumni_id, event_id,note)
        VALUES (%s, %s, %s)
     """, (alumni_id, event_id,note))
    conn.commit()
    return redirect(url_for('alumni_dashboard'))


@app.route('/my_event_applications')
def my_event_applications():
    if session.get('role') != 'alumni':
        return "Unauthorized Access", 403

    alumni_id = session.get('user_id')
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT ea.id, e.title, ea.note, ea.event_application_status
        FROM event_applications ea
        JOIN events e ON ea.event_id = e.id
        WHERE ea.alumni_id = %s
    """, (alumni_id,))
    applications = cursor.fetchall()

    return render_template('my_event_applications.html', applications=applications)

@app.route('/alumni_projects')
def alumni_projects():
    if session.get('role') != 'alumni':
        return "Unauthorized Access", 403

    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()
    return render_template('alumni_projects.html', projects=projects)

@app.route('/view_internship_applications')
def view_internship_applications():
    if session.get('role') != 'alumni':
        return "Unauthorized Access", 403

    alumni_id = session.get('user_id')  # Get the alumni user ID from the session

    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch all internship applications for the internships posted by this alumni
    cursor.execute("""
        SELECT ia.id, u.username AS student_name, ia.application_text, i.title,ia.internship_application_status AS internship_title
        FROM internship_applications ia
        JOIN users u ON ia.student_id = u.id
        JOIN internships i ON ia.internship_id = i.id
        WHERE ia.alumni_id = %s
    """, (alumni_id,))
    applications = cursor.fetchall()

    return render_template('view_internship_applications.html', applications=applications)


@app.route('/update_internship_application_status/<int:application_id>/<string:status>', methods=['POST'])
def update_internship_application_status(application_id, status):
    if session.get('role') != 'alumni':
        return "Unauthorized Access", 403

    if status not in ['approved', 'rejected']:
        return "Invalid status", 400

    conn = create_connection()
    cursor = conn.cursor()

    # Update the application status
    cursor.execute("""
        UPDATE internship_applications
        SET internship_application_status = %s
        WHERE id = %s
    """, (status, application_id))

    conn.commit()
    return redirect(url_for('view_internship_applications'))


@app.route('/view_job_applications')
def view_job_applications():
    if session.get('role') != 'alumni':
        return "Unauthorized Access", 403

    alumni_id = session.get('user_id')  # Get the alumni user ID from the session

    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch all job applications for the jobs posted by this alumni
    cursor.execute("""
        SELECT ja.id, u.username AS student_name, ja.application_text, j.title,ja.job_application_status AS job_title
        FROM jobs_applications ja
        JOIN users u ON ja.student_id = u.id
        JOIN jobs j ON ja.job_id = j.id
        WHERE ja.alumni_id = %s
    """, (alumni_id,))
    applications = cursor.fetchall()

    return render_template('view_job_applications.html', applications=applications)


@app.route('/update_job_application_status/<int:application_id>/<string:status>', methods=['POST'])
def update_job_application_status(application_id, status):
    if session.get('role') != 'alumni':
        return "Unauthorized Access", 403

    if status not in ['approved', 'rejected']:
        return "Invalid status", 400

    conn = create_connection()
    cursor = conn.cursor()

    # Update the job application status
    cursor.execute("""
        UPDATE jobs_applications
        SET job_application_status = %s
        WHERE id = %s
    """, (status, application_id))

    conn.commit()
    return redirect(url_for('view_job_applications'))


# Admin approval route
@app.route('/admin_approve/<type>/<id>')
def admin_approve(type, id):
    if session.get('role') != 'admin':
        return "Unauthorized Access", 403

    conn = create_connection()
    cursor = conn.cursor()
    table = 'jobs' if type == 'job' else 'internships'
    cursor.execute(f"UPDATE {table} SET status = 'approved' WHERE id = %s", (id,))
    conn.commit()
    return redirect(url_for('admin_dashboard'))  # Assuming there's an admin dashboard

# student dashboard
@app.route('/student_dashboard')
def student_dashboard():
    return render_template('student.html', data=get_alumni_data())

@app.route('/student_events')
def student_events():
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    return render_template('student-events.html', events=events)

@app.route('/jobs')
def jobs():
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM jobs WHERE status = 'approved'")
    jobs = cursor.fetchall()
    return render_template('student-jobs.html', jobs=jobs)

@app.route('/apply_job', methods=['POST'])
def apply_job():
    if session.get('role') != 'student':
        return "Unauthorized Access", 403

    job_id = request.form['job_id']  # Retrieve job_id from the form
    application_text = request.form.get('application_text', '')
    student_id = session.get('user_id')

    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    # Retrieve alumni_id associated with the job
    cursor.execute("SELECT alumni_id FROM jobs WHERE id = %s AND status = 'approved'", (job_id,))
    job = cursor.fetchone()

    if job:
        alumni_id = job['alumni_id']
        cursor.execute("""
            INSERT INTO jobs_applications (student_id, job_id, alumni_id, application_text)
            VALUES (%s, %s, %s, %s)
        """, (student_id, job_id, alumni_id, application_text))
        conn.commit()
        return redirect(url_for('student_dashboard'))
    else:
        return "Job not found or not approved", 404

@app.route('/my_job_applications')
def my_job_applications():
    if session.get('role') != 'student':
        return "Unauthorized Access", 403

    student_id = session.get('user_id')
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT ja.id, j.title, ja.application_text,ja.job_application_status
        FROM jobs_applications ja
        JOIN jobs j ON ja.job_id = j.id
        WHERE ja.student_id = %s
    """, (student_id,))
    applications = cursor.fetchall()

    return render_template('my_job_applications.html', applications=applications)


@app.route('/internships')
def internships():
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM internships")
    internships = cursor.fetchall()
    return render_template('student-internships.html', internships=internships)


@app.route('/apply_internship', methods=['POST'])
def apply_internship():
    if session.get('role') != 'student':
        return "Unauthorized Access", 403

    internship_id = request.form['internship_id']  # Retrieve internship_id from the form
    application_text = request.form.get('application_text', '')
    student_id = session.get('user_id')

    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    # Retrieve alumni_id associated with the internship
    cursor.execute("SELECT alumni_id FROM internships WHERE id = %s AND status = 'approved'", (internship_id,))
    internship = cursor.fetchone()

    if internship:
        alumni_id = internship['alumni_id']
        cursor.execute("""
            INSERT INTO internship_applications (student_id, internship_id, alumni_id, application_text)
            VALUES (%s, %s, %s, %s)
        """, (student_id, internship_id, alumni_id, application_text))
        conn.commit()
        return redirect(url_for('student_dashboard'))
    else:
        return "Internship not found or not approved", 404



@app.route('/my_internship_applications')
def my_internship_applications():
    if session.get('role') != 'student':
        return "Unauthorized Access", 403

    student_id = session.get('user_id')
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT ia.id, i.title, ia.application_text,ia.internship_application_status
        FROM internship_applications ia
        JOIN internships i ON ia.internship_id = i.id
        WHERE ia.student_id = %s
    """, (student_id,))
    applications = cursor.fetchall()

    return render_template('my_internship_applications.html', applications=applications)


@app.route('/projects')
def projects():
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()
    return render_template('student-projects.html', projects=projects)



# Faculty dashboard
@app.route('/faculty_dashboard')
def faculty_dashboard():
    return render_template('faculty.html', data=get_alumni_data())

@app.route('/post_event', methods=['GET', 'POST'])
def post_event():
    if session.get('role') != 'faculty':
        return "Unauthorized Access", 403

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        location = request.form['location']
        faculty_id = session.get('user_id')

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events (faculty_id, title, description, date, location)
            VALUES (%s, %s, %s, %s, %s)
        """, (faculty_id, title, description, date, location))
        conn.commit()
        return redirect(url_for('faculty_dashboard'))

    return render_template('faculty-post-event.html')

@app.route('/view_event_applications')
def view_event_applications():
    if session.get('role') != 'faculty':
        return "Unauthorized Access", 403

    faculty_id = session.get('user_id')

    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT ea.id, u.username AS alumni_name, ea.note, e.title, ea.event_application_status
        FROM event_applications ea
        JOIN users u ON ea.alumni_id = u.id
        JOIN events e ON ea.event_id = e.id
        WHERE e.faculty_id = %s
    """, (faculty_id,))
    applications = cursor.fetchall()

    return render_template('view_event_applications.html', applications=applications)

@app.route('/update_event_application_status/<int:application_id>/<string:status>', methods=['POST'])
def update_event_application_status(application_id, status):
    if session.get('role') != 'faculty':
        return "Unauthorized Access", 403

    if status not in ['pending', 'coming']:
        return "Invalid status", 400

    conn = create_connection()
    cursor = conn.cursor()

    # Update the event application status
    cursor.execute("""
        UPDATE event_applications
        SET event_application_status = %s
        WHERE id = %s
    """, (status, application_id))

    conn.commit()
    return redirect(url_for('view_event_applications'))


@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin.html', data=get_alumni_data())

def get_alumni_data():
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM alumni")
    data = cursor.fetchall()
    conn.close()
    return data

if __name__ == "__main__":
    app.run(debug=True)
