from flask import Flask, session, request, render_template, redirect, url_for, flash, jsonify, make_response
from logging import DEBUG
from flask_session import Session
import re
import firebase_admin
from firebase_admin import credentials, db, firestore, storage
import uuid
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask import session
import openai
from dotenv import load_dotenv
import json
import logging
import os
import requests
import time
# from langchain_openai import OpenAI
# from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
# from langchain.chains import LLMChain
# from langchain.memory import ConversationBufferMemory
# from langchain_community.utilities import WikipediaAPIWrapper
from functools import wraps
# from chatbot.Disorders import Disorders
import fitz
import pycountry
from datetime import datetime
import random
from questions.personal_info import personal_info_questions_phase_1, personal_info_questions_phase_2, personal_info_questions_phase_3
from questions.diagnose_questions import diagnose_questions
from questions.personal_insight import personal_insights_questions
from guard.anonymize import anonymize_text
from guard.code import scan_code
from guard.topics import topic_scan
from guard.gibberish import gibberish_scan
from guard.language import language_scan
from guard.injection import injection_scan
from guard.secrets import secrets_scan
from llm_guard.input_scanners import BanCode
from multiprocessing.dummy import Pool
import whisper
import os

pool = Pool(5)
app = Flask(__name__, static_folder='static')
app.secret_key = 'your_secret_key_here'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
Session(app)
load_dotenv()
#openAI = openai.OpenAI()
DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL')

def sanitize_filename(filename: str) -> str:
    return re.sub(r"[^\w\s-]", "", filename).strip()

@app.route("/generate_summary", methods=['POST'])
def generate_summary():
    # llm = ChatOpenAI(model="gpt-4o-mini") # OpenAI model
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")
    prompt = PromptTemplate.from_template("""
You are a psychologist about to make mental diagnoses based on this subject's mental data and the therapy session. You have to make summaries about the therapy session that are helpful to combine with the subject's mental data.
----Therapy session----
{therapy_session}

Make summary of the therapy session with all key points, ONLY with information related to the subject/patient.
Summary should be well structured, informative, in-depth, and comprehensive, with facts and numbers mentioned.
Please ensure the summary contains only the factual information that was discussed, and that there is no preamble or introductory statement.
The summary should be structured into sections, with each section containing one or more paragraphs of information
    """)
    chain = prompt | llm

    # Check if a file is in the request
    if 'audio_file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    # Get the file from the request
    audio_file = request.files['audio_file']
    print("audio_file", audio_file)

    if audio_file:
        # Ensure the directory exists
        if not os.path.exists('uploaded_audio'):
            os.makedirs('uploaded_audio')

        # I added to test the path
        audio_file_path = os.path.join('uploaded_audio', audio_file.filename)
        # Save the file to the server
        audio_file.save(f"uploaded_audio/{audio_file.filename}")
        print(f"File saved to {audio_file_path}")
    else:
        return jsonify({"error": "No audio file received"}), 400

    try:
        model = whisper.load_model("turbo")
        result = model.transcribe(f"uploaded_audio/{audio_file.filename}", verbose=True)

        '''Transcribe the audio directly without saving. 
        NOTE: the quality of the text is not quality as the above method.'''
        # from io import BytesIO
        # from pydub import AudioSegment
        # import numpy as np

        # file_like_object = BytesIO(audio_file.read())
        # Load the audio using pydub (this should work for various formats like mp3, wav, etc.)
        # audio = AudioSegment.from_file(file_like_object)
        # Convert to mono and resample to 16000 Hz if needed
        # audio = audio.set_channels(1).set_frame_rate(16000)
        # Convert audio to numpy array
        # samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
        # Normalize the audio (Whisper expects values between -1 and 1)
        # samples = samples / 2 ** 15
        # result = model.transcribe(samples, task="translate")
        # result = model.transcribe(samples)

        print("Text", result["text"])
        audio_report_suffix = int(time.time())

        sanitized_filename = sanitize_filename(f"therapy_{audio_report_suffix}")
        bucket = storage.bucket()
        blob = bucket.blob(f"therapy_transcription/{session['random_key']}/{sanitized_filename}.md")
        blob.upload_from_string(result["text"], content_type='text/markdown')

        summary = chain.invoke(
            {
                "therapy_session": result["text"]
            }
        )
        print("summary", summary.content)

        session['summary'] = summary.content

        sanitized_filename = sanitize_filename(f"therapy_{audio_report_suffix}")
        bucket = storage.bucket()
        blob = bucket.blob(f"therapy_session/{session['random_key']}/{sanitized_filename}.md")
        blob.upload_from_string(summary.content, content_type='text/markdown')
    except Exception as e:
        print(f"An error occurred when generating summary: {e}")
        return jsonify({"error": str(e)}), 500

    os.remove(f"uploaded_audio/{audio_file.filename}")
    return {"success": True}


