from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime

from ..base import BaseSchema, BaseResponseSchema

class BaliseGPSBase(BaseSchema):
    code: str = Field(..., min_length=3, max_length=50)
    lot_id: Optional[str] = None
    modele: Optional[str] = None

class BaliseGPSCreate(BaliseGPSBase):
    position: Optional[str] = None

class BaliseGPSUpdate(BaseSchema):
    lot_id: Optional[str] = None
    position: Optional[str] = None
    vitesse: Optional[float] = None
    batterie: Optional[float] = None
    alerte: Optional[bool] = None

class BaliseGPSResponse(BaseResponseSchema, BaliseGPSBase):
    position: Optional[str]
    altitude: Optional[float]
    vitesse: Optional[float]
    cap: Optional[float]
    derniere_position: Optional[str]
    derniere_mise_a_jour: Optional[datetime]
    temperature: Optional[float]
    humidite: Optional[float]
    batterie: Optional[float]
    signal: Optional[int]
    choc: bool
    alerte: bool
    historique_positions: List[Dict]
    alertes: List[Dict]