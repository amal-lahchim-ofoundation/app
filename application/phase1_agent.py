import pycountry
import requests
from bs4 import BeautifulSoup
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain.prompts import SystemMessage, AIMessage, HumanMessage

class Phase1Agent:
    def __init__(self, api_key, search_engine_id):
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.llm = ChatOpenAI(model="gpt-4")
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.agent, self.agent_executor = self.create_agent()

    def create_agent(self):
        # Define tools
        tools = [
            Tool(
                name="Online Search",
                func=self.search_online,
                description="Searches the web using Google Custom Search API.",
            ),
        ]
        
        # Load the correct JSON Chat Prompt from the hub
        prompt = hub.pull("hwchase17/structured-chat-agent")
        
        # Create the structured chat agent
        agent = create_structured_chat_agent(llm=self.llm, tools=tools, prompt=prompt)
        
        # Create an AgentExecutor with the agent and tools
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=tools,
            verbose=True,
            memory=self.memory,
            handle_parsing_errors=True,
        )
        
        return agent, agent_executor

    def search_online(self, query):
        """Searches online using Google Custom Search API and returns results."""
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': query
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        search_results = response.json()

        search_data = []
        for item in search_results.get('items', []):
            title = item.get('title')
            snippet = item.get('snippet')
            link = item.get('link')
            search_data.append(f"{title}: {snippet} ({link})")

        return "\n".join(search_data)

    def collect_user_data(self):
        """Collects user responses for Phase 1."""
        questions = [
            {"question": "What has led you to seek help at this particular moment?", "type": "text"},
            {"question": "How would you summarize your biggest concerns or complaints in one or two sentences?", "type": "text"},
            {"question": "What changes have you noticed in your life since these issues began?", "type": "text"},
            {"question": "What thoughts and feelings frequently come up in relation to these issues?", "type": "text"},
            {"question": "What do you believe is the cause of these problems?", "type": "text"},
            {"question": "Are there specific situations, people, or places that make your symptoms worse or better?", "type": "text"},
            {"question": "How have aspects of your daily life, such as work, relationships, or sleep, been affected by these issues?", "type": "text"},
            {"question": "What have you tried so far to cope with these issues, and what were the results?", "type": "text"},
            {"question": "Have you sought help for these issues before? If so, what did you take away from that experience?", "type": "text"},
            {"question": "If you look back a year from now on this treatment, what would you like to have changed?", "type": "text"},
            {"question": "What support or changes would you need to achieve these goals?", "type": "text"},
            {"question": "Is there anything else you think I should know or understand to help you best?", "type": "text"},
            {"question": "What is your age?", "type": "number"},
            {"question": "What is your gender?", "type": "select", "options": ["Male", "Female", "Other"]},
            {"question": "What is your nationality?", "type": "select", "options": [country.name for country in pycountry.countries]},
            {"question": "What is your current country of residence?", "type": "select", "options": [country.name for country in pycountry.countries]},
            {"question": "What cultural or ethnic background do you identify with? How does this influence your daily life?", "type": "text"},
            {"question": "What is your marital status?", "type": "select", "options": ["Single", "Married", "Divorced", "Other"]},
            {"question": "What is your education level?", "type": "select", "options": ["High School", "Bachelor's", "Master's", "Other"]},
            {"question": "What is your employment status?", "type": "select", "options": ["Employed", "Unemployed", "Retired", "Other"]},
            {"question": "What is your living situation?", "type": "select", "options": ["Alone", "With Family", "With Friends", "Other"]}
        ]

        user_responses = {}
        for q in questions:
            response = input(f"{q['question']}: ")
            user_responses[q['question']] = response
        
        return user_responses

    def analyze_and_report(self, user_responses):
        """Analyzes user responses with collected data and generates a report."""
        # Search online for mental health information based on user responses
        search_queries = [response for response in user_responses.values() if response]
        search_results = [self.search_online(query) for query in search_queries]
        
        # Combine results into a comprehensive report
        report = "### Phase 1 Report\n\n"
        report += "#### User Responses:\n"
        for question, response in user_responses.items():
            report += f"**{question}**: {response}\n"
        
        report += "\n#### Online Search Results:\n"
        for result in search_results:
            report += f"{result}\n"
        
        return report

    def run(self):
        user_responses = self.collect_user_data()
        report = self.analyze_and_report(user_responses)
        print(report)

# Example usage
# agent = Phase1Agent(api_key='your_google_api_key', search_engine_id='your_search_engine_id')
# agent.run()
