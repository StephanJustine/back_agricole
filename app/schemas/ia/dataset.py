from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

from ..base import BaseSchema, BaseResponseSchema
from ...models.enums import SourceDataset

class DatasetBase(BaseSchema):
    nom: str = Field(..., min_length=2, max_length=100)
    source: SourceDataset = SourceDataset.TERRAIN
    description: Optional[str] = None

class DatasetCreate(DatasetBase):
    features: Optional[List[str]] = []
    labels: Optional[List[str]] = []
    url_data: Optional[str] = None

class DatasetUpdate(BaseSchema):
    nom: Optional[str] = None
    nb_echantillons: Optional[int] = None
    description: Optional[str] = None

class DatasetResponse(BaseResponseSchema, DatasetBase):
    nb_echantillons: int
    features: List[str]
    labels: List[str]
    url_data: Optional[str]
    taille: Optional[str]