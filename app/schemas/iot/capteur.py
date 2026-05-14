from pydantic import BaseModel, Field, validator
from typing import Optional, Dict
from datetime import datetime

from ..base import BaseSchema, BaseResponseSchema
from ...models.enums import TypeCapteur

class CapteurBase(BaseSchema):
    passerelle_id: str
    parcelle_id: Optional[str] = None
    code: Optional[str] = None
    type: TypeCapteur
    reference: Optional[str] = None
    precision: Optional[float] = None
    unite: Optional[str] = None

class CapteurCreate(CapteurBase):
    seuil_alerte_bas: Optional[float] = None
    seuil_alerte_haut: Optional[float] = None
    configuration: Optional[Dict] = None

class CapteurUpdate(BaseSchema):
    code: Optional[str] = None
    precision: Optional[float] = None
    seuil_alerte_bas: Optional[float] = None
    seuil_alerte_haut: Optional[float] = None
    est_actif: Optional[bool] = None
    configuration: Optional[Dict] = None

class CapteurResponse(BaseResponseSchema, CapteurBase):
    valeur_min: Optional[float]
    valeur_max: Optional[float]
    seuil_alerte_bas: Optional[float]
    seuil_alerte_haut: Optional[float]
    date_installation: datetime
    date_dernier_main: Optional[datetime]
    est_actif: bool
    derniere_valeur: Optional[float]
    derniere_mise_a_jour: Optional[datetime]
    configuration: Dict