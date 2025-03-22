# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse  # Add this import
from app.routers import vip
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),  # Log to a file
        logging.StreamHandler()          # Also log to console
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Registration")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(vip.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")

# # Root endpoint for testing
# @app.get("/")
# async def root():
#     logger.info("Root endpoint accessed")
#     return {"message": "Welcome to Registraction"}

# Updated root endpoint to redirect to registration
@app.get("/")
async def root():
    logger.info("Root endpoint accessed, redirecting to /vip/register")
    return RedirectResponse(url="/vip/register")

