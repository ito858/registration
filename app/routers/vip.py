# app/routers/vip.py
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.dependencies import get_db
from app.models.vip import Vip  # Note: We'll need to handle dynamic tables
from app.models.cliente import Cliente
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
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")
RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY")

if not RECAPTCHA_SECRET_KEY or not RECAPTCHA_SITE_KEY:
    logger.error("reCAPTCHA keys not found in environment variables")
    raise ValueError("RECAPTCHA_SITE_KEY and RECAPTCHA_SECRET_KEY are required")

router = APIRouter(prefix="/vip", tags=["vip"])
templates = Jinja2Templates(directory="app/templates")

# Helper function to get the table name from token
def get_table_name_from_token(token: str, db: Session) -> str:
    query = text("SELECT dbnome FROM cliente WHERE token_registrazione = :token AND active = 1")
    result = db.execute(query, {"token": token}).fetchone()
    if not result:
        logger.error(f"No active store found for token: {token}")
        raise HTTPException(status_code=404, detail="Store not found or inactive")
    table_name = result[0]
    logger.info(f"Resolved token {token} to table name: {table_name}")
    return table_name

@router.post("/{token}/check-phone", response_model=dict)
async def check_phone(token: str, phone: VipCheckPhone, db: Session = Depends(get_db)):
    logger.info(f"Starting phone check for token: {token}, phone: {phone.cellulare}")

    # Step 1: Store Identification
    try:
        table_name = get_table_name_from_token(token, db)
    except HTTPException as e:
        logger.error(f"Store identification failed: {str(e)}")
        raise e

    # Step 2: Check if phone exists in the store's table
    query = text(f"SELECT 1 FROM {table_name} WHERE cellulare = :cellulare LIMIT 1")
    result = db.execute(query, {"cellulare": phone.cellulare}).fetchone()
    exists = bool(result)

    if exists:
        logger.debug(f"Phone number {phone.cellulare} found in table {table_name}")
    else:
        logger.debug(f"Phone number {phone.cellulare} not found in table {table_name}")

    return {"exists": exists}

@router.get("/{token}/register", response_class=HTMLResponse)
async def get_register_form(request: Request, token: str, db: Session = Depends(get_db)):
    logger.info(f"Rendering registration form for token: {token}")

    # Verify token exists
    try:
        get_table_name_from_token(token, db)
    except HTTPException as e:
        logger.error(f"Invalid token {token}: {str(e)}")
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "warning": "Invalid or inactive store token",
                "form_data": {},
                "recaptcha_site_key": RECAPTCHA_SITE_KEY
            }
        )

    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "warning": None,
            "form_data": {},
            "recaptcha_site_key": RECAPTCHA_SITE_KEY,
            "token": token  # Pass token to template if needed
        }
    )

