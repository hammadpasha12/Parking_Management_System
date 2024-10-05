import os
from sqlmodel import create_engine, SQLModel,Session
from dotenv import load_dotenv
from fastapi import Depends

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_db():
    with Session(engine) as session:
        yield session