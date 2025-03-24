# app/routers/vip.py
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.vip import Vip
from app.schemas.vip import VipCheckPhone, VipResponse
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging
from barcode import Code128
from barcode.writer import ImageWriter
import os
import re
import requests
from dotenv import load_dotenv
from io import BytesIO
import base64

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variable
load_dotenv()
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")
RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY")

if not RECAPTCHA_SECRET_KEY or not RECAPTCHA_SITE_KEY:
    logger.error("reCAPTCHA keys not found in environment variables")
    raise ValueError("RECAPTCHA_SITE_KEY and RECAPTCHA_SECRET_KEY are required")

router = APIRouter(prefix="/vip", tags=["vip"])
templates = Jinja2Templates(directory="app/templates")

@router.post("/check-phone", response_model=dict)
async def check_phone(phone: VipCheckPhone, db: Session = Depends(get_db)):
    logger.info(f"Checking phone number: {phone.cellulare}")
    existing = db.query(Vip).filter(Vip.cellulare == phone.cellulare).first()
    if existing:
        logger.debug(f"Phone number {phone.cellulare} found in database")
        return {"exists": True}
    logger.debug(f"Phone number {phone.cellulare} not found")
    return {"exists": False}

@router.get("/register", response_class=HTMLResponse)
async def get_register_form(request: Request):
    logger.info("Rendering registration form")
    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "warning": None,
            "form_data": {},
            "recaptcha_site_key": RECAPTCHA_SITE_KEY
        }
    )

@router.post("/register", response_class=HTMLResponse)
async def register_vip(
    request: Request,
    cellulare: str = Form(...),
    Nome: str = Form(...),
    cognome: str = Form(...),
    nascita: str = Form(None),
    Email: str = Form(None),
    Indirizzo: str = Form(None),
    Citta: str = Form(None),
    Prov: str = Form(None),
    Cap: str = Form(None),
    recaptcha_response: str = Form(...),
    db: Session = Depends(get_db)
):
    logger.info(f"Registering new VIP with phone: {cellulare}")

    # Verify reCAPTCHA v3
    verification_url = "https://www.google.com/recaptcha/api/siteverify"
    payload = {
        "secret": RECAPTCHA_SECRET_KEY,
        "response": recaptcha_response
    }
    try:
        response = requests.post(verification_url, data=payload)
        result = response.json()
        logger.debug(f"reCAPTCHA response: {result}")

        if not result.get("success") or result.get("score", 0) < 0.5:
            logger.warning(f"reCAPTCHA verification failed: success={result.get('success')}, score={result.get('score')}")
            return templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "warning": "CAPTCHA verification failed. Are you a bot?",
                    "form_data": {
                        "cellulare": cellulare,
                        "Nome": Nome,
                        "cognome": cognome,
                        "nascita": nascita,
                        "Email": Email,
                        "Indirizzo": Indirizzo,
                        "Citta": Citta,
                        "Prov": Prov,
                        "Cap": Cap
                    },
                    "recaptcha_site_key": RECAPTCHA_SITE_KEY
                }
            )
    except Exception as e:
        logger.error(f"reCAPTCHA verification request failed: {str(e)}")
        raise HTTPException(status_code=500, detail="CAPTCHA verification error")

    # Validate phone number (Italian, 10 digits)
    cellulare_cleaned = re.sub(r"^\+?39", "", cellulare.strip())
    cellulare_cleaned = re.sub(r"\D", "", cellulare_cleaned)
    if not re.match(r"^\d{10}$", cellulare_cleaned):
        logger.warning(f"Invalid phone number format: {cellulare}")
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "warning": "Phone number must be a 10-digit Italian number",
                "form_data": {
                    "cellulare": cellulare,
                    "Nome": Nome,
                    "cognome": cognome,
                    "nascita": nascita,
                    "Email": Email,
                    "Indirizzo": Indirizzo,
                    "Citta": Citta,
                    "Prov": Prov,
                    "Cap": Cap
                },
                "recaptcha_site_key": RECAPTCHA_SITE_KEY
            }
        )

    # Step 1: Check if phone exists
    existing = db.query(Vip).filter(Vip.cellulare == cellulare_cleaned).first()
    if existing:
        logger.warning(f"Phone number {cellulare_cleaned} already registered")
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "warning": "This phone number is already registered",
                "form_data": {
                    "cellulare": cellulare,
                    "Nome": Nome,
                    "cognome": cognome,
                    "nascita": nascita,
                    "Email": Email,
                    "Indirizzo": Indirizzo,
                    "Citta": Citta,
                    "Prov": Prov,
                    "Cap": Cap
                },
                "recaptcha_site_key": RECAPTCHA_SITE_KEY
            }
        )

    # Step 2: Find available row (stato = 1)
    available_vip = db.query(Vip).filter(Vip.stato == 1).order_by(Vip.IDvip.asc()).first()
    if not available_vip:
        logger.error("No available VIP rows found")
        raise HTTPException(status_code=400, detail="No available VIP slots")

    logger.debug(f"Found available VIP row with IDvip: {available_vip.IDvip}")

    # Step 3: Clean the row
    fields_to_clean = ["nascita", "cellulare", "Nome", "cognome", "Email", "Indirizzo", "Citta", "Prov", "Cap"]
    for field in fields_to_clean:
        setattr(available_vip, field, "")  # Set to empty string instead of None
    logger.debug(f"Cleaned fields for IDvip: {available_vip.IDvip}")

    # Step 4: Assign new data
    available_vip.nascita = nascita
    available_vip.cellulare = cellulare_cleaned
    available_vip.Nome = Nome
    available_vip.cognome = cognome
    available_vip.Email = Email
    available_vip.Indirizzo = Indirizzo
    available_vip.Citta = Citta
    available_vip.Prov = Prov
    available_vip.Cap = Cap

    # Step 5: Set stato = 0 (taken)
    available_vip.stato = 0
    db.commit()
    db.refresh(available_vip)
    logger.info(f"VIP registered with IDvip: {available_vip.IDvip}, code: {available_vip.code}")

    # Step 6: Generate barcode in memory
    try:
        barcode = Code128(available_vip.code, writer=ImageWriter())
        buffer = BytesIO()
        barcode.write(buffer)  # Write PNG data to buffer
        barcode_data = buffer.getvalue()  # Get bytes
        buffer.close()
        # Encode as base64 for embedding in HTML
        barcode_base64 = base64.b64encode(barcode_data).decode('utf-8')
        barcode_data_url = f"data:image/png;base64,{barcode_base64}"
        logger.info(f"Barcode generated in memory for code: {available_vip.code}")
    except Exception as e:
        logger.error(f"Failed to generate barcode: {str(e)}")
        raise HTTPException(status_code=500, detail="Barcode generation failed")

    # Step 7: Render dashboard with in-memory barcode
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "vip": available_vip,
            "barcode_data_url": barcode_data_url  # Pass the data URL to the template
        }
    )
