from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime

from ..base import BaseSchema, BaseResponseSchema

class InferenceBase(BaseSchema):
    modele_id: str
    culture_id: Optional[str] = None

class InferenceCreate(InferenceBase):
    image_url: str
    resultat: str
    confidence: float
    bbox: Optional[Dict] = None
    segmentation: Optional[Dict] = None

class InferenceResponse(BaseResponseSchema, InferenceBase):
    image_url: str
    resultat: str
    confidence: float
    bbox: Optional[Dict]
    segmentation: Optional[Dict]
    temps_inference: Optional[float]
    date_inference: datetime
    notes: Optional[str]