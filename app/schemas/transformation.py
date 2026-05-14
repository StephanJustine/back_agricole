"""
Schémas Pydantic pour les transformations.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime

from .base import BaseSchema, BaseResponseSchema
from ..models.enums import TypeTransformation


class RecetteSavon(BaseSchema):
    """Schéma pour la recette de savon."""
    huile_l: float = Field(..., gt=0, description="Quantité d'huile en litres")
    surgraissage: float = Field(5, ge=0, le=20, description="Pourcentage de surgraissage")
    additifs: Optional[List[str]] = Field(default=[], description="Additifs (miel, citron, etc.)")
    parfum: Optional[str] = Field(None, description="Parfum")


class TransformationBase(BaseSchema):
    """Schéma de base pour une transformation."""
    type: TypeTransformation = Field(..., description="Type de transformation")
    lot_entree_id: str = Field(..., description="ID du lot entrant")
    date_transformation: date = Field(..., description="Date de transformation")
    responsable_id: Optional[str] = Field(None, description="ID du responsable")
    observations: Optional[str] = Field(None, max_length=500, description="Observations")
    
    @field_validator('date_transformation')
    @classmethod
    def validate_date(cls, v):
        if v > date.today():
            raise ValueError('La date ne peut pas être dans le futur')
        return v


class TransformationHuileCreate(TransformationBase):
    """Schéma pour la création d'une transformation en huile."""
    quantite_entree: float = Field(..., gt=0, description="Quantité d'arachide à transformer (kg)")
    quantite_sortie: float = Field(..., gt=0, description="Quantité d'huile produite (L)")


class TransformationSavonCreate(TransformationBase):
    """Schéma pour la création d'une transformation en savon."""
    recette: RecetteSavon = Field(..., description="Recette du savon")
    quantite_sortie: Optional[int] = Field(None, description="Nombre de savons produits")


class TransformationUpdate(BaseSchema):
    """Schéma pour la mise à jour d'une transformation."""
    quantite_sortie: Optional[float] = None
    observations: Optional[str] = None


class TransformationResponse(BaseResponseSchema):
    """Schéma de réponse pour une transformation."""
    type: TypeTransformation
    lot_entree_id: str
    lot_entree_code: Optional[str] = None
    lot_sortie_id: Optional[str]
    lot_sortie_code: Optional[str] = None
    date_transformation: date
    responsable_id: Optional[str]
    responsable_nom: Optional[str] = None
    quantite_entree: float
    quantite_sortie: Optional[float]
    rendement: Optional[float]
    recette: Optional[Dict[str, Any]]
    observations: Optional[str]
    
    class Config:
        from_attributes = True


class TransformationList(BaseSchema):
    """Schéma pour la liste des transformations."""
    total: int
    page: int
    size: int
    pages: int
    items: List[TransformationResponse]


class CalculSavonResponse(BaseSchema):
    """Schéma pour le calcul de recette de savon."""
    huile_kg: float
    soude_kg: float
    eau_kg: float
    poids_total: float
    nb_savons: int
    surgraissage: float
    additifs: Optional[List[str]] = None
    parfum: Optional[str] = None