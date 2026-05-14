"""
Modèle Mesure - Mesures de croissance.
"""
from sqlalchemy import Column, String, Date, Float, Integer, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, date
import uuid

from .base import BaseModel


class Mesure(BaseModel):
    """
    Mesure de croissance d'une culture.
    """
    __tablename__ = "mesures"
    
    # Lien avec la culture
    culture_id = Column(String, ForeignKey("cultures.id", ondelete="CASCADE"), nullable=False)
    
    # Date de la mesure
    date_mesure = Column(Date, nullable=False)  # <-- C'est bien date_mesure
    
    # Mesures de croissance
    hauteur_moyenne = Column(Float, nullable=True)  # cm
    nb_feuilles_moyen = Column(Integer, nullable=True)
    nb_fleurs_moyen = Column(Integer, nullable=True)
    nb_gousses_moyen = Column(Integer, nullable=True)
    diametre_tige = Column(Float, nullable=True)  # cm
    
    # Indices de santé
    indice_vigueur = Column(Integer, nullable=True)  # 1-5
    couleur_feuillage = Column(String, nullable=True)
    stress_hydrique = Column(Float, nullable=True)  # 0-100%
    
    # Photos
    photo_url = Column(String, nullable=True)
    photos = Column(JSON, default=[])
    
    # Observations
    observations = Column(Text, nullable=True)
    date_saisie = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    culture = relationship("Culture", back_populates="mesures")
    
    def __repr__(self):
        return f"<Mesure {self.date_mesure} - Hauteur {self.hauteur_moyenne}cm>"
    
    @property
    def age_culture(self):
        """Âge de la culture au moment de la mesure (jours)."""
        if self.culture and self.culture.date_debut:
            return (self.date_mesure - self.culture.date_debut).days
        return 0