@app.route("/general_summary", methods=['GET'])
def general_summary():
    transcription = session.get('transcription')
    return render_template('summary.html', transcription=transcription)


@app.route("/", methods=['GET', 'POST'])
def home():
    cards = [
        {'title': 'Time-Efficient Therapy', 'text': 'By automating documentation and administrative tasks, therapists can devote their full attention to patient care. This increased efficiency reduces the number of sessions needed, making therapy quicker and more effective.'},
        {'title': 'Privacy by Design', 'text': 'We prioritize your privacy. Our system does not collect personal information. Instead, we generate a unique key that serves as your identifier within the app, ensuring your data remains secure and anonymous.'},
        {'title': 'Streamlined Administrative Workflow', 'text': 'Therapists typically spend 30-40% of session time on manual documentation. Our app automates this process, freeing up more time for patient care and enhancing the overall quality of therapy.'},
        {'title': 'Pre-Intake Questionnaires and Analysis', 'text': 'Before therapy, patients complete dynamic questionnaires, and the app analyzes their responses to provide therapists with valuable insights into risks and key concerns. It also offers evidence-based resources, promoting time-saving, deeper insights, and more informed care.'},
        {'title': 'Therapy Session Summaries', 'text': 'Our AI-powered app generates clear and accurate therapy session summaries, capturing key points and insights. Saving therapists valuable time. By automating note-taking, therapists can focus on patient care, improve continuity, and reduce mental strain, making therapy more efficient and effective.'},
        {'title': 'Diagnoses', "text": "By analyzing both the patient’s responses and key insights from the session, the app helps therapists form a comprehensive understanding of the patients condition, our app make a evidence-based diagnoses."},
    ]
    doctors = [
        {"name": "Dr. Joseph Morgan", "specialty": "Psychiatrist", 'message': "I recommend this website for therapists and psychologists as a good source for per-session  with your patients to find necessary data and possible disorders", "image": "./static/assets/img/dr1.png"},
        {"name": "Dr. Elena Gilbert", "specialty": "Clinical Psychologist", "message": "I recommend this website for therapists and psychologists as a good source for per-session  with your patients to find necessary data and possible disorders", "image": "./static/assets/img/dr2.png"},
        {"name": "Dr. Laura Greens", "specialty": "Therapist", "message": "I recommend this website for therapists and psychologists as a good source for per-session  with your patients to find necessary data and possible disorders", "image": "./static/assets/img/dr3.png"},
        {"name": "Dr. Emily Johnson1", "specialty": "Therapist", "message": "I recommend this website for therapists and psychologists as a good source for per-session  with your patients to find necessary data and possible disorders", "image": "./static/assets/img/dr1.png"},
        {"name": "Dr. Emily Johnson2", "specialty": "Therapist", "message": "I recommend this website for therapists and psychologists as a good source for per-session  with your patients to find necessary data and possible disorders", "image": "./static/assets/img/dr2.png"},
        {"name": "Dr. Emily Johnson3", "specialty": "Therapist", "message": "I recommend this website for therapists and psychologists as a good source for per-session  with your patients to find necessary data and possible disorders", "image": "./static/assets/img/dr3.png"},
        # Add more doctors as needed
    ]
    random_key = session.get('random_key', 'No key available')
    logging.debug("redirecting index.html")
    return render_template('index.html', cards=cards, doctors=doctors, random_key=random_key)

