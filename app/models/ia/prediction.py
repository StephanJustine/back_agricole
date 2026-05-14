"""
Modèle Prediction - Prédictions de rendement.
"""
from sqlalchemy import Column, String, DateTime, Float, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from ..base import BaseModel


class Prediction(BaseModel):
    """
    Prédiction de rendement par IA.
    """
    __tablename__ = "predictions"
    
    modele_id = Column(String, ForeignKey("modeles_ia.id"), nullable=False)
    parcelle_id = Column(String, ForeignKey("parcelles.id"), nullable=True)
    culture_id = Column(String, ForeignKey("cultures.id"), nullable=True)
    
    # Date de la prédiction
    date_prediction = Column(DateTime, default=datetime.utcnow)
    
    # Résultat
    rendement_estime = Column(Float, nullable=True)      # kg/ha
    intervalle_inferieur = Column(Float, nullable=True)  # kg/ha
    intervalle_superieur = Column(Float, nullable=True)  # kg/ha
    probabilite = Column(Float, nullable=True)           # 0-100%
    
    # Détails
    facteurs_influents = Column(JSON, default={})        # facteurs les plus importants
    donnees_utilisees = Column(JSON, default={})         # données utilisées pour la prédiction
    
    # Qualité
    confiance = Column(Float, nullable=True)             # 0-100%
    est_valide = Column(Boolean, default=True)
    
    # Relations
    modele = relationship("ModeleIA", back_populates="predictions")
    parcelle = relationship("Parcelle", back_populates="predictions")
    culture = relationship("Culture")
    
    def __repr__(self):
        return f"<Prediction {self.rendement_estime} kg/ha>"