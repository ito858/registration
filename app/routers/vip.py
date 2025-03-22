# app/routers/vip.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.vip import Vip
from app.schemas.vip import VipCheckPhone, VipCreate, VipResponse
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging
from barcode import Code128  # Using Code128, a well-supported barcode format
from barcode.writer import ImageWriter
import os

# Configure logging
logger = logging.getLogger(__name__)

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

@router.post("/register", response_class=HTMLResponse)
async def register_vip(
    request: Request,
    vip_data: VipCreate,
    db: Session = Depends(get_db)
):
    logger.info(f"Registering new VIP with phone: {vip_data.cellulare}")

    # Step 1: Check if phone exists
    existing = db.query(Vip).filter(Vip.cellulare == vip_data.cellulare).first()
    if existing:
        logger.warning(f"Phone number {vip_data.cellulare} already registered")
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "warning": "This phone number is already registered",
                "form_data": vip_data.dict()
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
        setattr(available_vip, field, None)
    logger.debug(f"Cleaned fields for IDvip: {available_vip.IDvip}")

    # Step 4: Assign new data
    available_vip.nascita = vip_data.nascita
    available_vip.cellulare = vip_data.cellulare
    available_vip.Nome = vip_data.Nome
    available_vip.cognome = vip_data.cognome
    available_vip.Email = vip_data.Email
    available_vip.Indirizzo = vip_data.Indirizzo
    available_vip.Citta = vip_data.Citta
    available_vip.Prov = vip_data.Prov
    available_vip.Cap = vip_data.Cap

    # Step 5: Set stato = 0 (taken)
    available_vip.stato = 0
    db.commit()
    db.refresh(available_vip)
    logger.info(f"VIP registered with IDvip: {available_vip.IDvip}, code: {available_vip.code}")

    # Step 6: Generate barcode
    barcode_path = f"app/static/images/barcode_{available_vip.IDvip}.png"
    try:
        barcode = Code128(available_vip.code, writer=ImageWriter())
        barcode.save(f"app/static/images/barcode_{available_vip.IDvip}")
        logger.info(f"Barcode generated for code {available_vip.code} at {barcode_path}")
    except Exception as e:
        logger.error(f"Failed to generate barcode: {str(e)}")
        raise HTTPException(status_code=500, detail="Barcode generation failed")

    # Step 7: Render dashboard
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "vip": available_vip
        }
    )
