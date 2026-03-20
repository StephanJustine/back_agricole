from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

from ..base import BaseSchema, BaseResponseSchema

class PredictionBase(BaseSchema):
    modele_id: str
    parcelle_id: Optional[str] = None
    culture_id: Optional[str] = None

class PredictionCreate(PredictionBase):
    rendement_estime: float
    intervalle_inferieur: Optional[float] = None
    intervalle_superieur: Optional[float] = None
    probabilite: Optional[float] = None
    facteurs_influents: Optional[Dict] = None

class PredictionResponse(BaseResponseSchema, PredictionBase):
    date_prediction: datetime
    rendement_estime: float
    intervalle_inferieur: Optional[float]
    intervalle_superieur: Optional[float]
    probabilite: Optional[float]
    facteurs_influents: Dict
    confiance: Optional[float]
    est_valide: bool