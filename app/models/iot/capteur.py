"""
Modèle Capteur - Capteur IoT.
"""
from sqlalchemy import Column, String, DateTime, Enum, Float, ForeignKey, JSON, Boolean, Integer
from sqlalchemy.orm import relationship
from datetime import datetime

from ..base import BaseModel
from ..enums import TypeCapteur


class Capteur(BaseModel):
    """
    Capteur IoT (humidité, température, pH, etc.).
    """
    __tablename__ = "capteurs"
    
    passerelle_id = Column(String, ForeignKey("passerelles.id", ondelete="CASCADE"), nullable=False)
    parcelle_id = Column(String, ForeignKey("parcelles.id"), nullable=True)
    
    # Identification
    code = Column(String, unique=True, nullable=True)
    type = Column(Enum(TypeCapteur), nullable=False)
    reference = Column(String, nullable=True)
    
    # Caractéristiques techniques
    precision = Column(Float, nullable=True)        # ± valeur
    unite = Column(String, nullable=True)           # °C, %, mm, etc.
    valeur_min = Column(Float, nullable=True)
    valeur_max = Column(Float, nullable=True)
    seuil_alerte_bas = Column(Float, nullable=True)
    seuil_alerte_haut = Column(Float, nullable=True)
    
    # Installation
    date_installation = Column(DateTime, default=datetime.utcnow)
    date_dernier_main = Column(DateTime, nullable=True)
    calibration = Column(JSON, default={})
    
    # Statut
    est_actif = Column(Boolean, default=True)
    derniere_valeur = Column(Float, nullable=True)
    derniere_mise_a_jour = Column(DateTime, nullable=True)
    
    # Métadonnées
    configuration = Column(JSON, default={})
    
    # Relations
    passerelle = relationship("Passerelle", back_populates="capteurs")
    parcelle = relationship("Parcelle", back_populates="capteurs")
    releves = relationship("ReleveCapteur", back_populates="capteur", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Capteur {self.type} - {self.code}>"