import os
import fitz  # PyMuPDF
import google.generativeai as genai
from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory, session
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from datetime import datetime

# --- REFACTORED: Set up app and secret key first ---
app = Flask(__name__)
# A secret key is required for the session to work
app.config['SECRET_KEY'] = 'a-strong-and-secret-key-for-your-app'

# --- Configuration ---
UPLOAD_FOLDER = 'videos'
# --- CORRECTED: Use the variable, not the string 'UPLOAD_FOLDER' ---
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Your MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Harshiv@25#07'
app.config['MYSQL_DB'] = 'mentormesh'

mysql = MySQL(app)

# Configure the Gemini API
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    # In a real app, you might handle this more gracefully
    exit()

# --- REFACTORED: Single, more efficient function to get questions ---
def generate_interview_questions(resume_text, college_year): # <-- Added college_year
    model = genai.GenerativeModel('models/gemini-2.5-pro')
    
    # The prompt is now an f-string to include the college_year
    prompt = (
        f"The candidate is a {college_year} student. Please adjust the difficulty of the questions "
        "accordingly. For 1st/2nd year, focus on foundational concepts. For 3rd year, focus on "
        "practical application. For a Final Year student, ask more complex, scenario-based questions.\n\n"
        "Based on the following resume text, "
        "generate exactly 3 distinct, insightful interview questions. The questions should "
        "probe the candidate's skills and experience. "
        "Return the questions as a numbered list (e.g., '1. Question one... 2. Question two...').\n\n"
        "--- RESUME ---\n"
        f"{resume_text}\n"
    )
    
    try:
        response = model.generate_content(prompt)
        # Split the response text into a list of questions
        questions = [q.strip() for q in response.text.strip().split('\n') if q]
        # Clean up the numbering (e.g., "1. ", "2. ")
        cleaned_questions = [q.split('. ', 1)[-1] for q in questions]
        return cleaned_questions[:3] # Return the first 3 questions
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        # Return fallback questions if the API fails
        return [
            "What is your experience with Flask?",
            "Describe a challenging project you've worked on.",
            "How do you handle database migrations in a web application?"
        ]

def extract_text_from_pdf(file_stream):
    """Extracts text from a PDF file stream."""
    try:
        doc = fitz.open(stream=file_stream.read(), filetype="pdf")
        text = "".join(page.get_text() for page in doc)
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

# --- Routes ---

@app.route('/')
def index():
    """Renders the main homepage with the resume upload form."""
    return render_template("index.html")

@app.route('/resume_sub', methods=['POST'])
def resume_sub():
    # Check if the file part is in the request
    if 'resume' not in request.files or request.files['resume'].filename == '':
        # Redirect back to the homepage if no file is uploaded
        return redirect(url_for('index'))

    # THIS LINE IS CRUCIAL AND WAS LIKELY MISSING
    # It gets the file object from the request and assigns it to the 'file' variable.
    file = request.files['resume']
    
    # Now that 'file' is defined, we can use it
    resume_text = extract_text_from_pdf(file)
    if not resume_text:
        return "Could not read text from PDF.", 400

    # Get the college year from the form
    college_year = request.form.get('college_year', '3rd Year') 

    # Pass the year and resume text to the generator function
    questions = generate_interview_questions(resume_text, college_year)
    
    # Store questions in the session and redirect
    session['interview_questions'] = questions
    return redirect(url_for('interview_page'))


@app.route('/interview')
def interview_page():
    """Renders the interview page, pulling questions from the session."""
    # --- CHANGED: Get questions safely from the session ---
    questions = session.get('interview_questions', ['Question 1', 'Question 2', 'Question 3']) # Provides default questions
  
    
    return render_template('interview.html', questions=questions)

# --- The rest of your video handling routes remain the same ---
@app.route('/upload-video', methods=['POST'])
def upload_video():
    if 'video_submission' not in request.files: return jsonify({'error': 'No video file part'}), 400
    file = request.files['video_submission']
    if file.filename == '': return jsonify({'error': 'No file selected'}), 400
    if file:
        filename = secure_filename(f"submission_{datetime.utcnow().timestamp()}.webm")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("INSERT INTO interview_submissions (student_id, alumni_id, video_filename) VALUES (%s, %s, %s)", (101, 202, filename))
            mysql.connection.commit()
            cursor.close()
            return jsonify({'message': f'Video "{filename}" uploaded successfully!'}), 200
        except Exception as e:
            return jsonify({'error': f'A database error occurred: {e}'}), 500
    return jsonify({'error': 'An unknown error occurred'}), 500

@app.route('/videos/<filename>')
def serve_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/submissions')
def list_submissions():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, student_id, submitted_at, video_filename FROM interview_submissions ORDER BY submitted_at DESC")
    submissions_tuples = cursor.fetchall()
    cursor.close()
    submissions = [{'id': r[0], 'student_id': r[1], 'submitted_at': r[2], 'video_filename': r[3]} for r in submissions_tuples]
    return render_template('submissions.html', submissions=submissions)

@app.route('/review/<int:submission_id>')
def review_submission(submission_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, student_id, submitted_at, video_filename FROM interview_submissions WHERE id = %s", (submission_id,))
    row = cursor.fetchone()
    cursor.close()
    if row:
        submission = {'id': row[0], 'student_id': row[1], 'submitted_at': row[2], 'video_filename': row[3]}
        return render_template('review.html', submission=submission)
    return "Submission not found", 404

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True, port=9000)