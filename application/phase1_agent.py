# import os
# import requests
# import pdfplumber
# from flask import Flask
# from dotenv import load_dotenv
# from duckduckgo_search import DDGS
# from bs4 import BeautifulSoup
# from langchain.memory import ConversationBufferMemory
# from langchain.agents import Tool, create_structured_chat_agent, AgentExecutor
# from langchain import hub
# from langchain.chat_models import ChatOpenAI
# from langchain.schema import SystemMessage, HumanMessage, AIMessage

# # Load environment variables
# load_dotenv()
# api_key = os.getenv('OPENAI_API_KEY_2')

# # FIXME - Adding tools for handling data
# class PersonalInfoAIAgent:
#     def __init__(self, api_key):
#         self.api_key = api_key

#     # Tool to get the current time
#     def get_current_time(*args, **kwargs):
#         """Returns the current time in H:MM AM/PM format."""
#         import datetime
#         now = datetime.datetime.now()
#         return now.strftime("%I:%M %p")

#     # Tool to search Wikipedia
#     def search_wikipedia(query):
#         """Searches Wikipedia and returns the summary of the first result."""
#         from wikipedia import summary
#         try:
#             return summary(query, sentences=2)
#         except:
#             return "I couldn't find any information on that."

#     # Define the PDF reading tool
#     def pdf_reader_tool(file_path):
#         """Tool to read PDF and return its content."""
#         return PersonalInfoAIAgent.read_pdf(file_path)

#     # Function to extract text from a PDF file
#     def read_pdf(file_path):
#         """Extracts text from a PDF file."""
#         pdf_text = ""
#         try:
#             print(f"Opening PDF file: {file_path}")  # Debug statement
#             with pdfplumber.open(file_path) as pdf:
#                 for page in pdf.pages:
#                     page_text = page.extract_text() or ""
#                     if page_text.strip():
#                         pdf_text += page_text + "\n"
#             print("Personal Info Agent read pdf >> Completed")
#         except Exception as e:
#             return f"Error reading PDF: {e}"

#         if not pdf_text.strip():
#             return "No text found in the PDF."
#         return "Personal Info Agent read pdf >> Completed"

#     # Web scraping tool
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
#     llm = ChatOpenAI(model="gpt-4o")

#     # Create a structured Chat Agent with Conversation Buffer Memory
#     memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

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

#     # FIXME - Adjust this according to new phases
#     # FIXME - Check SRS
#     initial_message = (
#         "You are an AI assistant that can provide helpful answers using available tools.\n"
#         "You can use these tools: Time, Wikipedia, PDF Reader, and Web Scraper."
#     )
#     memory.chat_memory.add_message(SystemMessage(content=initial_message))

#     # FIXME - Make central data for many PDFs
#     pdf_file_path = "/Users/dandev947366/Desktop/test/llama/data/data-to-analyze.pdf"  # Update this path to your PDF file
#     pdf_content = PersonalInfoAIAgent.read_pdf(pdf_file_path)
#     if pdf_content:
#         memory.chat_memory.add_message(AIMessage(content=f"PDF Content:\n{pdf_content}"))

#     # Chat Loop to interact with the user
#     while True:
#         #!SECTION - prompt input
#         #NOTE - prompt needs to be handled separately as personal info agent asks back manager agent for prompt
#         user_input = input("User: ")
#         if user_input.lower() == "exit":
#             break

#         # Add the user's message to the conversation memory
#         memory.chat_memory.add_message(HumanMessage(content=user_input))

#         # Check if user input requests a web scraping action
#         if user_input.lower().startswith("scrape"):
#             # Extract the URL from user input (assuming URL is provided after the command)
#             url = user_input[len("scrape"):].strip()
#             if url:
#                 scrape_result = PersonalInfoAIAgent.scrape_web(url)
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

# # Instantiate and run the agent
# if __name__ == "__main__":
#     agent = PersonalInfoAIAgent(api_key)
#     agent.chat_loop()
