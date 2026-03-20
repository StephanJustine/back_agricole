"""
Modèle AnalyseSol - Analyse de sol.
"""
from sqlalchemy import Column, String, Date, Float, ForeignKey, Text
from sqlalchemy.orm import relationship

from .base import BaseModel


class AnalyseSol(BaseModel):
    """
    Analyse de sol pour une parcelle.
    """
    __tablename__ = "analyses_sol"
    
    parcelle_id = Column(String, ForeignKey("parcelles.id", ondelete="CASCADE"), nullable=False)
    
    date_prelevement = Column(Date, nullable=False)
    date_resultats = Column(Date, nullable=True)
    
    # Résultats
    ph = Column(Float, nullable=True)
    matiere_organique = Column(Float, nullable=True)  # %
    azote = Column(Float, nullable=True)  # ppm
    phosphore = Column(Float, nullable=True)  # ppm
    potassium = Column(Float, nullable=True)  # ppm
    calcium = Column(Float, nullable=True)  # ppm
    magnesium = Column(Float, nullable=True)  # ppm
    
    recommandations = Column(Text, nullable=True)
    laboratoire = Column(String, nullable=True)
    
    # Relations
    parcelle = relationship("Parcelle", back_populates="analyses_sol")
    
    def __repr__(self):
        return f"<AnalyseSol Parcelle {self.parcelle_id} - pH {self.ph}>"