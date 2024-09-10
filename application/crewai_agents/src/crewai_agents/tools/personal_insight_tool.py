from crewai_tools import BaseTool
import requests
import json

class PersonalInsightResearchAgent(BaseTool):
    name: str = "Personal Insight Research Agent"
    description: str = (
        "Analyzes user-submitted personal insights and compares them with relevant mental health research "
        "to generate a report on potential mental health risks."
    )

    def _run(self, user_id: str) -> dict:
        """
        Main method to process personal insights submitted by the user and return an analysis report.
        
        Args:
            user_id (str): Unique identifier for the user to fetch their submitted answers.

        Returns:
            dict: Analysis report with potential risks and insights.
        """
        try:
            # Fetching user's submitted personal insight answers
            personal_insight_data = self.fetch_user_insight_data(user_id)

            # Fetching relevant research data
            research_data = self.fetch_mental_health_research(personal_insight_data)

            # Analyzing the user's insights
            analysis = self.analyze_personal_insights(personal_insight_data, research_data)

            # Creating a report based on the analysis
            report = self.generate_report(analysis)

            return report

        except Exception as e:
            self.log(f"Error in processing personal insights: {str(e)}")
            return {"error": "Failed to process personal insights"}

    def fetch_user_insight_data(self, user_id: str) -> dict:
        """
        Fetch personal insight answers submitted by the user from the API.
        
        Args:
            user_id (str): Unique identifier for the user.

        Returns:
            dict: User's personal insight data.
        """
        try:
            # Example: API call to fetch the user's personal insight data
            api_url = f"https://api.example.com/user_insights/{user_id}"
            response = requests.get(api_url)

            if response.status_code == 200:
                return response.json()
            else:
                self.log(f"Failed to fetch personal insight data: {response.status_code}")
                return {}

        except Exception as e:
            self.log(f"Error fetching personal insight data: {str(e)}")
            return {}

    def fetch_mental_health_research(self, personal_insight_data: dict) -> dict:
        """
        Fetch relevant mental health research based on the user's submitted insights.
        
        Args:
            personal_insight_data (dict): User's submitted personal insights.

        Returns:
            dict: Mental health research data related to the user's insights.
        """
        try:
            # Example: Simulating API call for relevant research based on user's insights
            api_url = "https://api.example.com/mental_health_research"
            response = requests.get(api_url, params=personal_insight_data)

            if response.status_code == 200:
                return response.json()
            else:
                self.log(f"Failed to fetch mental health research: {response.status_code}")
                return {}

        except Exception as e:
            self.log(f"Error fetching mental health research: {str(e)}")
            return {}

    def analyze_personal_insights(self, personal_insight_data: dict, research_data: dict) -> dict:
        """
        Analyze the user's personal insight data against mental health research.
        
        Args:
            personal_insight_data (dict): User's submitted personal insights.
            research_data (dict): Mental health research data.

        Returns:
            dict: Analysis of potential mental health risks and insights.
        """
        analysis = {}

        # Example: Compare user's reported stress levels with research data
        stress_level = personal_insight_data.get('stress_level')
        if stress_level:
            analysis['stress_risk'] = research_data.get('stress_research', {}).get(str(stress_level), "No data available")

        # Example: Compare user's emotional state with mental health trends
        emotional_state = personal_insight_data.get('emotional_state')
        if emotional_state:
            analysis['emotional_risk'] = research_data.get('emotional_research', {}).get(emotional_state, "No data available")

        # Add more comparisons based on personal insights and research data

        return analysis

    def generate_report(self, analysis: dict) -> dict:
        """
        Generate a detailed report based on the analysis of the user's personal insights.
        
        Args:
            analysis (dict): The analysis output containing risk factors and insights.

        Returns:
            dict: A structured report with analysis results.
        """
        report = {
            "summary": "Personal Insight Research Agent Report",
            "analysis": analysis,
            "recommendations": "Consider consulting a healthcare professional if any risks are identified."
        }
        return report
