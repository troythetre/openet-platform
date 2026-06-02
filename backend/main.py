import os

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from database import init_db
from fastapi import FastAPI
from routes.chatbot import router as chatbot_router
from routes.et_data import router as et_router
from routes.reports import router as reports_router
from routes.visualize import router as viz_router

app = FastAPI(title="OpenET Platform API")

# Create DB tables on startup — works on both local and Render
init_db()

app.include_router(et_router, prefix="/api")
app.include_router(viz_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(chatbot_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "OpenET Platform API is running"}


@app.get("/health")
def health():
    api_key = os.getenv("OPENET_API_KEY")
    return {"status": "ok", "openet_key_loaded": api_key is not None}
