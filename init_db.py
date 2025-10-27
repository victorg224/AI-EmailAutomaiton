from app import app, db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    with app.app_context():
        logger.info("Creating database tables...")
        db.create_all()
        logger.info("Database tables created successfully!")

if __name__ == "__main__":
    init_db() 