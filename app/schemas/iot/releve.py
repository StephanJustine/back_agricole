from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from ..base import BaseSchema, BaseResponseSchema

class ReleveCapteurBase(BaseSchema):
    capteur_id: str
    valeur: float

class ReleveCapteurCreate(ReleveCapteurBase):
    batterie: Optional[float] = None
    signal: Optional[int] = None
    temperature_interne: Optional[float] = None

class ReleveCapteurResponse(BaseResponseSchema, ReleveCapteurBase):
    timestamp: datetime
    batterie: Optional[float]
    signal: Optional[int]
    temperature_interne: Optional[float]
    est_valide: bool
    erreur: Optional[str]