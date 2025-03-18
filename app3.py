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
from werkzeug.security import generate_password_hash, check_password_hash
import openai
from dotenv import load_dotenv
import json
import logging
import os
import requests
import time
import asyncio
from utils.home import cards, doctors
from langchain_google_genai import ChatGoogleGenerativeAI
from functools import wraps
from datetime import datetime
from celery import Celery
from flask_caching import Cache
import whisper
from google.api_core.exceptions import NotFound
from pyannote.audio import Pipeline
import subprocess
import multiprocessing

# Flask app setup
app = Flask(__name__, static_folder="static")
app.secret_key = "your_secret_key_here"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL")
THERAPY_SESSION_PREFIX = os.getenv("THERAPY_SESSION_PREFIX")
THERAPY_TRANSCRIPTION_PREFIX = os.getenv("THERAPY_TRANSCRIPTION_PREFIX")
THERAPY_PREFIX = os.getenv("THERAPY_PREFIX")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")

# Initialize Firebase
cred = credentials.Certificate(os.getenv("FIREBASE_DATABASE_CERTIFICATE"))
firebase_admin.initialize_app(
    cred, {"databaseURL": DATABASE_URL, "storageBucket": FIREBASE_STORAGE_BUCKET}
)
firestore_db = firestore.client()
USERS_REF = db.reference("users")

# Initialize AI and Cache
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")
app.config["CACHE_TYPE"] = "simple"
cache = Cache(app)


# Celery Setup
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config["CELERY_RESULT_BACKEND"],
        broker=app.config["CELERY_BROKER_URL"],
    )
    celery.conf.update(app.config)
    return celery


app.config.update(
    CELERY_BROKER_URL="redis://localhost:6379/0",
    CELERY_RESULT_BACKEND="redis://localhost:6379/0",
)

celery_app = make_celery(app)


# Celery Task to fetch user data from Firebase
@celery_app.task
def get_user_data(random_key):
    return db.reference("users").child(random_key).get()


# Session management helpers
def login_required(route_function):
    if asyncio.iscoroutinefunction(route_function):

        @wraps(route_function)
        async def async_wrapper(*args, **kwargs):
            if "user_logged_in" not in session:
                flash("Please log in to access this page.")
                return redirect(url_for("login_page"))
            return await route_function(*args, **kwargs)

        return async_wrapper
    else:

        @wraps(route_function)
        def sync_wrapper(*args, **kwargs):
            if "user_logged_in" not in session:
                flash("Please log in to access this page.")
                return redirect(url_for("login_page"))
            return route_function(*args, **kwargs)

        return sync_wrapper


def redirect_if_logged_in(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "user_logged_in" in session:
            return redirect(url_for("home"))
        return route_function(*args, **kwargs)

    return wrapper


# Routes
@app.route("/", methods=["GET", "POST"])
def home():
    random_key = session.get("random_key", "No key available")
    return render_template(
        "index.html", cards=cards, doctors=doctors, random_key=random_key
    )


@app.route("/dashboard")
def dashboard():
    random_key = session.get("random_key", "No key available")
    return render_template("dash_main.html", random_key=random_key)


@app.route("/register", methods=["POST"])
def register():
    password1 = request.form.get("pass")
    password2 = request.form.get("pass2")
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

    random_key = str(uuid.uuid4())
    ref = db.reference("users")
    ref.child(random_key).set(
        {"random_key": random_key, "password": generate_password_hash(password1)}
    )
    flash(
        f"Your registration key is: {random_key}. Please save it for future logins.",
        "success",
    )
    session["random_key"] = random_key
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
    session["has_interacted"] = user_data.get("has_interacted", False)
    session["first_login"] = "diagnosis" not in user_data
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET"])
@redirect_if_logged_in
def login_page():
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_logged_in", None)
    session.clear()
    session["new_session_can_start"] = True
    return redirect(url_for("home"))


# Celery Task to fetch user data from Firebase
@celery_app.task
def get_user_data(random_key):
    return db.reference("users").child(random_key).get()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
