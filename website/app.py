from flask import Flask, render_template, url_for, request, flash, session, redirect, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
import bcrypt
from flask_mysqldb import MySQL

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
jwt = JWTManager(app)
#mySQL configurations
#mySQL configurations
app.config['MYSQL_HOST']=''
app.config['MYSQL_USER']=''
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']=''

mysql=MySQL(app)



'''class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    phone = StringField("Phone", validators=[DataRequired()])
    submit = SubmitField("Register")'''

class RegisterForm(FlaskForm):
    name = StringField(validators=[DataRequired()])
    email = StringField(validators=[DataRequired(), Email()])
    password = PasswordField(validators=[DataRequired()])
    phone = StringField(validators=[DataRequired()])
    submit = SubmitField("Register")   

class completeprofile_alumniForm(FlaskForm):
    designation = StringField("Designation", validators=[DataRequired()])
    description = StringField("Description", validators=[DataRequired()])
    education = StringField("Education", validators=[DataRequired()])
    skills = StringField("Skills", validators=[DataRequired()])
    achievements = StringField("Achievements", validators=[DataRequired()])
    
    location = StringField("Location", validators=[DataRequired()])
    mentee = StringField("Mentee", validators=[DataRequired()])
    working_experiance = StringField("Working Experiance", validators=[DataRequired()])
    submit = SubmitField("Submit")
    

class LoginForm(FlaskForm):

    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("login")    

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/welcome_back')
def welcome_back():
    return render_template("welcome_back.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    form=RegisterForm()
    if request.method == 'POST':
        name = form.name.data
        email = form.email.data
        password = form.password.data
        phone = form.phone.data
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        


        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO alumni (name, email, password, phone) VALUES (%s, %s, %s, %s)", (name, email, hashed_password, phone))
        mysql.connection.commit()
        cursor.close()

        return redirect('/login')

    return render_template('register.html',form=form)

#LOGIN WALE ROUTES LOGIN
#LOGIN WALE ROUTES LOGIN
'''@app.route('/login', methods=['GET', 'POST'])
def login():
    form=LoginForm()
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        cursor = mysql.connection.cursor()

        cursor.execute("SELECT * FROM register WHERE email = %s", (email,))

        user = cursor.fetchone()
        cursor.close()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Please check your email and password.')
            return redirect(url_for('login'))
    return render_template('login.html', form=form)
'''

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    form=LoginForm()
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        cursor = mysql.connection.cursor()

        cursor.execute("SELECT * FROM register WHERE email = %s", (email,))

        user = cursor.fetchone()
        cursor.close()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Please check your email and password.')
            return redirect(url_for('student_login'))
    return render_template("student_login.html", form=form)


@app.route('/alumni_login', methods=['GET', 'POST'])
def alumni_login():
    form=LoginForm()
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        cursor = mysql.connection.cursor()

        cursor.execute("SELECT * FROM alumni WHERE email = %s", (email,))

        user = cursor.fetchone()
        cursor.close()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            session['user_id'] = user[0]
            return redirect(url_for('dashboard_alumni'))
        else:
            flash('Login failed. Please check your email and password.')
            return redirect(url_for('alumni_login'))
    return render_template("alumni_login.html", form=form)


@app.route('/institute_login', methods=['GET', 'POST'])
def institute_login():
    form=LoginForm()
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        cursor = mysql.connection.cursor()

        cursor.execute("SELECT * FROM register WHERE email = %s", (email,))

        user = cursor.fetchone()
        cursor.close()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Please check your email and password.')
            return redirect(url_for('institute_login'))
    return render_template("institute_login.html", form=form)



@app.route('/dashboard_alumni')
# NEW: This decorator protects the route
def dashboard_alumni():
    if 'user_id' in session:
        user_id = session['user_id']
        # CHANGED: We get the user's ID from the JWT instead of the session.

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM alumni WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()

        if user:
            return render_template('dashboard_alumni.html', user=user)
        
    return redirect(url_for('alumni_login'))



@app.route('/completeprofile_alumni', methods=['GET', 'POST'])

def completeprofile_alumni():
   form=completeprofile_alumniForm()
   if request.method == 'POST':
            designation = form.designation.data
            description = form.description.data
            education = form.education.data
            skills = form.skills.data
            achievements = form.achievements.data
            gallery = form.gallery.data
            location = form.location.data
            mentee = form.mentee.data
            working_experiance = form.working_experiance.data

            
            cursor = mysql.connection.cursor()
            cursor.execute("INSERT INTO alumni (designation, description, education, skills, achievements, location, working_experiance) VALUES (%s, %s, %s, %s, %s, %s, %s)", (designation, description, education, skills, achievements, location, working_experiance))
            mysql.connection.commit()
            cursor.close()

            return redirect('/dashboard_alumni')
   return render_template("completeprofile_alumni.html")

if __name__ == '__main__':
    print('connecting to db')
    app.run(port=1000, debug=True)