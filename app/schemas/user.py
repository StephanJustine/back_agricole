"""
Schémas Pydantic pour les utilisateurs.
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
import re

from .base import BaseSchema, BaseResponseSchema
from ..models.enums import UserRole


class UserBase(BaseSchema):
    """Schéma de base pour un utilisateur."""
    email: EmailStr
    nom: str = Field(..., min_length=2, max_length=50)
    prenom: str = Field(..., min_length=2, max_length=50)
    telephone: str = Field(..., min_length=8, max_length=20)
    role: Optional[UserRole] = UserRole.PRODUCTEUR
    adresse: Optional[str] = None
    photo_url: Optional[str] = None
    
    @validator('telephone')
    def validate_telephone(cls, v):
        """Validation du téléphone Madagascar."""
        pattern = r'^(0[0-9]{9})$|^(\+261[0-9]{9})$'
        if not re.match(pattern, v):
            raise ValueError('Format téléphone invalide. Utilisez 0341234567 ou +261341234567')
        return v


class UserCreate(UserBase):
    """Schéma pour la création d'un utilisateur."""
    password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Vérifie que les mots de passe correspondent."""
        if 'password' in values and v != values['password']:
            raise ValueError('Les mots de passe ne correspondent pas')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        """Validation du mot de passe."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule')
        if not re.search(r'[a-z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une minuscule')
        if not re.search(r'[0-9]', v):
            raise ValueError('Le mot de passe doit contenir au moins un chiffre')
        return v


class UserUpdate(BaseSchema):
    """Schéma pour la mise à jour d'un utilisateur."""
    nom: Optional[str] = Field(None, min_length=2, max_length=50)
    prenom: Optional[str] = Field(None, min_length=2, max_length=50)
    telephone: Optional[str] = Field(None, min_length=8, max_length=20)
    adresse: Optional[str] = None
    photo_url: Optional[str] = None
    preferences: Optional[dict] = None


class UserResponse(BaseResponseSchema):
    """Schéma de réponse pour un utilisateur."""
    email: EmailStr
    nom: str
    prenom: str
    telephone: str
    role: UserRole
    is_active: bool
    is_verified: bool
    date_inscription: datetime
    derniere_connexion: Optional[datetime] = None
    photo_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserList(BaseSchema):
    """Schéma pour la liste des utilisateurs."""
    total: int
    page: int
    size: int
    items: List[UserResponse]