"""
Modèle ModeleIA - Modèles d'intelligence artificielle.
"""
from sqlalchemy import Column, String, DateTime, Enum, JSON, Text, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from ..base import BaseModel
from ..enums import TypeModeleIA


class ModeleIA(BaseModel):
    """
    Modèle d'intelligence artificielle.
    """
    __tablename__ = "modeles_ia"
    
    nom = Column(String, nullable=False)
    type = Column(Enum(TypeModeleIA), nullable=False)
    version = Column(String, nullable=False)
    
    framework = Column(String, nullable=True)
    path = Column(String, nullable=True)
    taille = Column(String, nullable=True)
    
    # Métriques de performance
    metriques = Column(JSON, default={})
    parametres = Column(JSON, default={})
    
    # Statut
    est_actif = Column(Boolean, default=True)
    est_pret = Column(Boolean, default=False)
    
    # Description
    description = Column(Text, nullable=True)
    
    # Relations
    predictions = relationship("Prediction", back_populates="modele", cascade="all, delete-orphan")
    inferences = relationship("Inference", back_populates="modele", cascade="all, delete-orphan")
    entrainements = relationship("Entrainement", back_populates="modele", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ModeleIA {self.nom} v{self.version}>"