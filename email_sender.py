import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def read_csv(file_path):
    """
    Read the CSV file containing email information
    Expected columns: email, subject, message
    """
    try:
        df = pd.read_csv(file_path)
        required_columns = ['email', 'subject', 'message']
        
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"CSV must contain these columns: {required_columns}")
        
        return df
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return None

def send_email(recipient, subject, message):
    """
    Send an email to a single recipient
    """
    # Get email configuration from environment variables
    sender_email = os.getenv('EMAIL_ADDRESS')
    sender_password = os.getenv('EMAIL_PASSWORD')
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    
    if not all([sender_email, sender_password, smtp_server]):
        raise ValueError("Missing email configuration in .env file")
    
    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject
    
    # Add body to email
    msg.attach(MIMEText(message, 'plain'))
    # Attach capabilities.html
    with open('capabilities.html', 'rb') as f:
        attachment = MIMEApplication(f.read(), _subtype='html')
        attachment.add_header('Content-Disposition', 'attachment', filename='capabilities.html')
        msg.attach(attachment)
    
    try:
        # Create SMTP session
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email to {recipient}: {str(e)}")
        return False

def process_emails(csv_file):
    """
    Process all emails from the CSV file
    """
    df = read_csv(csv_file)
    if df is None:
        return
    
    successful = 0
    failed = 0
    
    for index, row in df.iterrows():
        try:
            if send_email(row['email'], row['subject'], row['message']):
                successful += 1
            else:
                failed += 1
        except Exception as e:
            print(f"Error processing row {index}: {str(e)}")
            failed += 1
    
    print(f"\nEmail sending complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

def send_test_email():
    """
    Send a test email to verify configuration
    """
    # Get email configuration from environment variables
    sender_email = os.getenv('EMAIL_ADDRESS')
    sender_password = os.getenv('EMAIL_PASSWORD')
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    
    # Send to self for testing
    recipient = sender_email
    subject = "Test Email - Configuration Check"
    message = "This is a test email to verify the email configuration is working correctly."
    
    try:
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        
        # Create SMTP session and send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            print("Attempting to login...")
            server.login(sender_email, sender_password)
            print("Login successful!")
            server.send_message(msg)
            print("Test email sent successfully!")
        return True
    except Exception as e:
        print(f"Error sending test email: {str(e)}")
        return False

if __name__ == "__main__":
    send_test_email() 