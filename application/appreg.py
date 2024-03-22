from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
import firebase_admin
from firebase_admin import credentials, db
import uuid
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask import session
import openai
from openai import OpenAI
from dotenv import load_dotenv
import json
import logging



load_dotenv() 
client = OpenAI()

import os
import time
from langchain_community.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_community.utilities import WikipediaAPIWrapper
from PyPDF2 import PdfReader
from functools import wraps

from Disorders import Disorders
 
import fitz

app = Flask(__name__, static_folder='static')  #creates a Flask web application object named app. It's a fundamental step in setting up a Flask web application
app.secret_key = 'your_secret_key_here'


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


USERS_REF = db.reference('users')

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
@login_required  # Ensure user is logged in to access this route
def treatment():
    return render_template('treatment.html')

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
        "Have you felt unusually tired or low on energy most days, making even small tasks seem exhausting?"
        
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
            responses = [request.form.get(f'q{i+1}') for i in range(len(diagnosequestions))]  # get all the answers
            prompt = request.form.get('prompt')  # get the prompt
            diagnosis_result = process_data(responses, prompt)  # process these two data
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
        
    

def process_data(responses, prompt):
    
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

    

    problem_template = PromptTemplate(
        input_variables=['a', 'q', 'topic'],
        template = "Act as a therapist to support the user's mental health needs. \
        Carefully analyze the user's responses and behavior to identify potential mental health \
        conditions. Utilize the information provided by the user in their description ({topic}) and their \
        answers ({a}) to specific questions ({q}). Based on this data, formulate a precise diagnosis"
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


    problem = problem_chain.run(
        a=responses, q=diagnosequestions, topic=prompt
    ) 
  
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
    messages = [ # initialize message list with system and user messages
        {"role": "system", "content": session_prompt},
        {"role": "user", "content": user_input}
    ]
    
    try:
        # generate chat response 
        response = client.chat.completions.create(model="gpt-4",
        messages=messages,
        temperature=temperature)
        return response.choices[0].message.content
    except openai.OpenAIError as e:
        # Handle OpenAI API errors
        return f"OpenAI API Error: {str(e)}"
    except openai.RateLimitError as e:
        # Handle rate limit errors
        return f"Rate Limit Error: {str(e)}"
    except openai.AuthenticationError as e:
        # Handle authentication errors
        return f"Authentication Error: {str(e)}"
    except openai.InternalServerError as e:
        # Handle invalid request errors
        return f"Invalid Server Error: {str(e)}"
    except openai.APIConnectionError as e:
        # Handle API connection errors
        return f"API Connection Error: {str(e)}"
    except Exception as e:
        # Handle any other unexpected errors
        return f"Error: {str(e)}"



def greeting(greeting_prompt, temperature=0.5): # start greeting function
    messages = [ # initialize message list with system message
        {"role": "system", "content": greeting_prompt},
    ]

    response = client.chat.completions.create(model="gpt-4", messages=messages, temperature=temperature) # generate greeting response 

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
    response = client.chat.completions.create(model="gpt-4",
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
            session_prompt = str(given_diagnose.get_session_questions(int(session_choice)))

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

