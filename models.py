from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime)



class EmailTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    template_content = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Template variables guide
    variables_guide = db.Column(db.Text, default="""
    Available variables:
    {company_name} - Name of the company
    {industry} - Company's industry
    {person_name} - Contact person's name (if available)
    {custom_research} - AI-generated company-specific research
    {value_prop} - AI-generated value proposition
    {pain_point} - AI-identified potential pain point
    """)

class EmailCampaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    company_name = db.Column(db.String(200))
    industry = db.Column(db.String(100))
    target_person = db.Column(db.String(100))
    context = db.Column(db.Text)
    template_id = db.Column(db.Integer, db.ForeignKey('email_template.id'))
    status = db.Column(db.String(20), default='pending')
    sent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    generated_content = db.Column(db.Text)  # AI-generated email body

class EmailActivity(db.Model):
    __tablename__ = 'emailAuto'

    id = db.Column(db.Integer, primary_key=True)
    email_from = db.Column(db.String(120), nullable=False)
    email_to = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200))
    context = db.Column(db.Text)
    company_name = db.Column(db.String(200))
    response_time = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SystemStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_emails_processed = db.Column(db.Integer, default=0)
    total_responses_sent = db.Column(db.Integer, default=0)
    avg_response_time = db.Column(db.Float)
    status = db.Column(db.String(20), default='stopped')
    last_check = db.Column(db.DateTime)

class ScenarioTraining(db.Model):
    """Store scenario training data and outcomes"""
    id = db.Column(db.Integer, primary_key=True)
    scenario_type = db.Column(db.String(50), nullable=False)
    input_text = db.Column(db.Text, nullable=False)
    analysis = db.Column(db.JSON)
    response_strategy = db.Column(db.JSON)
    success_metrics = db.Column(db.JSON)
    learning_insights = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ScenarioTraining {self.scenario_type}>' 