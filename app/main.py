from fastapi import FastAPI
from app.views.parking_view import router
from app.database import init_db
from contextlib import asynccontextmanager
from app.controllers.parking_controller import initialize_parking_slots

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  
    initialize_parking_slots() 
    yield

app: FastAPI = FastAPI(lifespan=lifespan)
app.include_router(router)
