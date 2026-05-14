"""
Schémas Pydantic pour les mesures.
"""
from pydantic import BaseModel, Field, field_validator, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import re

from .base import BaseSchema, BaseResponseSchema


class MesureBase(BaseSchema):
    """Schéma de base pour une mesure."""
    culture_id: str = Field(..., description="ID de la culture")
    date_mesure: date = Field(..., description="Date de la mesure")
    hauteur_moyenne: Optional[float] = Field(None, ge=0, le=200, description="Hauteur moyenne (cm)")
    nb_feuilles_moyen: Optional[int] = Field(None, ge=0, le=100, description="Nombre moyen de feuilles")
    nb_fleurs_moyen: Optional[int] = Field(None, ge=0, le=500, description="Nombre moyen de fleurs")
    nb_gousses_moyen: Optional[int] = Field(None, ge=0, le=200, description="Nombre moyen de gousses")
    diametre_tige: Optional[float] = Field(None, ge=0, le=10, description="Diamètre de la tige (cm)")
    indice_vigueur: Optional[int] = Field(None, ge=1, le=5, description="Indice de vigueur (1-5)")
    couleur_feuillage: Optional[str] = Field(None, description="Couleur du feuillage")
    stress_hydrique: Optional[float] = Field(None, ge=0, le=100, description="Stress hydrique (%)")
    photo_url: Optional[str] = Field(None, description="URL de la photo principale")
    observations: Optional[str] = Field(None, max_length=500, description="Observations")
    
    @field_validator('date_mesure')
    @classmethod
    def validate_date(cls, v):
        """Validation de la date de mesure."""
        if v > date.today():
            raise ValueError('La date de mesure ne peut pas être dans le futur')
        return v
    
    @field_validator('couleur_feuillage')
    @classmethod
    def validate_couleur(cls, v):
        """Validation de la couleur du feuillage."""
        if v:
            couleurs_valides = ['vert_clair', 'vert_fonce', 'jaunâtre', 'jaune', 'brun']
            if v.lower() not in couleurs_valides:
                raise ValueError(f'Couleur invalide. Choisissez parmi: {couleurs_valides}')
        return v


class MesureCreate(MesureBase):
    """Schéma pour la création d'une mesure."""
    pass


class MesureUpdate(BaseSchema):
    """Schéma pour la mise à jour d'une mesure."""
    hauteur_moyenne: Optional[float] = None
    nb_feuilles_moyen: Optional[int] = None
    nb_fleurs_moyen: Optional[int] = None
    nb_gousses_moyen: Optional[int] = None
    indice_vigueur: Optional[int] = None
    couleur_feuillage: Optional[str] = None
    stress_hydrique: Optional[float] = None
    photo_url: Optional[str] = None
    observations: Optional[str] = None


class MesureResponse(BaseResponseSchema):
    """Schéma de réponse pour une mesure."""
    culture_id: str
    culture_nom: Optional[str] = None
    date_mesure: date
    hauteur_moyenne: Optional[float]
    nb_feuilles_moyen: Optional[int]
    nb_fleurs_moyen: Optional[int]
    nb_gousses_moyen: Optional[int]
    diametre_tige: Optional[float]
    indice_vigueur: Optional[int]
    couleur_feuillage: Optional[str]
    stress_hydrique: Optional[float]
    photo_url: Optional[str]
    photos: List[str] = []
    observations: Optional[str]
    age_culture: int
    date_saisie: datetime
    
    class Config:
        from_attributes = True


class MesureList(BaseSchema):
    """Schéma pour la liste des mesures."""
    total: int
    page: int
    size: int
    pages: int
    items: List[MesureResponse]


class GraphiqueCroissance(BaseSchema):
    """Schéma pour les données du graphique de croissance."""
    dates: List[str]
    hauteurs: List[float]
    feuilles: List[int]
    fleurs: List[int]
    gousses: List[int]
    vigueur: List[int]


class MesureBulkCreate(BaseModel):
    culture_id: str
    date_mesure: date

    hauteur_moyenne: Optional[float] = None
    nb_feuilles_moyen: Optional[int] = None
    nb_fleurs_moyen: Optional[int] = None
    nb_gousses_moyen: Optional[int] = None
    diametre_tige: Optional[float] = None

    indice_vigueur: Optional[int] = Field(None, ge=1, le=5)
    couleur_feuillage: Optional[str] = None

    stress_hydrique: Optional[float] = Field(None, ge=0, le=100)

    photo_url: Optional[str] = None
    observations: Optional[str] = None

    @validator("couleur_feuillage")
    def validate_couleur(cls, v):
        if v is None:
            return v

        allowed = ["vert_clair", "vert_fonce", "jaunâtre", "jaune", "brun"]
        if v not in allowed:
            raise ValueError(f"Couleur invalide. Choisissez parmi: {allowed}")
        return v