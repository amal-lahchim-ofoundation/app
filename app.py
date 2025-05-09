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
import base64
import json
import re
import json
import boto3
from collections import defaultdict
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TextClassificationPipeline
import markdown
from datetime import datetime
import tiktoken 
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
import openai
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
import tempfile
import random
from questions.personal_info import (
    personal_info_questions_phase_1,
    personal_info_questions_phase_2,
    personal_info_questions_phase_3,
)
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
THERAPY_TRANSCRIPTION_PREFIX = "therapy_transcription/transcription/"
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
result = []
# Directories
UPLOADED_DIR = "uploaded_audio"
OUTPUT_DIR = "processed_chunks"
os.makedirs(UPLOADED_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
pubsub_key_b64 = os.getenv("PUBSUB_KEY_B64")  # Make sure you added this in App Runner env vars
pubsub_key_info = json.loads(base64.b64decode(pubsub_key_b64).decode())
gg_credentials = service_account.Credentials.from_service_account_info(pubsub_key_info)

transcription_results = {}
transcription_lock = asyncio.Lock() 
abs_path = ""
audio_file_name = ""
processing_files = {}
publisher = pubsub_v1.PublisherClient(credentials=gg_credentials)
subscriber = pubsub_v1.SubscriberClient(credentials=gg_credentials)
GG_PROJECT_ID = os.getenv("GG_PROJECT_ID")
GG_TOPIC_ID = os.getenv("GG_TOPIC_ID")
topic_path = publisher.topic_path(GG_PROJECT_ID, "audio-transcriptions")
GG_SUBSCRIPTION_ID = os.getenv("GG_SUBSCRIPTION_ID")
subscription_path = subscriber.subscription_path(GG_PROJECT_ID, GG_SUBSCRIPTION_ID)
openai.api_key = os.getenv("OPENAI_API_KEY")

def set_transcriptions_ref(user_id, folder_id):
    global transcriptions_ref
    transcriptions_ref = db.reference(f"users/{user_id}/transcriptions/{folder_id}")

def store_result(folder_id, filename, data):
    transcriptions_ref.child(filename).set(data)

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



def llama_guard_anonymize_and_check(text):
    """
    Send raw text to HIPAA instance for anonymization.
    """
    hippa_instance_url = "http://hippa-instance.duckdns.org:8080/process"
    try:
        response = requests.post(hippa_instance_url, json={"text": text})
        print("🔍 HIPAA returned:", response.json())

        response.raise_for_status()
        return response.json().get("anonymized_text", text)
    except Exception as e:
        print(f"❌ HIPAA instance failed: {e}")
        return text  # fallback if HIPAA server is unreachable
def split_text_into_chunks(text, max_tokens=3000):
    enc = tiktoken.encoding_for_model("gpt-4")
    words = text.split()
    chunks, current_chunk = [], []
    current_tokens = 0

    for word in words:
        word_tokens = len(enc.encode(word + " "))
        if current_tokens + word_tokens > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk, current_tokens = [], 0
        current_chunk.append(word)
        current_tokens += word_tokens

    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def compress_transcript_for_diagnosis(chunk):
    prompt = f"""
You are a clinical assistant. A therapist will later analyze this session.

Summarize this 1-hour therapy transcript in a way that preserves:
- The client’s symptoms
- Key statements and expressions
- Emotional tone and topics discussed

Keep it detailed enough so that another therapist reading the summary can perform a diagnosis later.

Transcript:
{chunk}
"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1000  # Use more if available
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error summarizing transcript: {e}")
        return "" # fallback to original


def generate_diagnostic_report(transcript_text):
    chunks = split_text_into_chunks(transcript_text)
    compressed_parts = [compress_transcript_for_diagnosis(c) for c in chunks]
    merged_summary = "\n\n".join(compressed_parts)
    prompt = f"""
You are an experienced licensed therapist.

The following is the transcription of a therapy session between a therapist and a client:

{merged_summary}

I want you to work step-by-step as follows:

Step 1: Carefully analyze the transcription. Identify and list all the potential psychological disorders based on the client's speech and behavior.

Step 2: For each potential disorder identified in Step 1:
- Explain the likely causes (based on the session content).
- Suggest evidence-based treatments.

Step 3: Based on the potential disorders and their treatments from Step 2:
- Create a detailed weekly plan with specific exercises and homework activities the patient should do to help improve their condition.

Step 4: Based directly on the exercises and homework from Step 3:
- Design a questionnaire that the patient will fill out after one week.
- The questionnaire should measure:
  - Whether the exercises and homework were completed.
  - How effective and helpful the patient found each task.
  - Any changes in the patient's symptoms compared to the previous week.

Important: Maintain a clinical, supportive tone. Be detailed but clear and practical, as if preparing real therapy session material for use with a patient.
"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return "Error generating diagnostic report."


@app.route("/generate_summary", methods=["GET", "POST"])
def generate_summary():
    if request.method == "GET":
        return render_template("upload_audio.html")

    audio_file = request.files.get("audio_file")
    if not audio_file:
        return jsonify({"error": "No audio file provided"}), 400

    user_id = session.get("random_key")
    if not user_id:
        return jsonify({"error": "User ID not found in session"}), 400

    timestamp_now = int(time.time())
    folder_id = str(timestamp_now)
    temp_audio_path = os.path.join(tempfile.gettempdir(), audio_file.filename)
    audio_file.save(temp_audio_path)

    storage_path = f"therapy_audio/{user_id}/session_{folder_id}/therapy_{folder_id}.wav"
    blob = bucket.blob(storage_path)
    blob.chunk_size = 5 * 1024 * 1024
    blob.upload_from_filename(temp_audio_path, timeout=300)
    blob.make_public()
    firebase_url = blob.public_url

    timestamp_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    db.reference(f"users/{user_id}/transcriptions/{folder_id}/meta").set({"timestamp": timestamp_str})

    start_instance_url = "https://tk6m28s7tc.execute-api.eu-central-1.amazonaws.com/prod/wakeUpEC2Instance"
    try:
        print(" Waking up EC2 instance...")
        wake_response = requests.post(start_instance_url, timeout=30)
        wake_response.raise_for_status()
        print(f"Instance wake-up triggered: {wake_response.text}")
    except Exception as e:
        print(f" Failed to wake up instance: {e}")
        flash("Failed to start processing backend. Please try again later.")
        return redirect(url_for("therapy_sessions"))

    print("⏳ Waiting 30 seconds for EC2 instance to be ready...")
    time.sleep(30)

    external_api_url = "http://g4-instance.duckdns.org:8080/process"
    api_key = os.getenv("MY_SECRET_API_KEY")

    payload = {"firebase_url": firebase_url, "user_id": user_id}
    headers = {"Content-Type": "application/json", "X-API-Key": api_key}

    try:
        res = requests.post(external_api_url, json=payload, headers=headers)
        res.raise_for_status()
        response_json = res.json()

        if "transcript" not in response_json:
            raise KeyError("Missing 'transcript' in API response")

        raw_markdown = "## Transcription\n\n"
        for segment in response_json["transcript"]:
            speaker = segment.get("speaker", "Speaker")
            text = segment.get("text", "")
            raw_markdown += f"**{speaker}:** {text}\n\n"
        markdown_content = llama_guard_anonymize_and_check(raw_markdown)
        # Save and upload transcription
        temp_md_path = os.path.join(tempfile.gettempdir(), f"therapy_{folder_id}.md")
        with open(temp_md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        md_storage_path = f"therapy_transcription/transcription/{user_id}/therapy_{folder_id}.md"
        md_blob = bucket.blob(md_storage_path)
        md_blob.upload_from_filename(temp_md_path)
        md_blob.make_public()

        anonymized_content = llama_guard_anonymize_and_check(markdown_content)
        markdown_content = anonymized_content  
        with open(temp_md_path, "w", encoding="utf-8") as f:
           f.write(markdown_content)

        md_blob = bucket.blob(md_storage_path)
        md_blob.upload_from_filename(temp_md_path)
        md_blob.make_public()

        print(" Anonymized content from HIPAA instance:")
        print(anonymized_content)

        print(" Sending anonymized content to OpenAI for diagnostic report generation...")
        compressed = compress_transcript_for_diagnosis(markdown_content)
        diagnostic_report_text = generate_diagnostic_report(compressed)



        diagnostic_md_path = os.path.join(tempfile.gettempdir(), f"therapy_diag_{folder_id}.md")
        with open(diagnostic_md_path, "w", encoding="utf-8") as f:
            f.write(diagnostic_report_text)

        diagnostic_storage_path = f"therapy_transcription/summary/{user_id}/therapy_{folder_id}.md"
        diagnostic_blob = bucket.blob(diagnostic_storage_path)
        diagnostic_blob.upload_from_filename(diagnostic_md_path)
        diagnostic_blob.make_public()


        flash("Session processed successfully! You can check therapy sessions and diagnostic reports in about 5 minutes.")
        return redirect(url_for("therapy_sessions"))

    except Exception as e:
        print(f" Error processing transcription or generating report: {e}")
        flash("Something went wrong while processing the audio. Try again.")
        return redirect(url_for("therapy_sessions"))


def sanitize_filename(filename: str) -> str:
    return re.sub(r"[^\w\s-]", "", filename).strip()


def convert_webm_to_wav(input_file, output_file):
    """Function to convert WebM to WAV using FFmpeg."""
    command = [
        "ffmpeg",
        "-i",
        input_file,  
        output_file,  
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
        
    ]
    random_key = session.get("random_key", "No key available")
    logging.debug("redirecting index.html")
    return render_template(
        "index.html", cards=cards, doctors=doctors, random_key=random_key
    )


firebase_key_b64 = os.environ["FIREBASE_KEY_B64"]  # New env var
firebase_key = json.loads(base64.b64decode(firebase_key_b64).decode())
cred = credentials.Certificate(firebase_key)

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


def generate_mnemonic_phrase(random_key):
    mnemo = Mnemonic("english")
    seed = random_key.encode("utf-8")
    mnemonic_phrase = mnemo.generate(strength=128)

    return mnemonic_phrase

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
@redirect_if_logged_in  
def register_page():
    return render_template("register.html")



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
    session["random_key"] = random_key 
    session["has_interacted"] = user_data.get(
        "has_interacted", False
    )  
    session["first_login"] = "diagnosis" not in user_data
    return redirect(url_for("dashboard"))


@app.route("/recover_username", methods=["GET", "POST"])
def recover_username():
    if request.method == "POST":
        mnemonic_phrase = request.form.get(
            "mnemonic_phrase"
        ).strip() 
        password = request.form.get("password")

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


@app.route('/summary-reporting')
@login_required
def summary_reporting():
    user_id = request.args.get('user_id')
    file_name = request.args.get('file')

    if not user_id or not file_name:
        return "No transcription found", 404

    # Transcription file
    transcription_storage_path = f"therapy_transcription/transcription/{user_id}/{file_name}"
    transcription_url = f"https://storage.googleapis.com/chat-psychologist-ai.appspot.com/{transcription_storage_path}"

    # Therapy session report file
    summary_storage_path = f"therapy_transcription/summary/{user_id}/{file_name}"
    summary_url = f"https://storage.googleapis.com/chat-psychologist-ai.appspot.com/{summary_storage_path}"

    try:
        # --- Load transcription ---
        transcription_response = requests.get(transcription_url)
        transcription_response.raise_for_status()
        transcription_markdown = transcription_response.text
        anonymized_markdown = llama_guard_anonymize_and_check(transcription_markdown)
        transcription_html = markdown.markdown(anonymized_markdown)


        # --- Load therapy session report ---
        summary_response = requests.get(summary_url)

        if summary_response.status_code == 200:
            summary_markdown = summary_response.text
            summary_html = markdown.markdown(summary_markdown)
        else:
            summary_html = "<p>Report not generated yet.</p>"

        return render_template(
            "summary_reporting.html",
            transcription_html=transcription_html,
            summary_html=summary_html
        )

    except Exception as e:
        print(f"Error loading transcription or summary: {e}")
        return "No transcription found", 404


# ------------------ View Therapy Sessions ------------------
@app.route("/therapy_sessions", methods=["GET", "POST"])
@login_required
def therapy_sessions():
    random_key = session["random_key"]
    prefix = f"{THERAPY_TRANSCRIPTION_PREFIX}{random_key}/"
    print(f"Searching in prefix: {prefix}")   # 👈 Add this line
    blobs = bucket.list_blobs(prefix=prefix)

    blobs_list = list(blobs)
    print(f"Found {len(blobs_list)} blobs")   # 👈 Add this line

    summaries = []
    for blob in blobs_list:
        if blob.name.endswith(".md"):
            filename = blob.name.split("/")[-1]
            timestamp_str = filename.replace(THERAPY_PREFIX, "").replace(".md", "")

            try:
                timestamp = datetime.utcfromtimestamp(int(timestamp_str))
                formatted_date = timestamp.strftime("%d/%m/%Y %H:%M")
            except ValueError:
                formatted_date = "Unknown Date"

            summaries.append({
                "filename": filename,
                "timestamp": formatted_date,
                "raw_timestamp": int(timestamp_str),
            })

    summaries.sort(key=lambda x: x["raw_timestamp"], reverse=True)
    return render_template("therapy_sessions.html", summaries=summaries)
@app.route('/check_summary_status')
@login_required
def check_summary_status():
    try:
        user_id = session.get("random_key")
        if not user_id:
            return {"status": "error", "message": "No user ID"}, 400

        prefix = f"{THERAPY_TRANSCRIPTION_PREFIX}{user_id}/"
        blobs = list(bucket.list_blobs(prefix=prefix))

        if any(blob.name.endswith('.md') for blob in blobs):
            return {"status": "completed"}
        else:
            return {"status": "pending"}
    except Exception as e:
        print(f"Error checking summary status: {e}")
        return {"status": "error"}, 500

# ---------------------- Run App ----------------------

if __name__ == "__main__":
    import os
    port = 8080  # just for testing
 # <- Use PORT env or default to 8080
    app.run(host="0.0.0.0", port=port)        # <- Host must be 0.0.0.0
