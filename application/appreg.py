from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
import firebase_admin
from firebase_admin import credentials, db
import uuid
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask import session
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv() 
openai = OpenAI()

import os
import time
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.utilities import WikipediaAPIWrapper
from PyPDF2 import PdfReader
from functools import wraps






app = Flask(__name__)  #creates a Flask web application object named app. It's a fundamental step in setting up a Flask web application
# app.secret_key = 'your_secret_key_here'
# os.environ['OPENAI_API_KEY'] = os.getenv("apiKey")
# app.secret_key = os.environ.get('FLASK_SECRET_KEY', '')
# CREDENTIALS_PATH = os.environ.get('FIREBASE_CREDENTIALS_PATH')  # we must make secure also th credential databaseKey.json!!!
DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL')
# DATABASE_URL = "https://chat-psychologist-ai-default-rtdb.europe-west1.firebasedatabase.app/"

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('index.html')

################################################### Firebase ####################################################################



# Initialize Firebase
cred = credentials.Certificate('/Users/rabia/Desktop/Chat psychologist/Application/ChatPsychologistAI-tanja/databaseKey.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': DATABASE_URL
})


#A function that dosn't allow to access login page if you are already loged in/regiterd 
def redirect_if_logged_in(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if 'user_logged_in' in session:
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
    ref = db.reference('users')
    user_data = ref.child(random_key).get()

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
    
    # Check if it's the user's first login
    if 'diagnosis' in user_data:
        session['first_login'] = False
    else:
        session['first_login'] = True

   # flash('Successfully logged in!')
    return redirect(url_for('home'))


@app.route('/login', methods=['GET'])
@redirect_if_logged_in  # Apply the redirect_if_logged_in decorator
def login_page():
    return render_template('login.html')

######################################### LogOut Firebase ###############################
@app.route('/logout')
def logout():
    session.pop('user_logged_in', None)
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



# From appreg.py
known_disorders = ['social anxiety','anxiety']
 



def extract_disorder(text, disorders):
    return [disorder for disorder in disorders if disorder in text.lower()]

def check_similarity(disorder_list1, disorder_list2):
    return len(set(disorder_list1).intersection(disorder_list2)) / len(set(disorder_list1).union(disorder_list2))

#change the file path and add it to the folder
file_path = '/Users/rabia/Desktop/Chat psychologist/Application/ChatPsychologistAI-tanja/content/APA_DSM5_Severity-Measure-For-Social-Anxiety-Disorder-Adult_update.pdf'
pdf_text = ""

@app.route("/questions", methods=['GET', 'POST'])
@login_required  # Ensure user is logged in to access this route
def questions():   
    questions = [
        "Do you feel extremely anxious or uncomfortable when meeting new people?",
        "Do you often worry about being judged or criticized by others in social situations?",
        "Do you frequently avoid social events or activities due to fear of embarrassment or humiliation?",
        "Do you experience intense anxiety when speaking or presenting in front of a group?",
        "Do you find it difficult to initiate or maintain conversations with others?"
       
        
    ]
    
    result = None
    diagnosis_found = False
    saved_diagnosis = None  # Initialize the saved_diagnosis variable
    USERS_REF = db.reference('users')

    # Check if it's the user's first login based on the session variable
    first_login = session.get('first_login', True)

    if request.method == 'POST':
        if first_login:       
            responses = [request.form.get(f'q{i+1}') for i in len(questions)]  # get all the answers
            prompt = request.form.get('prompt')  # get the prompt
            diagnosis_result = process_data(responses, prompt)  # process these two data
            result = diagnosis_result['message']  # add these processed data into message
            diagnosis_found = diagnosis_result['diagnosis_found']

            if diagnosis_found:
                user_data = USERS_REF.child(session['random_key']).get()
                if user_data:
                    user_data['diagnosis'] = result
                    USERS_REF.child(session['random_key']).set(user_data)
            
            session['first_login'] = False
            
            return render_template('diagnose.html', result=result, questions=questions, diagnosis_found=diagnosis_found)
        
        return render_template('diagnose.html', questions=questions)      
         
    else:
        if first_login:
            return render_template('diagnose.html', questions=questions)
        else:
            # If it's not the user's first login, retrieve the saved diagnosis
            user_data = USERS_REF.child(session['random_key']).get()
            if user_data:
                saved_diagnosis = user_data.get('diagnosis')
                if saved_diagnosis:
                    diagnosis_found = True  # Update the diagnosis_found variable here
            return render_template('diagnose.html', saved_diagnosis=saved_diagnosis, diagnosis_found=diagnosis_found)
        
    

def process_data(responses, prompt):
    
    # Initialize the various components
    llm = OpenAI(temperature=0.9)
    
    _templates = db.reference('templates')
    problem_template_text = _templates.child('problem_template').get()

    problem_template = PromptTemplate(
        input_variables=['q1', 'q2', 'q3', 'q4', 'q5', 'topic'],
        template='Act as a therapist and help the user with their mental health problem. Try to come to a conclusion about which mental illness the user may have based on their responses. Set a specific diagnosis based on answers \nQ1: {q1}\nQ2: {q2}\nQ3: {q3}\nQ4: {q4}\nQ5: {q5}\n and this user Description: {topic}'
    )
    
    script_template = PromptTemplate(
        input_variables=['problem', 'wikipedia_research'],
        template='Provide solutions and treatments based on the diagnosis :\n {problem}  also use the information of \nWikipedia Research: {wikipedia_research} to reach a better solution and treatments '
    )
    
    diagnosis_template = PromptTemplate(
        input_variables=['pdf_text'],
        template='I have a long text document and need a brief summary. Extract the main diagnosis mentiond in this medical text.The text is: {pdf_text} . '
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
    
    pdf_text = ""
    with open(file_path, 'rb') as file:    #open the file and read it 
        pdf_reader = PdfReader(file)
        for page in pdf_reader.pages:
            pdf_text += page.extract_text()

#run all the chains
    problem = problem_chain.run(
        q1=responses[0], q2=responses[1], q3=responses[2], q4=responses[3], q5=responses[4], topic=prompt
    )    
    wiki_research = wiki.run(prompt)
    script = script_chain.run(problem=problem, wikipedia_research=wiki_research)
    pdf_diagnosis = diagnosis_chain.run(pdf_text=pdf_text)
    
    #extract disorder from pdf and from the GPT diagnosed
    problem_disorder = extract_disorder(problem, known_disorders)
    pdf_disorder = extract_disorder(pdf_diagnosis, known_disorders)
    
    similarity = check_similarity(problem_disorder, pdf_disorder)
    
    if similarity > 0.2:
        return {
        'message': f"Good news! We found a match!\n\n{problem}\n\n{script}",
        'diagnosis_found': True
    }
    else:
       return {
        'message': "Based on our analysis, the diagnoses from your answers and the uploaded document do not match. Please provide more information and try again.",
        'diagnosis_found': False
    }


@app.route('/result')   #dispaly diagnose and treatment
@login_required  # Ensure user is logged in to access this route
def result():
    questions = session.get('questions', [])
    return render_template('diagnose.html', questions=questions)

#########################################################Chat Page##############################################

def generate_response(user_input, session_prompt, temperature=0.1):
    messages = [
        {"role": "system", "content": session_prompt},
        {"role": "user", "content": user_input}
    ]
    
    try:
        response = openai.chat.completions.create(model="gpt-4",
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
    except openai.InvalidRequestError as e:
        # Handle invalid request errors
        return f"Invalid Request Error: {str(e)}"
    except openai.APIConnectionError as e:
        # Handle API connection errors
        return f"API Connection Error: {str(e)}"
    except Exception as e:
        # Handle any other unexpected errors
        return f"Error: {str(e)}"



def greeting(greeting_prompt, temperature=0.5):
    messages = [
        {"role": "system", "content": greeting_prompt},
    ]

    response = openai.chat.completions.create(model="gpt-4", messages=messages, temperature=temperature)

    return response.choices[0].message.content


def summarize(conversation_history, temperature=0.5):
    summarized_text = ' '.join([msg['content']
                               for msg in conversation_history])
    prompt = f" Make a summerize of the following conversation: {summarized_text} go more in ditail and cover most important things. Also you have to be not to long."
    messages = [
        {"role": "system", "content": prompt},
    ]
    response = openai.chat.completions.create(model="gpt-4",
    messages=messages,
    temperature=temperature)
    return response.choices[0].message.content

def initialize_session():
    session['start_time'] = time.time()
    session["conversation_history"] = []
    session['greeted'] = False
    session['summary'] = ""

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'conversation_history' not in session:
        initialize_session()

    if session_has_expired():
        return handle_session_expiry()


    if not session['greeted']:
        greeting_prompt = 'Welcome the user. Present yourself as an AnnaAI psychologist and also mention that the duration of one session is 5 minutes. After that time passes, you have to inform the user that the time has passed and the session has ended.'
        greeting_message = greeting(greeting_prompt, temperature=0.5)
        session['conversation_history'].append({"role": "assistant", "content": greeting_message})
        session['greeted'] = True
        

    if request.method == 'POST':
        user_input = request.form['user_input']
        session_choice = request.form.get('session_choice', '')
        if session_choice == "Session 1":
            session_prompt = " You are highly professional psychologist. Your primary role is to help patient diagnosed with social anxiety to deal with it. This is the first treatment session. Start first with short interdiction, establish rapport and explain the treatment process. The goal is to gather information to create an appropriate treatment plan while also establishing trust and rapport. This questions you have to ask one by one and to wait for response for each of them : Can you share with me what led you to seek therapy and what specific challenges or concerns you're facing related to social situations?, How long have you been experiencing symptoms of social anxiety, and have they changed or worsened over time? ,Can you describe the specific situations or social settings where you feel most anxious or uncomfortable?, Have you noticed any triggers or patterns that intensify your social anxiety?, How does social anxiety impact your daily life, relationships, and overall well-being?, Have you attempted any coping mechanisms or strategies to manage your anxiety in social situations? How effective have they been for you?, Are there any past experiences or traumas that you think might be contributing to your social anxiety?, Do you have any concerns or fears about the therapy process itself, or is there anything specific you'd like to know about how therapy works?, Have you received any previous treatment or therapy for social anxiety, and if so, what was your experience like?, Are there any specific goals or outcomes you hope to achieve through therapy for social anxiety?, Are there any cultural, religious, or personal beliefs that may influence your approach to therapy or your experience of social anxiety?, Is there anything you'd like to know about social anxiety, its causes, or its treatment options?, How do you currently perceive yourself in social situations, and how would you like to see yourself in these situations in the future? What strengths or coping skills do you have that you feel might help you in overcoming social anxiety?,How comfortable are you with the idea of gradually confronting social situations that trigger your anxiety as part of therapy?, Conduct a comprehensive assessment to understand the extent and impact of social anxiety in their life. Help them and provide them with solutions to their ."
        else:
            session_prompt = "Psychoeducation on Social Anxiety.Educate the client about the nature of social anxiety, its common symptoms, and the cognitive-behavioral model of treatment. Present information about social anxiety, how it develops, and its maintenance factors. Encourage the client to ask questions and share personal experiences related to the topics discussed."

        assistant_response = generate_response(user_input, session_prompt, temperature=0.2)
        session['conversation_history'].append({"role": "user", "content": user_input})
        session['conversation_history'].append({"role": "assistant", "content": assistant_response})
    
        return jsonify({"assistant_response": assistant_response})

        
    return render_template('chat.html', conversation_history=session['conversation_history'])


@app.route('/end_session', methods=['GET'])
def end_session():
    initialize_session()
    return redirect(url_for('chat'))

def session_has_expired():
    return time.time() - session.get('start_time', 0) >= 5 * 60


def handle_session_expiry():
    initialize_session()
    return render_template('chat.html', conversation_history=session['conversation_history'])


@app.route('/session_status', methods=['GET'])
def session_status():
    if session_has_expired():
        # Generate a summary of the conversation
        summary = summarize(session["conversation_history"])
        session["summary"] = summary
        return jsonify({"expired": True, "summary": summary})
    return jsonify({"expired": False})


if __name__ == '__main__':
    app.run(debug=True)