### Firebase ###
cred = credentials.Certificate(os.getenv('FIREBASE_DATABASE_CERTIFICATE'))
firebase_admin.initialize_app(cred, {
    'databaseURL': DATABASE_URL,
    'storageBucket': 'chat-psychologist-ai.appspot.com'
})

#### Firestore #####
firestore_db = firestore.client()
try:
    USERS_REF = db.reference('users')
    print("Firebase connected successfully")
except Exception as e:
    print(f"Error creating Realtime Database reference: {e}")

try:
    WALLETS_REF = firestore_db.collection('wallets')
    print("Firestore connected successfully")
except Exception as e:
    print(f"Error creating Firestore collection reference: {e}")

def redirect_if_logged_in(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if 'user_logged_in' in session:
            logging.debug("redirecting to home page since already loggd in")
            return redirect(url_for('home'))
        return route_function(*args, **kwargs)
    return wrapper


##### Register Firebase #####

@app.route('/register', methods=['POST'])
def register():
    password1 = request.form.get('pass')
    password2 = request.form.get('pass2')
    # Password validation criteria
    password_regex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_\-+=<>?])[A-Za-z\d!@#$%^&*()_\-+=<>?]{12,}$')

    if not password1 or not password2:
        flash('Please fill in both password fields.' )
        return redirect(url_for('register_page'))

    if password1 != password2:
        flash('Passwords do not match.')
        return redirect(url_for('register_page'))

    if not password_regex.match(password1):
        flash('Password does not meet the required criteria.')
        return redirect(url_for('register_page'))

    # Generate a random key
    random_key = str(uuid.uuid4())

    # Store the random key and hashed password in Firebase Realtime Database
    ref = db.reference('users')
    ref.child(random_key).set({
        'random_key': random_key,
        'password': generate_password_hash(password1)
    })

    flash(f'Your registration key is: {random_key}. Please save it for future logins.', 'success')
    session['random_key'] = random_key
    logging.info("user registered with random key ["+random_key+"]")
    return redirect(url_for('register_page'))


@app.route('/register', methods=['GET'])
@redirect_if_logged_in  # Apply the redirect_if_logged_in decorator
def register_page():
    return render_template('register.html')


##### LogIN Firebase #####

@app.route('/login', methods=['POST'])
def login():
    random_key = request.form.get('random_key')
    password = request.form.get('password')
    if not random_key or not password:
        flash('Please fill in all fields.')
        return redirect(url_for('login_page'))
    user_data = USERS_REF.child(random_key).get()
    if not user_data:
        flash('Invalid random key.')
        return redirect(url_for('login_page'))
    stored_password_hash = user_data.get('password')
    if not stored_password_hash or not check_password_hash(stored_password_hash, password):
        flash('Invalid password.')
        return redirect(url_for('login_page'))
    session['user_logged_in'] = True
    session['random_key'] = random_key  # Store the random_key in the session
    session['has_interacted'] = user_data.get('has_interacted', False)  # Get interaction status
    session['first_login'] = 'diagnosis' not in user_data
    return redirect(url_for('dashboard'))


@app.route('/login', methods=['GET'])
@redirect_if_logged_in  # Apply the redirect_if_logged_in decorator
def login_page():
    return render_template('login.html')

##### LogOut Firebase #####
@app.route('/logout')
def logout():
    logging.debug("user logged out")
    session.pop('user_logged_in', None)
    logging.debug("setting user_logged_in flag to none")
    session.clear()
    logging.debug("session is cleared")
    session['new_session_can_start']=True
    logging.debug("new_session_can_start is set to True")
   # flash('Successfully logged out!')
    return redirect(url_for('home'))

#####A function that doesn't alow to acces that page if you are not loged in ####

def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if 'user_logged_in' not in session:
            flash('Please log in to access this page.')
            return redirect(url_for('login_page'))
        return route_function(*args, **kwargs)
    return wrapper


########## Therapy Session Display Page ##########
# @app.route('/therapy-transcription', methods=['GET', 'POST'])
# @login_required
# def therapy_transcription():
#     bucket = storage.bucket()
#     transcription = ""
#     blobs = bucket.list_blobs(prefix=f"therapy_transcription/{session['random_key']}/")

#     for blob in blobs:
#         print(blob.name)
#         file_name = os.path.basename(blob.name)
#         print(file_name)
#         blob = bucket.blob(blob.name)

#         contents = blob.download_as_bytes()
#         markdown_content = contents.decode('utf-8')
#         html_content = convert_markdown_to_html(markdown_content)
#         transcription += f"---{file_name}---\n{html_content}\n\n"

#     print("transcription", transcription)

#     return render_template('conversation.html', summary=transcription)

@app.route('/therapy-transcription', methods=['GET', 'POST'])
@login_required
def therapy_transcription():
    bucket = storage.bucket()
    transcription = ""
    blobs = bucket.list_blobs(prefix=f"therapy_transcription/{session['random_key']}/")

    for blob in blobs:
        print(blob.name)
        file_name = os.path.basename(blob.name)
        print(file_name)
        blob = bucket.blob(blob.name)

        contents = blob.download_as_bytes()
        markdown_content = contents.decode('utf-8')
        html_content = convert_markdown_to_html(markdown_content)
        transcription += f"---{file_name}---\n{html_content}\n\n"

    print("transcription", transcription)

    return render_template('conversation.html', transcription=transcription)

@app.route('/summary-report', methods=['GET', 'POST'])
@login_required
def summary_report():
    bucket = storage.bucket()
    summaries = ""
    blobs = bucket.list_blobs(prefix=f"therapy_session/{session['random_key']}/")

    for blob in blobs:
        print(blob.name)
        file_name = os.path.basename(blob.name)
        print(file_name)
        blob = bucket.blob(blob.name)

        contents = blob.download_as_bytes()
        markdown_content = contents.decode('utf-8')
        html_content = convert_markdown_to_html(markdown_content)
        summaries += f"---{file_name}---\n{html_content}\n\n"

    print("summaries", summaries)

    return render_template('summary.html', summary=summaries)

@app.route('/dashboard')
def dashboard():
    random_key = session.get('random_key', 'No key available')
    return render_template('dash_main.html', random_key=random_key)


######### Treatment Page #############
@app.route('/treatment')
@login_required
def treatment():
    user_data = get_user()
    # Check completion flags
    personal_info_phase_1_complete = user_data.get('personal_info_phase_1_completed', False)
    personal_info_phase_2_complete = user_data.get('personal_info_phase_2_completed', False)
    personal_info_phase_3_complete = user_data.get('personal_info_phase_3_completed', False)
    personal_info_complete = all([
        personal_info_phase_1_complete,
        personal_info_phase_2_complete,
        personal_info_phase_3_complete
    ])
    # Redirect to the appropriate page if any step is incomplete
    if not personal_info_complete:
        return redirect(url_for('personal_info_phase_1'))

    return render_template('treatment.html')

###########################################personal info Page ########################################

@app.route('/personal_info_phase_1', methods=['GET', 'POST'])
@login_required
def personal_info_phase_1():
    user_data = get_user()

    # Redirect to phase 2 if already completed
    if user_data.get('personal_info_phase_1_completed', False):
        return redirect(url_for('personal_info_phase_2'))

    if request.method == 'POST':
        personal_info_responses = {}

        for index, question in enumerate(personal_info_questions_phase_1, start=1):
            topic = sanitize_key(question.get('topic', f"Topic {index}"))
            personal_info_responses[topic] = {}

            questions = question.get('questions')
            for index, question in enumerate(questions, start=1):
                question_info_type = sanitize_key(question.get('info_type', f"Info type {index}"))

                if question['type'] == 'group':
                     # Capture range and text input for the grouped question
                    score = request.form.get(f'{topic}_phase_1_score_{index}')
                    comments = request.form.get(f'{topic}_phase_1_comments_{index}')
                    # Log to console for debugging
                    personal_info_responses[topic][question_info_type] = {
                        'score': (str(score) if score else "0") + "/100",  # Default to 0 if score is empty
                        'comments': comments if comments else None  # Default to None if comments are empty
                    }

                else:
                    # Capture other question types normally
                    answer = request.form.get(f'{topic}_question_{index}')
                    # Log to console for debugging
                    print(f"Received answer: {answer} for question {index}")

                    personal_info_responses[topic][question_info_type] = answer if answer else None  # Default to None if answer is empty

        # Update user data
        user_data['personal_info_phase_1_completed'] = True
        user_data['personal_info_responses_phase_1'] = personal_info_responses

        # Save updated user data to the database
        USERS_REF.child(session['random_key']).set(user_data)
        research_data('personal_info_responses_phase_1')
         # Call the agent to process the personal info responses
        #call_phase1_agent(user_data['personal_info_responses_phase_1'])

        return redirect(url_for('personal_info_phase_2'))

    return render_template('personal_info_phase_1.html', questions=personal_info_questions_phase_1)

def research_data(data_ref, write_report = False):
    data = {'user_key': session['random_key'], 'data_ref': data_ref, 'write_report': write_report}
    headers = {'Content-Type': 'application/json'}

    print("data", data)
    '''res = requests.post(
        'https://main-bvxea6i-hq3wucu75qstu.eu.platformsh.site/research-data',
        data=json.dumps(data),
        headers=headers
    )'''
    pool.apply_async(
        requests.post,
        args=[os.getenv('GPT_RESEACHER_BASE_URL') + '/research-data'],
        kwds={'data': json.dumps(data), 'headers': headers}
    )
    print("end of research_data")

def generate_final_report():
    data = {'user_key': session['random_key']}
    headers = {'Content-Type': 'application/json'}

    print("data", data)
    pool.apply_async(
        requests.post,
        args=[os.getenv('GPT_RESEACHER_BASE_URL') + '/write-final-report'],
        kwds={'data': json.dumps(data), 'headers': headers}
    )
    print("end of generate_final_report")


def get_recent_final_report():
    bucket = storage.bucket()
    blob = bucket.blob(f"research/{session['random_key']}/final_report.md")
    contents = blob.download_as_bytes()
    return contents.decode("utf-8")

##### Sahar added this to change Markdown text to Hyper Text(HTML)
def convert_markdown_to_html(text):
    # Convert headers
    text = re.sub(r'### (.*)', r'<h4>\1</h4>', text)
    text = re.sub(r'## (.*)', r'<h3>\1</h3>', text)
    text = re.sub(r'# (.*)', r'<h2>\1</h2>', text)

    # Convert numbered lists
    text = re.sub(r'(\d+)\. ', r'<li>\1. ', text)
    text = re.sub(r'(\d+)\. (.*)', r'<li>\2</li>', text)

    # Wrap list items in <ul> tags
    text = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', text)

    # Make text bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

    # Make text italic
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)

    # Make text strikethrough
    text = re.sub(r'--(.*?)--', r'<del>\1</del>', text)
    
    # Wrap plain text in <p> tags
    lines = text.split('\n')
    for i in range(len(lines)):
        if not re.match(r'<h\d>|<ul>|<li>|<b>', lines[i]):
            lines[i] = f'<p>{lines[i]}</p>'
    text = '\n'.join(lines)

    return text

