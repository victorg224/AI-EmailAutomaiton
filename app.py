from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from models import db, EmailCampaign, EmailActivity, SystemStats, EmailTemplate, ScenarioTraining
from automated_email_system import EmailAutomation
from scenario_analyzer import ScenarioAnalyzer
from config import Config
import threading
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import sys
import argparse
import pandas as pd
import tempfile
from werkzeug.utils import secure_filename


# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['FLASK_SECRET_KEY']

# Enable Flask debug mode
app.debug = True

db.init_app(app)

# Global variable to store the automation thread
automation_thread = None
email_automation = None

def run_automation():
    global email_automation
    with app.app_context():
        email_automation = EmailAutomation()
        email_automation.run_automation(check_interval=300)

@app.route('/')
def index():
    logger.debug("Accessing index route")
    try:
        stats = SystemStats.query.first()
        logger.debug(f"Retrieved stats: {stats}")
        recent_activities = EmailActivity.query.order_by(EmailActivity.created_at.desc()).limit(10).all()
        logger.debug(f"Retrieved {len(recent_activities)} recent activities")
        campaigns = EmailCampaign.query.order_by(EmailCampaign.created_at.desc()).limit(5).all()
        logger.debug(f"Retrieved {len(campaigns)} campaigns")
        return render_template('index.html', stats=stats, activities=recent_activities, campaigns=campaigns)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return f"An error occurred: {str(e)}", 500

@app.route('/templates')
def templates():
    """View all email templates"""
    try:
        templates = EmailTemplate.query.order_by(EmailTemplate.created_at.desc()).all()
        return render_template('templates.html', templates=templates)
    except Exception as e:
        logger.error(f"Error in templates route: {str(e)}")
        return f"An error occurred: {str(e)}", 500

@app.route('/add_template', methods=['GET', 'POST'])
def add_template():
    """Add a new email template"""
    if request.method == 'POST':
        try:
            template = EmailTemplate(
                name=request.form['name'],
                description=request.form['description'],
                template_content=request.form['template_content']
            )
            db.session.add(template)
            db.session.commit()
            return redirect(url_for('templates'))
        except Exception as e:
            logger.error(f"Error adding template: {str(e)}")
            return f"An error occurred: {str(e)}", 500
    return render_template('add_template.html')

@app.route('/edit_template/<int:template_id>', methods=['GET', 'POST'])
def edit_template(template_id):
    """Edit an existing email template"""
    template = EmailTemplate.query.get_or_404(template_id)
    
    if request.method == 'POST':
        try:
            template.name = request.form['name']
            template.description = request.form['description']
            template.template_content = request.form['template_content']
            template.updated_at = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('templates'))
        except Exception as e:
            logger.error(f"Error updating template: {str(e)}")
            return f"An error occurred: {str(e)}", 500
    
    return render_template('add_template.html', template=template)

@app.route('/delete_template/<int:template_id>')
def delete_template(template_id):
    """Delete an email template"""
    try:
        template = EmailTemplate.query.get_or_404(template_id)
        db.session.delete(template)
        db.session.commit()
        return redirect(url_for('templates'))
    except Exception as e:
        logger.error(f"Error deleting template: {str(e)}")
        return f"An error occurred: {str(e)}", 500

@app.route('/campaigns')
def campaigns():
    logger.debug("Accessing campaigns route")
    try:
        campaigns = EmailCampaign.query.order_by(EmailCampaign.created_at.desc()).all()
        templates = EmailTemplate.query.all()
        return render_template('campaigns.html', campaigns=campaigns, templates=templates)
    except Exception as e:
        logger.error(f"Error in campaigns route: {str(e)}")
        return f"An error occurred: {str(e)}", 500

@app.route('/add_campaign', methods=['GET', 'POST'])
def add_campaign():
    logger.debug(f"Accessing add_campaign route with method {request.method}")
    if request.method == 'POST':
        try:
            logger.debug(f"Form data received: {request.form}")
            company_name = request.form.get('company_name', '')
            email = request.form.get('email', '')
            target_person = request.form.get('target_person', '')
            context = request.form.get('context', '')
            email_automation = EmailAutomation()
            ai_subject = email_automation.genai_client.models.generate_content(
                model='models/gemini-1.5-pro',
                contents=f"Generate a concise, professional subject line for a B2B outreach email based on this context. The subject line should be only 2 or 3 words, no more: {context}"
            ).text.strip()
            ai_subject = ai_subject[:200]  # Truncate to 200 characters
            # Use AI to generate the full email body
            ai_body = email_automation.generate_company_email(
                company_name=company_name,
                company_info=context,
                target_person=target_person,
                recipient_email=email
            )
            campaign = EmailCampaign(
                company_name=company_name,
                email=email,
                subject=ai_subject,
                target_person=target_person,
                context=context,
                generated_content=ai_body
            )
            logger.debug(f"Created campaign object: {campaign}")
            db.session.add(campaign)
            db.session.commit()
            logger.info(f"Successfully added campaign for {campaign.company_name}")
            return redirect(url_for('campaigns'))
        except Exception as e:
            logger.error(f"Error adding campaign: {str(e)}")
            db.session.rollback()
            return f"An error occurred: {str(e)}", 500
    return render_template('add_campaign.html')

