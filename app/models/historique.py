"""
Modèle Historique - Historique des actions.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import BaseModel


class Historique(BaseModel):
    """
    Historique des actions des utilisateurs.
    """
    __tablename__ = "historique"
    
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Action
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=True)
    details = Column(JSON, default={})
    description = Column(Text, nullable=True)
    
    # Contexte
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    utilisateur = relationship("User", back_populates="historique")
    
    def __repr__(self):
        """Représentation string de l'historique."""
        return f"<Historique {self.action} - {self.entity_type}>"