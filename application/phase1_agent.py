import os
import requests
import pdfplumber
from flask import Flask
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
from your_memory_module import ConversationBufferMemory  # Replace with your actual memory module
from your_tool_module import Tool, create_structured_chat_agent, AgentExecutor  # Adjust import paths as necessary

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY_2')

class PersonalInfoAIAgent:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_current_time(self):
        """Returns the current time in H:MM AM/PM format."""
        import datetime
        now = datetime.datetime.now()
        return now.strftime("%I:%M %p")

    def search_wikipedia(self, query):
        """Searches Wikipedia and returns the summary of the first result."""
        from wikipedia import summary
        try:
            return summary(query, sentences=2)
        except Exception:
            return "I couldn't find any information on that."

    def read_pdf(self, file_path):
        """Extracts text from a PDF file."""
        pdf_text = ""
        try:
            print(f"Opening PDF file: {file_path}")  # Debug statement
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        pdf_text += page_text + "\n"
            print("Personal Info Agent read pdf >> Completed")
        except Exception as e:
            return f"Error reading PDF: {e}"

        if not pdf_text.strip():
            return "No text found in the PDF."
        return pdf_text
    
    def scrape_web(self, url):
        """Scrapes content from a given URL and returns the text."""
        try:
            response = requests.get(url)
            response.raise_for_status()  # Check for HTTP request errors
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            return text
        except requests.RequestException as e:
            return f"Error scraping the web page: {e}"

    # Define the tools that the agent can use
    tools = [
        Tool(name="Time", func=get_current_time, description="Useful for when you need to know the current time."),
        Tool(name="Wikipedia", func=search_wikipedia, description="Useful for when you need to know information about a topic."),
        Tool(name="PDF Reader", func=read_pdf, description="Extracts text from a PDF file."),
        Tool(name="Web Scraper", func=scrape_web, description="Scrapes text content from a specified URL."),
    ]
    
    # Load the correct JSON Chat Prompt from the hub
    prompt = hub.pull("hwchase17/structured-chat-agent")

    # Initialize a ChatOpenAI model
    llm = ChatOpenAI(model="gpt-4o")

    # Create a structured Chat Agent with Conversation Buffer Memory
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # Create the structured chat agent
    agent = create_structured_chat_agent(llm=llm, tools=tools, prompt=prompt)

    # Create an AgentExecutor with the agent and tools
    agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, memory=memory, handle_parsing_errors=True)

    # Initial system message
    initial_message = (
        "You are an AI assistant that can provide helpful answers using available tools.\n"
        "You can use these tools: Time, Wikipedia, PDF Reader, and Web Scraper."
    )
    memory.chat_memory.add_message(SystemMessage(content=initial_message))

    # Load PDF content into memory
    pdf_file_path = "/Users/dandev947366/Desktop/test/llama/data/data-to-analyze.pdf"  # Update this path to your PDF file
    pdf_content = self.read_pdf(pdf_file_path)
    if pdf_content:
        memory.chat_memory.add_message(AIMessage(content=f"PDF Content:\n{pdf_content}"))

    # Chat Loop to interact with the user
    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            break

        # Add the user's message to the conversation memory
        memory.chat_memory.add_message(HumanMessage(content=user_input))

        # Check if user input requests a web scraping action
        if user_input.lower().startswith("scrape"):
            # Extract the URL from user input (assuming URL is provided after the command)
            url = user_input[len("scrape"):].strip()
            if url:
                scrape_result = self.scrape_web(url)
                response = {"output": scrape_result}
            else:
                response = {"output": "Please provide a URL to scrape."}
        else:
            # Invoke the agent with the user input and the current chat history
            try:
                response = agent_executor.invoke({"input": user_input})
            except Exception as e:
                response = {"output": f"Error during agent execution: {e}"}

        print("Bot:", response["output"])

        # Add the agent's response to the conversation memory
        memory.chat_memory.add_message(AIMessage(content=response["output"]))
