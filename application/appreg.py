from flask import Flask, session, request, render_template, redirect, url_for, flash, jsonify, make_response
from flask_session import Session
import firebase_admin
from firebase_admin import credentials, db, firestore
import uuid
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask import session
import openai
from dotenv import load_dotenv
import json
import logging
import os
import time
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_community.utilities import WikipediaAPIWrapper
from functools import wraps
from Disorders import Disorders
import fitz
import pycountry
from datetime import datetime
import random

app = Flask(__name__, static_folder='static')  #creates a Flask web application object named app. It's a fundamental step in setting up a Flask web application
app.secret_key = 'your_secret_key_here'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
Session(app)
load_dotenv() 
openAI = openai.OpenAI()


DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL')
    
@app.route("/", methods=['GET', 'POST'])
def home():
    logging.debug("redirecting index.html")
    return render_template('index.html')

################################################### Firebase ####################################################################



# Initialize Firebase
cred = credentials.Certificate(os.getenv('FIREBASE_DATABASE_CERTIFICATE'))
firebase_admin.initialize_app(cred, {
    'databaseURL': DATABASE_URL
})

################################################### Firestore ####################################################################
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

#A function that doesn't allow to access login page if you are already logged in/regiterd 
def redirect_if_logged_in(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if 'user_logged_in' in session:
            logging.debug("redirecting to home page since already loggd in")
            return redirect(url_for('home'))  # Redirect to the home page if already logged in
        return route_function(*args, **kwargs)
    return wrapper

###################################################### Register Firebase ########################################################

@app.route('/register', methods=['POST'])
def register():
    password1 = request.form.get('pass')
    password2 = request.form.get('pass2')

    if not password1 or not password2:
        flash('Please fill in both password fields.' )
        return redirect(url_for('register_page'))

    if password1 != password2:
        flash('Passwords do not match.')
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

########################################## LogIN Firebase #################################

@app.route('/login', methods=['POST'])
def login():
    random_key = request.form.get('random_key')
    password = request.form.get('password')

    if not random_key or not password:
        flash('Please fill in all fields.')
        return redirect(url_for('login_page'))
    
    

    # Retrieve the user data from Firebase Realtime Database
    user_data = USERS_REF.child(random_key).get()
    if not user_data:
        flash('Invalid random key.')
        return redirect(url_for('login_page'))

    # Verify the password
    stored_password_hash = user_data.get('password')
    if not stored_password_hash or not check_password_hash(stored_password_hash, password):
        flash('Invalid password.')
        return redirect(url_for('login_page'))
    
    # Set a session variable to indicate the user is logged in
    
    session['user_logged_in'] = True
    session['random_key'] = random_key  # Store the random_key in the session
    session['has_interacted'] = user_data.get('has_interacted', False)  # Get interaction status
    
    # Check if it's the user's first login
    session['first_login'] = 'diagnosis' not in user_data

    # Redirect to home
    return redirect(url_for('home'))


@app.route('/login', methods=['GET'])
@redirect_if_logged_in  # Apply the redirect_if_logged_in decorator
def login_page():
    return render_template('login.html')

######################################### LogOut Firebase ###############################
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



###################A function that doesn't alow to acces that page if you are not loged in ############  


def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if 'user_logged_in' not in session:
            flash('Please log in to access this page.')
            return redirect(url_for('login_page'))
        return route_function(*args, **kwargs)
    return wrapper


############################################Treatment Page #######################################

@app.route('/treatment')
@login_required
def treatment():
    user_data = get_user()
    diagnosis_complete = 'diagnosis_name' in user_data and bool(user_data['diagnosis_name'])
    personal_info_complete = user_data.get('personal_info_completed', False)  # Use the database flag
    personal_insights_complete = user_data.get('personal_insights_completed', False)

    if not personal_info_complete:
        return redirect(url_for('personal_info'))
    
    if not personal_insights_complete:
        return redirect(url_for('personal_insights'))

    return render_template('treatment.html', diagnosis_complete=diagnosis_complete)

###########################################personal info Page ########################################
personal_info_questions = [
    {"question":"What is your age?", "type":"number", "placeholder":""},
    {"question":"What is your gender?", "type":"select", "options":["Male", "Female", "Other"],"placeholder":""},
    {"question": "What is your nationality?", "type": "select", "options": [country.name for country in pycountry.countries], "placeholder": "Select your nationality"},
    {"question": "What is your current country of residence?", "type": "select", "options": [country.name for country in pycountry.countries], "placeholder": "Select your current country of residence"},
    {"question":"What cultural or ethnic background do you identify with? How does this influence your daily life?", "type":"text","placeholder":""},
    {"question":"What is your marital status?", "type":"select","options":["Single","Married","Divorced","Other"],"placeholder":""},
    {"question":"What is your education level?", "type":"select", "options":["High School","Bachelor's, Master's","Other"], "placeholder":""},
    {"question":"What is your employment status?", "type":"select", "options":["Employed","Unemployed","Retired","Other"],"placeholder":""},
    {"question":"what is your living situation?","type":"select","options":["Alone","With Family","With Friends","Other"],"placeholder":""},
    {"question":"Do you have a stable support system?","type":"text","placeholder":"Yes/No; If yes, please specify"},
    {"question":"Who are the most significant people in your life, and what kind of relationships do you have with them?", "type":"text","placeholder":""},
    {"question":"Are you actively involved in any community or social groups? How does this impact your social interactions?","type":"text","placeholder":""},
    {"question":"Do you have any chronic physical illnesses?","type":"text","placeholder":"Yes/No; If yes, please specify"},
    {"question":"Are you currently taking any medications?", "type":"text", "placeholder":"Yes/No; If yes, please specify"},
    {"question":"Do you use substances like tobacco, alcohol, or recreational drugs?","type":"select", "options":["Yes","No"],"placeholder":""},
    {"question":"How often do you exercise?", "type":"select", "options":["Daily","Weekly","Rarely","Never"],"placeholder":""},
    {"question":"Can you describe your typical daily diet? Do you follow any specific dietary restrictions?", "type":"text","placeholder":""},
    {"question":"How would you describe your typical sleep patterns and quality?", "type":"text","placeholder":""},
    {"question":"Have you been diagnosed with any mental health disorders?", "type":"text","placeholder":"Yes/No; If yes, please specify"},
    {"question":"Have you experienced significant life changes or stressors recently?","type":"text","placeholder":"Yes/No; If yes, please specify"},
    {"question":"Rate your overall stress level on a scale from 1 to 10:","type":"select", "options":["1","2","3","4","5","6","7","8","9","10"], "placeholder":""},
    {"question":"What are your primary ways of coping with stress or emotional distress?","type":"text","placeholder":""},
    {"question":"Can you share an instance where you successfully managed a challenging life event?","type":"text","placeholder":""},
    {"question":"Do you feel content with your personal life?", "type":"text","placeholder":"Yes/No; If no, what areas would you like to improve?"},
    {"question":"How often do you engage in activities that you enjoy?","type":"select", "options":["Daily","Weekly","Rarely","Never"],"placeholder":""},
    {"question":"Do you feel you have adequate social interactions?","type":"text","placeholder":"Yes/No; If no, what barriers do you face?"},
    {"question":"How would you rate your overall happiness on a scale from 1 to 10?", "type":"select", "options":["1","2","3","4","5","6","7","8","9","10"], "placeholder":""},
    {"question":"What aspects of your life are you most satisfied or dissatisfied with? Why?","type":"text","placeholder":""},
    {"question":"What are your hopes and aspirations for the future? How do you plan to achieve them?","type":"text","placeholder":""},
    {"question":"How would you describe your overall level of physical activity?","type":"select","options":["Very active","Moderately active","Lightly active","Sedentary"],"placeholder":""},
    {"question":"What do you typically do in your leisure time? How do you balance relaxation with activity?","type":"text","placeholder":""},
    {"question":"Would you describe yourself more as an introvert or an extrovert?","type":"text","placeholder":""},
    {"question":"How comfortable do you feel in social gatherings and public speaking scenarios?","type":"select","options":["Very comfortable","Somewhat comfortable","Neutral","Somewhat uncomfortable","Very uncomfortable"],"placeholder":""},
    {"question":"How do you typically react to meeting new people or being in unfamiliar social situations?","type":"text","placeholder":"Examples:Seek interaction,Observe first then join,Remain mostly on the sidelines,Avoid if possible"},
    {"question":"What skills or talents do you believe you possess?","type":"text","placeholder":""},
    {"question":"How have you developed these skills over time?","type":"text","placeholder":"Examples:Formal education,Self-taught,Mentorship,On-the-job experience"},
    {"question":"Can you provide examples of how you apply these skills in your personal or professional life?", "type":"text","placeholder":""},
    {"question":"What skills do you find most useful in social interactions?","type":"text","placeholder":"Examples: Active listening, Empathy, Clear communication, Persuasiveness, Conflict resolution"},
]
personal_insights_questions = [
{"question":"How important is your cultural background to your identity?", "type":"text","placeholder":"Examples:Not important,Somewhat important,Very important"},
{"question":"Do you feel your cultural background affects your mental health?","type":"text","placeholder":"Yes/No; If yes, please explain how","placeholder":""},
{"question":"Do you face any discrimination or social stigma?","type":"text","placeholder":"Yes/No; If yes, please specify context and frequency","placeholder":""},
{"question":"How well do you feel that your cultural or personal identity aligns with societal expectations?","type":"text","placeholder":""},
{"question":"Do you face any challenges with language or communication in your daily life?","type":"text","placeholder":""},
{"question":"What are the core values that you live by?","type":"text","placeholder":""},
{"question":"From where or whom have you adopted most of your beliefs?","type":"text","placeholder":""},
{"question":"How do your values influence your decision-making processes?","type":"text","placeholder":""},
{"question":"Describe a situation where your values were challenged. How did you handle it?","placeholder":""},
{"question":"How do your values affect your relationships with others?","type":"text","placeholder":""},
{"question":"How do your values align with your professional life or career choices?","type":"text","placeholder":""},
{"question":"In what ways do you try to promote your values in your community or social circle?","type":"text","placeholder":""},
{"question":"How do your beliefs influence your daily behavior and interactions with others?","type":"text","placeholder":""},
{"question":"How do your beliefs impact your feelings of happiness or contentment?","type":"text","placeholder":""},
{"question":"Have you ever encountered situations where your beliefs were challenged? How did you react?","type":"text","placeholder":""},
{"question":"Can you provide examples of significant life decisions that were guided by your beliefs?","type":"text","placeholder":""},
{"question":"How has your identity evolved over the years? What factors have been most influential in shaping your identity?","type":"text","placeholder":""},
{"question":"Have you faced any challenges due to your identity? How have you addressed these challenges?","type":"text","placeholder":""},
{"question":"What aspects of your identity are you most proud of?","type":"text","placeholder":""},
{"question":"How do you define spirituality? Does it involve religious beliefs, personal philosophy, or something else?","type":"text","placeholder":""},
{"question":"How does spirituality manifest in your daily life?","type":"text","placeholder":""},
{"question":"Are you part of a spiritual community? How does this community support your spiritual growth?","type":"text","placeholder":""},
{"question":"How has your spirituality evolved over time? What events or experiences have led to significant changes in your spiritual outlook?","type":"text","placeholder":""},
{"question":"How does your spirituality influence your relationships with others?","type":"text","placeholder":""},
{"question":"What are the most important teachings or values you have learned from your spiritual beliefs?","type":"text","placeholder":""},
{"question":"Do you have any goals related to your spiritual life? What steps are you taking to achieve them?","type":"text","placeholder":""},
]
file_path = '/Users/dandev947366/Desktop/test/ChatPsychologistAI/application/data/Mental_Health_Statistics_2024.docx'
import docx
api_key = os.getenv('OPENAI_API_KEY_2')
@app.route('/personal_info', methods=['GET', 'POST'])
@login_required
def personal_info():
    user_data = get_user()   
    if user_data.get('personal_info_completed', False):
        return redirect(url_for('treatment'))
    if request.method == 'POST':
        # personal_info_responses = {question['question']: request.form.get(str(index)) for index, question in enumerate(personal_info_questions)}
        
        # personal_info_responses = {
        #     f"Question {index}": request.form.get(str(index)) 
        #     for index in range(1, len(personal_info_questions) + 1)
        # }
        personal_info_responses = {}
        # Map form data to questions
        for index, question in enumerate(personal_info_questions, start=1):
            question_text = question.get('question', f"Question {index}")
            answer = request.form.get(str(index))
            personal_info_responses[question_text] = answer
            
        user_data['personal_info_completed'] = True
        user_data['personal_info_responses'] = personal_info_responses
        USERS_REF.child(session['random_key']).set(user_data)
        # Call the CrewAI agent to process the personal info responses
        call_crewai_agent(user_data['personal_info_responses'], api_key, file_path)
        return redirect(url_for('treatment'))

    return render_template('personal_info.html', questions=personal_info_questions)


# ManagerAgent class for handling interactions between user and CrewAI
class ManagerAgent:
    def __init__(self, api_key):
        self.api_key = api_key
        self.personal_info_agent = PersonalInfoAIAgent(api_key)

    def pass_to_personal_info_agent(self, responses, docx_path):
        # Extract the DOCX content
        docx_text = self.personal_info_agent.read_docx(docx_path)
        
        if not docx_text:
            return "Error: Could not extract text from DOCX."

        # Pass the responses to the PersonalInfoAIAgent for processing
        result = self.personal_info_agent.compare_user_responses(responses, docx_text)
        return result

class PersonalInfoAIAgent:
    def __init__(self, api_key):
        self.api_key = api_key

    def read_docx(self, file_path):
        """
        Reads a DOCX file and returns its text content.
        """
        try:
            # Open the DOCX file
            doc = docx.Document(file_path)
            extracted_text = "\n".join([para.text for para in doc.paragraphs])

            return extracted_text
        except Exception as e:
            return f"Error reading DOCX: {e}"

    def compare_user_responses(self, user_responses, doc_statistics):
        """
        Compare user responses with mental health statistics to estimate the percentage likelihood of mental health issues.
    
        :param user_responses: A dictionary of user responses with question and answer pairs.
        :param doc_statistics: A dictionary containing mental health statistics.
        :return: A dictionary with estimated percentages based on the provided statistics.
        """
    
        # Define statistics based on the document
        statistics = {
            'age_groups': {
                '18 to 25': 33.7,
                '26 to 49': 28.1,
                '50 and older': 15.0
            },
            'mental_health_type': {
                'anxiety_disorders': 19.1,
                'major_depression': 8.3
            },
            'race': {
                'American Indian or Alaska Native': 26.6,
                'Mixed Race or Multiracial': 34.9
            },
            'gender': {
                'Female': 11.9,  # Percentage of females with mental illness
                'Male': 9.3      # Percentage of males with mental illness
            },
            'young_women': 16,  # Prevalence of mental illness among young women aged 20-29
            'young_men': 8,     # Prevalence of mental illness among young men aged 20-29
            'general_young_adults': 22,  # General prevalence for young adults aged 15-34
            'general_older_adults': 14,  # General prevalence for adults aged 60 and over
            'older_adults_disability': 10.6,  # Disability adjusted life years (DALYs) for older adults
            'loneliness_isolation': 25,  # Percentage of older adults affected by loneliness and isolation
            'abuse': 16,  # Percentage of older adults experiencing abuse
            'employment_recovery_boost': 54  # Percentage increase in recovery likelihood due to employment
        }
    
        # Extract user responses
        try:
            age = int(user_responses.get('What is your age?', 0))
        except ValueError:
            age = 0  # Handle invalid age input
    
        race = user_responses.get('What cultural or ethnic background do you identify with?', '').strip()
        gender = user_responses.get('What is your gender?', '').strip()
        employment_status = user_responses.get('What is your employment status?', '').strip()
        living_situation = user_responses.get('What is your living situation?', '').strip()  # New input field
        social_factors = user_responses.get('Do you feel lonely or socially isolated?', '').strip()  # New input field
        abuse_experience = user_responses.get('Have you experienced any form of abuse?', '').strip()  # New input field
    
        # Determine age group percentage
        if 18 <= age <= 25:
            age_group_percentage = statistics['age_groups']['18 to 25']
        elif 26 <= age <= 49:
            age_group_percentage = statistics['age_groups']['26 to 49']
        elif age >= 60:
            age_group_percentage = statistics['general_older_adults']
            # Include additional factors for older adults
            if social_factors.lower() == 'yes':
                age_group_percentage += statistics['loneliness_isolation']
            if abuse_experience.lower() == 'yes':
                age_group_percentage += statistics['abuse']
        else:
            age_group_percentage = statistics['age_groups'].get('50 and older', 0)
    
        # Determine specific percentages for young adults
        if 15 <= age <= 34:
            if gender == 'Female':
                age_group_percentage = statistics['young_women']
            elif gender == 'Male':
                age_group_percentage = statistics['young_men']
            else:
                age_group_percentage = statistics['general_young_adults']
    
        # Determine race-related percentage
        race_percentage = statistics['race'].get(race, 0)  # Default to 0 if race is not listed
    
        # Determine gender-related percentage
        gender_percentage = statistics['gender'].get(gender, 0)  # Default to 0 if gender is not listed
    
        # Employment status adjustment
        if employment_status.lower() == 'employed':
            if age <= 60:
                recovery_boost = statistics['employment_recovery_boost']  # 54% recovery boost for employed under 60
            else:
                recovery_boost = 0  # No boost for those older than 60 years
        else:
            recovery_boost = 0
    
        # Living situation adjustment
        if living_situation.lower() == 'with single parent' and age >= 18:
            recovery_boost = 0  # No boost for those living with a single parent
    
        # Combine percentages and apply employment status adjustment
        combined_percentage = max(age_group_percentage, race_percentage, gender_percentage)
        adjusted_percentage = combined_percentage + recovery_boost
    
        return {
            'age_group_percentage': age_group_percentage,
            'race_percentage': race_percentage,
            'gender_percentage': gender_percentage,
            'combined_percentage': combined_percentage,
            'adjusted_percentage': adjusted_percentage
        }

    
    def call_llm_api(prompt):
        """
        Placeholder function to call the LLM API.
        """
        # Implementation will depend on the specific LLM service you are using.
        pass
    
    def parse_llm_response(response):
        """
        Parse the LLM response to extract meaningful results.
        """
        # Implementation will depend on the format of the LLM response.
        return response


# Function to call CrewAI agent to process the user's personal info responses
def call_crewai_agent(data, api_key, docx_path):
    # Instantiate the ManagerAgent
    manager_agent = ManagerAgent(api_key)
    
    # Call the agent to analyze the responses using GPT
    result = manager_agent.pass_to_personal_info_agent(data, docx_path)
    
    # Log or save the result
    print("User's responses:\n", data)
    print('--------------------------------')
    print("CrewAI Agent Data:\n", result)

###########################################Personal insights Page ########################################

@app.route('/personal_insights', methods=['GET', 'POST'])
@login_required
def personal_insights():
    user_data = get_user()
    if user_data.get('personal_insights_completed', False):
        return redirect(url_for('treatment'), questions=personal_insights_questions)
    if request.method == 'POST':
        personal_insights_responses = {index: request.form.get(str(index)) for index, item in enumerate(personal_insights_questions)}
        user_data['personal_insights_completed'] = True
        user_data['personal_insights_responses'] = personal_insights_responses
        USERS_REF.child(session['random_key']).set(user_data)
        return redirect(url_for('treatment'))
    return render_template('personal_insights.html', questions=personal_insights_questions)


###########################################Diagnose Page ########################################


disorders_instance = Disorders()
# From appreg.py
known_disorders = [disorder.name for disorder in disorders_instance.disorder_list]
 


def extract_disorder(text, disorders): #extracts the disorder from text if it exists
    matches={}   #initialize matches dictionary
    for disorder in disorders:
        #iterate through each disorder
        if disorder.lower() in text.lower(): #check if disorder exists in text, case insensitive
            matches[disorder]=disorder
            logging.debug("extract_disorder matching disorder found " + text.lower())
    
        return max(matches, key=len)
   

def check_similarity(disorder_list1, disorder_list2):
    if disorder_list1 == disorder_list2:
        return 1
    return len(set(disorder_list1).intersection(disorder_list2)) / len(set(disorder_list1).union(disorder_list2))


diagnosequestions = [
        "Do you feel extremely anxious or uncomfortable when meeting new people?",
        "Do you often worry about being judged or criticized by others in social situations?",
        "Do you frequently avoid social events or activities due to fear of embarrassment or humiliation?",
        "Do you experience intense anxiety when speaking or presenting in front of a group?",
        "Do you find it difficult to initiate or maintain conversations with others?",
        "Are you often overwhelmed by your worries?",
        "Do many situations cause you to worry?",
        "Do you tend to worry a lot when you are under pressure?",
        "Once you start worrying, do you find it hard to stop?",
        "Do you worry all the time? ",
        "Over the past two weeks, have you experienced a noticeable change in your mood, such as feeling sad, empty, hopeless, or appearing tearful to others?",
        "During the same period, have you found it difficult to enjoy activities that you previously found pleasurable or interesting?",
        "Have you noticed changes in your appetite or weight (either gain or loss) without attempting to diet?",
        "Can you tell me about your sleeping patterns lately? Have you experienced insomnia or excessive sleeping?",
        "Have you felt unusually tired or low on energy most days, making even small tasks seem exhausting?",
        "Do you ever feel despair about your complaints or how you feel?",
        "Have you ever had thoughts of death?",
        "Have you ever considered harming yourself or ending your life?",
        "Have you had these complaints before in your life?"
    ]

@app.route("/questions", methods=['GET', 'POST']) 
@login_required  # Ensure user is logged in to access this route
def questions():   
    
   # Initialize variables
    result = None
    diagnosis_found = False
    saved_diagnosis = None  
    

    # Check if it's the user's first login based on the session variable
    first_login = session.get('first_login', True)
    
    if request.method == 'POST':
        if first_login:       
            diagnose_responses = [request.form.get(f'q{i+1}') for i in range(len(diagnosequestions))]  # get all the answers
            personal_info_responses = {question['question']: request.form.get(str(index)) for index, question in enumerate(personal_info_questions)}
            personal_insights_responses = {question['question']: request.form.get(str(index)) for index, question in enumerate(personal_insights_questions)}
            prompt = request.form.get('prompt')  # get the prompt
            diagnosis_result = process_data(diagnose_responses, personal_info_responses,personal_insights_responses, prompt)  # process these datas
            result = diagnosis_result['message']  # add these processed data into message
            diagnosis_found = diagnosis_result['diagnosis_found']
            session['given_diagnose'] = diagnosis_result['given_diagnose']

            if diagnosis_found:
                user_data = get_user()
                if user_data:
                    user_data['diagnosis'] = result
                    user_data['diagnosis_name'] = session['given_diagnose']
                    USERS_REF.child(session['random_key']).set(user_data)
            
            session['first_login'] = False
            
            return render_template('diagnose.html', result=result, questions=diagnosequestions, diagnosis_found=diagnosis_found)
        
        return render_template('diagnose.html', questions=diagnosequestions)      
         
    else:
        if first_login:
            return render_template('diagnose.html', questions=diagnosequestions)
        else:
            # If it's not the user's first login, retrieve the saved diagnosis
            user_data = get_user()
            if user_data:
                saved_diagnosis = user_data.get('diagnosis')
                if saved_diagnosis:
                    diagnosis_found = True  # Update the diagnosis_found variable here
            return render_template('diagnose.html', saved_diagnosis=saved_diagnosis, diagnosis_found=diagnosis_found)
        
    

def process_data(diagnose_responses, personal_info_responses, personal_insights_responses, prompt):
    # Initialize the various components
    llm = OpenAI(temperature=0.9)
    
    social_anxiety_directory_path = os.path.abspath(disorders_instance.SOCIAL_ANXIETY.file_name)
    if os.path.exists(social_anxiety_directory_path):
        social_anxiety_pdf_text = process_directory(social_anxiety_directory_path)

    anxiety_directory_path = os.path.abspath(disorders_instance.ANXIETY.file_name)
    if os.path.exists(anxiety_directory_path):
        anxiety_pdf_text = process_directory(anxiety_directory_path)

    depression_directory_path = os.path.abspath(disorders_instance.DEPRESSION.file_name)
    if os.path.exists(depression_directory_path):
        depression_pdf_text = process_directory(depression_directory_path)    

    combined_input = {
        'a': diagnose_responses,
        'q': diagnosequestions,
        'topic': prompt,
        'personal_info': personal_info_responses,
        'personal_insights' : personal_insights_responses 
    }

    problem_template = PromptTemplate(
    input_variables=['a', 'q', 'topic', 'personal_info', 'personal_insights'],  # Added 'personal_insights' to input variables
    template = "Act as a therapist to support the user's mental health needs. \
Carefully analyze the user's responses and behavior to identify potential mental health \
conditions. Utilize the information provided by the user in their description ({topic}) and their \
answers ({a}) to specific questions ({q}). Additionally, consider the following personal information and personal insights \
provided by the user: {personal_info} {personal_insights}. Based on this data, formulate a precise diagnosis."
)

    
    script_template = PromptTemplate(
        input_variables=['problem', 'wikipedia_research'],
        template='Provide solutions and treatments based on the diagnosis :\n {problem}  also use \
            the information of \nWikipedia Research: {wikipedia_research} to reach a better solution and treatments '
    )
    
    diagnosis_template = PromptTemplate(
        input_variables=['pdf_text'],
        template='I have a long text document and need a brief summary. \
            Extract the main diagnosis mentiond in this medical text. And Without providing any other text in your response just match the disorder to one of these '+str(known_disorders)+' The text is: {pdf_text} . '
    )
    
    problem_memory = ConversationBufferMemory(input_key='topic', memory_key='chatHistory')
    script_memory = ConversationBufferMemory(input_key='problem', memory_key='chatHistory')
    
    problem_chain = LLMChain(
        llm=llm, prompt=problem_template, verbose=True, output_key='problem', memory=problem_memory
    )
    
    script_chain = LLMChain(
        llm=llm, prompt=script_template, verbose=True, output_key='script', memory=script_memory
    )
    
    diagnosis_chain = LLMChain(
        llm=llm, prompt=diagnosis_template, verbose=True, output_key='diagnosis'
    )
    
    wiki = WikipediaAPIWrapper()


    problem = problem_chain.run(**combined_input)
  
    wiki_research = wiki.run(prompt)
    script = script_chain.run(problem=problem, wikipedia_research=wiki_research)

    social_anxiety_pdf_summary = diagnosis_chain.run(pdf_text=social_anxiety_pdf_text) 
    anxiety_pdf_summary = diagnosis_chain.run(pdf_text=anxiety_pdf_text)
    depression_pdf_summary = diagnosis_chain.run(pdf_text=depression_pdf_text)

    Disorder_Summary = db.reference("Disorder_Summary")
    
    socialAnxietyRow = Disorder_Summary.child(disorders_instance.SOCIAL_ANXIETY.name).get()
    socialAnxietyRow["Summary"] = social_anxiety_pdf_summary
    Disorder_Summary.child(disorders_instance.SOCIAL_ANXIETY.name).set(socialAnxietyRow) # store social_anxiety_pdf_summary 

    anxietyRow = Disorder_Summary.child(disorders_instance.ANXIETY.name).get()
    anxietyRow["Summary"] = anxiety_pdf_summary
    Disorder_Summary.child(disorders_instance.ANXIETY.name).set(anxietyRow)

    depressionRow = Disorder_Summary.child(disorders_instance.DEPRESSION.name).get()
    depressionRow["Summary"] = depression_pdf_summary
    Disorder_Summary.child(disorders_instance.DEPRESSION.name).set(depressionRow)


    # extract disorder from pdf and from the GPT diagnosed
    problem_disorder = extract_disorder(problem, known_disorders)
    pdf_disorder = extract_disorder(social_anxiety_pdf_summary, known_disorders)
    
    similarity = check_similarity(problem_disorder, pdf_disorder)

   
    
    if similarity > 0.2:
        return {
        'message': f"Good news! We found a match!\n\n{problem}\n\n{script}",
        'diagnosis_found': True,
        'given_diagnose' : problem_disorder.strip()
    }
    else:
       return {
        'message': "Based on our analysis, the diagnoses from your answers and the uploaded document do not match. Please provide more information and try again.",
        'diagnosis_found': False
    }


@app.route('/result')   # Route for displaying diagnose and treatment result
@login_required  # Ensure user is logged in to access this route
def result():
    questions = session.get('questions', [])
    return render_template('diagnose.html', questions=questions)

#########################################################Chat Page##############################################

def generate_response(user_input, session_prompt, temperature=0.3): # start a chat page function
    logging.debug("chatbot is generating respons")
    messages = [ # initialize message list with system and user messages
        {"role": "system", "content": session_prompt},
        {"role": "user", "content": user_input}
    ]
    keywords = ["alone", "lonely", "isolated","not happy","'t happy","feel","mental health","cry","be happy","depressed","helpless","worthless","numb","desperate","ashamed","heartbroken","hopeless","despondent","agitated","disheartened","traumatized","distressed","dispirited","somber","Aaonized","dismayed","desolate","dejected","anguished","disappointed","hurt"]  
    if any(keyword in user_input.lower() for keyword in keywords):
        return "Whatever you're feeling right now, I'm here to support you. By sharing your emotions and experiences, we can overcome this together. Talking about the challenges in your life, we can explore the best solutions together. Can you tell me about what's been happening in your life? This will help us understand where to begin."
    try:
        # generate chat response 
        response = openAI.chat.completions.create(model="gpt-4",
        messages=messages,
        temperature=temperature)
        return response.choices[0].message.content
    except openai.RateLimitError as e:
        # Handle rate limit errors
        return f"Rate Limit Error: {str(e)}"
    except openai.AuthenticationError as e:
        # Handle authentication errors
        return f"Authentication Error: {str(e)}"
    except openai.APIConnectionError as e:
        # Handle API connection errors
        return f"API Connection Error: {str(e)}"
    except openai.OpenAIError as e:
        # Handle OpenAI API errors
        return f"OpenAI API Error: {str(e)}"
    except Exception as e:
        # Handle any other unexpected errors
        return f"Error: {str(e)}"



def greeting(greeting_prompt, temperature=0.5): # start greeting function
    messages = [ # initialize message list with system message
        {"role": "system", "content": greeting_prompt},
    ]

    response = openAI.chat.completions.create(model="gpt-4", messages=messages, temperature=temperature) # generate greeting response 

    return response.choices[0].message.content


def summarize(conversation_history, temperature=0.5): # join conversation content, make summary prompt
    summarized_text = ' '.join([msg['content']
                               for msg in conversation_history])
    logging.debug("summarizing the chat history " + summarized_text)
    prompt = f" Make a summerize of the following conversation: {summarized_text} go more in detail and \
        cover most important things. Also you have to be not too long."
    messages = [
        {"role": "system", "content": prompt},
    ]
    response = openAI.chat.completions.create(model="gpt-4",
        messages=messages,
        temperature=temperature)
   
    return response.choices[0].message.content
@app.route('/initialize_session', methods=['GET'])
def initialize_session():
    logging.debug("inititialize session and reset conversation_history, summary, start_time, greeted")
    session['start_time'] = time.time() # Records the elapsed time between the client and the server. time.time() returns the current time
    session["conversation_history"] = []
    session['greeted'] = False
    session['summary'] = ""

  # Retrieve personal information responses from the user data
    user_data = get_user() or {}
    personal_info_responses = user_data.get('personal_info_responses', {})
    
    # Append personal information responses to the conversation history
    for question, response in personal_info_responses.items():
        session['conversation_history'].append({"role": "user", "content": f"{question}: {response}"})
    
    return '', 204

@app.route('/chat', methods=['GET', 'POST'])
def chat():
   
    
    user_data = get_user() or {}
    remaining_time = int(user_data.get('remaining_time', 45 * 60 * 1000))

    session_number = getSessionNumber(user_data)
    if 'new_session_can_start' in session and session['new_session_can_start']==False:
        session_number -= 1
        session_summary = user_data.get(f"{session_number}_summary", [])
        return render_template('chat.html', current_session=session_number,session_summary=session_summary)


    if 'conversation_history' not in session or (remaining_time != 45 * 60 * 1000 and remaining_time > 5):
        session['conversation_history'] = user_data.get(f"{session_number}_conversationHistory", [])
        session['start_time'] = time.time() + (45 * 60 * 1000 - remaining_time) / 1000

    if remaining_time != 45 * 60 * 1000:
        session['greeted'] = True

    if ('greeted' not in session or session['greeted']==False) and len(session['conversation_history']) == 0:
        greeting_prompt = 'Welcome the user. Introduce yourself as a psychologist named AnnaAI. Inform the user that each session lasts 45 minutes. Emphasize the importance of answering each question, explaining that their responses are crucial for understanding their needs and tailoring the session effectively. Encourage them to share openly, as this will help in providing the most relevant support and guidance.'
        greeting_message = greeting(greeting_prompt, temperature=0.5)
        session['conversation_history'].append({"role": "assistant", "content": greeting_message})
        session['greeted'] = True
    
    elif session['greeted'] == True and request.method != 'POST':
        catchup_prompt = 'You are an psychologist and your name is AnnaAI. You had a session with this user in the past and the user left the chat after some time.\
            The sessions take 45 minutes. This user has '+str(remaining_time/1000)+ ' seconds left. Remind this time to user in the mm:ss format.\
            Here is the conversation history from you previous chat belonging to this session: '+ json.dumps(session['conversation_history']) + '\
            Also, catchup with the user.'
        
        greeting_message = greeting(catchup_prompt, temperature=0.5)
        session['conversation_history'].append({"role": "assistant", "content": greeting_message})          
    

    if request.method == 'POST':
        user_input = request.form['user_input']
        session_choice = request.form.get('session_choice', '1')
        session['choice'] = session_choice  # Store the selected session choice in the session

        if user_input.strip():  # Check if the input is not just whitespace
            session['has_interacted'] = True  # Set the flag to True when user interacts

            disorder_name = session.get('given_diagnose', '').strip()
            if not disorder_name:
                disorder_name = user_data.get('diagnosis_name', '').strip()

            given_diagnose = disorders_instance.get_disorder_by_name(disorder_name)
            session_prompt = str(given_diagnose.get_session_questions(int(session_choice))) + " Here is the conversation history so far: " + ' '.join(str(line) for line in session['conversation_history'])

            assistant_response = generate_response(user_input, session_prompt, temperature=0.2)
            session['conversation_history'].append({"role": "user", "content": user_input})
            session['conversation_history'].append({"role": "assistant", "content": assistant_response})

            user_data[f"{session_choice}_conversationHistory"] = session['conversation_history']
            USERS_REF.child(session['random_key']).set(user_data)

            return jsonify({"assistant_response": assistant_response})

   

    return render_template('chat.html', conversation_history=session['conversation_history'], current_session=session_number, remaining_time=remaining_time)


@app.route('/end_session', methods=['GET'])
def end_session():
    logging.debug("The time for the session has ended")
    # get user data
    
    user_data = get_user()

    # Get session numbers
    session_from_ui = request.args.get('selectedSession')
    session_from_db = getSessionNumber(user_data)

    logging.debug("Ending session number ["+str(session_from_ui)+"] for user ["+user_data['random_key']+"] ")
    logging.debug("Session number from db "+str(session_from_db))


    logging.debug("Conversation history size "+str(len(session['conversation_history'])))
    # Check if conversation history exists and has more than just the greeting message
    if 'conversation_history' in session and len(session['conversation_history']) > 1:
        if int(session_from_ui) == session_from_db and int(session_from_ui) < 8:
            logging.debug("Session from db and ui matched incrementing the session number")
            # update/set user data
            user_data['session_number'] = session_from_db + 1
            USERS_REF.child(session['random_key']).set(user_data)
    else:
        # Handle the case where there was no interaction
        flash("No interaction in the chat. Session will not be advanced.")
        return redirect(url_for('chat'))

    # Reset session data
    logging.debug("calling initialize session from end session")
    session_status()
    initialize_session()
    return redirect(url_for('chat'))



def session_has_expired():
    logging.debug("session has expired :: start time==="+str(time.time()-session.get('start_time', 0)))
    return time.time() - session.get('start_time', 0) >= 45 * 60


def handle_session_expiry():
    logging.debug("calling initialize session from handle session expiry")
    initialize_session()  # Start a new session
    return render_template('chat.html', conversation_history=session['conversation_history'])   # Render chat template with session data

def update_remaining_time(remaining_time):
    user_key = session.get('random_key')

    # Update the remaining time in your database
    USERS_REF.child(user_key).update({'remaining_time': remaining_time})

    return '', 204  # Return a 204 No Content status to indicate success

def remove_remaining_time():
    user_key = session.get('random_key')
    USERS_REF.child(user_key).update({'remaining_time': None})
    

@app.route('/session_status', methods=['GET'])
def session_status():

    remaining_time = request.args.get('data')
    logging.debug("remaining time::::"+str(remaining_time))
    user = get_user()
    
    session_number=getSessionNumber(user)-1 # since session is already incremented in end_session

    if (session_has_expired() or (remaining_time and int(remaining_time) < 1000)) and str(session_number)+'_summary' not in user:
        # Generate a summary of the conversation
        summary = summarize(session.get('conversation_history'))
        session["summary"] = summary
        
        user_key = session.get('random_key')
        
        
        user[str(session_number)+'_summary']=summary
        USERS_REF.child(user_key).set(user)
        logging.debug(str(session_number)+"_summary is stored in db")

        session['new_session_can_start']=False
        logging.debug("new_session_can_start is set to False")
        remove_remaining_time()
        return jsonify({"expired": True, "summary": summary})
    elif remaining_time and int(remaining_time) > -5000: # if remaning time is between 0 and -5
        update_remaining_time(remaining_time)
    elif remaining_time and int(remaining_time) < -5000:
        remove_remaining_time()
    
    return jsonify({"expired": False})

@app.route('/complete_session', methods=['POST'])
def complete_session():
    # Example of updating session progress
    current_session = session.get('current_session', 0) # Get current session from session
    if 0 < current_session < 9:
     session[current_session - 1]['completed'] = True
    session['current_session'] = current_session + 1
    return 'Session completed'  # Redirect or render template as needed


def get_user():
    user_data = USERS_REF.child(session['random_key']).get()
    return user_data

def process_pdf_file(filePath):
    pdf_text = ""  # initialize PDF text variable
    with fitz.open(filePath) as pdf_document: # open PDF document
        for page_num in range(pdf_document.page_count):  # iterate over each page
            page = pdf_document[page_num]  # get the current page
            pdf_text += page.get_text() # append the page text to PDF text
    return pdf_text # return the concatenated text

def process_directory(directory_path):
    all_text = ""
    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            if filename.endswith(".pdf"):
                filePath = os.path.join(root, filename)
                file_text = process_pdf_file(filePath)
                all_text += file_text
    return all_text

def getSessionNumber(user_data):
    try:
        session_number = user_data['session_number']
    except KeyError:
        print("Session number not found. Using default value.")
        session_number = 1
    
    return session_number

@app.route('/agree_to_summary', methods=['POST'])
def agree_to_summary():
     return jsonify({"success": True, "message": "Summary agreement recorded."})
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

### end web3 routes ####

if __name__ == '__main__':
    # Configure the logging system
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] - %(message)s',
        handlers=[
            logging.FileHandler('example.log'),  # Output to a log file
        ]
    )
    logger = logging.getLogger(__name__)
    
    serverHost = os.getenv('host')
    serverPort = os.getenv('port')
    app.run(host=serverHost,port=serverPort, debug=os.getenv('debug') ) 

