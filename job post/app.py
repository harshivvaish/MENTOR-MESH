# app.py
import os
import fitz  # PyMuPDF
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
import markdown

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Configurations ---
# MySQL Configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor' # Returns rows as dictionaries

# Secret Key for flashing messages
app.secret_key = 'your_very_secret_key' # Change this in a real app

# Gemini API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-2.5-pro')

# File Upload Configuration
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize MySQL
mysql = MySQL(app)

# --- Helper Functions ---
def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

# --- Routes ---
@app.route('/')
def index():
    """Renders the main student resume upload page."""
    return render_template('index.html')

@app.route('/alumni')
def alumni_form():
    """Renders the alumni profile creation form."""
    return render_template('alumni_profile.html')

@app.route('/add_alumni', methods=['POST'])
def add_alumni():
    """Handles the submission of the alumni profile form."""
    if request.method == 'POST':
        details = request.form
        name = details['name']
        email = details['email']
        grad_year = details['graduation_year']
        description = details.get('description', '')
        skills = details.get('skills', '')
        achievements = details.get('achievements', '')
        gallery_links = details.get('gallery_links', '')
        
        cur = mysql.connection.cursor()
        try:
            cur.execute(
                "INSERT INTO alumni_main (name, email, graduation_year, description, skills, achievements, gallery_links) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (name, email, grad_year, description, skills, achievements, gallery_links)
            )
            mysql.connection.commit()
            flash("Profile created successfully!", "success")
        except Exception as e:
            mysql.connection.rollback()
            flash(f"An error occurred: {e}", "danger")
        finally:
            cur.close()

        return redirect(url_for('alumni_form'))


@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    """Handles resume upload, analysis, matching, and roadmap generation."""
    if 'resume' not in request.files:
        flash("No file part")
        return redirect(request.url)
    
    file = request.files['resume']
    if file.filename == '':
        flash("No selected file")
        return redirect(request.url)

    if file and file.filename.endswith('.pdf'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # 1. Extract text from the PDF resume
        resume_text = extract_text_from_pdf(filepath)
        os.remove(filepath) # Clean up the uploaded file

        if not resume_text:
            flash("Could not read text from the PDF.", "danger")
            return redirect(url_for('index'))

        try:
            # 2. Use Gemini to extract skills from resume text
            skill_prompt = f"Analyze the following resume text and extract the key technical skills, programming languages, and frameworks. List them as a simple comma-separated string without any introduction. For example: Python, Flask, JavaScript, React, MySQL. Resume Text: '{resume_text}'"
            skill_response = model.generate_content(skill_prompt)
            extracted_skills = skill_response.text.strip().split(',')
            extracted_skills = [skill.strip() for skill in extracted_skills]

            # 3. Find matching alumni from the database
            if extracted_skills:
                cur = mysql.connection.cursor()
                query_parts = ["skills LIKE %s"] * len(extracted_skills)
                query = "SELECT * FROM alumni_main WHERE " + " OR ".join(query_parts)
                # Create a list of parameters for the query
                params = ['%' + skill + '%' for skill in extracted_skills]
                cur.execute(query, params)
                matched_alumni = cur.fetchall()
                cur.close()
            else:
                matched_alumni = []

            # 4. Use Gemini to generate the 1-month roadmap
            roadmap_prompt = f"""
            You are a helpful career coach. Based on the following resume text, create a personalized 4-week (1-month) learning roadmap to help this person fill their skill gaps and advance their career. 
            For each week, suggest specific skills to learn and a small project to build.
            Format the entire output in Markdown with headings for each week (e.g., '### Week 1: Foundational Python').
            
            Resume Text: '{resume_text}'
            """
            # ... inside the upload_resume function
            roadmap_response = model.generate_content(roadmap_prompt)
            roadmap_markdown = roadmap_response.text 
            roadmap_html = markdown.markdown(roadmap_markdown) # <-- ADD THIS LINE to convert to HTML

            return render_template('results.html', roadmap=roadmap_html, alumni=matched_alumni) # <-- Pass the HTML version
            

        except Exception as e:
            flash(f"An error occurred while processing with Gemini API: {e}", "danger")
            return redirect(url_for('index'))

    flash("Invalid file type. Please upload a PDF.", "warning")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True,port=4000)