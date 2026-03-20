from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

from ..base import BaseSchema, BaseResponseSchema

class DroneBase(BaseSchema):
    modele: str = Field(..., min_length=2, max_length=50)
    numero_serie: Optional[str] = None

class DroneCreate(DroneBase):
    plan_vol: Optional[Dict] = None
    zone_survolee: Optional[Dict] = None

class DroneResponse(BaseResponseSchema, DroneBase):
    date_mission: datetime
    duree_vol: Optional[int]
    altitude: Optional[float]
    vitesse: Optional[float]
    plan_vol: Dict
    zone_survolee: Dict
    surface_couverte: Optional[float]
    images: List[str]
    videos: List[str]
    indice_ndvi: Optional[float]
    indice_ndre: Optional[float]
    zones_a_probleme: List[Dict]
    observations: Optional[str]