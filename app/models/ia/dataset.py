"""
Modèle Dataset - Jeux de données pour l'IA.
"""
from sqlalchemy import Column, String, DateTime, Enum, JSON, Integer, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from ..base import BaseModel
from ..enums import SourceDataset


class Dataset(BaseModel):
    """
    Jeu de données pour l'entraînement des modèles IA.
    """
    __tablename__ = "datasets"
    
    nom = Column(String, nullable=False)
    source = Column(Enum(SourceDataset), default=SourceDataset.TERRAIN)
    
    date_creation = Column(DateTime, default=datetime.utcnow)
    nb_echantillons = Column(Integer, default=0)
    
    # Structure des données
    features = Column(JSON, default=[])
    labels = Column(JSON, default=[])
    
    # Stockage
    url_data = Column(String, nullable=True)
    taille = Column(String, nullable=True)
    
    # Description
    description = Column(Text, nullable=True)
    
    # Relations
    entrainements = relationship("Entrainement", back_populates="dataset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Dataset {self.nom} - {self.nb_echantillons} échantillons>"