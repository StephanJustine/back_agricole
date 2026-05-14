"""
Schémas Pydantic pour les récoltes.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime

from .base import BaseSchema, BaseResponseSchema
from ..models.enums import QualiteRecolte


class RecolteBase(BaseSchema):
    """Schéma de base pour une récolte."""
    culture_id: str = Field(..., description="ID de la culture")
    date_debut: date = Field(..., description="Date de début de récolte")
    date_fin: Optional[date] = Field(None, description="Date de fin de récolte")
    poids_frais: float = Field(..., gt=0, description="Poids frais (kg)")
    poids_sec: Optional[float] = Field(None, gt=0, description="Poids sec (kg)")
    humidite: Optional[float] = Field(None, ge=0, le=100, description="Taux d'humidité (%)")
    qualite: Optional[QualiteRecolte] = Field(QualiteRecolte.MOYENNE, description="Qualité")
    taux_gousses_vides: Optional[float] = Field(0, ge=0, le=100, description="Taux de gousses vides (%)")
    taux_gousses_abimees: Optional[float] = Field(0, ge=0, le=100, description="Taux de gousses abîmées (%)")
    taux_impuretes: Optional[float] = Field(0, ge=0, le=100, description="Taux d'impuretés (%)")
    poids_100_gousses: Optional[float] = Field(None, gt=0, description="Poids de 100 gousses (g)")
    poids_100_graines: Optional[float] = Field(None, gt=0, description="Poids de 100 graines (g)")
    nb_gousses_par_plant: Optional[int] = Field(None, ge=0, description="Nombre moyen de gousses par plant")
    nb_sacs: Optional[int] = Field(None, ge=0, description="Nombre de sacs")
    observations: Optional[str] = Field(None, max_length=500, description="Observations")
    
    @field_validator('date_fin')
    @classmethod
    def validate_dates(cls, v, info):
        """Validation des dates"""
        if v and info.data.get('date_debut') and v < info.data['date_debut']:
            raise ValueError('La date de fin ne peut pas être antérieure à la date de début')
        return v


class RecolteCreate(RecolteBase):
    """Schéma pour la création d'une récolte."""
    pass


class RecolteUpdate(BaseSchema):
    """Schéma pour la mise à jour d'une récolte."""
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    poids_frais: Optional[float] = None
    poids_sec: Optional[float] = None
    humidite: Optional[float] = None
    qualite: Optional[QualiteRecolte] = None
    taux_gousses_vides: Optional[float] = None
    taux_gousses_abimees: Optional[float] = None
    taux_impuretes: Optional[float] = None
    observations: Optional[str] = None
    nb_sacs: Optional[int] = None


class RecolteResponse(BaseResponseSchema):
    """Schéma de réponse pour une récolte."""
    culture_id: str
    culture_nom: Optional[str] = None
    parcelle_nom: Optional[str] = None
    parcelle_type: Optional[str] = None
    code: Optional[str]
    date_debut: date
    date_fin: Optional[date]
    poids_frais: float
    poids_sec: Optional[float]
    humidite: Optional[float]
    qualite: QualiteRecolte
    taux_gousses_vides: float
    taux_gousses_abimees: float
    taux_impuretes: float
    poids_100_gousses: Optional[float]
    poids_100_graines: Optional[float]
    nb_gousses_par_plant: Optional[int]
    nb_sacs: Optional[int]
    observations: Optional[str]
    photos: List[str] = []
    rendement_kg_ha: Optional[float]
    perte_poids: float
    qualite_note: int
    
    class Config:
        from_attributes = True


class RecolteDetailResponse(RecolteResponse):
    """Schéma de réponse détaillé pour une récolte."""
    lots: List[Dict[str, Any]] = []
    culture_details: Optional[Dict[str, Any]] = None


class RecolteList(BaseSchema):
    """Schéma pour la liste des récoltes."""
    total: int
    page: int
    size: int
    pages: int
    items: List[RecolteResponse]


class ComparaisonRecolte(BaseSchema):
    """Schéma pour la comparaison des récoltes."""
    amelioration: Dict[str, Any]
    traditionnelle: Dict[str, Any]
    ecart: Dict[str, Any]
    analyse: str