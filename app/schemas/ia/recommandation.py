# from pydantic import BaseModel, Field
# from typing import Optional, Dict
# from datetime import datetime

# from ..base import BaseSchema, BaseResponseSchema
# from ...models.enums import TypeRecommandation

# class RecommandationBase(BaseSchema):
#     type: TypeRecommandation
#     parcelle_id: str
#     culture_id: Optional[str] = None
#     titre: str = Field(..., min_length=2, max_length=100)
#     message: str = Field(..., min_length=10)

# class RecommandationCreate(RecommandationBase):
#     priorite: int = Field(2, ge=1, le=3)
#     details: Optional[Dict] = None

# class RecommandationUpdate(BaseSchema):
#     est_lue: Optional[bool] = None
#     est_appliquee: Optional[bool] = None

# class RecommandationResponse(BaseResponseSchema, RecommandationBase):
#     priorite: int
#     details: Dict
#     est_lue: bool
#     est_appliquee: bool
#     date_emission: datetime
#     date_lecture: Optional[datetime]
#     date_action: Optional[datetime]

# schemas/ia/recommandation.py
"""
Schémas Pydantic pour les recommandations agronomiques.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

from ..base import BaseSchema, BaseResponseSchema
from app.models.enums import TypeRecommandation



class RecommandationBase(BaseSchema):
    """Schéma de base pour les recommandations"""
    type: TypeRecommandation
    parcelle_id: str = Field(..., description="ID de la parcelle concernée")
    culture_id: Optional[str] = Field(None, description="ID de la culture (optionnel)")
    titre: str = Field(..., min_length=3, max_length=100, description="Titre de la recommandation")
    message: str = Field(..., min_length=10, max_length=2000, description="Message détaillé")
    
    @field_validator('titre')
    @classmethod
    def valider_titre(cls, v: str) -> str:
        """Valide le titre (pas de caractères dangereux)"""
        if not v.strip():
            raise ValueError("Le titre ne peut pas être vide")
        return v.strip()
    
    @field_validator('message')
    @classmethod
    def valider_message(cls, v: str) -> str:
        """Valide le message"""
        if not v.strip():
            raise ValueError("Le message ne peut pas être vide")
        return v.strip()


class TypeRecommandation(str, Enum):
    """Types de recommandations agronomiques"""
    FERTILISATION = "fertilisation"
    TRAITEMENT = "traitement"
    CALENDRIER = "calendrier"
    ARROSAGE = "arrosage"


class RecommandationCreate(BaseModel):
    """Schéma pour la création d'une recommandation"""
    type: str = Field(..., description="Type de recommandation")
    parcelle_id: str = Field(..., description="ID de la parcelle concernée")
    culture_id: Optional[str] = Field(None, description="ID de la culture (optionnel)")
    titre: str = Field(..., min_length=3, max_length=100, description="Titre de la recommandation")
    message: str = Field(..., min_length=10, max_length=2000, description="Message détaillé")
    priorite: int = Field(2, ge=1, le=3, description="Priorité (1: Urgent, 2: Important, 3: Normal)")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Métadonnées supplémentaires")
    
    @field_validator('type')
    @classmethod
    def valider_type(cls, v: str) -> str:
        """Valide et normalise le type"""
        types_valides = ["fertilisation", "traitement", "calendrier", "arrosage"]
        v_normalise = v.lower()
        
        # Mapping des variantes
        mapping = {
            "irrigation": "arrosage",
            "irriguer": "arrosage",
            "engrais": "fertilisation",
            "pesticide": "traitement"
        }
        
        if v_normalise in mapping:
            return mapping[v_normalise]
        
        if v_normalise not in types_valides:
            raise ValueError(f"Type invalide. Types acceptés: {', '.join(types_valides)}")
        
        return v_normalise
    
    @field_validator('titre')
    @classmethod
    def valider_titre(cls, v: str) -> str:
        """Valide le titre"""
        if not v or not v.strip():
            raise ValueError("Le titre ne peut pas être vide")
        return v.strip()
    
    @field_validator('message')
    @classmethod
    def valider_message(cls, v: str) -> str:
        """Valide le message"""
        if not v or not v.strip():
            raise ValueError("Le message ne peut pas être vide")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "arrosage",
                "parcelle_id": "b8c2ade5-34c1-45d6-af3a-16c554f4b2b4",
                "culture_id": "votre_culture_id",
                "titre": "Alerte sécheresse",
                "message": "Risque de sécheresse détecté sur la parcelle Riz Ambatondrazaka. Arrosage recommandé immédiatement.",
                "priorite": 1,
                "details": {
                    "risque": "élevé",
                    "recommandation": "Arroser 20L/m²"
                }
            }
        }

class RecommandationUpdate(BaseSchema):
    """Schéma pour la mise à jour du statut"""
    est_lue: Optional[bool] = Field(None, description="Marquer comme lue")
    est_appliquee: Optional[bool] = Field(None, description="Marquer comme appliquée")
    
    @field_validator('est_lue', 'est_appliquee')
    @classmethod
    def valider_booleen(cls, v: Optional[bool]) -> Optional[bool]:
        """Validation des booléens"""
        return v


class RecommandationResponse(BaseResponseSchema, RecommandationBase):
    """Schéma pour la réponse"""
    priorite: int = Field(..., ge=1, le=3)
    details: Dict[str, Any] = Field(default_factory=dict)
    est_lue: bool = Field(default=False)
    est_appliquee: bool = Field(default=False)
    date_emission: datetime
    date_lecture: Optional[datetime] = None
    date_action: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "type": "IRRIGATION",
                "parcelle_id": "123e4567-e89b-12d3-a456-426614174000",
                "titre": "Alerte sécheresse",
                "message": "Risque de sécheresse détecté...",
                "priorite": 1,
                "est_lue": False,
                "est_appliquee": False,
                "date_emission": "2024-01-01T00:00:00",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }