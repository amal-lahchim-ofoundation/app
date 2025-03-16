from flask import (
    Flask,
    session,
    request,
    render_template,
    redirect,
    url_for,
    flash,
    jsonify,
    make_response,
)
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
import asyncio
from utils.home import cards, doctors

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
from questions.personal_info import (
    personal_info_questions_phase_1,
    personal_info_questions_phase_2,
    personal_info_questions_phase_3,
)
from datetime import datetime
from multiprocessing.dummy import Pool
import whisper
import os
from google.api_core.exceptions import NotFound
from pyannote.audio import Pipeline
import subprocess

THERAPY_SESSION_PREFIX = "therapy_session/"
THERAPY_TRANSCRIPTION_PREFIX = "therapy_transcription/"
THERAPY_PREFIX = "therapy_"

pool = Pool(5)
app = Flask(__name__, static_folder="static")
app.secret_key = "your_secret_key_here"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)
load_dotenv()
# openAI = openai.OpenAI()
DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL")


async def sanitize_filename(filename: str) -> str:
    return re.sub(r"[^\w\s-]", "", filename).strip()


async def convert_webm_to_wav(input_file, output_file):
    """Function to convert WebM to WAV using FFmpeg."""
    command = [
        "ffmpeg",
        "-i",
        input_file,  # Input WebM file
        output_file,  # Output WAV file
    ]
    # subprocess.run(command, check=True)
    # Offload the blocking subprocess.run to a background thread
    await asyncio.to_thread(subprocess.run, command, check=True)


llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")


@app.route("/generate_summary", methods=["POST"])
def generate_summary():
    # llm = ChatOpenAI(model="gpt-4o-mini") # OpenAI model
    prompt = PromptTemplate.from_template(
        """
You are a psychologist about to make mental diagnoses based on this subject's mental data and the therapy session. You have to make summaries about the therapy session that are helpful to combine with the subject's mental data.
----Therapy session----
{therapy_session}

Make summary of the therapy session with all key points, ONLY with information related to the subject/patient.
Summary should be well structured, informative, in-depth, and comprehensive, with facts and numbers mentioned.
Please ensure the summary contains only the factual information that was discussed, and that there is no preamble or introductory statement.
The summary should be structured into sections, with each section containing one or more paragraphs of information
    """
    )
    chain = prompt | llm

    # Check if a file is in the request
    if "audio_file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    # Get the file from the request
    audio_file = request.files["audio_file"]
    print("audio_file", audio_file)

    if audio_file:
        # Ensure the directory exists
        if not os.path.exists("uploaded_audio"):
            os.makedirs("uploaded_audio")

        audio_file_path = os.path.join("uploaded_audio", audio_file.filename)
        # Save the file to the server
        audio_file.save(f"uploaded_audio/{audio_file.filename}")
        convert_webm_to_wav(
            audio_file_path, f"uploaded_audio/{audio_file.filename}.wav"
        )
        print(f"File saved to {audio_file_path}")
        audio_filename = f"uploaded_audio/{audio_file.filename}.wav"
    else:
        return jsonify({"error": "No audio file received"}), 400

    try:
        # Transcribing audio
        cache_dir = os.path.join(os.getcwd(), "cache")
        download_root = os.path.join(cache_dir, "whisper")
        model = whisper.load_model("turbo", download_root=download_root)
        result = model.transcribe(audio_filename, verbose=True, word_timestamps=True)

        """Transcribe the audio directly without saving. 
        NOTE: the quality of the text is not quality as the above method."""

        print("Text", result["text"])
        audio_report_suffix = int(time.time())
        session["last_audio_report_suffix"] = (
            audio_report_suffix  # Store timestamp for tracking
        )

        sanitized_filename = sanitize_filename(f"therapy_{audio_report_suffix}")
        bucket = storage.bucket()
        blob = bucket.blob(
            f"therapy_transcription/{session['random_key']}/{sanitized_filename}.md"
        )
        blob.upload_from_string(result["text"], content_type="text/markdown")

        # Generate summary
        summary = chain.invoke({"therapy_session": result["text"]})
        print("summary", summary.content)

        session["summary"] = summary.content

        bucket = storage.bucket()
        blob = bucket.blob(
            f"therapy_session/{session['random_key']}/{sanitized_filename}.md"
        )
        blob.upload_from_string(summary.content, content_type="text/markdown")

        # Diarizing speakers
        segments_with_timestamps = result["segments"]
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=os.getenv("PYANNOTE_AUDIO_AUTH_KEY"),
        )

        print("Preparing diarization...")
        diarization = pipeline({"uri": "audio_file", "audio": audio_filename})

        # Print out diarization output
        """for speech_turn, _, speaker_id in diarization.itertracks(yield_label=True):
            print(f"Speaker {speaker_id}: {speech_turn.start} --> {speech_turn.end}")"""

        transription_with_speakers = map_speakers_to_transcript(
            diarization, segments_with_timestamps
        )
        sanitized_prompt, is_valid, risk_score = scanner.scan(
            transription_with_speakers
        )
        print("------transription_with_speakers----", sanitized_prompt)
        bucket = storage.bucket()
        blob = bucket.blob(
            f"therapy_transcription/{session['random_key']}/{sanitized_filename}.md"
        )
        blob.upload_from_string(
            transription_with_speakers, content_type="text/markdown"
        )
    except Exception as e:
        print(f"An error occurred when generating summary: {e}")
        return jsonify({"error": str(e)}), 500

    os.remove(audio_filename)
    os.remove(f"uploaded_audio/{audio_file.filename}")
    return {"success": True}


