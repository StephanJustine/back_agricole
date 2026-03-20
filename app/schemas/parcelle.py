"""
Schémas Pydantic pour les parcelles.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re

from .base import BaseSchema, BaseResponseSchema
from ..models.enums import TypeParcelle


class ParcelleBase(BaseSchema):
    """Schéma de base pour une parcelle."""
    nom: str = Field(..., min_length=2, max_length=100)
    superficie: float = Field(..., gt=0, le=1000)
    type: TypeParcelle
    region: Optional[str] = Field(None, max_length=100)
    commune: Optional[str] = Field(None, max_length=100)
    lieu_dit: Optional[str] = Field(None, max_length=200)
    coord_gps: Optional[str] = Field(None, description="Coordonnées GPS au format: latitude,longitude")
    altitude: Optional[float] = Field(None, ge=0, le=5000)
    type_sol: Optional[str] = Field(None, max_length=50)
    exposition: Optional[str] = Field(None, max_length=20)
    pente: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=500)
    
    @field_validator('coord_gps')
    @classmethod
    def validate_gps(cls, v):
        """Validation des coordonnées GPS."""
        # Si None ou vide, on ignore
        if v is None or v == "" or v == "string":
            return None
        
        # Nettoyer la chaîne
        v = v.strip()
        
        # Vérifier le format
        pattern = r'^-?\d+\.?\d*,-?\d+\.?\d*$'
        if not re.match(pattern, v):
            raise ValueError('Format GPS invalide. Utilisez: latitude,longitude (ex: -18.914,47.531)')
        
        # Vérifier les valeurs
        try:
            lat, lon = map(float, v.split(','))
            if not (-90 <= lat <= 90):
                raise ValueError('Latitude doit être entre -90 et 90')
            if not (-180 <= lon <= 180):
                raise ValueError('Longitude doit être entre -180 et 180')
        except:
            raise ValueError('Coordonnées GPS invalides')
        
        return v
    
    @field_validator('superficie')
    @classmethod
    def validate_superficie(cls, v):
        if v <= 0:
            raise ValueError('La superficie doit être positive')
        return v


class ParcelleCreate(ParcelleBase):
    """Schéma pour la création d'une parcelle."""
    pass


class ParcelleUpdate(BaseSchema):
    """Schéma pour la mise à jour d'une parcelle."""
    nom: Optional[str] = Field(None, min_length=2, max_length=100)
    type: Optional[TypeParcelle] = None
    region: Optional[str] = None
    commune: Optional[str] = None
    lieu_dit: Optional[str] = None
    coord_gps: Optional[str] = None
    type_sol: Optional[str] = None
    exposition: Optional[str] = None
    pente: Optional[str] = None
    notes: Optional[str] = None
    photo_principale: Optional[str] = None
    is_active: Optional[bool] = None


class ParcelleResponse(BaseResponseSchema):
    """Schéma de réponse pour une parcelle."""
    nom: str
    superficie: float
    type: TypeParcelle
    code: Optional[str]
    region: Optional[str]
    commune: Optional[str]
    lieu_dit: Optional[str]
    coord_gps: Optional[str]
    altitude: Optional[float]
    type_sol: Optional[str]
    exposition: Optional[str]
    pente: Optional[str]
    proprietaire_id: str
    is_active: bool
    is_cultivee: bool = False
    photo_principale: Optional[str]
    photos: List[str] = []
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class ParcelleDetailResponse(ParcelleResponse):
    """Schéma de réponse détaillé pour une parcelle."""
    analyses_sol: List[dict] = []
    travaux: List[dict] = []
    cultures: List[dict] = []
    capteurs: List[dict] = []
    predictions: List[dict] = []
    recommandations: List[dict] = []


class ParcelleList(BaseSchema):
    """Schéma pour la liste des parcelles."""
    total: int
    page: int
    size: int
    pages: int
    items: List[ParcelleResponse]