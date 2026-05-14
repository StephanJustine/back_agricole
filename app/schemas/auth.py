"""
Schémas Pydantic pour l'authentification.
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Any, Dict

from .user import UserResponse


class LoginRequest(BaseModel):
    """Schéma pour la demande de connexion."""
    email: EmailStr
    password: str
    remember_me: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "stephanson.stp@gmail.com",
                "password": "admin123",
                "remember_me": False
            }
        }


class LoginResponse(BaseModel):
    """Schéma pour la réponse de connexion."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]  # Changé de UserResponse à Dict pour éviter les problèmes de validation
    
    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    """Schéma pour la demande de rafraîchissement de token."""
    refresh_token: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
            }
        }


class RefreshTokenResponse(BaseModel):
    """Schéma pour la réponse de rafraîchissement de token."""
    access_token: str
    expires_in: int
    
    class Config:
        from_attributes = True


class ForgotPasswordRequest(BaseModel):
    """Schéma pour la demande de réinitialisation de mot de passe."""
    email: EmailStr
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "stephanson.stp@gmail.com"
            }
        }


class ForgotPasswordResponse(BaseModel):
    """Schéma pour la réponse de réinitialisation de mot de passe."""
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Si l'email existe, un lien de réinitialisation a été envoyé"
            }
        }


class ResetPasswordRequest(BaseModel):
    """Schéma pour la réinitialisation du mot de passe."""
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Vérifie que les mots de passe correspondent."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Les mots de passe ne correspondent pas')
        return v
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validation du mot de passe."""
        if len(v) < 8:
            raise ValueError('Le mot de passe doit contenir au moins 8 caractères')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset_token_123456",
                "new_password": "NouveauMotDePasse123",
                "confirm_password": "NouveauMotDePasse123"
            }
        }


class ChangePasswordRequest(BaseModel):
    """Schéma pour le changement de mot de passe."""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Vérifie que les mots de passe correspondent."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Les mots de passe ne correspondent pas')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "admin123",
                "new_password": "NouveauMotDePasse123",
                "confirm_password": "NouveauMotDePasse123"
            }
        }


class VerifyEmailRequest(BaseModel):
    """Schéma pour la vérification d'email."""
    token: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "verification_token_123456"
            }
        }


class VerifyEmailResponse(BaseModel):
    """Schéma pour la réponse de vérification d'email."""
    message: str
    verified: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Email vérifié avec succès",
                "verified": True
            }
        }


class TokenPayload(BaseModel):
    """Schéma pour le payload du token JWT."""
    sub: str
    exp: int
    type: str
    
    class Config:
        from_attributes = True