async def map_speakers_to_transcript(diarization, whisper_output):
    speaker_transcriptions = []

    words = []
    for trans_segment in whisper_output:
        words.extend(trans_segment["words"])

    for speech_turn, _, speaker_id in diarization.itertracks(yield_label=True):
        start_time = speech_turn.start
        end_time = speech_turn.end
        text = f"{speaker_id}: "

        new_words = words[:]
        for word in words:
            if word["end"] <= end_time:
                new_words.remove(word)
                text += word["word"]
            else:
                break

        words = new_words
        speaker_transcriptions.append(text)

    # Print the combined result
    print("==========MAP SPEAKER TO TRANSCRIPT OUTPUT=========")
    for text in speaker_transcriptions:
        print(text)
    print("==========END MAP SPEAKER TO TRANSCRIPT OUTPUT=========")
    return "\n".join(speaker_transcriptions)


@app.route("/general_summary", methods=["GET"])
async def general_summary():
    transcription = session.get("transcription")
    return await render_template("summary.html", transcription=transcription)


@app.route("/", methods=["GET", "POST"])
async def home():
    random_key = session.get("random_key", "No key available")
    logging.debug("redirecting index.html")
    return render_template(
        "index.html", cards=cards, doctors=doctors, random_key=random_key
    )


### Firebase ###
cred = credentials.Certificate(os.getenv("FIREBASE_DATABASE_CERTIFICATE"))
firebase_admin.initialize_app(
    cred,
    {"databaseURL": DATABASE_URL, "storageBucket": "chat-psychologist-ai.appspot.com"},
)

#### Firestore #####
firestore_db = firestore.client()
try:
    USERS_REF = db.reference("users")
    print("Firebase connected successfully")
except Exception as e:
    print(f"Error creating Realtime Database reference: {e}")

try:
    WALLETS_REF = firestore_db.collection("wallets")
    print("Firestore connected successfully")
except Exception as e:
    print(f"Error creating Firestore collection reference: {e}")


def redirect_if_logged_in(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "user_logged_in" in session:
            logging.debug("redirecting to home page since already loggd in")
            return redirect(url_for("home"))
        return route_function(*args, **kwargs)

    return wrapper


##### Register Firebase #####
# Asynchronous function to handle Firebase operations
async def store_user_data_async(random_key, password_hash):
    ref = db.reference("users")
    await asyncio.to_thread(
        ref.child(random_key).set, {"random_key": random_key, "password": password_hash}
    )


@app.route("/register", methods=["POST"])
def register():
    password1 = request.form.get("pass")
    password2 = request.form.get("pass2")
    # Password validation criteria
    password_regex = re.compile(
        r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_\-+=<>?])[A-Za-z\d!@#$%^&*()_\-+=<>?]{12,}$"
    )

    if not password1 or not password2:
        flash("Please fill in both password fields.")
        return redirect(url_for("register_page"))

    if password1 != password2:
        flash("Passwords do not match.")
        return redirect(url_for("register_page"))

    if not password_regex.match(password1):
        flash("Password does not meet the required criteria.")
        return redirect(url_for("register_page"))

    # Generate a random key
    random_key = str(uuid.uuid4())

    # Store the random key and hashed password in Firebase Realtime Database
    ref = db.reference("users")
    ref.child(random_key).set(
        {"random_key": random_key, "password": generate_password_hash(password1)}
    )

    flash(
        f"Your registration key is: {random_key}. Please save it for future logins.",
        "success",
    )
    session["random_key"] = random_key
    logging.info("user registered with random key [" + random_key + "]")
    return redirect(url_for("register_page"))


@app.route("/register", methods=["GET"])
@redirect_if_logged_in  # Apply the redirect_if_logged_in decorator
def register_page():
    return render_template("register.html")


##### LogIN Firebase #####