@app.route('/delete_campaign/<int:campaign_id>', methods=['POST'])
def delete_campaign(campaign_id):
    """Delete an email campaign"""
    try:
        campaign = EmailCampaign.query.get_or_404(campaign_id)
        db.session.delete(campaign)
        db.session.commit()
        flash('Campaign deleted successfully!', 'success')
        return redirect(url_for('campaigns'))
    except Exception as e:
        logger.error(f"Error deleting campaign: {str(e)}")
        flash(f'Error deleting campaign: {str(e)}', 'error')
        return f"An error occurred: {str(e)}", 500

@app.route('/activities')
def activities():
    logger.debug("Accessing activities route")
    try:
        activities = EmailActivity.query.order_by(EmailActivity.created_at.desc()).all()
        return render_template('activities.html', activities=activities)
    except Exception as e:
        logger.error(f"Error in activities route: {str(e)}")
        return f"An error occurred: {str(e)}", 500

@app.route('/start')
def start_automation():
    logger.debug("Starting automation")
    global automation_thread, email_automation
    
    # First make sure any existing automation is stopped
    if automation_thread and automation_thread.is_alive():
        logger.warning("Existing automation thread is still running, stopping it first")
        if email_automation:
            email_automation.stop_flag = True
        automation_thread.join(timeout=5)
    
    # Create new automation instance and thread
    email_automation = EmailAutomation()
    automation_thread = threading.Thread(target=run_automation)
    automation_thread.daemon = True
    automation_thread.start()
    
    stats = SystemStats.query.first()
    if not stats:
        stats = SystemStats()
        db.session.add(stats)
    stats.status = 'running'
    stats.last_check = datetime.utcnow()
    db.session.commit()
    
    logger.info("Automation system started successfully")
    return redirect(url_for('index'))

@app.route('/stop')
def stop_automation():
    logger.debug("Stopping automation")
    global automation_thread, email_automation
    
    try:
        if email_automation:
            logger.info("Setting stop flag...")
            email_automation.stop_flag = True
        
        if automation_thread and automation_thread.is_alive():
            logger.info("Waiting for automation thread to finish...")
            automation_thread.join(timeout=10)
            
            if automation_thread.is_alive():
                logger.warning("Thread did not stop gracefully, forcing stop...")
                # Reset the thread
                automation_thread = None
        
        # Reset the automation
        email_automation = None
        
        # Update database status
        with app.app_context():
            stats = SystemStats.query.first()
            if stats:
                stats.status = 'stopped'
                stats.last_check = datetime.utcnow()
                db.session.commit()
                logger.info("Updated system status to stopped")
    except Exception as e:
        logger.error(f"Error stopping automation: {str(e)}")
    
    return redirect(url_for('index'))

@app.route('/api/stats')
def get_stats():
    logger.debug("Accessing API stats route")
    stats = SystemStats.query.first()
    if stats:
        return jsonify({
            'total_emails_processed': stats.total_emails_processed,
            'total_responses_sent': stats.total_responses_sent,
            'avg_response_time': stats.avg_response_time,
            'status': stats.status,
            'last_check': stats.last_check.isoformat() if stats.last_check else None
        })
    return jsonify({})

