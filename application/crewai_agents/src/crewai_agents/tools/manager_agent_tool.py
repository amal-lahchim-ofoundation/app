import httpx
from crewai_tools import BaseTool, Agent, Task

class ManagerAgent(Agent):
    async def run(self, user_id: str):
        try:
            # Fetch data from database via API
            data = await self.fetch_data_from_api(user_id)
            
            if not data:
                raise ValueError("No data returned from the database.")

            # Dynamically activate and coordinate agents based on the input data
            personal_info_task = self.submit_task('analyze_personal_info', data['personal_info'])
            personal_insight_task = self.submit_task('analyze_personal_insight', data['personal_insight'])
            questionnaire_task = self.submit_task('analyze_questionnaire', data['questionnaire_results'])

            # Wait for all tasks to complete and gather their results
            personal_info_result = personal_info_task.get_result()
            personal_insight_result = personal_insight_task.get_result()
            questionnaire_result = questionnaire_task.get_result()

            # Validate results before proceeding
            if not self.validate_results(personal_info_result, personal_insight_result, questionnaire_result):
                raise ValueError("Validation failed for research agent results.")

            # Synthesize results into a final report
            final_report = self.generate_final_report(
                personal_info_result, personal_insight_result, questionnaire_result
            )
            self.log("Final report generated successfully.")
            
            return final_report
        
        except Exception as e:
            self.log(f"Error in ManagerAgent: {str(e)}")
            raise

    async def fetch_data_from_api(self, user_id: str):
        """Fetch user data from the API (e.g., Firestore API)."""
        try:
            # Example API endpoint (replace with your actual database endpoint)
            api_url = f"https://your-api-url.com/users/{user_id}/data"
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url)
                if response.status_code == 200:
                    return response.json()  # Assuming the response is JSON
                else:
                    self.log(f"Failed to fetch data: {response.status_code}")
                    return None
        except Exception as e:
            self.log(f"API request failed: {str(e)}")
            return None

    def validate_results(self, *results):
        # Add validation logic here (e.g., checking if the results are complete or consistent)
        for result in results:
            if not result or 'error' in result:
                return False
        return True

    def log(self, message):
        # Basic logging function
        print(f"[ManagerAgent] {message}")

    def generate_final_report(self, personal_info, personal_insight, questionnaire):
        # Example of a detailed final report generation
        return {
            "personal_info_summary": personal_info.get('summary', 'No info'),
            "personal_insight_summary": personal_insight.get('summary', 'No insights'),
            "questionnaire_summary": questionnaire.get('summary', 'No questionnaire data'),
            "recommendations": self.generate_recommendations(personal_info, personal_insight, questionnaire)
        }

    def generate_recommendations(self, personal_info, personal_insight, questionnaire):
        # A placeholder for recommendation logic based on analysis results
        recommendations = []
        if "high_risk" in questionnaire:
            recommendations.append("Further assessment recommended based on questionnaire.")
        # Additional recommendation logic here
        return recommendations
