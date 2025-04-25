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
from markupsafe import Markup
from flask_session import Session
import re
import firebase_admin
from firebase_admin import credentials, db, firestore, storage
import uuid
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask import session
from dotenv import load_dotenv
import json
import logging
import os
import requests
import time
import shutil
from logger import logger
import aiohttp
import asyncio
import hashlib
from mnemonic import Mnemonic
from functools import wraps
import requests
import requests
from concurrent.futures import ThreadPoolExecutor
import datetime
import random
from questions.personal_info import (
    personal_info_questions_phase_1,
    personal_info_questions_phase_2,
    personal_info_questions_phase_3,
)
import datetime
from multiprocessing.dummy import Pool
import os
from google.api_core.exceptions import NotFound
import subprocess
import asyncio
from pydub import AudioSegment
from pydub.silence import split_on_silence
from tqdm import tqdm
import os
import asyncio
import threading
from google.cloud import pubsub_v1
from google.oauth2 import service_account
import shutil

THERAPY_SESSION_PREFIX = "therapy_session"
THERAPY_TRANSCRIPTION_PREFIX = "therapy_transcription/transcription"
THERAPY_DIARIZATION_PREFIX = "therapy_transcription/diarization"
THERAPY_PREFIX = "therapy_"

pool = Pool(5)
app = Flask(__name__, static_folder="static")
app.secret_key = "your_secret_key_here"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)
load_dotenv()
DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL")
TRANSCRIPTION_API_URL = os.getenv("TRANSCRIPTION_API_URL")
result = []
# Directories
UPLOADED_DIR = "uploaded_audio"
OUTPUT_DIR = "processed_chunks"
os.makedirs(UPLOADED_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
PUB_SUB_KEY = os.getenv("PUB_SUB_KEY")

transcription_results = {}
transcription_lock = asyncio.Lock()  # Prevent race conditions
abs_path = ""
audio_file_name = ""
processing_files = {}
### Google Cloud pub/sub setup ###
gg_credentials = service_account.Credentials.from_service_account_file(PUB_SUB_KEY)
publisher = pubsub_v1.PublisherClient(credentials=gg_credentials)
subscriber = pubsub_v1.SubscriberClient(credentials=gg_credentials)
GG_PROJECT_ID = os.getenv("GG_PROJECT_ID")
GG_TOPIC_ID = os.getenv("GG_TOPIC_ID")
topic_path = publisher.topic_path(GG_PROJECT_ID, "audio-transcriptions")
GG_SUBSCRIPTION_ID = os.getenv("GG_SUBSCRIPTION_ID")
subscription_path = subscriber.subscription_path(GG_PROJECT_ID, GG_SUBSCRIPTION_ID)


#### 🙌🏼 CHUNKING AUDIO AND PUSH TO FIREBASE 🙌🏼 ####
user_key = None


def set_user_key(new_user_key):
    global user_key
    user_key = new_user_key
    return user_key


def get_user_key():
    return user_key


def upload_audio_to_firebase(local_file_path, firebase_path, num_chunks):
    """
    Uploads an audio file to Firebase Storage and returns its public URL.
    """
    global chunk_urls
    chunk_urls = []
    num_chunks += 1
    try:
        blob = bucket.blob(firebase_path)
        abs_folder_path = os.path.abspath(local_file_path)
        blob.upload_from_filename(abs_folder_path)
        # Make the file publicly accessible
        blob.make_public()
        folder_id = firebase_path.split("/")[2]
        logger.warning(f"FOLDER ID: {folder_id}")

        # Get the public URL
        url = blob.public_url
        user_key = get_user_key()
        logger.info(f"USER KEY : {user_key}")
        if url not in chunk_urls:  # Ensure unique URLs

            chunk_urls.append(url)
            attributes = {
                "user_key": user_key,
                "folder_id": folder_id,
                "total_chunks": str(num_chunks),
            }
            logger.warning(f"TOTAL CHUNKS: {num_chunks}")
            future = publisher.publish(topic_path, url.encode("utf-8"), **attributes)
            message_id = future.result()
            logger.info(f"message_id: {message_id}")
        if os.path.exists(abs_folder_path):
            os.remove(abs_folder_path)
        else:
            logger.warning(f"Local file {local_file_path} not found for deletion.")
        return None
    except Exception as e:
        logger.error(f"Error uploading {local_file_path}: {e}")
        return None


def save_chunk(chunk, start_time, output_dir, output_format, file_name):
    """
    Save audio chunk to disk and return the path - does NOT upload to Firebase
    """
    file_name_without_extension = os.path.splitext(file_name)[0]
    file_output_dir = os.path.join(output_dir, file_name_without_extension)
    res = os.makedirs(file_output_dir, exist_ok=True)
    chunk_path = os.path.join(file_output_dir, f"chunk_{start_time}.{output_format}")
    result_chunk = chunk.export(chunk_path, format=output_format)
    return chunk_path


def upload_chunks_to_firebase(chunk_folder, num_chunks):
    """
    Upload all chunks in a folder to Firebase (called ONCE after all chunks are processed)
    """
    if not os.path.exists(chunk_folder):
        logger.error(f"Folder does not exist: {chunk_folder}")
        return []
    user_key = get_user_key()
    folder_name = os.path.basename(chunk_folder)
    folder_name = folder_name.split(".")[0]
    firebase_folder_path = f"audio_chunks/{user_key}/{folder_name}/"

    file_urls = []
    for filename in os.listdir(chunk_folder):
        file_path = os.path.join(chunk_folder, filename)
        abs_folder_path = os.path.abspath(file_path)
        if os.path.isfile(file_path) and filename.endswith(".wav"):
            firebase_file_path = firebase_folder_path + filename
            file_url = upload_audio_to_firebase(
                abs_folder_path, firebase_file_path, num_chunks
            )
            if file_url and file_url not in file_urls:
                file_urls.append(file_url)
    return file_urls


def merge_short_chunks(chunks, min_chunk_length_ms):
    merged_chunks = []
    current_chunk = chunks[0]
    for chunk in chunks[1:]:
        if len(current_chunk) + len(chunk) < min_chunk_length_ms:
            current_chunk += chunk
        else:
            merged_chunks.append(current_chunk)
            current_chunk = chunk

    merged_chunks.append(current_chunk)
    return merged_chunks


def split_audio_internal(
    filename, chunk_length_ms=120000, output_format="wav", silence_based=False
):
    input_file = os.path.join(UPLOADED_DIR, filename)
    if not os.path.exists(input_file):
        return {"error": "File not found"}
    audio = AudioSegment.from_file(input_file)
    chunk_paths = []
    file_name_without_extension = os.path.splitext(filename)[0]
    output_subfolder = os.path.join(OUTPUT_DIR, file_name_without_extension)
    output_subfolder = os.path.abspath(output_subfolder)
    if silence_based:
        min_silence_len = 100
        silence_thresh = -40
        chunks = split_on_silence(
            audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh
        )
        chunks = merge_short_chunks(chunks, chunk_length_ms)
        pbar = tqdm(total=len(chunks), desc="Processing chunks based on silence")

        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    save_chunk, chunk, i, OUTPUT_DIR, output_format, filename
                )
                for i, chunk in enumerate(chunks)
            ]
            for future in futures:
                chunk_paths.append(future.result())
                pbar.update(1)

    else:
        audio_length_ms = len(audio)
        num_chunks = audio_length_ms // chunk_length_ms
        pbar = tqdm(
            total=num_chunks + (audio_length_ms % chunk_length_ms != 0),
            desc="Processing fixed-size chunks",
        )

        with ThreadPoolExecutor() as executor:
            for i in range(num_chunks):
                start_time = i * chunk_length_ms
                chunk = audio[start_time : start_time + chunk_length_ms]
                chunk_paths.append(
                    executor.submit(
                        save_chunk,
                        chunk,
                        start_time,
                        OUTPUT_DIR,
                        output_format,
                        filename,
                    ).result()
                )
                pbar.update(1)

            if audio_length_ms % chunk_length_ms != 0:
                start_time = num_chunks * chunk_length_ms
                chunk = audio[start_time:]
                chunk_paths.append(
                    executor.submit(
                        save_chunk,
                        chunk,
                        start_time,
                        OUTPUT_DIR,
                        output_format,
                        filename,
                    ).result()
                )
                pbar.update(1)

    pbar.close()
    upload_chunks_to_firebase(output_subfolder, num_chunks)
    if os.path.exists(input_file):
        os.remove(input_file)
    else:
        logger.warning(f"WAV file not found for deletion")

    if os.path.exists(output_subfolder) and not os.listdir(output_subfolder):
        shutil.rmtree(output_subfolder)
    return {"message": "Audio processed successfully", "chunks": chunk_paths}


