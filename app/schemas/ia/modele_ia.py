from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

from ..base import BaseSchema, BaseResponseSchema
from ...models.enums import TypeModeleIA

class ModeleIABase(BaseSchema):
    nom: str = Field(..., min_length=2, max_length=100)
    type: TypeModeleIA
    version: str = Field(..., min_length=1, max_length=20)
    framework: Optional[str] = None
    description: Optional[str] = None

class ModeleIACreate(ModeleIABase):
    path: Optional[str] = None
    parametres: Optional[Dict] = None

class ModeleIAUpdate(BaseSchema):
    nom: Optional[str] = None
    version: Optional[str] = None
    metriques: Optional[Dict] = None
    est_actif: Optional[bool] = None
    description: Optional[str] = None

class ModeleIAResponse(BaseResponseSchema, ModeleIABase):
    metriques: Optional[Dict] = None
    parametres: Optional[Dict] = None
    est_actif: bool
    est_pret: bool
    taille: Optional[str] = None