@app.route('/train', methods=['GET', 'POST'])
def train_scenario():
    """Train the AI with new scenarios"""
    if request.method == 'POST':
        try:
            # Get scenario data from form
            scenario_data = {
                'input_text': request.form['scenario_text'],
                'scenario_type': request.form.get('scenario_type'),
                'additional_context': request.form.get('additional_context')
            }
            
            # Initialize scenario analyzer
            analyzer = ScenarioAnalyzer()
            
            # Analyze scenario
            analysis = analyzer.analyze_scenario(
                scenario_data['input_text'],
                scenario_data['additional_context']
            )
            
            if analysis:
                # Generate response strategy
                strategy = analyzer.generate_response_strategy(analysis)
                
                # Save training data
                training = ScenarioTraining(
                    scenario_type=analysis['scenario_type'],
                    input_text=scenario_data['input_text'],
                    analysis=analysis,
                    response_strategy=strategy,
                    success_metrics={},  # Will be updated after email campaign
                    learning_insights={}  # Will be updated with feedback
                )
                
                db.session.add(training)
                db.session.commit()
                
                flash('Scenario analyzed and saved successfully!', 'success')
                return redirect(url_for('view_scenarios'))
            else:
                flash('Error analyzing scenario', 'error')
                
        except Exception as e:
            logger.error(f"Error in scenario training: {str(e)}")
            flash('Error processing scenario', 'error')
            
    return render_template('train_scenario.html')

@app.route('/scenarios')
def view_scenarios():
    """View all training scenarios"""
    scenarios = ScenarioTraining.query.order_by(ScenarioTraining.created_at.desc()).all()
    return render_template('scenarios.html', scenarios=scenarios)

@app.route('/analyze_scenario', methods=['POST'])
def analyze_new_scenario():
    """Analyze a new scenario and return recommended approach"""
    try:
        data = request.get_json()
        analyzer = ScenarioAnalyzer()
        
        analysis = analyzer.analyze_scenario(
            data['input_text'],
            data.get('additional_context')
        )
        
        if analysis:
            strategy = analyzer.generate_response_strategy(analysis)
            return jsonify({
                'success': True,
                'analysis': analysis,
                'strategy': strategy
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Could not analyze scenario'
            }), 400
            
    except Exception as e:
        logger.error(f"Error analyzing scenario: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/upload_cab', methods=['GET', 'POST'])
def upload_cab():
    ALLOWED_EXTENSIONS = {'.cab', '.csv', '.xlsx', '.xls'}
    if request.method == 'POST':
        file = request.files.get('cabfile')
        if file:
            filename = secure_filename(file.filename)
            ext = os.path.splitext(filename)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                flash('Only .cab, .csv, .xlsx, and .xls files are allowed.', 'danger')
                return redirect(url_for('upload_cab'))
            # Save to a temp file for pandas
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name
            try:
                # Try reading as Excel or CSV
                if ext in ['.xlsx', '.xls']:
                    df = pd.read_excel(tmp_path)
                elif ext == '.csv' or ext == '.cab':
                    df = pd.read_csv(tmp_path)
                else:
                    flash('Unsupported file type.', 'danger')
                    return redirect(url_for('upload_cab'))
                required_cols = {'company name', 'email', 'name'}
                df.columns = [c.strip().lower() for c in df.columns]
                if not required_cols.issubset(set(df.columns)):
                    flash(f'File must contain columns: {required_cols}', 'danger')
                    return redirect(url_for('upload_cab'))
                email_automation = EmailAutomation()
                created = 0
                for _, row in df.iterrows():
                    company_name = row.get('company name', '')
                    email = row.get('email', '')
                    target_person = row.get('name', '')
                    context = row.get('context', '') if 'context' in row else ''
                    # Generate subject with AI
                    ai_subject = email_automation.genai_client.models.generate_content(
                        model='models/gemini-1.5-pro',
                        contents=f"Generate a concise, professional subject line for a B2B outreach email based on this context. The subject line should be only 2 or 3 words, no more: {context}"
                    ).text.strip()[:200]
                    # Generate body with AI
                    ai_body = email_automation.generate_company_email(
                        company_name=company_name,
                        company_info=context,
                        target_person=target_person,
                        recipient_email=email
                    )
                    campaign = EmailCampaign(
                        company_name=company_name,
                        email=email,
                        subject=ai_subject,
                        target_person=target_person,
                        context=context,
                        generated_content=ai_body
                    )
                    db.session.add(campaign)
                    created += 1
                db.session.commit()
                flash(f'Successfully created {created} campaign(s) from CAB file!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error processing file: {str(e)}', 'danger')
            finally:
                os.remove(tmp_path)
            return redirect(url_for('upload_cab'))
        else:
            flash('No file uploaded.', 'danger')
    return render_template('upload_cab.html')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=None, help='Port to run the Flask app on')
    args = parser.parse_args()
    port = args.port or int(os.getenv('PORT', 8080))
    with app.app_context():
        db.create_all()
        logger.info("Creating database tables")
    logger.info("Starting Flask application")
    app.run(host='0.0.0.0', port=port, debug=True) 