def process_audio(
    filename: str,
    chunk_length: int = 120000,
    output_format: str = "wav",
    silence_based: bool = False,
):
    return split_audio_internal(filename, chunk_length, output_format, silence_based)


#### 🙌🏼 CHUNKING AUDIO AND PUSH TO FIREBASE 🙌🏼 ####


@app.route("/generate_summary", methods=["POST"])
def generate_summary():
    user_key = session["random_key"]
    set_user_key(user_key)
    global processing_flag
    if "audio_file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    audio_file = request.files["audio_file"]
    try:
        local_audio_path = os.path.join(UPLOADED_DIR, audio_file.filename)
        result_audio_save = audio_file.save(local_audio_path)
        file_name = f"{audio_file.filename}.wav"
        wav_audio_path = f"{local_audio_path}.wav"
        converted_file_name = convert_webm_to_wav(local_audio_path, wav_audio_path)
        processing_files[file_name] = True
        abs_audio_path = os.path.abspath(wav_audio_path)
        thread = threading.Thread(target=process_audio, args=(file_name,))
        thread.start()
        if not processing_files[file_name]:
            return jsonify({"file_name": "processing..."}), 200
        os.remove(f"uploaded_audio/{audio_file.filename}")
        return jsonify({"file_name": file_name}), 200

    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        return jsonify({"error": "Audio processing failed"}), 500
    finally:
        pass


