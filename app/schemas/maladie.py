"""
Schémas Pydantic pour les maladies.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime

from .base import BaseSchema, BaseResponseSchema
from ..models.enums import TypeMaladie


class MaladieBase(BaseSchema):
    """Schéma de base pour une maladie."""
    culture_id: str = Field(..., description="ID de la culture")
    type: TypeMaladie = Field(..., description="Type de maladie")
    date_detection: date = Field(..., description="Date de détection")
    gravite: int = Field(3, ge=1, le=5, description="Gravité (1-5)")
    surface_touchee: Optional[float] = Field(None, ge=0, le=100, description="Surface touchée (%)")
    traitement_applique: Optional[str] = Field(None, description="Traitement appliqué")
    date_traitement: Optional[date] = Field(None, description="Date du traitement")
    observations: Optional[str] = Field(None, max_length=500, description="Observations")
    recommandations: Optional[str] = Field(None, description="Recommandations")
    photo_url: Optional[str] = Field(None, description="URL de la photo principale")
    
    @field_validator('date_detection')
    @classmethod
    def validate_date_detection(cls, v):
        """Validation de la date de détection."""
        if v > date.today():
            raise ValueError('La date de détection ne peut pas être dans le futur')
        return v
    
    @field_validator('date_traitement')
    @classmethod
    def validate_date_traitement(cls, v, info):
        """Validation de la date de traitement."""
        if v:
            # Récupérer date_detection depuis les valeurs
            data = info.data
            if 'date_detection' in data and v < data['date_detection']:
                raise ValueError('La date de traitement ne peut pas être antérieure à la détection')
            if v > date.today():
                raise ValueError('La date de traitement ne peut pas être dans le futur')
        return v


class MaladieCreate(MaladieBase):
    """Schéma pour la création d'une maladie."""
    pass


class MaladieUpdate(BaseSchema):
    """Schéma pour la mise à jour d'une maladie."""
    gravite: Optional[int] = Field(None, ge=1, le=5)
    traitement_applique: Optional[str] = None
    date_traitement: Optional[date] = None
    efficace: Optional[bool] = None
    est_resolu: Optional[bool] = None
    observations: Optional[str] = None
    recommandations: Optional[str] = None
    photo_url: Optional[str] = None


class MaladieResponse(BaseResponseSchema):
    """Schéma de réponse pour une maladie."""
    culture_id: str
    culture_nom: Optional[str] = None
    type: TypeMaladie
    date_detection: date
    gravite: int
    surface_touchee: Optional[float]
    traitement_applique: Optional[str]
    date_traitement: Optional[date]
    efficace: Optional[bool]
    est_resolu: bool
    date_guerison: Optional[date]
    observations: Optional[str]
    recommandations: Optional[str]
    photo_url: Optional[str]
    photos: List[str] = []
    est_critique: bool
    niveau_alerte: str
    alerte_envoyee: bool
    
    class Config:
        from_attributes = True


class MaladieDetailResponse(MaladieResponse):
    """Schéma de réponse détaillé pour une maladie."""
    culture_details: Optional[Dict[str, Any]] = None


class MaladieList(BaseSchema):
    """Schéma pour la liste des maladies."""
    total: int
    page: int
    size: int
    pages: int
    items: List[MaladieResponse]


class AlerteMaladie(BaseSchema):
    """Schéma pour les alertes de maladie."""
    maladie_id: str
    culture_id: str
    culture_nom: str
    parcelle_nom: str
    type: TypeMaladie
    gravite: int
    niveau_alerte: str
    surface_touchee: Optional[float]
    message: str
    recommandations: str
    date_detection: date