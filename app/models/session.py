"""
Modèle UserSession - Sessions utilisateur.
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

from .base import BaseModel


class UserSession(BaseModel):
    """
    Session utilisateur pour la gestion des tokens.
    """
    __tablename__ = "user_sessions"
    
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Tokens
    token = Column(String, unique=True, nullable=False)
    refresh_token = Column(String, unique=True, nullable=True)
    
    # Informations de connexion
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    device_info = Column(JSON, default={})
    location = Column(String, nullable=True)
    
    # Dates
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Statut
    is_active = Column(Boolean, default=True)
    is_revoked = Column(Boolean, default=False)
    
    # Relations
    utilisateur = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        """Représentation string de la session."""
        return f"<UserSession {self.id} - User {self.user_id}>"
    
    def is_expired(self) -> bool:
        """Vérifie si la session est expirée."""
        return datetime.utcnow() > self.expires_at