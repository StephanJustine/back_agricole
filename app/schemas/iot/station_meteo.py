from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

from ..base import BaseSchema, BaseResponseSchema

class StationMeteoBase(BaseSchema):
    parcelle_id: str

class StationMeteoCreate(StationMeteoBase):
    temperature: Optional[float] = None
    humidite: Optional[float] = None
    pression: Optional[float] = None
    pluie_24h: Optional[float] = None
    vent_moyen: Optional[float] = None

class StationMeteoUpdate(BaseSchema):
    temperature: Optional[float] = None
    temperature_min: Optional[float] = None
    temperature_max: Optional[float] = None
    humidite: Optional[float] = None
    pression: Optional[float] = None
    pluie_24h: Optional[float] = None
    pluie_mensuelle: Optional[float] = None
    vent_moyen: Optional[float] = None
    vent_rafale: Optional[float] = None
    direction_vent: Optional[str] = None
    luminosite: Optional[float] = None
    uv: Optional[float] = None
    previsions: Optional[Dict] = None

class StationMeteoResponse(BaseResponseSchema, StationMeteoBase):
    temperature: Optional[float]
    temperature_min: Optional[float]
    temperature_max: Optional[float]
    humidite: Optional[float]
    pression: Optional[float]
    pluie_24h: Optional[float]
    pluie_mensuelle: Optional[float]
    vent_moyen: Optional[float]
    vent_rafale: Optional[float]
    direction_vent: Optional[str]
    luminosite: Optional[float]
    uv: Optional[float]
    previsions: Dict
    date_maj: datetime