def sanitize_filename(filename: str) -> str:
    return re.sub(r"[^\w\s-]", "", filename).strip()


def convert_webm_to_wav(input_file, output_file):
    """Function to convert WebM to WAV using FFmpeg."""
    command = [
        "ffmpeg",
        "-i",
        input_file,  # Input WebM file
        output_file,  # Output WAV file
    ]
    subprocess.run(command, check=True)


@app.route("/", methods=["GET", "POST"])
def home():
    cards = [
        {
            "title": "Time-Efficient Therapy",
            "text": "By automating documentation and administrative tasks, therapists can devote their full attention to patient care. This increased efficiency reduces the number of sessions needed, making therapy quicker and more effective.",
        },
        {
            "title": "Privacy by Design",
            "text": "We prioritize your privacy. Our system does not collect personal information. Instead, we generate a unique key that serves as your identifier within the app, ensuring your data remains secure and anonymous.",
        },
        {
            "title": "Streamlined Administrative Workflow",
            "text": "Therapists typically spend 30-40% of session time on manual documentation. Our app automates this process, freeing up more time for patient care and enhancing the overall quality of therapy.",
        },
        {
            "title": "Pre-Intake Questionnaires and Analysis",
            "text": "Before therapy, patients complete dynamic questionnaires, and the app analyzes their responses to provide therapists with valuable insights into risks and key concerns. It also offers evidence-based resources, promoting time-saving, deeper insights, and more informed care.",
        },
        {
            "title": "Therapy Session Summaries",
            "text": "Our AI-powered app generates clear and accurate therapy session summaries, capturing key points and insights. Saving therapists valuable time. By automating note-taking, therapists can focus on patient care, improve continuity, and reduce mental strain, making therapy more efficient and effective.",
        },
        {
            "title": "Diagnoses",
            "text": "By analyzing both the patient’s responses and key insights from the session, the app helps therapists form a comprehensive understanding of the patients condition, our app make a evidence-based diagnoses.",
        },
    ]
    doctors = [
        {
            "name": "Dr. Joseph Morgan",
            "specialty": "Psychiatrist",
            "message": "I recommend this website for therapists and psychologists as a good source for per-session  with your patients to find necessary data and possible disorders",
            "image": "./static/assets/img/dr1.png",
        },
        {
            "name": "Dr. Elena Gilbert",
            "specialty": "Clinical Psychologist",
            "message": "I recommend this website for therapists and psychologists as a good source for per-session  with your patients to find necessary data and possible disorders",
            "image": "./static/assets/img/dr2.png",
        },
        {
            "name": "Dr. Laura Greens",
            "specialty": "Therapist",
            "message": "I recommend this website for therapists and psychologists as a good source for per-session  with your patients to find necessary data and possible disorders",
            "image": "./static/assets/img/dr3.png",
        },
        {
            "name": "Dr. Emily Johnson1",
            "specialty": "Therapist",
            "message": "I recommend this website for therapists and psychologists as a good source for per-session  with your patients to find necessary data and possible disorders",
            "image": "./static/assets/img/dr1.png",
        },
        {
            "name": "Dr. Emily Johnson2",
            "specialty": "Therapist",
            "message": "I recommend this website for therapists and psychologists as a good source for per-session  with your patients to find necessary data and possible disorders",
            "image": "./static/assets/img/dr2.png",
        },
        {
            "name": "Dr. Emily Johnson3",
            "specialty": "Therapist",
            "message": "I recommend this website for therapists and psychologists as a good source for per-session  with your patients to find necessary data and possible disorders",
            "image": "./static/assets/img/dr3.png",
        },
        # Add more doctors as needed
    ]
    random_key = session.get("random_key", "No key available")
    logging.debug("redirecting index.html")
    return render_template(
        "index.html", cards=cards, doctors=doctors, random_key=random_key
    )


