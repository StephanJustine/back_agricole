"""
Modèle Client - Clients.
"""
from sqlalchemy import Column, String, Float, Enum, Boolean
from sqlalchemy.orm import relationship

from .base import BaseModel
from .enums import TypeClient


class Client(BaseModel):
    """
    Client acheteur de produits.
    """
    __tablename__ = "clients"
    
    nom = Column(String, nullable=False)
    telephone = Column(String, nullable=False)
    email = Column(String, nullable=True)
    adresse = Column(String, nullable=True)
    
    type = Column(Enum(TypeClient), default=TypeClient.PARTICULIER)
    fidelite = Column(Float, default=0)  # 0-10
    
    is_active = Column(Boolean, default=True)
    
    # Relations
    ventes = relationship("Vente", back_populates="client")
    
    def __repr__(self):
        return f"<Client {self.nom} - {self.type}>"