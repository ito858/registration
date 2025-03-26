# app/models/cliente.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, DECIMAL
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Cliente(Base):
    __tablename__ = "cliente"

    id_negozio = Column(Integer, primary_key=True, autoincrement=True)
    nome_negozio = Column(String(255), nullable=False)
    tipo_negozio = Column(String(50), nullable=True)
    indirizzo = Column(String(255), nullable=True)
    citta = Column(String(100), nullable=True)
    provincia = Column(String(50), nullable=True)
    cap = Column(String(10), nullable=True)
    telefono = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    sito_web = Column(String(255), nullable=True)
    partita_iva = Column(String(11), nullable=True, unique=True)
    data_creazione = Column(DateTime, nullable=False, default="CURRENT_TIMESTAMP")
    attivo = Column(Boolean, nullable=True, default=True)
    coordinate_latitudine = Column(DECIMAL(10, 8), nullable=True)
    coordinate_longitudine = Column(DECIMAL(11, 8), nullable=True)
    descrizione = Column(Text, nullable=True)
    orari_apertura = Column(String(255), nullable=True)
    token_registrazione = Column(String(32), nullable=True, unique=True)
    data_scadenza_token = Column(DateTime, nullable=False, default="0000-00-00 00:00:00")
    active = Column(Boolean, nullable=True, default=True)
    dbnome = Column(String(255), nullable=False)  # e.g., vip1, vip2