def get_recent_final_report():
    bucket = storage.bucket()
    blob = bucket.blob(f"research/{session['random_key']}/final_report.md")
    contents = blob.download_as_bytes()
    return convert_markdown_to_html(contents.decode("utf-8"))

def sanitize_key(key):
    # Replace invalid characters with an underscore or remove them
    return key.replace('$', '_').replace('#', '_').replace('[', '_').replace(']', '_').replace('/', '_').replace('.', '_')


@app.route('/personal_info_phase_2', methods=['GET', 'POST'])
@login_required
def personal_info_phase_2():
    user_data = get_user()

    # Redirect to phase 3 if phase 2 is already completed
    if user_data.get('personal_info_phase_2_completed', False):
        return redirect(url_for('personal_info_phase_3'))

    if request.method == 'POST':
        personal_info_responses = {}

        for index, question in enumerate(personal_info_questions_phase_2, start=1):
            topic = sanitize_key(question.get('topic', f"Topic {index}"))
            personal_info_responses[topic] = {}

            questions = question.get('questions')
            for index, question in enumerate(questions, start=1):
                question_info_type = sanitize_key(question.get('info_type', f"Info type {index}"))

                # Capture range and text input for the grouped question
                score = request.form.get(f'{topic}_phase_2_score_{index}')
                comments = request.form.get(f'{topic}_phase_2_comments_{index}')
                personal_info_responses[topic][question_info_type] = {
                    'score': (str(score) if score else "0") + "/100",  # Default to None if score is empty
                    'comments': comments if comments else None  # Default to None if comments are empty
                }

        # Update user data
        user_data['personal_info_phase_2_completed'] = True
        user_data['personal_info_responses_phase_2'] = personal_info_responses

        # Save updated user data to the database
        USERS_REF.child(session['random_key']).set(user_data)
        research_data('personal_info_responses_phase_2')
        return redirect(url_for('personal_info_phase_3'))
    return render_template('personal_info_phase_2.html', questions=personal_info_questions_phase_2)

