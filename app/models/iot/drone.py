"""
Modèle Drone - Drone agricole.
"""
from sqlalchemy import Column, String, DateTime, Float, JSON, Integer, Text
from datetime import datetime

from ..base import BaseModel


class Drone(BaseModel):
    """
    Drone agricole pour imagerie.
    """
    __tablename__ = "drones"
    
    modele = Column(String, nullable=False)
    numero_serie = Column(String, unique=True, nullable=True)
    
    # Mission
    date_mission = Column(DateTime, default=datetime.utcnow)
    duree_vol = Column(Integer, nullable=True)        # minutes
    altitude = Column(Float, nullable=True)           # m
    vitesse = Column(Float, nullable=True)            # m/s
    
    # Plan de vol
    plan_vol = Column(JSON, default={})               # waypoints, etc.
    zone_survolee = Column(JSON, default={})          # polygon
    surface_couverte = Column(Float, nullable=True)   # hectares
    
    # Images
    images = Column(JSON, default=[])                  # liste URLs
    videos = Column(JSON, default=[])
    
    # Analyses
    indice_ndvi = Column(Float, nullable=True)        # moyenne NDVI
    indice_ndre = Column(Float, nullable=True)        # moyenne NDRE
    indice_norm = Column(Float, nullable=True)        # normalisé
    
    # Détections
    zones_a_probleme = Column(JSON, default=[])        # zones détectées
    observations = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Drone {self.modele} - Mission du {self.date_mission}>"