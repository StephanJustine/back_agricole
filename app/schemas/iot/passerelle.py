from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

from ..base import BaseSchema, BaseResponseSchema
from ...models.enums import StatusPasserelle

class PasserelleBase(BaseSchema):
    nom: str = Field(..., min_length=2, max_length=50)
    modele: Optional[str] = None
    adresse_mac: str = Field(..., min_length=12, max_length=17)
    localisation: Optional[str] = None
    adresse_physique: Optional[str] = None

class PasserelleCreate(PasserelleBase):
    configuration: Optional[Dict] = None

class PasserelleUpdate(BaseSchema):
    nom: Optional[str] = None
    adresse_ip: Optional[str] = None
    firmware_version: Optional[str] = None
    status: Optional[StatusPasserelle] = None
    configuration: Optional[Dict] = None
    notes: Optional[str] = None

class PasserelleResponse(BaseResponseSchema, PasserelleBase):
    adresse_ip: Optional[str]
    firmware_version: Optional[str]
    date_installation: datetime
    derniere_connexion: Optional[datetime]
    status: StatusPasserelle
    est_connectee: bool
    configuration: Dict
    notes: Optional[str]