def get_user():
    user_data = USERS_REF.child(session['random_key']).get()
    return user_data

##### Sahar's Work on Reports Page #####
@app.route('/reports', methods=['GET', 'POST'])
@login_required
def reports():

    user_data = get_user()
    personal_info_phase_3_complete = user_data.get('personal_info_phase_3_completed', False)
    # Fetch the reports (this is just a placeholder, replace with actual logic)
    reports = [
        {"id": "01", "title": "Diagnose Mental Disorder Report", "download": "", "url": "./first_report" if personal_info_phase_3_complete else "#"},
        {"id": "02", "title": "Ttherapy Session Reports", "download": ".", "url": "./summary-report"},
        {"id": "03", "title": "Report 3", "download": "Content for report 3.", "url": "#"},
        {"id": "04", "title": "Report 4", "download": "Content for report 4.", "url": "#"}
    ]
    return render_template('reports.html', reports=reports)

# My Code
@app.route('/sessions', methods=['GET', 'POST'])
@login_required
def sessions():
    return render_template('sessions.html')

##### Sahar's Work Profile Page #####
@app.route('/first_report', methods=['GET', 'POST'])
@login_required
def first_report():
    report_content = get_recent_final_report()
    return render_template('first_report.html', report_content=report_content)

@app.route('/personal_info_phase_3', methods=['GET', 'POST'])
@login_required
def personal_info_phase_3():
    user_data = get_user()

    # Redirect to phase 3 if phase 2 is already completed
    if user_data.get('personal_info_phase_3_completed', False):
        return redirect(url_for('treatment'))

    if request.method == 'POST':
        personal_info_responses = {}

        for index, question in enumerate(personal_info_questions_phase_3, start=1):
            topic = sanitize_key(question.get('topic', f"Topic {index}"))
            personal_info_responses[topic] = {}

            questions = question.get('questions')
            for index, question in enumerate(questions, start=1):
                question_info_type = sanitize_key(question.get('info_type', f"Info type {index}"))

                # Capture range and text input for the grouped question
                score = request.form.get(f'{topic}_phase_3_score_{index}')
                comments = request.form.get(f'{topic}_phase_3_comments_{index}')
                personal_info_responses[topic][question_info_type] = {
                    'score': (str(score) if score else "0") + "/100",  # Default to None if score is empty
                    'comments': comments if comments else None  # Default to None if comments are empty
                }

        # Update user data
        user_data['personal_info_phase_3_completed'] = True
        user_data['personal_info_responses_phase_3'] = personal_info_responses

        # Save updated user data to the database
        USERS_REF.child(session['random_key']).set(user_data)
        research_data('personal_info_responses_phase_3', write_report=True)
        return redirect(url_for('treatment'))
    return render_template('personal_info_phase_3.html', questions=personal_info_questions_phase_3)