@app.route("/login", methods=["POST"])
def login():
    random_key = request.form.get("random_key")
    password = request.form.get("password")
    if not random_key or not password:
        flash("Please fill in all fields.")
        return redirect(url_for("login_page"))
    user_data = USERS_REF.child(random_key).get()
    if not user_data:
        flash("Invalid random key.")
        return redirect(url_for("login_page"))
    stored_password_hash = user_data.get("password")
    if not stored_password_hash or not check_password_hash(
        stored_password_hash, password
    ):
        flash("Invalid password.")
        return redirect(url_for("login_page"))
    session["user_logged_in"] = True
    session["random_key"] = random_key  # Store the random_key in the session
    session["has_interacted"] = user_data.get(
        "has_interacted", False
    )  # Get interaction status
    session["first_login"] = "diagnosis" not in user_data
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET"])
@redirect_if_logged_in  # Apply the redirect_if_logged_in decorator
def login_page():
    return render_template("login.html")


##### LogOut Firebase #####
@app.route("/logout")
def logout():
    logging.debug("user logged out")
    session.pop("user_logged_in", None)
    logging.debug("setting user_logged_in flag to none")
    session.clear()
    logging.debug("session is cleared")
    session["new_session_can_start"] = True
    logging.debug("new_session_can_start is set to True")
    # flash('Successfully logged out!')
    return redirect(url_for("home"))


#####A function that doesn't alow to acces that page if you are not loged in ####


# def login_required(route_function):
#     @wraps(route_function)
#     def wrapper(*args, **kwargs):
#         if "user_logged_in" not in session:
#             flash("Please log in to access this page.")
#             return redirect(url_for("login_page"))
#         return route_function(*args, **kwargs)

#     return wrapper


def login_required(route_function):
    if asyncio.iscoroutinefunction(route_function):  # Check if function is async

        @wraps(route_function)
        async def async_wrapper(*args, **kwargs):
            if "user_logged_in" not in session:
                flash("Please log in to access this page.")
                return redirect(url_for("login_page"))
            return await route_function(*args, **kwargs)  # ✅ Await async route

        return async_wrapper
    else:

        @wraps(route_function)
        def sync_wrapper(*args, **kwargs):
            if "user_logged_in" not in session:
                flash("Please log in to access this page.")
                return redirect(url_for("login_page"))
            return route_function(*args, **kwargs)

        return sync_wrapper


@app.route("/therapy-transcription", methods=["GET", "POST"])
@login_required
async def therapy_transcription():
    bucket = storage.bucket()
    transcription = ""
    blobs = bucket.list_blobs(prefix=f"therapy_transcription/{session['random_key']}/")

    for blob in blobs:
        print(blob.name)
        file_name = os.path.basename(blob.name)
        print(file_name)
        blob = bucket.blob(blob.name)

        contents = blob.download_as_bytes()
        markdown_content = contents.decode("utf-8")
        html_content = convert_markdown_to_html(markdown_content)
        transcription += f"---{file_name}---\n{html_content}\n\n"

    print("transcription", transcription)

    return render_template("conversation.html", transcription=transcription)


# @app.route("/therapy-transcription", methods=["GET", "POST"])
# @login_required
# async def therapy_transcription():
#     bucket = storage.bucket()
#     transcription = ""
#     # blobs = bucket.list_blobs(prefix=f"therapy_transcription/{session['random_key']}/")
#     # List blobs asynchronously
#     blobs = await asyncio.to_thread(
#         bucket.list_blobs, prefix=f"therapy_transcription/{session['random_key']}/"
#     )
#     # Process each blob asynchronously
#     tasks = []
#     for blob in blobs:
#         tasks.append(process_blob(blob, bucket))

#     # Await results of processing all blobs
#     results = await asyncio.gather(*tasks)

#     # Combine transcription results
#     transcription = "\n".join(results)

#     return render_template("conversation.html", transcription=transcription)

#     # for blob in blobs:
#     #     print("====BLOB NAME====", blob.name)
#     #     file_name = os.path.basename(blob.name)
#     #     print("====FILE NAME====", file_name)
#     #     blob = bucket.blob(blob.name)

#     #     contents = blob.download_as_bytes()
#     #     markdown_content = contents.decode("utf-8")
#     #     html_content = convert_markdown_to_html(markdown_content)
#     #     transcription += f"---{file_name}---\n{html_content}\n\n"

#     # print("transcription", transcription)

#     # return render_template("conversation.html", transcription=transcription)
#     # Process each blob asynchronously


# async def process_blob(blob, bucket):
#     file_name = os.path.basename(blob.name)
#     contents = await download_blob(blob)
#     markdown_content = contents.decode("utf-8")
#     html_content = await asyncio.to_thread(convert_markdown_to_html, markdown_content)

#     # Combine into transcription format
#     return f"---{file_name}---\n{html_content}\n\n"


# # Async function to download blob contents
# async def download_blob(blob):
#     contents = await asyncio.to_thread(blob.download_as_bytes)
#     return contents


@app.route("/dashboard")
async def dashboard():
    random_key = session.get("random_key", "No key available")
    return render_template("dash_main.html", random_key=random_key)


