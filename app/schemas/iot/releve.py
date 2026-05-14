# from pydantic import BaseModel, Field
# from typing import Optional
# from datetime import datetime

# from ..base import BaseSchema, BaseResponseSchema

# class ReleveCapteurBase(BaseSchema):
#     capteur_id: str
#     valeur: float

# class ReleveCapteurCreate(ReleveCapteurBase):
#     batterie: Optional[float] = None
#     signal: Optional[int] = None
#     temperature_interne: Optional[float] = None

# class ReleveCapteurResponse(BaseResponseSchema, ReleveCapteurBase):
#     timestamp: datetime
#     batterie: Optional[float]
#     signal: Optional[int]
#     temperature_interne: Optional[float]
#     est_valide: bool
#     erreur: Optional[str]

# schemas/iot/releve.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

from ..base import BaseSchema, BaseResponseSchema


class ReleveCapteurBase(BaseSchema):
    """Schéma de base pour les relevés"""
    capteur_id: str = Field(..., description="ID du capteur")
    valeur: float = Field(..., description="Valeur mesurée")


class ReleveCapteurCreate(ReleveCapteurBase):
    """Schéma pour la création d'un relevé"""
    batterie: Optional[float] = Field(None, ge=0, le=100, description="Niveau de batterie (%)")
    signal: Optional[int] = Field(None, ge=0, le=100, description="Qualité du signal (%)")
    temperature_interne: Optional[float] = Field(None, description="Température interne (°C)")
    
    @field_validator('valeur')
    @classmethod
    def valider_valeur(cls, v: float) -> float:
        """Valide la valeur mesurée"""
        if v is None:
            raise ValueError("La valeur ne peut pas être nulle")
        return v


class ReleveCapteurResponse(BaseResponseSchema, ReleveCapteurBase):
    """Schéma pour la réponse"""
    timestamp: datetime
    batterie: Optional[float] = None
    signal: Optional[int] = None
    temperature_interne: Optional[float] = None
    est_valide: bool = True
    erreur: Optional[str] = None
    
    class Config:
        from_attributes = True