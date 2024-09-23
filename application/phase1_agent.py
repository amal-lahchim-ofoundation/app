import requests

class Phase1Agent:
    def __init__(self, api_key, search_engine_id):
        self.api_key = api_key
        self.search_engine_id = search_engine_id

    def search_online(self, query):
        """Searches online using Google Custom Search API."""
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

    def analyze_user_data(self, user_responses):
        """Analyzes user responses and generates insights."""
        analysis = {}
        
        # Analyze scores and comments
        for question, response in user_responses.items():
            if isinstance(response, dict):
                score = response.get('score')
                comment = response.get('comments')
                analysis[question] = {
                    "score": score,
                    "comment": comment,
                    "interpretation": self.interpret_score(score)
                }
            else:
                analysis[question] = response
        
        return analysis

    def interpret_score(self, score):
        """Interprets the score based on predefined thresholds."""
        score = int(score)
        if score >= 80:
            return "Very Positive"
        elif score >= 60:
            return "Positive"
        elif score >= 40:
            return "Neutral"
        elif score >= 20:
            return "Negative"
        else:
            return "Very Negative"

    def generate_report(self, analysis):
        """Generates a report based on the analysis."""
        report = "### Analysis Report\n\n"
        for question, details in analysis.items():
            if isinstance(details, dict):
                report += f"**{question}**:\n"
                report += f"  - Score: {details['score']}\n"
                report += f"  - Comment: {details['comment']}\n"
                report += f"  - Interpretation: {details['interpretation']}\n\n"
            else:
                report += f"**{question}**: {details}\n\n"

        return report

    def run(self):
        user_responses = self.collect_user_data()
        analysis = self.analyze_user_data(user_responses)
        
        # Perform online searches based on user responses
        search_results = []
        for question in user_responses.keys():
            if isinstance(user_responses[question], dict):
                search_results.append(self.search_online(user_responses[question]['comments']))
        
        report = self.generate_report(analysis)
        
        # Append search results to the report
        report += "\n### Online Search Results:\n"
        for result in search_results:
            report += f"{result}\n"

        print(report)

# Example usage
# agent = Phase1Agent(api_key='your_google_api_key', search_engine_id='your_search_engine_id')
# agent.run()
