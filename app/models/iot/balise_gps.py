"""
Modèle BaliseGPS - Balise GPS pour traçabilité.
"""
from sqlalchemy import Column, String, DateTime, Float, Boolean, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship
from datetime import datetime

from ..base import BaseModel


class BaliseGPS(BaseModel):
    """
    Balise GPS pour traçabilité des lots.
    """
    __tablename__ = "balises_gps"
    
    lot_id = Column(String, ForeignKey("lots.id"), nullable=True)
    
    # Identification
    code = Column(String, unique=True, nullable=False)
    modele = Column(String, nullable=True)
    
    # Position actuelle
    position = Column(String, nullable=True)          # "lat,lon"
    altitude = Column(Float, nullable=True)           # m
    vitesse = Column(Float, nullable=True)            # km/h
    cap = Column(Float, nullable=True)                # degrés
    
    # Dernière position
    derniere_position = Column(String, nullable=True)
    derniere_mise_a_jour = Column(DateTime, nullable=True)
    
    # Environnement
    temperature = Column(Float, nullable=True)
    humidite = Column(Float, nullable=True)
    
    # Statut
    batterie = Column(Float, nullable=True)           # %
    signal = Column(Integer, nullable=True)           # 0-100
    choc = Column(Boolean, default=False)
    alerte = Column(Boolean, default=False)
    
    # Historique
    historique_positions = Column(JSON, default=[])
    alertes = Column(JSON, default=[])
    
    # Relations
    lot = relationship("Lot")
    
    def __repr__(self):
        return f"<BaliseGPS {self.code} - Batterie {self.batterie}%>"