######### Treatment Page #############
@app.route("/treatment")
@login_required
async def treatment():
    # user_data = get_user()
    user_data = await asyncio.to_thread(get_user)
    # Check completion flags
    personal_info_phase_1_complete = user_data.get(
        "personal_info_phase_1_completed", False
    )
    personal_info_phase_2_complete = user_data.get(
        "personal_info_phase_2_completed", False
    )
    personal_info_phase_3_complete = user_data.get(
        "personal_info_phase_3_completed", False
    )
    personal_info_complete = all(
        [
            personal_info_phase_1_complete,
            personal_info_phase_2_complete,
            personal_info_phase_3_complete,
        ]
    )
    # Redirect to the appropriate page if any step is incomplete
    if not personal_info_complete:
        return redirect(url_for("personal_info_phase_1"))

    return render_template("treatment.html")


###########################################personal info Page ########################################


@app.route("/personal_info_phase_1", methods=["GET", "POST"])
@login_required
async def personal_info_phase_1():
    user_data = await asyncio.to_thread(get_user)

    # Redirect to phase 2 if already completed
    if user_data.get("personal_info_phase_1_completed", False):
        return redirect(url_for("personal_info_phase_2"))

    if request.method == "POST":
        personal_info_responses = {}

        for index, question in enumerate(personal_info_questions_phase_1, start=1):
            topic = sanitize_key(question.get("topic", f"Topic {index}"))
            personal_info_responses[topic] = {}

            questions = question.get("questions")
            for index, question in enumerate(questions, start=1):
                question_info_type = sanitize_key(
                    question.get("info_type", f"Info type {index}")
                )

                if question["type"] == "group":
                    # Capture range and text input for the grouped question
                    score = request.form.get(f"{topic}_phase_1_score_{index}")
                    comments = request.form.get(f"{topic}_phase_1_comments_{index}")
                    # Log to console for debugging
                    personal_info_responses[topic][question_info_type] = {
                        "score": (str(score) if score else "0")
                        + "/100",  # Default to 0 if score is empty
                        "comments": (
                            comments if comments else None
                        ),  # Default to None if comments are empty
                    }

                else:
                    # Capture other question types normally
                    answer = request.form.get(f"{topic}_question_{index}")
                    # Anonymize answers
                    sanitized_prompt, is_valid, risk_score = scanner.scan(answer)

                    print("======PHASE 1 ANONYMIZE ANSWER======", sanitized_prompt)
                    # Log to console for debugging
                    # print(f"Received answer: {answer} for question {index}")

                    personal_info_responses[topic][question_info_type] = (
                        answer if answer else None
                    )  # Default to None if answer is empty

        # Update user data
        user_data["personal_info_phase_1_completed"] = True
        user_data["personal_info_responses_phase_1"] = personal_info_responses
        # Save updated user data to the database (offload to a separate thread)
        await asyncio.to_thread(USERS_REF.child(session["random_key"]).set, user_data)
        # Save updated user data to the database
        # USERS_REF.child(session["random_key"]).set(user_data)
        research_data("personal_info_responses_phase_1")
        # Call the agent to process the personal info responses
        # call_phase1_agent(user_data['personal_info_responses_phase_1'])

        return redirect(url_for("personal_info_phase_2"))

    return render_template(
        "personal_info_phase_1.html", questions=personal_info_questions_phase_1
    )


def research_data(data_ref, write_report=False):
    data = {
        "user_key": session["random_key"],
        "data_ref": data_ref,
        "write_report": write_report,
    }
    headers = {"Content-Type": "application/json"}

    print("==========RESEARCH DATA==========", data)
    """res = requests.post(
        'https://main-bvxea6i-hq3wucu75qstu.eu.platformsh.site/research-data',
        data=json.dumps(data),
        headers=headers
    )"""
    pool.apply_async(
        requests.post,
        args=[os.getenv("GPT_RESEACHER_BASE_URL") + "/research-data"],
        kwds={"data": json.dumps(data), "headers": headers},
    )
    print("==========END OF RESEARCH DATA==========")


async def generate_final_report():
    data = {"user_key": session["random_key"]}
    headers = {"Content-Type": "application/json"}

    print("==========FINAL REPORT==========", data)
    sanitized_prompt, is_valid, risk_score = scanner.scan(data)

    print("sanitized_prompt report", sanitized_prompt)
    pool.apply_async(
        requests.post,
        args=[os.getenv("GPT_RESEACHER_BASE_URL") + "/write-final-report"],
        kwds={"data": json.dumps(data), "headers": headers},
    )
    print("==========END OF FINAL REPORT==========")


async def get_recent_final_report():
    bucket = storage.bucket()
    blob = bucket.blob(f"research/{session['random_key']}/final_report.md")
    contents = blob.download_as_bytes()
    return contents.decode("utf-8")


