"""
Modèle ReleveCapteur - Relevés de capteurs.
"""
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
from datetime import datetime

from ..base import BaseModel


class ReleveCapteur(BaseModel):
    """
    Relevé de mesure d'un capteur.
    """
    __tablename__ = "releves_capteurs"
    
    capteur_id = Column(String, ForeignKey("capteurs.id", ondelete="CASCADE"), nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    valeur = Column(Float, nullable=False)
    
    # État du capteur
    batterie = Column(Float, nullable=True)        # %
    signal = Column(Integer, nullable=True)        # 0-100
    temperature_interne = Column(Float, nullable=True)  # °C
    
    # Qualité de la donnée
    est_valide = Column(Boolean, default=True)
    erreur = Column(String, nullable=True)
    
    # Relations
    capteur = relationship("Capteur", back_populates="releves")
    
    def __repr__(self):
        return f"<ReleveCapteur {self.valeur} à {self.timestamp}>"