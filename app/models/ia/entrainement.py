"""
Modèle Entrainement - Entraînement des modèles IA.
"""
from sqlalchemy import Column, String, DateTime, Float, Enum, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from ..base import BaseModel
from ..enums import StatusEntrainement


class Entrainement(BaseModel):
    """
    Entraînement d'un modèle IA.
    """
    __tablename__ = "entrainements"
    
    modele_id = Column(String, ForeignKey("modeles_ia.id"), nullable=False)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    
    # Dates
    date_debut = Column(DateTime, default=datetime.utcnow)
    date_fin = Column(DateTime, nullable=True)
    
    # Métriques
    precision = Column(Float, nullable=True)
    rappel = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    r2 = Column(Float, nullable=True)
    
    # Paramètres
    params = Column(JSON, default={})
    
    # Détails
    logs = Column(Text, nullable=True)
    status = Column(Enum(StatusEntrainement), default=StatusEntrainement.EN_COURS)
    
    # Relations
    modele = relationship("ModeleIA", back_populates="entrainements")
    dataset = relationship("Dataset", back_populates="entrainements")
    
    def __repr__(self):
        return f"<Entrainement {self.modele_id} - {self.status}>"
    
    @property
    def duree(self):
        if self.date_fin and self.date_debut:
            delta = self.date_fin - self.date_debut
            return delta.total_seconds() / 60
        return None