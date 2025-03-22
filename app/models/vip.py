# app/models/vip.py
from sqlalchemy import Column, BigInteger, String, Integer, Boolean, DECIMAL, TIMESTAMP, LargeBinary
from app.dependencies import Base
import logging

# Configure logging
logger = logging.getLogger(__name__)

class Vip(Base):
    __tablename__ = "vip"

    IDvip = Column(BigInteger, primary_key=True)
    code = Column(String(13), nullable=True)
    nascita = Column(String(255), nullable=True)
    cellulare = Column(String(255), nullable=True)
    sms = Column(Boolean, default=False)  # tinyint as Boolean
    Punti = Column(Integer, nullable=True)
    Sconto = Column(Integer, nullable=True)
    Ck = Column(String(255), nullable=True)
    idata = Column(TIMESTAMP, nullable=True, default="CURRENT_TIMESTAMP")
    ioperatore = Column(Integer, nullable=True)
    inegozio = Column(Integer, nullable=True)
    P_cs = Column(Integer, default=0)
    P_ldata = Column(String(255), nullable=True)
    P_importo = Column(DECIMAL(10, 2), default=0.00)
    Nome = Column(String(255), nullable=True)
    Indirizzo = Column(String(255), nullable=True)
    Cap = Column(String(255), nullable=True)
    Citta = Column(String(255), nullable=True)
    Prov = Column(String(255), nullable=True)
    CodiceFiscale = Column(String(255), nullable=True)
    PartitaIva = Column(String(255), nullable=True)
    Email = Column(String(255), nullable=True)
    sesso = Column(Integer, default=0)
    VIPanno = Column(Integer, default=0)
    maps = Column(String(255), nullable=True)
    VIPscadenza = Column(String(255), nullable=True)
    Blocco = Column(Integer, default=0)
    cognome = Column(String(255), default="")
    SerBlocco = Column(Integer, default=0)
    SerBloccoBz = Column(String(255), default="")
    omail = Column(Boolean, default=False)
    oposte = Column(Boolean, default=False)
    msg = Column(Integer, default=0)
    msgstr = Column(String(255), default="")
    utime = Column(String(255), default="")
    upc = Column(String(255), default="")
    uzt = Column(Integer, default=0)
    un = Column(String(255), default="")
    lotteria = Column(String(20), default="")
    statoanno = Column(String(10), default="")
    img = Column(LargeBinary, nullable=True)  # mediumblob for images
    n = Column(String(255), default="")
    SCOscadenza = Column(String(20), default="")
    stato = Column(Boolean, default=False)  # tinyint as Boolean

    def __repr__(self):
        return f"<Vip(IDvip={self.IDvip}, code={self.code}, cellulare={self.cellulare}, stato={self.stato})>"

logger.info("Vip model defined")
