from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

from ..base import BaseSchema, BaseResponseSchema
from ...models.enums import StatusEntrainement

class EntrainementBase(BaseSchema):
    modele_id: str
    dataset_id: str

class EntrainementCreate(EntrainementBase):
    params: Optional[Dict] = None

class EntrainementUpdate(BaseSchema):
    status: Optional[StatusEntrainement] = None
    precision: Optional[float] = None
    rappel: Optional[float] = None
    f1_score: Optional[float] = None
    logs: Optional[str] = None

class EntrainementResponse(BaseResponseSchema, EntrainementBase):
    date_debut: datetime
    date_fin: Optional[datetime]
    precision: Optional[float]
    rappel: Optional[float]
    f1_score: Optional[float]
    mae: Optional[float]
    rmse: Optional[float]
    r2: Optional[float]
    params: Dict
    logs: Optional[str]
    status: StatusEntrainement
    duree: Optional[float]  # minutes