##### Sahar's Work on Personal Insight Page #####

# @app.route('/personal_insights', methods=['GET', 'POST'])
# @login_required
# def personal_insights():
#     user_data = get_user()

#     if request.method == 'POST':
#         personal_insight_responses = {}

#         for index, question in enumerate(personal_insights_questions, start=1):
#             topic = sanitize_key(question.get('topic', f"Topic {index}"))
#             personal_insight_responses[topic] = {}

#             questions = question.get('questions')
#             for index, question in enumerate(questions, start=1):
#                 question_info_type = sanitize_key(question.get('info_type', f"Info type {index}"))

#                 answer = request.form.get(f'{topic}_question_{index}')
#                 print(f"Received answer: {answer} for question {index}")

#                 personal_insight_responses[topic][question_info_type] = answer if answer else None

#         user_data['personal_insights_completed'] = True
#         user_data['personal_insight_responses'] = personal_insight_responses
#         USERS_REF.child(session['random_key']).set(user_data)

#         return redirect(url_for('questions'))

#     return render_template('personal_insights.html', questions=personal_insights_questions)
###### End of personal insight Page ####

@app.route('/appointment', methods=['GET', 'POST'])
@login_required
def appointment():
    return render_template('appointment.html')

#### web3 routes ####
@app.route('/nonce')
def nonce():
    wallet_address = request.args.get('walletAddress')
    nonce = str(random.randint(1, 10000))
    nonce_id = f"{nonce}-{datetime.now().timestamp()}"
    created_at = datetime.now()

    # Check if wallet address already exists in Firestore
    doc_ref = WALLETS_REF.document(wallet_address)
    doc = doc_ref.get()

    if doc.exists:
        # Wallet address already exists, update the nonce and updatedAt
        doc_ref.update({
            'nonce': nonce_id,
            'updatedAt': datetime.now()
        })
    else:
        # Wallet address does not exist, insert a new document with createdAt
        WALLETS_REF.document(wallet_address).set({
            'wallet_address': wallet_address,
            'nonce': nonce_id,
            'createdAt': created_at,
            'updatedAt': created_at
        })

    return jsonify({'nonce': nonce_id})