##### Sahar added this to change Markdown text to Hyper Text(HTML)
async def convert_markdown_to_html(text):
    # Convert headers
    text = re.sub(r"### (.*)", r"<h4>\1</h4>", text)
    text = re.sub(r"## (.*)", r"<h3>\1</h3>", text)
    text = re.sub(r"# (.*)", r"<h2>\1</h2>", text)

    # Convert numbered lists
    text = re.sub(r"(\d+)\. ", r"<li>\1. ", text)
    text = re.sub(r"(\d+)\. (.*)", r"<li>\2</li>", text)

    # Wrap list items in <ul> tags
    text = re.sub(r"(<li>.*</li>)", r"<ul>\1</ul>", text)

    # Make text bold
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)

    # Make text italic
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)

    # Make text strikethrough
    text = re.sub(r"--(.*?)--", r"<del>\1</del>", text)

    # Wrap plain text in <p> tags
    lines = text.split("\n")
    for i in range(len(lines)):
        if not re.match(r"<h\d>|<ul>|<li>|<b>", lines[i]):
            lines[i] = f"<p>{lines[i]}</p>"
    text = "\n".join(lines)

    return text


#  def get_recent_final_report():
#     bucket = storage.bucket()
#     blob = bucket.blob(f"research/{session['random_key']}/final_report.md")
#     contents = blob.download_as_bytes()
#     return convert_markdown_to_html(contents.decode("utf-8"))


def sanitize_key(key):
    # Replace invalid characters with an underscore or remove them
    return (
        key.replace("$", "_")
        .replace("#", "_")
        .replace("[", "_")
        .replace("]", "_")
        .replace("/", "_")
        .replace(".", "_")
    )


@app.route("/personal_info_phase_2", methods=["GET", "POST"])
@login_required
async def personal_info_phase_2():
    # user_data = get_user()
    user_data = await asyncio.to_thread(get_user)

    # Redirect to phase 3 if phase 2 is already completed
    if user_data.get("personal_info_phase_2_completed", False):
        return redirect(url_for("personal_info_phase_3"))

    if request.method == "POST":
        personal_info_responses = {}

        for index, question in enumerate(personal_info_questions_phase_2, start=1):
            topic = sanitize_key(question.get("topic", f"Topic {index}"))
            personal_info_responses[topic] = {}

            questions = question.get("questions")
            for index, question in enumerate(questions, start=1):
                question_info_type = sanitize_key(
                    question.get("info_type", f"Info type {index}")
                )

                # Capture range and text input for the grouped question
                score = request.form.get(f"{topic}_phase_2_score_{index}")
                comments = request.form.get(f"{topic}_phase_2_comments_{index}")
                personal_info_responses[topic][question_info_type] = {
                    "score": (str(score) if score else "0")
                    + "/100",  # Default to None if score is empty
                    "comments": (
                        comments if comments else None
                    ),  # Default to None if comments are empty
                }

        # Update user data
        user_data["personal_info_phase_2_completed"] = True
        user_data["personal_info_responses_phase_2"] = personal_info_responses
        print("=======personal_info_responses========", personal_info_responses)
        # Anonymize comments in the provided data
        anonymized_data = anonymize_comments(personal_info_responses)
        # Anonymize user data
        # sanitized_prompt, is_valid, risk_score = scanner.scan(personal_info_responses)
        print("=====PHASE 2 ANONYMIZED ANSWER=====", anonymized_data)
        # Save updated user data to the database
        # USERS_REF.child(session["random_key"]).set(user_data)
        await asyncio.to_thread(USERS_REF.child(session["random_key"]).set, user_data)
        research_data("personal_info_responses_phase_2")
        return redirect(url_for("personal_info_phase_3"))
    return render_template(
        "personal_info_phase_2.html", questions=personal_info_questions_phase_2
    )


def anonymize_comments(data):
    # Iterate over the categories and their responses
    for category, responses in data.items():
        for question, answer in responses.items():
            # Get the comment value (which is either a string or None)
            comment = answer.get("comments")
            if comment:
                # Anonymize the comment if it exists
                sanitized_comment, is_valid, risk_score = scanner.scan(comment)
                answer["comments"] = sanitized_comment
    return data


def get_user():
    user_data = USERS_REF.child(session["random_key"]).get()
    return user_data


##### Reports Page #####
@app.route("/reports", methods=["GET", "POST"])
@login_required
async def reports():

    user_data = get_user()
    personal_info_phase_3_complete = user_data.get(
        "personal_info_phase_3_completed", False
    )
    # Fetch the reports (this is just a placeholder, replace with actual logic)
    reports = [
        {
            "id": "01",
            "title": "Diagnose Mental Disorder Report",
            "download": "",
            "url": "./first_report" if personal_info_phase_3_complete else "#",
        },
        {
            "id": "02",
            "title": "Therapy Session Reports",
            "download": ".",
            "url": "./therapy_sessions",
        },
        {
            "id": "03",
            "title": "Report 3",
            "download": "Content for report 3.",
            "url": "#",
        },
        {
            "id": "04",
            "title": "Report 4",
            "download": "Content for report 4.",
            "url": "#",
        },
        # >>>>>>> 8af9dc25e96f7522a2b96603aceb37231efa913e
    ]
    return render_template("reports.html", reports=reports)


