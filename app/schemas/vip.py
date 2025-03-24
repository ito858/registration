# app/schemas/vip.py
from pydantic import BaseModel, validator, EmailStr
import re
import logging

# Configure logging
logger = logging.getLogger(__name__)

class VipCheckPhone(BaseModel):
    cellulare: str

    @validator("cellulare")
    def validate_phone(cls, v):
        # Remove any country code (+39 or 39) and non-digit chars
        v = re.sub(r"^\+?39", "", v.strip())
        v = re.sub(r"\D", "", v)
        if not re.match(r"^\d{10}$", v):
            logger.error(f"Invalid Italian phone number: {v}")
            raise ValueError("Cellulare must be a 10-digit Italian number")
        logger.debug(f"Validated phone number: {v}")
        return v

class VipCreate(BaseModel):
    nascita: str  # Will use date widget in front-end
    cellulare: str
    Nome: str
    cognome: str
    Email: str | None = None
    Indirizzo: str | None = None
    Citta: str | None = None
    Prov: str | None = None
    Cap: str | None = None

    @validator("cellulare")
    def validate_phone(cls, v):
        v = re.sub(r"^\+?39", "", v.strip())
        v = re.sub(r"\D", "", v)
        if not re.match(r"^\d{10}$", v):
            logger.error(f"Invalid Italian phone number: {v}")
            raise ValueError("Cellulare must be a 10-digit Italian number")
        return v

    @validator("Nome", "cognome")
    def no_special_chars(cls, v):
        if not re.match(r"^[a-zA-Z\s]+$", v):
            logger.error(f"Special characters found in field: {v}")
            raise ValueError("Nome and cognome must contain only letters and spaces")
        return v

    @validator("Email", pre=True, always=True)
    def validate_email(cls, v):
        if v and not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            logger.error(f"Invalid email format: {v}")
            raise ValueError("Invalid email format")
        return v

class VipResponse(BaseModel):
    IDvip: int
    code: str | None
    cellulare: str
    Nome: str
    cognome: str

    class Config:
        from_attributes = True

logger.info("Pydantic schemas defined")