@app.route('/verify', methods=['GET'])
def verify_signature():
    wallet_address = request.args.get('walletAddress')
    doc_ref = WALLETS_REF.document(wallet_address)
    doc = doc_ref.get()
    if doc.exists:
        response = make_response(jsonify({'success': True}))
        response.set_cookie('walletAddress', wallet_address)
        return response
    else:
        return jsonify({'success': False, 'error': 'Wallet address not found'})

@app.route('/check')
def check_session():
    wallet_address = request.cookies.get('walletAddress')
    if wallet_address:
        # Check if wallet address exists in Firestore
        doc_ref = WALLETS_REF.document(wallet_address)
        doc = doc_ref.get()
        if doc.exists:
            return jsonify({'success': True, 'walletAddress': wallet_address})
        else:
            return jsonify({'success': False, 'error': 'Wallet address not found in Firestore'})
    else:
        return jsonify({'success': False})

@app.route('/disconnect')
def disconnect():
    response = make_response(jsonify({'success': True}))
    response.set_cookie('walletAddress', '', expires=0)
    return response

@app.route('/health', methods=['GET'])
def check_health():
    return {"status": "OK"}, 200

@app.route('/anonymize', methods=['POST'])
def anonymize_data():
    """
    Anonymizes sensitive information in the provided text prompt.
    Request (JSON):
    {
        "prompt": "Text containing sensitive information."
    }
    Response (JSON):
    {
        "sanitized_prompt": "Anonymized text",
        "is_valid": true,
        "risk_score": 0.5
    }
    """
    data = request.json
    prompt = data.get('prompt', '')
    allowed_names = []
    hidden_names = []
    preamble = ""
    response = anonymize_text(prompt, allowed_names, hidden_names, preamble)
    return jsonify(response), 200

