"""
Modèle TravailSol - Travaux du sol.
"""
from sqlalchemy import Column, String, Date, Enum, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import BaseModel
from .enums import TypeTravail


class TravailSol(BaseModel):
    """
    Travail effectué sur une parcelle.
    """
    __tablename__ = "travaux_sol"
    
    # Identifiants
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Lien avec la parcelle
    parcelle_id = Column(String, ForeignKey("parcelles.id", ondelete="CASCADE"), nullable=False)
    
    # Informations sur le travail
    date = Column(Date, nullable=False)
    type = Column(Enum(TypeTravail), nullable=False)
    
    # Détails du travail
    description = Column(Text, nullable=True)
    profondeur = Column(Float, nullable=True)  # cm (pour labour)
    produit = Column(String, nullable=True)  # pour amendement/traitement
    dose = Column(Float, nullable=True)  # kg/ha ou L/ha
    
    # Coûts
    cout_intrants = Column(Float, nullable=True)  # Coût des produits (Ar)
    cout_main_oeuvre = Column(Float, nullable=True)  # Coût de la main d'œuvre (Ar)
    cout_total = Column(Float, nullable=True)  # Coût total (calculé)
    
    # Métadonnées
    observations = Column(Text, nullable=True)
    responsable = Column(String, nullable=True)  # Qui a effectué le travail
    
    # Relations
    parcelle = relationship("Parcelle", back_populates="travaux")
    
    def __repr__(self):
        return f"<TravailSol {self.type} - {self.date}>"
    
    def calculer_cout_total(self):
        """Calcule le coût total du travail."""
        self.cout_total = (self.cout_intrants or 0) + (self.cout_main_oeuvre or 0)
        return self.cout_total