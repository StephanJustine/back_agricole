"""
Modèle Vente - Ventes de produits.
"""
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import BaseModel


class Vente(BaseModel):
    """
    Vente d'un lot.
    """
    __tablename__ = "ventes"
    
    date = Column(DateTime, default=datetime.utcnow)
    
    lot_id = Column(String, ForeignKey("lots.id"), nullable=False)
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)
    commercial_id = Column(String, ForeignKey("users.id"), nullable=True)
    
    quantite = Column(Float, nullable=False)
    prix_unitaire = Column(Float, nullable=False)
    montant_total = Column(Float, nullable=False)
    
    paye = Column(Boolean, default=False)
    date_paiement = Column(DateTime, nullable=True)
    
    # Relations
    lot = relationship("Lot", back_populates="ventes")
    client = relationship("Client", back_populates="ventes")
    commercial = relationship("User", back_populates="ventes")
    
    def __repr__(self):
        return f"<Vente {self.montant_total} Ar - Client {self.client_id}>"