@app.route("/sessions", methods=["GET", "POST"])
@login_required
async def sessions():
    return render_template("sessions.html")


##### first report Page #####
@app.route("/first_report", methods=["GET", "POST"])
@login_required
async def first_report():
    report_content = get_recent_final_report()
    return render_template("first_report.html", report_content=report_content)


@app.route("/personal_info_phase_3", methods=["GET", "POST"])
@login_required
async def personal_info_phase_3():
    # user_data = get_user()
    user_data = await asyncio.to_thread(get_user)

    # Redirect to phase 3 if phase 2 is already completed
    if user_data.get("personal_info_phase_3_completed", False):
        return redirect(url_for("treatment"))

    if request.method == "POST":
        personal_info_responses = {}

        for index, question in enumerate(personal_info_questions_phase_3, start=1):
            topic = sanitize_key(question.get("topic", f"Topic {index}"))
            personal_info_responses[topic] = {}

            questions = question.get("questions")
            for index, question in enumerate(questions, start=1):
                question_info_type = sanitize_key(
                    question.get("info_type", f"Info type {index}")
                )

                # Capture range and text input for the grouped question
                score = request.form.get(f"{topic}_phase_3_score_{index}")
                comments = request.form.get(f"{topic}_phase_3_comments_{index}")
                personal_info_responses[topic][question_info_type] = {
                    "score": (str(score) if score else "0")
                    + "/100",  # Default to None if score is empty
                    "comments": (
                        comments if comments else None
                    ),  # Default to None if comments are empty
                }

        # Update user data
        user_data["personal_info_phase_3_completed"] = True
        user_data["personal_info_responses_phase_3"] = personal_info_responses
        anonymized_data = anonymize_comments(personal_info_responses)
        # Anonymize user data
        # sanitized_prompt, is_valid, risk_score = scanner.scan(personal_info_responses)
        print("=====PHASE 3 ANONYMIZED ANSWER=====", anonymized_data)
        # Save updated user data to the database
        # USERS_REF.child(session["random_key"]).set(user_data)
        await asyncio.to_thread(USERS_REF.child(session["random_key"]).set, user_data)
        research_data("personal_info_responses_phase_3", write_report=True)
        return redirect(url_for("treatment"))
    return render_template(
        "personal_info_phase_3.html", questions=personal_info_questions_phase_3
    )


@app.route("/therapy_sessions", methods=["GET", "POST"])
@login_required
async def therapy_sessions():
    if "random_key" not in session:
        return "User not authenticated", 401

    random_key = session["random_key"]
    prefix = f"{THERAPY_SESSION_PREFIX}{random_key}/"
    # Offload the blocking I/O to a separate thread
    blobs = await asyncio.to_thread(storage.bucket().list_blobs, prefix=prefix)
    # bucket = storage.bucket()
    # blobs = bucket.list_blobs(prefix=prefix)

    summaries = []
    for blob in blobs:
        if blob.name.endswith(".md"):
            filename = blob.name.split("/")[-1]
            timestamp_str = filename.replace(THERAPY_PREFIX, "").replace(".md", "")

            # Convert Unix timestamp to readable format
            try:
                timestamp = datetime.utcfromtimestamp(int(timestamp_str))
                formatted_date = timestamp.strftime("%d/%m/%y")  # Convert to dd/mm/yy
            except ValueError:
                formatted_date = "Unknown Date"

            summaries.append(
                {
                    "filename": filename,
                    "timestamp": formatted_date,
                    "raw_timestamp": int(timestamp_str),
                }
            )

    # Sorting Summaries: Most Recent First
    summaries.sort(key=lambda x: x["raw_timestamp"], reverse=True)
    return render_template("therapy_sessions.html", summaries=summaries)


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


@app.route("/appointment", methods=["GET", "POST"])
@login_required
def appointment():
    return render_template("appointment.html")


#### web3 routes ####
@app.route("/nonce")
def nonce():
    wallet_address = request.args.get("walletAddress")
    nonce = str(random.randint(1, 10000))
    nonce_id = f"{nonce}-{datetime.now().timestamp()}"
    created_at = datetime.now()

    # Check if wallet address already exists in Firestore
    doc_ref = WALLETS_REF.document(wallet_address)
    doc = doc_ref.get()

    if doc.exists:
        # Wallet address already exists, update the nonce and updatedAt
        doc_ref.update({"nonce": nonce_id, "updatedAt": datetime.now()})
    else:
        # Wallet address does not exist, insert a new document with createdAt
        WALLETS_REF.document(wallet_address).set(
            {
                "wallet_address": wallet_address,
                "nonce": nonce_id,
                "createdAt": created_at,
                "updatedAt": created_at,
            }
        )

    return jsonify({"nonce": nonce_id})


