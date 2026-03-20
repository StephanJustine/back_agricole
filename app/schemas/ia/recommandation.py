from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

from ..base import BaseSchema, BaseResponseSchema
from ...models.enums import TypeRecommandation

class RecommandationBase(BaseSchema):
    type: TypeRecommandation
    parcelle_id: str
    culture_id: Optional[str] = None
    titre: str = Field(..., min_length=2, max_length=100)
    message: str = Field(..., min_length=10)

class RecommandationCreate(RecommandationBase):
    priorite: int = Field(2, ge=1, le=3)
    details: Optional[Dict] = None

class RecommandationUpdate(BaseSchema):
    est_lue: Optional[bool] = None
    est_appliquee: Optional[bool] = None

class RecommandationResponse(BaseResponseSchema, RecommandationBase):
    priorite: int
    details: Dict
    est_lue: bool
    est_appliquee: bool
    date_emission: datetime
    date_lecture: Optional[datetime]
    date_action: Optional[datetime]