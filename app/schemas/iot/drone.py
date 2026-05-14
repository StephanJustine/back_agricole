# from pydantic import BaseModel, Field
# from typing import Optional, List, Dict
# from datetime import datetime

# from ..base import BaseSchema, BaseResponseSchema

# class DroneBase(BaseSchema):
#     modele: str = Field(..., min_length=2, max_length=50)
#     numero_serie: Optional[str] = None

# class DroneCreate(DroneBase):
#     plan_vol: Optional[Dict] = None
#     zone_survolee: Optional[Dict] = None

# class DroneResponse(BaseResponseSchema, DroneBase):
#     date_mission: datetime
#     duree_vol: Optional[int]
#     altitude: Optional[float]
#     vitesse: Optional[float]
#     plan_vol: Dict
#     zone_survolee: Dict
#     surface_couverte: Optional[float]
#     images: List[str]
#     videos: List[str]
#     indice_ndvi: Optional[float]
#     indice_ndre: Optional[float]
#     zones_a_probleme: List[Dict]
#     observations: Optional[str]

# schemas/iot/drone.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..base import BaseSchema, BaseResponseSchema


class DroneBase(BaseSchema):
    """Schéma de base pour les drones"""
    modele: str = Field(..., min_length=2, max_length=50, description="Modèle du drone")
    numero_serie: Optional[str] = Field(None, max_length=50, description="Numéro de série")
    duree_vol: Optional[int] = Field(None, ge=1, description="Durée de vol (minutes)")
    altitude: Optional[float] = Field(None, ge=0, le=400, description="Altitude (mètres)")
    vitesse: Optional[float] = Field(None, ge=0, description="Vitesse (m/s)")
    surface_couverte: Optional[float] = Field(None, ge=0, description="Surface couverte (hectares)")
    observations: Optional[str] = Field(None, max_length=1000, description="Observations")
    
    @field_validator('numero_serie')
    @classmethod
    def valider_numero_serie(cls, v: Optional[str]) -> Optional[str]:
        if v:
            import re
            if not re.match(r'^[A-Z0-9]{4,20}$', v.upper()):
                raise ValueError('Numéro de série invalide (4-20 caractères alphanumériques)')
        return v


class DroneCreate(DroneBase):
    """Schéma pour la création d'une mission drone"""
    plan_vol: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Plan de vol")
    zone_survolee: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Zone survolée")
    images: Optional[List[str]] = Field(default_factory=list, description="URLs des images")
    videos: Optional[List[str]] = Field(default_factory=list, description="URLs des vidéos")


class DroneResponse(BaseResponseSchema, DroneBase):
    """Schéma pour la réponse"""
    date_mission: datetime
    plan_vol: Dict[str, Any] = {}
    zone_survolee: Dict[str, Any] = {}
    images: List[str] = []
    videos: List[str] = []
    indice_ndvi: Optional[float] = None
    indice_ndre: Optional[float] = None
    zones_a_probleme: List[Dict[str, Any]] = []
    
    class Config:
        from_attributes = True