@app.route("/verify", methods=["GET"])
def verify_signature():
    wallet_address = request.args.get("walletAddress")
    doc_ref = WALLETS_REF.document(wallet_address)
    doc = doc_ref.get()
    if doc.exists:
        response = make_response(jsonify({"success": True}))
        response.set_cookie("walletAddress", wallet_address)
        return response
    else:
        return jsonify({"success": False, "error": "Wallet address not found"})


@app.route("/check")
def check_session():
    wallet_address = request.cookies.get("walletAddress")
    if wallet_address:
        # Check if wallet address exists in Firestore
        doc_ref = WALLETS_REF.document(wallet_address)
        doc = doc_ref.get()
        if doc.exists:
            return jsonify({"success": True, "walletAddress": wallet_address})
        else:
            return jsonify(
                {"success": False, "error": "Wallet address not found in Firestore"}
            )
    else:
        return jsonify({"success": False})


@app.route("/disconnect")
def disconnect():
    response = make_response(jsonify({"success": True}))
    response.set_cookie("walletAddress", "", expires=0)
    return response


@app.route("/health", methods=["GET"])
async def check_health():
    return {"status": "OK"}, 200


### end web3 routes ####


################################################################### MY CODE ####################################################################


@app.route("/summaries", methods=["GET", "POST"])
@login_required
async def list_summaries():
    if "random_key" not in session:
        return "User not authenticated", 401

    random_key = session["random_key"]
    prefix = f"{THERAPY_SESSION_PREFIX}{random_key}/"
    # Offload the blocking I/O to a separate thread
    blobs = await asyncio.to_thread(storage.bucket().list_blobs, prefix=prefix)
    # bucket = storage.bucket()
    # blobs = bucket.list_blobs(prefix=prefix)

    summaries = []
    for blob in blobs:
        if blob.name.endswith(".md"):
            filename = blob.name.split("/")[-1]
            timestamp_str = filename.replace(THERAPY_PREFIX, "").replace(".md", "")

            # Convert Unix timestamp to readable format
            try:
                timestamp = datetime.utcfromtimestamp(int(timestamp_str))
                formatted_date = timestamp.strftime("%d/%m/%y")  # Convert to dd/mm/yy
            except ValueError:
                formatted_date = "Unknown Date"

            summaries.append(
                {
                    "filename": filename,
                    "timestamp": formatted_date,
                    "raw_timestamp": int(timestamp_str),
                }
            )

    # Sorting Summaries: Most Recent First
    summaries.sort(key=lambda x: x["raw_timestamp"], reverse=True)

    return render_template("therapy_sessions.html", summaries=summaries)


@app.route("/summary-reporting", methods=["GET", "POST"])
@login_required
async def summary_reporting():
    filename = request.args.get("file")
    if not filename:
        return "No summary specified", 400

    random_key = session.get("random_key")
    if not random_key:
        return "User not authenticated", 401

    # Fetch the summary content
    summary_file_path = f"{THERAPY_SESSION_PREFIX}{random_key}/{filename}"
    bucket = storage.bucket()
    summary_blob = bucket.blob(summary_file_path)
    # Offload the blocking I/O operation to a separate thread
    summary_content = await asyncio.to_thread(summary_blob.download_as_text)

    summary_content = summary_blob.download_as_text()

    # Convert the summary markdown content to HTML
    html_summary_content = convert_markdown_to_html(summary_content)

    # Adjust the filename for the transcription
    transcription_filename = (
        filename  # Since both summary and transcription have the same filename
    )
    transcription_file_path = (
        f"{THERAPY_TRANSCRIPTION_PREFIX}{random_key}/{transcription_filename}"
    )
    transcription_blob = bucket.blob(transcription_file_path)

    try:
        # Offload the blocking I/O operation to a separate thread for transcription
        transcription_content = await asyncio.to_thread(
            transcription_blob.download_as_text
        )
        # transcription_content = transcription_blob.download_as_text()
        # Convert the transcription markdown content to HTML
        html_transcription_content = convert_markdown_to_html(transcription_content)
    except NotFound:
        html_transcription_content = (
            "<p>No transcription available for this summary.</p>"
        )

    # Combine the summary and transcription content
    combined_content = (
        f"{html_summary_content}<hr><h2>Transcription</h2>{html_transcription_content}"
    )
    # Add anonymize
    sanitized_prompt, is_valid, risk_score = scanner.scan(combined_content)
    print("=====ANONYMIZE PROMPT=====", sanitized_prompt)
    return render_template("summary.html", summary=combined_content)


