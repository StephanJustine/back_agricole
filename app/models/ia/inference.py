"""
Modèle Inference - Inférence sur images.
"""
from sqlalchemy import Column, String, DateTime, Float, JSON, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from ..base import BaseModel


class Inference(BaseModel):
    """
    Inférence d'un modèle IA sur une image.
    """
    __tablename__ = "inferences"
    
    modele_id = Column(String, ForeignKey("modeles_ia.id"), nullable=False)
    culture_id = Column(String, ForeignKey("cultures.id"), nullable=True)
    
    # Image
    image_url = Column(String, nullable=False)
    image_originale = Column(String, nullable=True)
    
    # Résultat
    resultat = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    
    # Détection (si modèle de vision)
    bbox = Column(JSON, nullable=True)
    segmentation = Column(JSON, nullable=True)
    
    # Métadonnées
    temps_inference = Column(Float, nullable=True)
    date_inference = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    # Relations
    modele = relationship("ModeleIA", back_populates="inferences")
    culture = relationship("Culture")
    
    def __repr__(self):
        return f"<Inference {self.resultat} - {self.confidence}%>"