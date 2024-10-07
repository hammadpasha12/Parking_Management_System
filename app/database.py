import os
from sqlmodel import create_engine, SQLModel,Session
from dotenv import load_dotenv
import  logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Table created succcessfully")
    except Exception as e:
        logger.error(f"Error in initalizing the database {e}") 
        raise   

def get_db():
    try:
        with Session(engine) as session:
            yield session
    except Exception as  e:
        logger.error(f"Error during databse session {e}") 
        raise       