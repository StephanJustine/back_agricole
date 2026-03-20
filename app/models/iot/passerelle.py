"""
Modèle Passerelle - Passerelle IoT.
"""
from sqlalchemy import Column, String, DateTime, Enum, JSON, Boolean, Integer
from sqlalchemy.orm import relationship
from datetime import datetime

from ..base import BaseModel
from ..enums import StatusPasserelle


class Passerelle(BaseModel):
    """
    Passerelle IoT (ESP32, Raspberry Pi).
    """
    __tablename__ = "passerelles"
    
    nom = Column(String, nullable=False)
    modele = Column(String, nullable=True)
    
    # Identifiants techniques
    adresse_mac = Column(String, unique=True, nullable=False)
    adresse_ip = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)
    
    # Localisation
    localisation = Column(String, nullable=True)  # "lat,lon"
    adresse_physique = Column(String, nullable=True)
    
    # Dates
    date_installation = Column(DateTime, default=datetime.utcnow)
    derniere_connexion = Column(DateTime, nullable=True)
    
    # Statut
    status = Column(Enum(StatusPasserelle), default=StatusPasserelle.ACTIVE)
    est_connectee = Column(Boolean, default=False)
    
    # Métadonnées
    configuration = Column(JSON, default={})
    notes = Column(String, nullable=True)
    
    # Relations
    capteurs = relationship("Capteur", back_populates="passerelle", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Passerelle {self.nom} - {self.status}>"