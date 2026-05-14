"""
Modèle Stock - Gestion des stocks.
"""
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import BaseModel


class Stock(BaseModel):
    """
    Stock d'un lot.
    """
    __tablename__ = "stocks"
    
    lot_id = Column(String, ForeignKey("lots.id", ondelete="CASCADE"), nullable=False)
    
    quantite = Column(Float, nullable=False)
    localisation = Column(String, nullable=True)  # magasin, entrepot
    
    date_entree = Column(DateTime, default=datetime.utcnow)
    date_sortie = Column(DateTime, nullable=True)
    
    alertes = Column(JSON, default={})
    
    # Relations
    lot = relationship("Lot", back_populates="stocks")
    
    def __repr__(self):
        return f"<Stock Lot {self.lot_id} - {self.quantite}>"