@app.route('/ban_code', methods=['POST'])
def ban_code_data():
    """
    Scans the provided text prompt for banned code patterns.
    Request (JSON):
    {
        "prompt": "Text containing potential banned code."
    }
    Response (JSON):
    {
        "sanitized_prompt": "Sanitized text",
        "is_valid": true,
        "risk_score": 0.5
    }
    """
    data = request.json
    prompt = data.get('prompt', '')
    scanner = BanCode()
    sanitized_prompt, is_valid, risk_score = scanner.scan(prompt)
    response = {
        "sanitized_prompt": sanitized_prompt,
        "is_valid": is_valid,
        "risk_score": risk_score
    }
    return jsonify(response), 200

@app.route('/code_scan', methods=['POST'])
def code_scan():
    data = request.json
    prompt = data.get('prompt', '')  # Extract prompt data
    sanitized_prompt, is_valid, risk_score = scan_code(prompt)
    response = {
        "sanitized_prompt": sanitized_prompt,
        "is_valid": is_valid,
        "risk_score": risk_score
    }
    return jsonify(response), 200

@app.route("/ban_topics", methods=["POST"])
def topics_scan():
    data = request.json
    prompt = data.get('prompt', '')
    sanitized_prompt, is_valid, risk_score = topic_scan(prompt)
    response = {
        "sanitized_prompt": sanitized_prompt,
        "is_valid": is_valid,
        "risk_score": risk_score
    }
    return jsonify(response), 200
    
@app.route("/ban_gibberish", methods=["POST"])
def gib_scan():
    data = request.json
    prompt = data.get('prompt', '')
    sanitized_prompt, is_valid, risk_score = gibberish_scan(prompt)
    response = {
        "sanitized_prompt": sanitized_prompt,
        "is_valid": is_valid,
        "risk_score": risk_score
    }
    return jsonify(response), 200

@app.route("/ban_language", methods=["POST"])
def lang_scan():
    data = request.json
    prompt = data.get('prompt', '')
    sanitized_prompt, is_valid, risk_score = language_scan(prompt)
    response = {
        "sanitized_prompt": sanitized_prompt,
        "is_valid": is_valid,
        "risk_score": risk_score
    }
    return jsonify(response), 200

@app.route("/ban_injection", methods=["POST"])
def scan_injection():
    data = request.json
    prompt = data.get('prompt', '')
    sanitized_prompt, is_valid, risk_score = injection_scan(prompt)
    response = {
        "sanitized_prompt": sanitized_prompt,
        "is_valid": is_valid,
        "risk_score": risk_score
    }
    return jsonify(response), 200

@app.route("/ban_secrets", methods=["POST"])
def scan_secrets():
    data = request.json
    prompt = data.get('prompt', '')
    sanitized_prompt, is_valid, risk_score = secrets_scan(prompt)
    response = {
        "sanitized_prompt": sanitized_prompt,
        "is_valid": is_valid,
        "risk_score": risk_score
    }
    return jsonify(response), 200


### end web3 routes ####
if __name__ == '__main__':
    # Configure the logging system
    logging.basicConfig(
        level=DEBUG,
        format='%(asctime)s [%(levelname)s] - %(message)s',
        handlers=[
            logging.FileHandler('appreg.log'),  # Output to a log file
        ]
    )
    logger = logging.getLogger(__name__)
    serverHost = os.getenv('host')
    serverPort = os.getenv('port')
    app.run(host=serverHost,port=serverPort, debug=os.getenv('debug') )