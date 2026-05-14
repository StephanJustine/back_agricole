"""
Classe de base pour tous les modèles SQLAlchemy.
Fournit les champs communs et les méthodes utiles.
"""
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
import uuid
import json

from ..database import Base  # Import Base depuis database.py


class BaseModel(Base):
    """
    Classe de base abstraite pour tous les modèles.
    
    Attributs communs :
    - id : identifiant unique (UUID)
    - created_at : date de création
    - updated_at : date de dernière modification
    - created_by : ID de l'utilisateur qui a créé (optionnel)
    - updated_by : ID de l'utilisateur qui a modifié (optionnel)
    - is_active : statut actif/inactif
    - extra_data : métadonnées JSON supplémentaires
    - tags : tags pour catégorisation
    """
    __abstract__ = True
    
    # Identifiant unique (UUID par défaut)
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Traçabilité utilisateur
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    
    # Statut
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Métadonnées extensibles
    extra_data = Column(JSON, default={}, nullable=True)
    tags = Column(JSON, default=[], nullable=True)
    
    # Version (pour contrôle de concurrence optimiste)
    version = Column(Integer, default=1, nullable=False)
    
    @declared_attr
    def __tablename__(cls):
        """
        Génère automatiquement le nom de la table à partir du nom de la classe.
        Exemple: User -> users, Parcelle -> parcelles
        """
        return cls.__name__.lower() + 's'
    
    def to_dict(self, exclude: list = None) -> dict:
        """
        Convertit l'objet en dictionnaire.
        """
        exclude = exclude or []
        exclude.extend(['_sa_instance_state'])
        
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                result[column.name] = value
        
        return result
    
    def to_json(self, exclude: list = None) -> str:
        """
        Convertit l'objet en JSON string.
        """
        return json.dumps(self.to_dict(exclude), default=str, ensure_ascii=False)
    
    def update(self, data: dict) -> None:
        """
        Met à jour les champs de l'objet avec un dictionnaire.
        """
        for key, value in data.items():
            if hasattr(self, key) and key not in ['id', 'created_at', 'created_by']:
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
    
    def soft_delete(self) -> None:
        """
        Suppression logique (désactive l'enregistrement).
        """
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def restore(self) -> None:
        """
        Restaure un enregistrement supprimé logiquement.
        """
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def add_tag(self, tag: str) -> None:
        """
        Ajoute un tag à l'objet.
        """
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """
        Supprime un tag de l'objet.
        """
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
    
    def has_tag(self, tag: str) -> bool:
        """
        Vérifie si l'objet a un tag.
        """
        return self.tags and tag in self.tags
    
    def set_extra_data(self, key: str, value: any) -> None:
        """
        Ajoute ou met à jour une donnée supplémentaire.
        """
        if not self.extra_data:
            self.extra_data = {}
        self.extra_data[key] = value
    
    def get_extra_data(self, key: str, default: any = None) -> any:
        """
        Récupère une donnée supplémentaire.
        """
        return self.extra_data.get(key, default) if self.extra_data else default
    
    def remove_extra_data(self, key: str) -> None:
        """
        Supprime une donnée supplémentaire.
        """
        if self.extra_data and key in self.extra_data:
            del self.extra_data[key]
    
    def increment_version(self) -> None:
        """
        Incrémente la version de l'objet.
        """
        self.version += 1
    
    def __repr__(self) -> str:
        """
        Représentation string de l'objet.
        """
        return f"<{self.__class__.__name__} id={self.id}>"