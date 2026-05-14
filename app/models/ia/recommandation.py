"""
Modèle Recommandation - Recommandations automatiques.
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from ..base import BaseModel
from ..enums import TypeRecommandation


class Recommandation(BaseModel):
    """
    Recommandation automatique pour l'agriculteur.
    """
    __tablename__ = "recommandations"
    
    type = Column(Enum(TypeRecommandation), nullable=False)
    parcelle_id = Column(String, ForeignKey("parcelles.id"), nullable=False)
    culture_id = Column(String, ForeignKey("cultures.id"), nullable=True)
    
    # Message
    titre = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, default={})
    
    # Priorité (1=urgent, 2=important, 3=info)
    priorite = Column(Integer, default=2)
    
    # Statut
    est_lue = Column(Boolean, default=False)
    est_appliquee = Column(Boolean, default=False)
    
    # Dates
    date_emission = Column(DateTime, default=datetime.utcnow)
    date_lecture = Column(DateTime, nullable=True)
    date_action = Column(DateTime, nullable=True)
    
    # Relations
    parcelle = relationship("Parcelle", back_populates="recommandations")
    culture = relationship("Culture")
    
    def __repr__(self):
        return f"<Recommandation {self.type} - {self.titre}>"