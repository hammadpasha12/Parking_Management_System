from fastapi import FastAPI
from app.views.parking_view import router
from app.database import init_db
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  
    yield

app: FastAPI = FastAPI(lifespan=lifespan)
app.include_router(router)