@app.route("/check_summary_status", methods=["GET"])
@login_required
async def check_summary_status():
    random_key = session.get("random_key")
    if not random_key:
        return jsonify({"status": "unauthorized"}), 401

    last_audio_report_suffix = session.get("last_audio_report_suffix")
    if not last_audio_report_suffix:
        return jsonify({"status": "pending"})  # No new recording found

    # Construct expected filename based on the latest session
    expected_filename = (
        f"therapy_session/{random_key}/therapy_{last_audio_report_suffix}.md"
    )

    # Offload the blocking check to a separate thread (e.g., check if the file exists)
    file_exists = await asyncio.to_thread(file_exists_check, expected_filename)

    if file_exists:
        return jsonify({"status": "completed"})  # File exists and summary is ready
    else:
        return jsonify({"status": "pending"})  # File doesn't exist yet


def file_exists_check(filename):
    bucket = storage.bucket()
    blob = bucket.blob(filename)
    return blob.exists()


# Helper function to list blobs with a given prefix
def list_blobs_with_prefix(bucket, prefix):
    return list(bucket.list_blobs(prefix=prefix))


@app.route("/most_recent_summary", methods=["GET"])
@login_required
async def most_recent_summary():
    random_key = session.get("random_key")
    if not random_key:
        return "User not authenticated", 401

    # Fetch the most recent summary
    prefix = f"{THERAPY_SESSION_PREFIX}{random_key}/"
    bucket = storage.bucket()
    blobs = bucket.list_blobs(prefix=prefix)
    # Offload blob listing and processing to a separate thread
    blobs = await asyncio.to_thread(list_blobs_with_prefix, bucket, prefix)
    most_recent_blob = None
    most_recent_timestamp = 0
    for blob in blobs:
        if blob.name.endswith(".md"):
            timestamp_str = (
                blob.name.split("/")[-1].replace(THERAPY_PREFIX, "").replace(".md", "")
            )
            try:
                timestamp = int(timestamp_str)
                if timestamp > most_recent_timestamp:
                    most_recent_timestamp = timestamp
                    most_recent_blob = blob
            except ValueError:
                continue

    if not most_recent_blob:
        return "No summaries found", 404
    # Offload the downloading and conversion to HTML
    summary_content = await asyncio.to_thread(most_recent_blob.download_as_text)
    # summary_content = most_recent_blob.download_as_text()
    html_summary_content = convert_markdown_to_html(summary_content)

    transcription_filename = most_recent_blob.name.replace(THERAPY_PREFIX, "")
    # transcription_blob = bucket.blob(transcription_filename)
    transcription_blob = bucket.blob(
        f"{THERAPY_TRANSCRIPTION_PREFIX}{random_key}/{transcription_filename}"
    )

    try:
        # transcription_content = transcription_blob.download_as_text()
        # Offload transcription download and conversion to HTML
        transcription_content = await asyncio.to_thread(
            transcription_blob.download_as_text
        )
        html_transcription_content = convert_markdown_to_html(transcription_content)
    except NotFound:
        html_transcription_content = (
            "<p>No transcription available for this summary.</p>"
        )

    combined_content = f"<h2>Summary</h2>{html_summary_content}<hr><h2>Transcription</h2>{html_transcription_content}"

    return render_template("summary.html", summary=combined_content)


from llm_guard.vault import Vault
from llm_guard.input_scanners import Anonymize
from llm_guard.input_scanners.anonymize_helpers import BERT_LARGE_NER_CONF

vault = Vault()

scanner = Anonymize(
    vault,
    preamble="",
    allowed_names=[],
    hidden_names=["*"],
    recognizer_conf=BERT_LARGE_NER_CONF,
)


@app.route("/anonymize", methods=["POST"])
async def anonymize_data():
    data = request.get_json()
    if "prompt" not in data:
        return jsonify({"error": "Missing 'prompt' field"}), 400
    prompt = data["prompt"]
    if prompt is None:
        return jsonify({"error": "Prompt cannot be None"}), 400
    sanitized_prompt, is_valid, risk_score = scanner.scan(data["prompt"])
    # Offload the sanitization process to a separate thread
    # sanitized_prompt, is_valid, risk_score = await asyncio.to_thread(
    #     scanner.scan, data["prompt"]
    # )

    return jsonify(
        {
            "sanitized_prompt": sanitized_prompt,
            "is_valid": is_valid,
            "risk_score": risk_score,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)

    # # Configure the logging system
    # logging.basicConfig(
    #     level=DEBUG,
    #     format='%(asctime)s [%(levelname)s] - %(message)s',
    #     handlers=[
    #         logging.FileHandler('appreg.log'),  # Output to a log file
    #     ]
    # )
    # logger = logging.getLogger(__name__)
    # serverHost = os.getenv('host')
    # serverPort = os.getenv('port')
    # app.run(host=serverHost,port=serverPort, debug=os.getenv('debug') )
