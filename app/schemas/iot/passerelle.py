# from pydantic import BaseModel, Field
# from typing import Optional, Dict
# from datetime import datetime

# from ..base import BaseSchema, BaseResponseSchema
# from ...models.enums import StatusPasserelle

# class PasserelleBase(BaseSchema):
#     nom: str = Field(..., min_length=2, max_length=50)
#     modele: Optional[str] = None
#     adresse_mac: str = Field(..., min_length=12, max_length=17)
#     localisation: Optional[str] = None
#     adresse_physique: Optional[str] = None

# class PasserelleCreate(PasserelleBase):
#     configuration: Optional[Dict] = None

# class PasserelleUpdate(BaseSchema):
#     nom: Optional[str] = None
#     adresse_ip: Optional[str] = None
#     firmware_version: Optional[str] = None
#     status: Optional[StatusPasserelle] = None
#     configuration: Optional[Dict] = None
#     notes: Optional[str] = None

# class PasserelleResponse(BaseResponseSchema, PasserelleBase):
#     adresse_ip: Optional[str]
#     firmware_version: Optional[str]
#     date_installation: datetime
#     derniere_connexion: Optional[datetime]
#     status: StatusPasserelle
#     est_connectee: bool
#     configuration: Dict
#     notes: Optional[str]

# schemas/iot/passerelle.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.enums import StatusPasserelle


class PasserelleBase(BaseModel):
    """Schéma de base pour les passerelles"""
    nom: str = Field(..., min_length=2, max_length=50, description="Nom de la passerelle")
    modele: Optional[str] = Field(None, max_length=100, description="Modèle")
    adresse_mac: str = Field(..., description="Adresse MAC (format: XX:XX:XX:XX:XX:XX)")
    adresse_ip: Optional[str] = Field(None, description="Adresse IP")
    firmware_version: Optional[str] = Field(None, max_length=50, description="Version du firmware")
    localisation: Optional[str] = Field(None, description="Localisation (latitude,longitude)")
    adresse_physique: Optional[str] = Field(None, max_length=255, description="Adresse physique")
    notes: Optional[str] = Field(None, max_length=500, description="Notes")
    
    @field_validator('adresse_mac')
    @classmethod
    def valider_mac(cls, v: str) -> str:
        """Valide le format de l'adresse MAC"""
        import re
        pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        if not re.match(pattern, v):
            raise ValueError('Format MAC invalide. Utilisez XX:XX:XX:XX:XX:XX')
        return v.upper()
    
    @field_validator('adresse_ip')
    @classmethod
    def valider_ip(cls, v: Optional[str]) -> Optional[str]:
        """Valide le format de l'adresse IP"""
        if v:
            import re
            pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if not re.match(pattern, v):
                raise ValueError('Format IP invalide')
            parts = v.split('.')
            if not all(0 <= int(p) <= 255 for p in parts):
                raise ValueError('Octets IP hors limites (0-255)')
        return v
    
    @field_validator('localisation')
    @classmethod
    def valider_localisation(cls, v: Optional[str]) -> Optional[str]:
        """Valide le format de localisation"""
        if v:
            import re
            pattern = r'^-?\d{1,3}\.\d+,-?\d{1,3}\.\d+$'
            if not re.match(pattern, v):
                raise ValueError('Format localisation invalide. Utilisez latitude,longitude')
        return v


class PasserelleCreate(PasserelleBase):
    """Schéma pour la création"""
    configuration: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PasserelleUpdate(BaseModel):
    """Schéma pour la mise à jour"""
    nom: Optional[str] = Field(None, min_length=2, max_length=50)
    adresse_ip: Optional[str] = None
    firmware_version: Optional[str] = None
    status: Optional[StatusPasserelle] = None
    configuration: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class PasserelleResponse(PasserelleBase):
    """Schéma pour la réponse"""
    id: str
    status: StatusPasserelle
    est_connectee: bool
    date_installation: datetime
    derniere_connexion: Optional[datetime] = None
    configuration: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True