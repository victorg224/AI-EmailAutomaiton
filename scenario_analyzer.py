import openai
import json
import logging
from datetime import datetime
from models import db, EmailCampaign

logger = logging.getLogger(__name__)

class ScenarioAnalyzer:
    def __init__(self):
        self.scenarios = {
            'expiring_contract': {
                'indicators': ['contract expiring', 'current vendor', 'incumbent', 'recompete', 'renewal'],
                'required_info': ['expiration_date', 'contract_value', 'incumbent_name', 'performance_location']
            },
            'new_solicitation': {
                'indicators': ['new contract', 'rfp', 'rfq', 'sources sought', 'new requirement'],
                'required_info': ['solicitation_number', 'response_deadline', 'naics_code', 'contract_value']
            },
            'partnership_opportunity': {
                'indicators': ['teaming', 'partnership', 'joint venture', 'collaboration', 'subcontracting'],
                'required_info': ['partner_capabilities', 'target_contracts', 'complementary_skills']
            },
            'capability_statement': {
                'indicators': ['capabilities', 'qualification', 'experience', 'past performance'],
                'required_info': ['relevant_experience', 'certifications', 'differentiators']
            }
        }
        
    def analyze_scenario(self, input_text, additional_context=None):
        """
        Analyze the input text to determine the scenario type and extract key information
        """
        try:
            analysis_prompt = f"""
            Analyze this business opportunity and categorize it:

            Input Text:
            {input_text}

            Additional Context (if any):
            {additional_context or 'None provided'}

            Please analyze and provide:
            1. Scenario Type (expiring_contract, new_solicitation, partnership_opportunity, or capability_statement)
            2. Key Information Extracted
            3. Recommended Approach
            4. Critical Deadlines
            5. Required Follow-up Information

            Format the response as a JSON object with these fields.
            """

            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in government contracting and business development, skilled at analyzing business opportunities."},
                    {"role": "user", "content": analysis_prompt}
                ]
            )

            # Parse the response
            analysis = json.loads(response.choices[0].message.content)
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing scenario: {str(e)}")
            return None

    def generate_response_strategy(self, scenario_analysis):
        """
        Generate a strategic response based on the scenario analysis
        """
        try:
            strategy_prompt = f"""
            Create a strategic response plan based on this scenario analysis:

            Analysis: {json.dumps(scenario_analysis, indent=2)}

            Provide a response strategy that includes:
            1. Key points to address
            2. Specific value propositions
            3. Past performance examples to highlight
            4. Call to action
            5. Risk mitigation approaches

            Format the response as a JSON object with these fields.
            """

            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a senior business development strategist specializing in government contracts."},
                    {"role": "user", "content": strategy_prompt}
                ]
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Error generating response strategy: {str(e)}")
            return None

    def learn_from_feedback(self, scenario_type, input_text, success_metrics):
        """
        Learn from the success or failure of previous responses
        """
        try:
            learning_prompt = f"""
            Analyze this scenario outcome and provide learning insights:

            Scenario Type: {scenario_type}
            Original Input: {input_text}
            Success Metrics: {json.dumps(success_metrics, indent=2)}

            Provide:
            1. Successful elements to retain
            2. Areas for improvement
            3. New patterns identified
            4. Recommended adjustments

            Format the response as a JSON object with these fields.
            """

            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an AI learning specialist focused on improving business development strategies."},
                    {"role": "user", "content": learning_prompt}
                ]
            )

            insights = json.loads(response.choices[0].message.content)
            
            # Update scenario indicators based on learning
            if scenario_type in self.scenarios:
                self.scenarios[scenario_type]['indicators'].extend(insights.get('new_patterns', []))
            
            return insights

        except Exception as e:
            logger.error(f"Error learning from feedback: {str(e)}")
            return None

    def save_training_data(self, scenario_data):
        """
        Save training data for future reference and learning
        """
        try:
            # Create a new training data entry
            training_entry = {
                'scenario_type': scenario_data['type'],
                'input_text': scenario_data['input'],
                'analysis': scenario_data['analysis'],
                'response_strategy': scenario_data['strategy'],
                'success_metrics': scenario_data['metrics'],
                'learning_insights': scenario_data['insights'],
                'timestamp': datetime.utcnow()
            }
            
            # Save to database (implement your database logic here)
            return True

        except Exception as e:
            logger.error(f"Error saving training data: {str(e)}")
            return False 