### Firebase ###
cred = credentials.Certificate(os.getenv("FIREBASE_DATABASE_CERTIFICATE"))
firebase_admin.initialize_app(
    cred,
    {"databaseURL": DATABASE_URL, "storageBucket": os.getenv("STORAGE_BUCKET")},
)
bucket = storage.bucket()
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


########################################## Code for Registration, Login, logout, Recover and Reset Accounts ##########################################
# Generate a mnemonic phrase using the Mnemonic library
def generate_mnemonic_phrase(random_key):
    mnemo = Mnemonic("english")
    seed = random_key.encode("utf-8")
    mnemonic_phrase = mnemo.generate(strength=128)

    return mnemonic_phrase


##### Register Firebase #####
@app.route("/register", methods=["POST"])
def register():
    password1 = request.form.get("pass")
    password2 = request.form.get("pass2")
    password_regex = re.compile(
        r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_\-+=<>?])[A-Za-z\d!@#$%^&*()_\-+=<>?]{12,}$"
    )

    if not password1 or not password2:
        flash("Please fill in both password fields.", "error")
        return redirect(url_for("register_page"))

    if password1 != password2:
        flash("Passwords do not match.", "error")
        return redirect(url_for("register_page"))

    if not password_regex.match(password1):
        flash("Password does not meet the required criteria.", "error")
        return redirect(url_for("register_page"))

    # Generate mnemonic phrase
    mnemo = Mnemonic("english")
    mnemonic_phrase = mnemo.generate(strength=128)

    # Derive random_key from the mnemonic phrase
    seed = mnemonic_phrase.encode("utf-8")
    random_key = hashlib.sha256(seed).hexdigest()

    # Hash the password before storing
    hashed_password = generate_password_hash(password1)

    # Store in session for display
    session["random_key"] = random_key
    session["mnemonic_phrase"] = mnemonic_phrase
    print(f"mnemonic_phrase: {mnemonic_phrase}")
    print(f"random_key: {random_key}")

    # Save user data in Firebase
    USERS_REF.child(random_key).set(
        {"password": hashed_password, "random_key": random_key}
    )

    flash(
        f"Registration successful! Your registration key is: {random_key}. Please save it for future logins.",
        "success",
    )

    logging.info("User registered with random key [" + random_key + "]")
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