# Replace the register_vip function in app/routers/vip.py with this version
@router.post("/{token}/register", response_class=HTMLResponse)
async def register_vip(
    request: Request,
    token: str,
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
    logger.info(f"Starting VIP registration for token: {token}, phone: {cellulare}")

    # Step 1: Store Identification
    try:
        table_name = get_table_name_from_token(token, db)
    except HTTPException as e:
        logger.error(f"Store identification failed: {str(e)}")
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "warning": "Invalid or inactive store token",
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

    # Step 2: Verify reCAPTCHA v3
    verification_url = "https://www.google.com/recaptcha/api/siteverify"
    payload = {
        "secret": RECAPTCHA_SECRET_KEY,
        "response": recaptcha_response
    }
    try:
        response = requests.post(verification_url, data=payload)
        result = response.json()
        logger.debug(f"reCAPTCHA response for token {token}: {result}")

        RECAPTCHA_THRESHOLD = float(os.getenv("RECAPTCHA_THRESHOLD", "0.3"))  # Adjusted threshold
        if not result.get("success") or result.get("score", 0) < RECAPTCHA_THRESHOLD:
            logger.warning(f"reCAPTCHA failed for token {token}: success={result.get('success')}, score={result.get('score')}")
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
        logger.error(f"reCAPTCHA verification failed for token {token}: {str(e)}")
        raise HTTPException(status_code=500, detail="CAPTCHA verification error")

    # Step 3: Validate phone number (Italian, 10 digits)
    cellulare_cleaned = re.sub(r"^\+?39", "", cellulare.strip())
    cellulare_cleaned = re.sub(r"\D", "", cellulare_cleaned)
    if not re.match(r"^\d{10}$", cellulare_cleaned):
        logger.warning(f"Invalid phone number format for token {token}: {cellulare}")
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

    # Step 4: Check if phone exists in the store's table
    query = text(f"SELECT 1 FROM {table_name} WHERE cellulare = :cellulare LIMIT 1")
    existing = db.execute(query, {"cellulare": cellulare_cleaned}).fetchone()
    if existing:
        logger.warning(f"Phone {cellulare_cleaned} already registered in table {table_name}")
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

    # Step 5: Find available row (stato = 1)
    query = text(f"SELECT * FROM {table_name} WHERE stato = 1 ORDER BY IDvip ASC LIMIT 1")
    available_vip = db.execute(query).fetchone()
    if not available_vip:
        logger.error(f"No available VIP rows in table {table_name} for token {token}")
        raise HTTPException(status_code=400, detail="No available VIP slots")

    # Access Row data using _mapping for named access
    logger.debug(f"Found available VIP row in {table_name} with IDvip: {available_vip._mapping['IDvip']}")

    # Step 6: Clean the row and update it
    fields_to_clean = ["nascita", "cellulare", "Nome", "cognome", "Email", "Indirizzo", "Citta", "Prov", "Cap"]
    update_data = {field: "" for field in fields_to_clean}  # Clean fields
    update_data.update({
        "nascita": nascita,
        "cellulare": cellulare_cleaned,
        "Nome": Nome,
        "cognome": cognome,
        "Email": Email,
        "Indirizzo": Indirizzo,
        "Citta": Citta,
        "Prov": Prov,
        "Cap": Cap,
        "stato": 0  # Mark as taken
    })

    update_query = text(f"""
        UPDATE {table_name}
        SET nascita = :nascita, cellulare = :cellulare, Nome = :Nome, cognome = :cognome,
            Email = :Email, Indirizzo = :Indirizzo, Citta = :Citta, Prov = :Prov, Cap = :Cap, stato = :stato
        WHERE IDvip = :IDvip
    """)
    db.execute(update_query, {**update_data, "IDvip": available_vip._mapping["IDvip"]})
    db.commit()
    logger.info(f"Updated VIP row in {table_name} with IDvip: {available_vip._mapping['IDvip']}")

    # Step 7: Fetch the updated row for dashboard
    select_query = text(f"SELECT * FROM {table_name} WHERE IDvip = :IDvip")
    updated_vip = db.execute(select_query, {"IDvip": available_vip._mapping["IDvip"]}).fetchone()

    # Step 8: Generate barcode in memory
    try:
        barcode = Code128(updated_vip._mapping["code"], writer=ImageWriter())
        buffer = BytesIO()
        barcode.write(buffer)
        barcode_data = buffer.getvalue()
        buffer.close()
        barcode_base64 = base64.b64encode(barcode_data).decode('utf-8')
        barcode_data_url = f"data:image/png;base64,{barcode_base64}"
        logger.info(f"Barcode generated for code: {updated_vip._mapping['code']} in table {table_name}")
    except Exception as e:
        logger.error(f"Barcode generation failed for token {token}: {str(e)}")
        raise HTTPException(status_code=500, detail="Barcode generation failed")

    # Step 9: Render dashboard
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "vip": updated_vip._mapping,  # Pass the mapping directly
            "barcode_data_url": barcode_data_url,
            "token": token
        }
    )

