from fastapi import FastAPI
from app.views.parking_view import router
from app.database import init_db
import  logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def lifespan(app: FastAPI):
    try:
        init_db()  
        logger.info("Database Initialized Successfully")
    except Exception as e:
        logger.error(f"Failed to initialized the database {e}")
        raise
    yield

        

app: FastAPI = FastAPI(lifespan=lifespan)
app.include_router(router)
