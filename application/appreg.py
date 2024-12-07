from flask import Flask, session, request, render_template, redirect, url_for, flash, jsonify, make_response
from logging import DEBUG
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
from personal_info import personal_info_questions_phase_1, personal_info_questions_phase_2, personal_info_questions_phase_3
from diagnose_questions import diagnose_questions
from personal_insight import personal_insights_questions
app = Flask(__name__, static_folder='static')
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

### Firebase ###
# Initialize Firebase
cred = credentials.Certificate(os.getenv('FIREBASE_DATABASE_CERTIFICATE'))
firebase_admin.initialize_app(cred, {
    'databaseURL': DATABASE_URL
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

    if not password1 or not password2:
        flash('Please fill in both password fields.' )
        return redirect(url_for('register_page'))

    if password1 != password2:
        flash('Passwords do not match.')
        return redirect(url_for('register_page'))
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
    return redirect(url_for('login_page'))


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


#####Treatment Page ######

# @app.route('/treatment')
# @login_required
# def treatment():
#     user_data = get_user()
#     diagnosis_complete = 'diagnosis_name' in user_data and bool(user_data['diagnosis_name'])
#     personal_info_complete = user_data.get('personal_info_completed', False)  # Use the database flag
#     personal_insights_complete = user_data.get('personal_insights_completed', False)

#     # if not personal_info_complete:
#     #     return redirect(url_for('personal_info'))
#     if not personal_info_complete:
#         return redirect(url_for('personal_info_phase_3'))

#     if not personal_insights_complete:
#         return redirect(url_for('personal_insights'))

#     return render_template('treatment.html', diagnosis_complete=diagnosis_complete)

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
    personal_insights_complete = user_data.get('personal_insights_completed', False)
    diagnosis_complete = 'diagnosis_name' in user_data and bool(user_data['diagnosis_name'])

    # Redirect to the appropriate page if any step is incomplete
    if not personal_info_complete:
        return redirect(url_for('personal_info_phase_1'))

    if not personal_insights_complete:
        return redirect(url_for('personal_insights'))

    return render_template('treatment.html')



###########################################personal info Page ########################################

#FIXME - Adding more data for each phases
#FIXME - Add more agents for reading pdf, look for flow of data
#FIXME - Check latency
file_path = '/Users/dandev947366/Desktop/test/ChatPsychologistAI/application/data/Mental_Health_Statistics_2024.docx'
txt_path = "/Users/dandev947366/Desktop/test/ChatPsychologistAI/application/data/personal_info_statistic.txt"
import docx
SERPER_API_KEY = os.getenv('SERPER_API_KEY')
api_key = os.getenv('OPENAI_API_KEY_2')

@app.route('/personal_info_phase_1', methods=['GET', 'POST'])
@login_required
def personal_info_phase_1():
    user_data = get_user()
    if user_data.get('personal_info_phase_1_completed', False):
        return redirect(url_for('personal_info_phase_2'))
    if request.method == 'POST':
        personal_info_responses = {key: value for key, value in request.form.items()}
        print("Form Responses:", personal_info_responses)
        user_data['personal_info_phase_1_completed'] = True
        user_data['personal_info_responses_phase_1'] = personal_info_responses
        USERS_REF.child(session['random_key']).set(user_data)
        return redirect(url_for('personal_info_phase_2'))
    return render_template('personal_info_phase_1.html', questions=personal_info_questions_phase_1)


def sanitize_key(key):
    # Replace invalid characters with an underscore or remove them
    return key.replace('$', '_').replace('#', '_').replace('[', '_').replace(']', '_').replace('/', '_').replace('.', '_')


@app.route('/personal_info_phase_2', methods=['GET', 'POST'])
@login_required
def personal_info_phase_2():
    user_data = get_user()
    if user_data.get('personal_info_phase_2_completed', False):
        return redirect(url_for('personal_info_phase_3'))
    if request.method == 'POST':
        personal_info_responses = {key: value for key, value in request.form.items()}
        print("Form Responses:", personal_info_responses)
        user_data['personal_info_phase_2_completed'] = True
        user_data['personal_info_responses_phase_2'] = personal_info_responses
        USERS_REF.child(session['random_key']).set(user_data)
        return redirect(url_for('personal_info_phase_3'))
    return render_template('personal_info_phase_2.html', questions=personal_info_questions_phase_2)



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

                if question['type'] == 'group':
                    # Capture range and text input for the grouped question
                    score = request.form.get(f'{topic}_phase_3_score_{index}')
                    comments = request.form.get(f'{topic}_phase_3_comments_{index}')

                    # Log to console for debugging
                    print(f"Received score: {score}, comments: {comments} for question {index}")

                    personal_info_responses[topic][question_info_type] = {
                        'score': (str(score) if score else "0") + "/100",  # Default to None if score is empty
                        'comments': comments if comments else None  # Default to None if comments are empty
                    }
                else:
                    # Capture other question types normally
                    answer = request.form.get(f'{topic}_question_{index}')
                    # Log to console for debugging
                    print(f"Received answer: {answer} for question {index}")

                    personal_info_responses[topic][question_info_type] = answer if answer else None  # Default to None if answer is empty

        # Update user data
        user_data['personal_info_phase_3_completed'] = True
        user_data['personal_info_responses_phase_3'] = personal_info_responses

        # Save updated user data to the database
        USERS_REF.child(session['random_key']).set(user_data)

        # Call the agent to process the personal info responses
        #call_phase3_agent(user_data['personal_info_responses_phase_3'], api_key, file_path)

        return redirect(url_for('treatment'))

    return render_template('personal_info_phase_3.html', questions=personal_info_questions_phase_3)



###################################################### Sahar's Work on Personal Insight Page #####################################################


@app.route('/personal_insights', methods=['GET', 'POST'])
@login_required
def personal_insights():
    user_data = get_user()

    # Redirect to phase 1 if already completed
    if user_data.get('personal_insight_completed', False):
        return redirect(url_for('questions'))

    if request.method == 'POST':
        personal_insight_responses = {}

        for index, question in enumerate(personal_insights_questions, start=1):
            topic = sanitize_key(question.get('topic', f"Topic {index}"))
            personal_insight_responses[topic] = {}

            questions = question.get('questions')
            for index, question in enumerate(questions, start=1):
                question_info_type = sanitize_key(question.get('info_type', f"Info type {index}"))

                # Capture text input for the question
                answer = request.form.get(f'{topic}_question_{index}')
                # Log to console for debugging
                print(f"Received answer: {answer} for question {index}")

                personal_insight_responses[topic][question_info_type] = answer if answer else None  # Default to None if answer is empty

        # Update user data
        user_data['personal_insight_completed'] = True
        user_data['personal_insight_responses'] = personal_insight_responses

        # Save updated user data to the database
        USERS_REF.child(session['random_key']).set(user_data)

        return redirect(url_for('questions'))

    return render_template('personal_insights.html', questions=personal_insights_questions)

########################################## End of personal insight Page ########################################


# ManagerAgent class for handling interactions between user and CrewAI
class ManagerAgent:
    def __init__(self, api_key):
        self.api_key = api_key
        self.personal_info_agent = PersonalInfoAIAgent(api_key)

    def generate_analysis_prompt(self, user_responses):
        # Parse the raw user data
        age = user_responses.get("What is your age?", "unknown")
        gender = user_responses.get("What is your gender?", "unknown")
        nationality = user_responses.get("What is your nationality?", "unknown")
        residence = user_responses.get("What is your current country of residence?", "unknown")
        ethnicity = user_responses.get("What cultural or ethnic background do you identify with? How does this influence your daily life?", "unknown")
        marital_status = user_responses.get("What is your marital status?", "unknown")
        education = user_responses.get("What is your education level?", "unknown")
        employment_status = user_responses.get("What is your employment status?", "unknown")
        living_situation = user_responses.get("What is your living situation?", "unknown")
        support_system = user_responses.get("Do you have a stable support system?", "unknown")
        community_involvement = user_responses.get("Are you actively involved in any community or social groups? How does this impact your social interactions?", "unknown")

        # Generate dynamic analysis prompt
        prompt = (
            f"Search for Race and Ethnicity, Gender, Employment, Education, Social Support, Community Involvement, Exercise, "
            f"and Stress factors that impact mental health. Search can be separated for each category. "
            f"Use the results to analyze this user: The individual is a {age}-year-old {gender} from {residence}, "
            f"of {ethnicity} ethnic background, currently residing in {residence}. "
            f"He/She is {marital_status}, has a {education} education, is {employment_status}, and lives {living_situation}. "
            f"The individual has a stable support system ({support_system}), with close relationships and is actively involved in {community_involvement}. "
            f"Based on these factors, estimate the mental health risk for conditions such as anxiety, depression, and stress-related disorders, "
            f"considering how unemployment, community involvement, family support, and other demographics might impact overall well-being. "
            f"Provide a detailed report with percentage estimates for diagnoses."
        )

        return prompt
    def pass_to_personal_info_agent(self, prompt):

        #FIXME - fix solution to handle prompt, analyze_prompt not present
        return self.personal_info_agent.analyze_prompt(prompt)


from dotenv import load_dotenv
from langchain import hub
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
import pdfplumber
import requests
from bs4 import BeautifulSoup


# #FIXME - Adjust agent for new questions
# #FIXME - Adding tools for handling data
# class PersonalInfoAIAgent:
#     def __init__(self, api_key):
#         self.api_key = api_key
#     def get_current_time(*args, **kwargs):
#         """Returns the current time in H:MM AM/PM format."""
#         import datetime
#         now = datetime.datetime.now()
#         return now.strftime("%I:%M %p")

#     def search_wikipedia(query):
#         """Searches Wikipedia and returns the summary of the first result."""
#         from wikipedia import summary
#         try:
#             return summary(query, sentences=2)
#         except:
#             return "I couldn't find any information on that."
# # Define the PDF reading tool
#     def pdf_reader_tool(file_path):
#         """Tool to read PDF and return its content."""
#         return read_pdf(file_path)
#     def read_pdf(file_path):
#         """Extracts text from a PDF file."""
#         pdf_text = ""
#         try:
#             print(f"Opening PDF file: {file_path}")  # Debug statement
#             with pdfplumber.open(file_path) as pdf:
#                 for page in pdf.pages:
#                     page_text = page.extract_text() or ""
#                     # print(f"Page text: {page_text}")  # Print PDF content
#                     if page_text.strip():
#                         pdf_text += page_text + "\n"
#             print("Personal Info Agent read pdf >> Completed")
#         except Exception as e:
#             return f"Error reading PDF: {e}"

#         if not pdf_text.strip():
#             return "No text found in the PDF."
#         return "Personal Info Agent read pdf >> Completed"
#         # return pdf_text

#     def scrape_web(url):
#         """Scrapes content from a given URL and returns the text."""
#         try:
#             response = requests.get(url)
#             response.raise_for_status()  # Check for HTTP request errors
#             soup = BeautifulSoup(response.text, 'html.parser')
#             text = soup.get_text()
#             return text
#         except requests.RequestException as e:
#             return f"Error scraping the web page: {e}"

#     # Define the tools that the agent can use
#     tools = [
#         Tool(
#             name="Time",
#             func=get_current_time,
#             description="Useful for when you need to know the current time.",
#         ),
#         Tool(
#             name="Wikipedia",
#             func=search_wikipedia,
#             description="Useful for when you need to know information about a topic.",
#         ),
#         Tool(
#             name="PDF Reader",
#             func=pdf_reader_tool,
#             description="Extracts text from a PDF file.",
#         ),
#         Tool(
#             name="Web Scraper",
#             func=scrape_web,
#             description="Scrapes text content from a specified URL.",
#         ),
#     ]

#     # Load the correct JSON Chat Prompt from the hub
#     prompt = hub.pull("hwchase17/structured-chat-agent")

#     # Initialize a ChatOpenAI model
#     llm = ChatOpenAI(model="gpt-4o")§

#     # Create a structured Chat Agent with Conversation Buffer Memory
#     memory = ConversationBufferMemory(
#         memory_key="chat_history", return_messages=True)

#     # Create the structured chat agent
#     agent = create_structured_chat_agent(llm=llm, tools=tools, prompt=prompt)

#     # Create an AgentExecutor with the agent and tools
#     agent_executor = AgentExecutor.from_agent_and_tools(
#         agent=agent,
#         tools=tools,
#         verbose=True,
#         memory=memory,
#         handle_parsing_errors=True,
#     )

#     # Initial system message
#     #FIXME - Adjust this according to new phases
#     #FIXME - Check SRS
#     initial_message = (
#         "You are an AI assistant that can provide helpful answers using available tools.\n"
#         "You can use these tools: Time, Wikipedia, PDF Reader, and Web Scraper."
#     )
#     memory.chat_memory.add_message(SystemMessage(content=initial_message))

#     # Load PDF content into memory
#     #FIXME - Make central data for many pdf
#     pdf_file_path = "/Users/dandev947366/Desktop/test/llama/data/data-to-analyze.pdf"  # Update this path to your PDF file
#     pdf_content = read_pdf(pdf_file_path)
#     if pdf_content:
#         memory.chat_memory.add_message(AIMessage(content=f"PDF Content:\n{pdf_content}"))

#     # Chat Loop to interact with the user
#     while True:
#     #!SECTION - prompt input
#     #NOTE - prompt needs to be handled separately as personal info agent asks back manager agent for prompt
#         user_input = input("User: ")
#         # user_input = input(prompt)
#         if user_input.lower() == "exit":
#             break

#         # Add the user's message to the conversation memory
#         memory.chat_memory.add_message(HumanMessage(content=user_input))

#         # Check if user input requests a web scraping action
#         if user_input.lower().startswith("scrape"):
#             # Extract the URL from user input (assuming URL is provided after the command)
#             url = user_input[len("scrape"):].strip()
#             if url:
#                 scrape_result = scrape_web(url)
#                 response = {"output": scrape_result}
#             else:
#                 response = {"output": "Please provide a URL to scrape."}
#         else:
#             # Invoke the agent with the user input and the current chat history
#             try:
#                 response = agent_executor.invoke({"input": user_input})
#             except Exception as e:
#                 response = {"output": f"Error during agent execution: {e}"}

#         print("Bot:", response["output"])

#         # Add the agent's response to the conversation memory
#         memory.chat_memory.add_message(AIMessage(content=response["output"]))

def call_phase3_agent(data, api_key, docx_path):
    # # Instantiate the ManagerAgent
    # manager_agent = ManagerAgent(api_key)

    # # Generate the analysis prompt
    # prompt = manager_agent.generate_analysis_prompt(data)

    # # Pass the prompt to the PersonalInfoAIAgent and get the result
    # result = manager_agent.pass_to_personal_info_agent(prompt)

    # Log or save the result
    print("Personal Info PHASE 3 >> User's responses:\n", data)
    print('--------------------------------')
    # print("Manager agent calling Personal Info agent >> Prompt:\n", prompt)
    print('--------------------------------')
    print("Personal Info Agent Analysis:\nReport >>", result)
# Function to call CrewAI agent to process the user's personal info responses
def call_phase2_agent(data, api_key, docx_path):
    # # Instantiate the ManagerAgent
    # manager_agent = ManagerAgent(api_key)

    # # Generate the analysis prompt
    # prompt = manager_agent.generate_analysis_prompt(data)

    # # Pass the prompt to the PersonalInfoAIAgent and get the result
    # result = manager_agent.pass_to_personal_info_agent(prompt)

    # Log or save the result
    print("Personal Info PHASE 2 >> User's responses:\n", data)
    print('--------------------------------')
    # print("Manager agent calling Personal Info agent >> Prompt:\n", prompt)
    print('--------------------------------')
    print("Personal Info Agent Analysis:\nReport >>", result)

def call_phase1_agent(data):
    # Instantiate the Phase1Agent
    phase1_agent = Phase1Agent()

    # Log the user's responses
    print("Personal Info PHASE 1 >> User's responses:\n", data)
    print('--------------------------------')

    # Call the process_user_response method to generate the report
    report = phase1_agent.process_user_response(data)

    # Print the report
    print("Personal Info Agent Analysis:\nReport >>", report)
###########################################Personal insights Page ########################################
########################################### Sahar comment it out because of crewai error and not storing in Firebase ########################################
insight_file_path=""
# @app.route('/personal_insights', methods=['GET', 'POST'])
# @login_required
# def personal_insights():
#     user_data = get_user()
#     if user_data.get('personal_insights_completed', False):
#         return redirect(url_for('treatment'), questions=personal_insights_questions)
#     if request.method == 'POST':
#       personal_insights_responses = {}

#       for index, question in enumerate(personal_insights_questions, start=1):
#         topic = sanitize_key(question.get('topic', f"Topic {index}"))
#         personal_insights_responses[topic] = {}
#         # personal_insights_responses = {index: request.form.get(str(index)) for index, item in enumerate(personal_insights_questions)}
#         user_data['personal_insights_completed'] = True
#         user_data['personal_insights_responses'] = personal_insights_responses
#         USERS_REF.child(session['random_key']).set(user_data)
#         # call_crewai_agent(user_data['personal_insights_responses'], api_key, insight_file_path)
#         return redirect(url_for('treatment'))
#     return render_template('personal_insights.html', questions=personal_insights_questions)

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

    user_data = get_user()


    # Check if it's the user's first login based on the session variable
    first_login = session.get('first_login', True)

    if request.method == 'POST':
        if first_login:
            diagnose_responses = {}

        for index, question in enumerate(diagnose_questions, start=1):
            topic = sanitize_key(question.get('topic', f"Topic {index}"))
            diagnose_responses[topic] = {}

            questions = question.get('questions')
            for index, question in enumerate(questions, start=1):
                question_info_type = sanitize_key(question.get('info_type', f"Info type {index}"))

                # Capture range and text input for the  question
                score = request.form.get(f'{topic}_diagnose_score_{index}')
                comments = request.form.get(f'{topic}_diagnose_comments_{index}')

                # Log to console for debugging
                print(f"Received score: {score}, comments: {comments} for question {index}")

                diagnose_responses[topic][question_info_type] = {
                    'score': (str(score) if score else "0") + "/5",  # Default to None if score is empty
                    'comments': comments if comments else None  # Default to None if comments are empty
                }

        # Update user data
        user_data['diagnose_responses'] = diagnose_responses

        # Save updated user data to the database
        USERS_REF.child(session['random_key']).set(user_data)

        # Call the agent to process the diagnose responses


        return redirect(url_for('treatment'))

    return render_template('diagnose.html', questions=diagnose_questions)
#################################################### End of Sahar's Work for diagnose page ########################################################
    #         diagnose_responses = [request.form.get(f'q{i+1}') for i in range(len(diagnosequestions))]  # get all the answers
    #         personal_info_responses = {question['question']: request.form.get(str(index)) for index, question in enumerate(personal_info_questions)}
    #         personal_insights_responses = {question['question']: request.form.get(str(index)) for index, question in enumerate(personal_insights_questions)}
    #         prompt = request.form.get('prompt')  # get the prompt
    #         diagnosis_result = process_data(diagnose_responses, personal_info_responses,personal_insights_responses, prompt)  # process these datas
    #         result = diagnosis_result['message']  # add these processed data into message
    #         diagnosis_found = diagnosis_result['diagnosis_found']
    #         session['given_diagnose'] = diagnosis_result['given_diagnose']

    #         if diagnosis_found:
    #             user_data = get_user()
    #             if user_data:
    #                 user_data['diagnosis'] = result
    #                 user_data['diagnosis_name'] = session['given_diagnose']
    #                 USERS_REF.child(session['random_key']).set(user_data)

    #         session['first_login'] = False

    #         return render_template('diagnose.html', result=result, questions=diagnosequestions, diagnosis_found=diagnosis_found)

    #     return render_template('diagnose.html', questions=diagnosequestions)

    # else:
    #     if first_login:
    #         return render_template('diagnose.html', questions=diagnosequestions)
    #     else:
    #         # If it's not the user's first login, retrieve the saved diagnosis
    #         user_data = get_user()
    #         if user_data:
    #             saved_diagnosis = user_data.get('diagnosis')
    #             if saved_diagnosis:
    #                 diagnosis_found = True  # Update the diagnosis_found variable here
    #         return render_template('diagnose.html', saved_diagnosis=saved_diagnosis, diagnosis_found=diagnosis_found)




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
        level=DEBUG,
        format='%(asctime)s [%(levelname)s] - %(message)s',
        handlers=[
            logging.FileHandler('example.log'),  # Output to a log file
        ]
    )
    logger = logging.getLogger(__name__)

    serverHost = os.getenv('host')
    serverPort = os.getenv('port')
    app.run(host=serverHost,port=serverPort, debug=os.getenv('debug') )

