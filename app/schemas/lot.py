"""
Schémas Pydantic pour les lots.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime

from .base import BaseSchema, BaseResponseSchema
from ..models.enums import TypeLot


class LotBase(BaseSchema):
    """Schéma de base pour un lot."""
    type: TypeLot = Field(..., description="Type de lot")
    recolte_id: Optional[str] = Field(None, description="ID de la récolte source")
    parcelle_source: Optional[str] = Field(None, description="ID de la parcelle source")
    quantite_initiale: float = Field(..., gt=0, description="Quantité initiale")
    unite: str = Field(..., description="Unité (kg, L, piece)")
    date_production: date = Field(..., description="Date de production")
    date_peremption: Optional[date] = Field(None, description="Date de péremption")
    qualite: Optional[str] = Field(None, max_length=50, description="Qualité du lot")
    certificats: Optional[List[str]] = Field(default=[], description="Certificats")
    est_transformable: bool = Field(True, description="Peut être transformé")
    notes: Optional[str] = Field(None, max_length=500, description="Notes")
    
    @field_validator('date_production')
    @classmethod
    def validate_date(cls, v):
        if v > date.today():
            raise ValueError('La date de production ne peut pas être dans le futur')
        return v
    
    @field_validator('date_peremption')
    @classmethod
    def validate_date_peremption(cls, v, info):
        if v and info.data.get('date_production') and v < info.data['date_production']:
            raise ValueError('La date de péremption ne peut pas être antérieure à la date de production')
        return v


class LotCreate(LotBase):
    """Schéma pour la création d'un lot."""
    pass


class LotUpdate(BaseSchema):
    """Schéma pour la mise à jour d'un lot."""
    qualite: Optional[str] = None
    certificats: Optional[List[str]] = None
    est_transformable: Optional[bool] = None
    notes: Optional[str] = None


class LotResponse(BaseResponseSchema):
    """Schéma de réponse pour un lot."""
    code: str
    type: TypeLot
    recolte_id: Optional[str]
    parcelle_source: Optional[str]
    quantite_initiale: float
    quantite_restante: float
    unite: str
    date_production: date
    date_peremption: Optional[date]
    qualite: Optional[str]
    certificats: List[str]
    est_transformable: bool
    est_vendu: bool
    est_epuise: bool
    notes: Optional[str]
    quantite_utilisee: float
    taux_utilisation: float
    est_disponible: bool
    
    class Config:
        from_attributes = True


class LotDetailResponse(LotResponse):
    """Schéma de réponse détaillé pour un lot."""
    origine_complete: Dict[str, Any]
    transformations: List[Dict[str, Any]] = []
    ventes: List[Dict[str, Any]] = []
    stocks: List[Dict[str, Any]] = []


class LotList(BaseSchema):
    """Schéma pour la liste des lots."""
    total: int
    page: int
    size: int
    pages: int
    items: List[LotResponse]


class ScanLotResponse(BaseSchema):
    """Schéma pour la réponse de scan de code."""
    code: str
    type: TypeLot
    origine: Dict[str, Any]
    quantite_restante: float
    unite: str
    date_production: date
    date_peremption: Optional[date]
    qualite: Optional[str]
    est_disponible: bool