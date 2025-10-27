from app import app, db
import os

def reset_database():
    # Make sure we're in app context
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
        print("Database has been reset successfully!")

if __name__ == "__main__":
    # Delete the database file if it exists
    if os.path.exists("email_automation.db"):
        os.remove("email_automation.db")
        print("Removed old database file")
    
    reset_database() 