@app.route("/recover_username", methods=["GET", "POST"])
def recover_username():
    if request.method == "POST":
        mnemonic_phrase = request.form.get(
            "mnemonic_phrase"
        ).strip()  # Strip whitespace
        password = request.form.get("password")

        # Validate mnemonic phrase
        mnemo = Mnemonic("english")
        if not mnemo.check(mnemonic_phrase):
            return jsonify({"error": "Invalid recovery key. Please try again."}), 400

        # Derive the random key from the mnemonic phrase
        seed = mnemonic_phrase.encode("utf-8")
        random_key = hashlib.sha256(seed).hexdigest()

        # Check if the random key exists in the database
        user_data = USERS_REF.child(random_key).get()
        if not user_data:
            return jsonify({"error": "Invalid recovery key or user not found."}), 400

        # Validate the password
        stored_password_hash = user_data.get("password")
        if not stored_password_hash or not check_password_hash(
            stored_password_hash, password
        ):
            return jsonify({"error": "Invalid password. Please try again."}), 400

        # If both validations pass, store the random key in the session
        session["random_key"] = random_key
        return jsonify({"random_key": random_key}), 200

    return render_template("recover_username.html")


@app.route("/recover_password", methods=["GET", "POST"])
def recover_password():
    if request.method == "POST":
        try:
            mnemonic_phrase = request.form.get("mnemonic_phrase").strip()
            random_key = request.form.get("random_key").strip()

            # Validate mnemonic phrase
            mnemo = Mnemonic("english")
            if not mnemo.check(mnemonic_phrase):
                return (
                    jsonify({"error": "Invalid recovery key. Please try again."}),
                    400,
                )

            # Derive the random key from the mnemonic phrase
            seed = mnemonic_phrase.encode("utf-8")
            derived_random_key = hashlib.sha256(seed).hexdigest()

            # Check if the derived random key matches the submitted random key
            if derived_random_key != random_key:
                return (
                    jsonify({"error": "Recovery Key and username do not match."}),
                    400,
                )

            # Check if the random key exists in the database
            user_data = USERS_REF.child(random_key).get()
            if not user_data:
                return jsonify({"error": "User not found."}), 400

            # If everything is valid, return success
            return jsonify({"success": True}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return render_template("recover_password.html")


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if "random_key" not in session:
        flash("You must recover your account first.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if new_password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("reset_password"))

        random_key = session["random_key"]

        # Update the password in the Firebase database
        ref = db.reference("users")
        ref.child(random_key).update({"password": generate_password_hash(new_password)})

        flash("Password reset successful! You can now log in.", "success")
        return redirect(url_for("login"))
    return render_template("reset_password.html")


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
    return redirect(url_for("home"))


########################################## End of Code for Registration, Login, Recover Accounts #########################################
#####A function that doesn't alow to acces that page if you are not loged in ####


def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "user_logged_in" not in session:
            flash("Please log in to access this page.")
            return redirect(url_for("login_page"))
        return route_function(*args, **kwargs)

    return wrapper


@app.route("/general_summary", methods=["GET"])
@login_required
def general_summary():
    bucket = storage.bucket()
    summary = ""
    blobs = bucket.list_blobs(
        prefix=f"therapy_transcription/summary/{session['random_key']}/"
    )

    for blob in blobs:
        print(blob.name)
        file_name = os.path.basename(blob.name)
        print(file_name)
        blob = bucket.blob(blob.name)

        contents = blob.download_as_bytes()
        markdown_content = contents.decode("utf-8")
        html_content = convert_markdown_to_html(markdown_content)
        summary += f"---{file_name}---\n{html_content}\n\n"

    return render_template("summary.html", summary=summary)


@app.route("/therapy-transcription", methods=["GET", "POST"])
@login_required
def therapy_transcription():
    bucket = storage.bucket()
    transcription = ""
    blobs = bucket.list_blobs(
        prefix=f"therapy_transcription/transcription/{session['random_key']}/"
    )

    for blob in blobs:
        print(blob.name)
        file_name = os.path.basename(blob.name)
        print(file_name)
        blob = bucket.blob(blob.name)

        contents = blob.download_as_bytes()
        markdown_content = contents.decode("utf-8")
        html_content = convert_markdown_to_html(markdown_content)
        transcription += f"---{file_name}---\n{html_content}\n\n"

    return render_template("conversation.html", transcription=transcription)


@app.route("/therapy-diarization", methods=["GET", "POST"])
@login_required
def therapy_diarization():
    bucket = storage.bucket()
    diarization = ""
    blobs = bucket.list_blobs(
        prefix=f"therapy_transcription/diarization/{session['random_key']}/"
    )

    for blob in blobs:
        print(blob.name)
        file_name = os.path.basename(blob.name)
        print(file_name)
        blob = bucket.blob(blob.name)

        contents = blob.download_as_bytes()
        markdown_content = contents.decode("utf-8")
        html_content = convert_markdown_to_html(markdown_content)
        diarization += f"---{file_name}---\n{html_content}\n\n"

    return render_template("conversation2.html", diarization=diarization)


@app.route("/dashboard")
def dashboard():
    random_key = session.get("random_key", "No key available")
    return render_template("dash_main.html", random_key=random_key)


######### Treatment Page #############
@app.route("/treatment")
@login_required
def treatment():
    user_data = get_user()
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
def personal_info_phase_1():
    user_data = get_user()

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
                    # Log to console for debugging
                    print(f"Received answer: {answer} for question {index}")

                    personal_info_responses[topic][question_info_type] = (
                        answer if answer else None
                    )  # Default to None if answer is empty

        # Update user data
        user_data["personal_info_phase_1_completed"] = True
        user_data["personal_info_responses_phase_1"] = personal_info_responses

        # Save updated user data to the database
        USERS_REF.child(session["random_key"]).set(user_data)
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

    print("data", data)
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
    print("end of research_data")


def generate_final_report():
    data = {"user_key": session["random_key"]}
    headers = {"Content-Type": "application/json"}

    print("data", data)
    pool.apply_async(
        requests.post,
        args=[os.getenv("GPT_RESEACHER_BASE_URL") + "/write-final-report"],
        kwds={"data": json.dumps(data), "headers": headers},
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


def get_recent_final_report():
    bucket = storage.bucket()
    blob = bucket.blob(f"research/{session['random_key']}/final_report.md")
    contents = blob.download_as_bytes()
    return convert_markdown_to_html(contents.decode("utf-8"))


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
def personal_info_phase_2():
    user_data = get_user()

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

        # Save updated user data to the database
        USERS_REF.child(session["random_key"]).set(user_data)
        research_data("personal_info_responses_phase_2")
        return redirect(url_for("personal_info_phase_3"))
    return render_template(
        "personal_info_phase_2.html", questions=personal_info_questions_phase_2
    )


def get_user():
    user_data = USERS_REF.child(session["random_key"]).get()
    return user_data


##### Reports Page #####
@app.route("/reports", methods=["GET", "POST"])
@login_required
def reports():
    reports = [
        {
            "id": "01",
            "title": "Diagnose Mental Disorder Report",
            "download": "",
            "url": "./first_report",
        },
    ]
    return render_template("reports.html", reports=reports)


@app.route("/sessions", methods=["GET", "POST"])
@login_required
def sessions():
    return render_template("sessions.html")


##### first report Page #####
@app.route("/first_report", methods=["GET", "POST"])
@login_required
def first_report():
    report_content = get_recent_final_report()
    return render_template("first_report.html", report_content=report_content)


@app.route("/personal_info_phase_3", methods=["GET", "POST"])
@login_required
def personal_info_phase_3():
    user_data = get_user()

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

        # Save updated user data to the database
        USERS_REF.child(session["random_key"]).set(user_data)
        research_data("personal_info_responses_phase_3", write_report=True)
        return redirect(url_for("reports"))
    return render_template(
        "personal_info_phase_3.html", questions=personal_info_questions_phase_3
    )


@app.route("/appointment", methods=["GET", "POST"])
@login_required
def appointment():
    if request.method == "POST":
        appointment_date = request.form.get("appointment_date")
        appointment_time = request.form.get("appointment_time")
        therapist = request.form.get("therapist")

        # Store appointment data in Firebase
        if "random_key" in session:
            appointment_data = {
                "date": appointment_date,
                "time": appointment_time,
                "therapist": therapist,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            USERS_REF.child(session["random_key"]).child("appointments").push(
                appointment_data
            )
            return redirect(url_for("personal_info_phase_1"))

    return render_template("appointment.html")


@app.route("/summaries", methods=["GET", "POST"])
@login_required
def list_summaries():
    if "random_key" not in session:
        return "User not authenticated", 401

    random_key = session["random_key"]
    prefix = f"{THERAPY_SESSION_PREFIX}{random_key}/"
    bucket = storage.bucket()
    blobs = bucket.list_blobs(prefix=prefix)

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
def summary_reporting():
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
        transcription_content = transcription_blob.download_as_text()
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

    return render_template("summary.html", summary=combined_content)


@app.route("/most_recent_summary", methods=["GET"])
@login_required
def most_recent_summary():
    random_key = session.get("random_key")
    if not random_key:
        return "User not authenticated", 401

    # Fetch the most recent summary
    prefix = f"{THERAPY_SESSION_PREFIX}{random_key}/"
    bucket = storage.bucket()
    blobs = bucket.list_blobs(prefix=prefix)

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

    summary_content = most_recent_blob.download_as_text()
    html_summary_content = convert_markdown_to_html(summary_content)

    transcription_filename = most_recent_blob.name.replace(THERAPY_PREFIX, "")
    # transcription_blob = bucket.blob(transcription_filename)
    transcription_blob = bucket.blob(
        f"{THERAPY_TRANSCRIPTION_PREFIX}{random_key}/{transcription_filename}"
    )

    try:
        transcription_content = transcription_blob.download_as_text()
        html_transcription_content = convert_markdown_to_html(transcription_content)
    except NotFound:
        html_transcription_content = (
            "<p>No transcription available for this summary.</p>"
        )

    combined_content = f"<h2>Summary</h2>{html_summary_content}<hr><h2>Transcription</h2>{html_transcription_content}"

    return render_template("summary.html", summary=combined_content)


############################# Code for Fetching Transcription, Diarization and Summary more related to frontend ##########################


@app.route("/therapy_sessions", methods=["GET", "POST"])
@login_required
def therapy_sessions():
    if "random_key" not in session:
        return "User not authenticated", 401

    random_key = session["random_key"]
    prefix = f"{THERAPY_SESSION_PREFIX}{random_key}/"
    bucket = storage.bucket()
    blobs = bucket.list_blobs(prefix=prefix)

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
