"""
Modèle StationMeteo - Station météo.
"""
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from ..base import BaseModel


class StationMeteo(BaseModel):
    """
    Station météo locale.
    """
    __tablename__ = "stations_meteo"
    
    parcelle_id = Column(String, ForeignKey("parcelles.id"), unique=True, nullable=False)
    
    # Mesures actuelles
    temperature = Column(Float, nullable=True)
    temperature_min = Column(Float, nullable=True)
    temperature_max = Column(Float, nullable=True)
    humidite = Column(Float, nullable=True)          # %
    pression = Column(Float, nullable=True)          # hPa
    pluie_24h = Column(Float, nullable=True)        # mm
    pluie_mensuelle = Column(Float, nullable=True)  # mm
    vent_moyen = Column(Float, nullable=True)       # km/h
    vent_rafale = Column(Float, nullable=True)      # km/h
    direction_vent = Column(String, nullable=True)  # N, NE, etc.
    luminosite = Column(Float, nullable=True)       # lux
    uv = Column(Float, nullable=True)               # index UV
    
    # Prévisions (si disponibles)
    previsions = Column(JSON, default={})
    
    # Date de dernière mise à jour
    date_maj = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    parcelle = relationship("Parcelle", back_populates="station_meteo")
    
    def __repr__(self):
        return f"<StationMeteo - Parcelle {self.parcelle_id}>"