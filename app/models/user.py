"""
Modèle User - Utilisateur du système.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import BaseModel
from .enums import UserRole


class User(BaseModel):
    """
    Utilisateur du système.
    """
    __tablename__ = "users"
    
    # Identifiants
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    
    # Informations personnelles
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    telephone = Column(String, nullable=False)
    photo_url = Column(String, nullable=True)
    adresse = Column(String, nullable=True)
    localisation_gps = Column(String, nullable=True)
    
    # Authentification
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(Enum(UserRole), default=UserRole.PRODUCTEUR)
    
    # Tokens
    refresh_token = Column(String, nullable=True)
    reset_password_token = Column(String, nullable=True)
    reset_password_expires = Column(DateTime, nullable=True)
    verification_token = Column(String, nullable=True)
    verification_expires = Column(DateTime, nullable=True)
    
    # Métadonnées
    date_inscription = Column(DateTime, default=datetime.utcnow)
    derniere_connexion = Column(DateTime, nullable=True)
    derniere_ip = Column(String, nullable=True)
    
    # Relations - Import différé pour éviter les imports circulaires
    parcelles = relationship("Parcelle", back_populates="proprietaire", cascade="all, delete-orphan")
    historique = relationship("Historique", back_populates="utilisateur", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="utilisateur", cascade="all, delete-orphan")
    transformations = relationship("Transformation", back_populates="responsable")
    ventes = relationship("Vente", back_populates="commercial")
    
    def __repr__(self):
        """Représentation string de l'utilisateur."""
        return f"<User {self.email}>"
    
    @property
    def full_name(self) -> str:
        """Retourne le nom complet de l'utilisateur."""
        return f"{self.prenom} {self.nom}"
    
    def set_preference(self, key: str, value: any) -> None:
        """Définit une préférence utilisateur."""
        if not self.extra_data:
            self.extra_data = {}
        if "preferences" not in self.extra_data:
            self.extra_data["preferences"] = {}
        self.extra_data["preferences"][key] = value
    
    def get_preference(self, key: str, default: any = None) -> any:
        """Récupère une préférence utilisateur."""
        if self.extra_data and "preferences" in self.extra_data:
            return self.extra_data["preferences"].get(key, default)
        return default