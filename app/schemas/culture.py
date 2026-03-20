"""
Schémas Pydantic pour les cultures.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime

from .base import BaseSchema, BaseResponseSchema
from ..models.enums import StadeCulture


class CultureBase(BaseSchema):
    """Schéma de base pour une culture."""
    parcelle_id: str = Field(..., description="ID de la parcelle")
    date_debut: date = Field(..., description="Date de début du semis")
    variete: str = Field(..., min_length=2, max_length=100, description="Variété d'arachide")
    type_semence: Optional[str] = Field(None, description="Type de semence (certifiee, fermiere)")
    densite_semis: Optional[int] = Field(None, ge=50000, le=300000, description="Densité de semis (plants/ha)")
    ecartement_lignes: Optional[int] = Field(None, ge=30, le=60, description="Écartement entre lignes (cm)")
    ecartement_poquets: Optional[int] = Field(None, ge=10, le=25, description="Écartement sur ligne (cm)")
    observations: Optional[str] = Field(None, max_length=500, description="Observations")
    
    @field_validator('date_debut')
    @classmethod
    def validate_date_debut(cls, v):
        """Validation de la date de début."""
        if v > date.today():
            raise ValueError('La date de début ne peut pas être dans le futur')
        return v
    
    @field_validator('variete')
    @classmethod
    def validate_variete(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError('La variété doit contenir au moins 2 caractères')
        return v.strip() if v else v


class CultureCreate(CultureBase):
    """Schéma pour la création d'une culture."""
    pass


class CultureUpdate(BaseSchema):
    """Schéma pour la mise à jour d'une culture."""
    stade: Optional[StadeCulture] = None
    sante: Optional[int] = Field(None, ge=1, le=10)
    vigueur: Optional[int] = Field(None, ge=1, le=10)
    observations: Optional[str] = None
    date_fin_prevue: Optional[date] = None
    date_fin_reelle: Optional[date] = None


class CultureResponse(BaseResponseSchema):
    """Schéma de réponse pour une culture."""
    parcelle_id: str
    parcelle_nom: Optional[str] = None
    date_debut: date
    date_fin_prevue: Optional[date]
    date_fin_reelle: Optional[date]
    variete: str
    type_semence: Optional[str]
    densite_semis: Optional[int]
    ecartement_lignes: Optional[int]
    ecartement_poquets: Optional[int]
    stade: StadeCulture
    sante: int
    vigueur: int
    code: Optional[str]
    duree_ecoulee: int
    progression: int
    jours_restants: int
    stade_description: str
    observations: Optional[str]
    photos: List[str] = []
    
    class Config:
        from_attributes = True


class CultureDetailResponse(CultureResponse):
    """Schéma de réponse détaillé pour une culture."""
    mesures: List[Dict[str, Any]] = []
    maladies: List[Dict[str, Any]] = []
    recolte: Optional[Dict[str, Any]] = None


class CultureList(BaseSchema):
    """Schéma pour la liste des cultures."""
    total: int
    page: int
    size: int
    pages: int
    items: List[CultureResponse]