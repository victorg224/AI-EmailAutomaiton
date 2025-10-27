import os
import time
from datetime import datetime, timedelta
import pandas as pd
import smtplib
import openai
import google.genai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from imap_tools import MailBox, AND
from dotenv import load_dotenv
import logging
import json
from models import db, EmailActivity, SystemStats, EmailCampaign, EmailTemplate
import random
import re
from email.mime.application import MIMEApplication
from sqlalchemy import exists

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure OpenAI (keep for now, or remove if fully switching)
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configure Google Generative AI
# genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

class EmailAutomation:
    def __init__(self):
        # Email configuration
        self.email = os.getenv('EMAIL_ADDRESS')
        self.password = os.getenv('EMAIL_PASSWORD')
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
        
        # THIS IS THE CRITICAL DEBUGGING LINE:
        logger.debug(f"Email address used: {self.email}")
        logger.debug(f"Password length: {len(self.password)} if self.password else 'N/A'")
        if self.password:
            logger.debug(f"Password starts with: {self.password[:5]} (DO NOT print the full password. Just check its presence and a few chars)")
        
        # Initialize Google Generative AI Client
        self.genai_client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'), http_options=genai.types.HttpOptions(api_version='v1'))
        
        # Rate limiting settings
        self.emails_per_hour = int(os.getenv('EMAILS_PER_HOUR', 20))  # Default 20 emails per hour
        self.min_delay = int(os.getenv('MIN_DELAY_SECONDS', 60))  # Minimum 1 minute between emails
        self.max_delay = int(os.getenv('MAX_DELAY_SECONDS', 180))  # Maximum 3 minutes between emails
        
        self.stop_flag = False
        
        # Initialize or get system stats
        self.stats = SystemStats.query.first()
        if not self.stats:
            self.stats = SystemStats()
            db.session.add(self.stats)
            db.session.commit()
        
        # Track sent emails for rate limiting
        self.sent_timestamps = []
        
        self.sender_name = os.getenv('SENDER_NAME', 'Your Name')
        self.sender_title = os.getenv('SENDER_TITLE', 'Your Title')
        self.phone_number = os.getenv('SENDER_PHONE', '555-555-5555')
        self.sender_email = os.getenv('SENDER_EMAIL', 'your@email.com')
        self.website_url = os.getenv('SENDER_WEBSITE', 'https://yourcompany.com')
    
    def check_rate_limit(self):
        """Check if we're within rate limits"""
        now = datetime.now()
        # Remove timestamps older than 1 hour
        self.sent_timestamps = [ts for ts in self.sent_timestamps 
                              if ts > now - timedelta(hours=1)]
        
        return len(self.sent_timestamps) < self.emails_per_hour

    def generate_company_email(self, company_name, company_info, target_person="", recipient_email=None, contract_type=None):
        try:
            # Do NOT overwrite company_name here; use the provided value as the recipient
            # Fetch all templates from the database
            templates = EmailTemplate.query.all()
            template_choices = "\n\n".join([
                f"Template {i+1}:\nName: {t.name}\nDescription: {t.description}\nContent:\n{t.template_content}" for i, t in enumerate(templates)
            ])
            ai_template_prompt = f"""
You are an expert B2B outreach email writer. You are writing an email FROM Enspyre Management Services TO {{company_name}} (recipient: {{target_person or 'the recipient'}}).

Given the following contract/context, select the most appropriate template from the list below and adapt it to generate ONLY the main body of the email. Adapt the technical details and bullet points to match the context. Use HTML <ul><li>...</li></ul> for bullet points, and include only 3 to 5 concise, high-impact bullets. Always include a line at the end of the email mentioning the attached capabilities statement (e.g., 'I've attached our capabilities statement for your review.'). Do NOT include any signature, closing, sender name, title, company, logo, website, or placeholders for these. The signature will be added automatically.

Templates:
{template_choices}

Context/Contract Details:
{company_info}

Variables:
- recipient_name: {target_person or 'the recipient'}
- contract_type: {contract_type or '(extract from context)'}
- company_name: {company_name}
- sender_company: Enspyre Management Services

Instructions:
- Write as Enspyre Management Services reaching out to {company_name}.
- Select the best template for the context.
- Adapt the technical bullet points to match the contract/context.
- Use HTML <ul><li>...</li></ul> for bullet points, and include only 3 to 5 concise, high-impact bullets.
- Always include a line at the end of the email mentioning the attached capabilities statement (e.g., 'I've attached our capabilities statement for your review.').
- Fill in all variables.
- Keep the message concise and professional.
- Do NOT include any signature, closing, sender name, title, company, logo, website, or placeholders for these in your output.
- Do NOT include a subject line in your output.
"""
            logger.debug(f"AI template selection and outreach prompt: {ai_template_prompt}")
            email_response = self.genai_client.models.generate_content(
                model='models/gemini-1.5-pro',
                contents=ai_template_prompt
            ).text.strip()
            logger.debug(f"AI outreach email response: {email_response}")
            return email_response
        except Exception as e:
            logger.error(f"Error generating email content: {str(e)}")
            logger.exception("Full traceback for email generation:")
            return None

    def send_email(self, recipient, subject, message, company_name, message_type='campaign'):
        """Send an email with rate limiting"""
        try:
            # Remove any leading subject line (case-insensitive, with or without colon, and any whitespace/newlines)
            message = re.sub(r'(?i)^\s*subject\s*:?\s*.*\n+', '', message, count=1).lstrip()

            if not self.check_rate_limit():
                logger.warning("Rate limit reached, skipping send")
                return False
            
            # Convert the message to HTML and add the signature with the logo
            html_signature = f'<br><br><span style="color:#000000;">Best regards,<br>Victor Gandara<br>AI Automation Intern<br>{self.phone_number}<br><a href="mailto:{self.sender_email}" style="color:#000000;">{self.sender_email}</a></span><br><img src="cid:enspyrelogo" style="max-width:300px;"><br><a href="https://www.enspyremanagementservices.com" style="color:#000000;">www.enspyremanagementservices.com</a>'
            html_message = message.replace('\n', '<br>') + html_signature

            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(html_message, 'html'))

            # Attach enspyre capabilities.pdf to every email
            with open('enspyre capabilities.pdf', 'rb') as f:
                attachment = MIMEApplication(f.read(), _subtype='pdf')
                attachment.add_header('Content-Disposition', 'attachment', filename='enspyre capabilities.pdf')
                msg.attach(attachment)

            # Attach the JPEG logo inline
            from email.mime.image import MIMEImage
            with open('enspyre_logo.jpg', 'rb') as img:
                logo = MIMEImage(img.read())
                logo.add_header('Content-ID', '<enspyrelogo>')
                logo.add_header('Content-Disposition', 'inline', filename='enspyre_logo.jpg')
                msg.attach(logo)
            
            start_time = time.time()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            response_time = time.time() - start_time
            self.sent_timestamps.append(datetime.now())
            
            logger.info(f"Successfully sent email to {recipient} at {company_name}")
            
            # Log activity and update stats
            self.log_activity(
                email_from=self.email,
                email_to=recipient,
                subject=subject,
                response_time=response_time,
                company_name=company_name,
            )
            self.update_stats(responses_sent=1, response_time=response_time)
            
            # Random delay between emails
            delay = random.randint(self.min_delay, self.max_delay)
            logger.info(f"Waiting {delay} seconds before next email...")
            time.sleep(delay)
            
            return True
        except Exception as e:
            logger.error(f"Error sending email to {recipient}: {str(e)}")
            self.log_activity(
                email_from=self.email,
                email_to=recipient,
                subject=subject,
                company_name=company_name,
            )
            return False

    def log_activity(self, email_from, email_to, subject, response_time=None, company_name=None):
        """Log email activity to database"""
        try:
            activity = EmailActivity(
                email_from=email_from,
                email_to=email_to,
                subject=subject,
                response_time=response_time,
                company_name=company_name
            )
            db.session.add(activity)
            db.session.commit()
            logger.debug(f"Logged activity: to {company_name} ({email_to})")
        except Exception as e:
            logger.error(f"Error logging activity: {str(e)}")

    def update_stats(self, emails_processed=0, responses_sent=0, response_time=None):
        """Update system statistics"""
        try:
            self.stats.total_emails_processed += emails_processed
            self.stats.total_responses_sent += responses_sent
            
            if response_time:
                if self.stats.avg_response_time:
                    self.stats.avg_response_time = (self.stats.avg_response_time + response_time) / 2
                else:
                    self.stats.avg_response_time = response_time
            
            self.stats.last_check = datetime.utcnow()
            db.session.commit()
            logger.debug(f"Updated stats: processed={emails_processed}, responses={responses_sent}")
        except Exception as e:
            logger.error(f"Error updating stats: {str(e)}")

    def process_campaigns(self):
        """Process email campaigns with rate limiting"""
        try:
            # Get pending campaigns
            campaigns = EmailCampaign.query.filter_by(status='pending').all()
            logger.info(f"Found {len(campaigns)} pending campaigns")
            
            for campaign in campaigns:
                if self.stop_flag:
                    logger.info("Stopping campaign processing due to stop flag")
                    return
                
                if not self.check_rate_limit():
                    logger.warning("Rate limit reached, pausing campaign processing")
                    return
                
                logger.info(f"Processing campaign for: {campaign.email} at {campaign.company_name}")
                logger.debug(f"Campaign details: template_id={campaign.template_id}, subject={campaign.subject}")
                
                # Verify email configuration
                if not all([self.email, self.password, self.smtp_server]):
                    logger.error("Missing email configuration. Check EMAIL_ADDRESS, EMAIL_PASSWORD, and SMTP_SERVER in .env")
                    campaign.status = 'failed'
                    db.session.commit()
                    continue
                
                # Verify OpenAI configuration (or Google AI configuration)
                if not (openai.api_key or os.getenv('GOOGLE_API_KEY')):
                    logger.error("Missing AI API key. Check OPENAI_API_KEY or GOOGLE_API_KEY in .env")
                    campaign.status = 'failed'
                    db.session.commit()
                    continue
                
                # Generate AI content
                logger.info("Generating email content with AI...")
                email_content = self.generate_company_email(
                    company_name=campaign.company_name,
                    company_info=campaign.context,
                    target_person=campaign.target_person,
                    recipient_email=campaign.email,
                    contract_type=campaign.context  # Let AI infer contract type from context
                )
                
                if email_content:
                    logger.info("Successfully generated email content, attempting to send...")
                    if self.send_email(
                        recipient=campaign.email,
                        subject=campaign.subject,
                        message=email_content,
                        company_name=campaign.company_name,
                        message_type='campaign'
                    ):
                        campaign.status = 'sent'
                        campaign.sent_at = datetime.utcnow()
                        logger.info(f"Successfully sent email to {campaign.email}")
                    else:
                        campaign.status = 'failed'
                        logger.error(f"Failed to send email to {campaign.email}")
                    db.session.commit()
                else:
                    logger.error("Failed to generate email content")
                    campaign.status = 'failed'
                    db.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing campaigns: {str(e)}")
            logger.exception("Full traceback:")

    def run_automation(self, check_interval=300):
        """Run the email automation system with focus on campaigns"""
        logger.info("Starting B2B outreach automation system...")
        
        try:
            while not self.stop_flag:
                # Process campaigns with rate limiting
                logger.info("Processing email campaigns...")
                self.process_campaigns()
                
                # Check stop flag every second for more responsive stopping
                for _ in range(min(check_interval, 300)):  # Max 5 minutes between checks
                    if self.stop_flag:
                        logger.info("Stop flag detected, stopping automation...")
                        return
                    time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in automation loop: {str(e)}")
        finally:
            logger.info("Email automation system stopped")
            self.stop_flag = True

if __name__ == "__main__":
    automation = EmailAutomation()
    # You can provide a CSV file for outgoing emails
    automation.run_automation(csv_file="emails.csv") 