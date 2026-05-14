# from pydantic import BaseModel, Field
# from typing import Optional, Dict
# from datetime import datetime

# from ..base import BaseSchema, BaseResponseSchema

# class PredictionBase(BaseSchema):
#     modele_id: str
#     parcelle_id: Optional[str] = None
#     culture_id: Optional[str] = None

# class PredictionCreate(PredictionBase):
#     rendement_estime: float
#     intervalle_inferieur: Optional[float] = None
#     intervalle_superieur: Optional[float] = None
#     probabilite: Optional[float] = None
#     facteurs_influents: Optional[Dict] = None

# class PredictionResponse(BaseResponseSchema, PredictionBase):
#     date_prediction: datetime
#     rendement_estime: float
#     intervalle_inferieur: Optional[float]
#     intervalle_superieur: Optional[float]
#     probabilite: Optional[float]
#     facteurs_influents: Dict
#     confiance: Optional[float]
#     est_valide: bool

# schemas/ia/prediction.py
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any
from datetime import datetime


class PredictionBase(BaseModel):
    """Schéma de base pour les prédictions"""
    modele_id: str
    parcelle_id: Optional[str] = None
    culture_id: Optional[str] = None
    rendement_estime: Optional[float] = Field(None, ge=0)
    probabilite: Optional[float] = Field(None, ge=0, le=100)
    facteurs_influents: Optional[Dict[str, Any]] = None
    donnees_utilisees: Optional[Dict[str, Any]] = None


class PredictionCreate(PredictionBase):
    """Schéma pour la création d'une prédiction"""
    marge_precision: Optional[float] = Field(0.15, ge=0, le=0.5, description="Marge d'erreur pour le calcul des intervalles")
    
    @model_validator(mode='after')
    def validate_rendement(self) -> 'PredictionCreate':
        """Validation supplémentaire"""
        if self.rendement_estime is not None and self.rendement_estime < 0:
            raise ValueError("Le rendement estimé ne peut pas être négatif")
        return self


class PredictionUpdate(BaseModel):
    """Schéma pour la mise à jour d'une prédiction"""
    rendement_estime: Optional[float] = Field(None, ge=0)
    intervalle_inferieur: Optional[float] = Field(None, ge=0)
    intervalle_superieur: Optional[float] = Field(None, ge=0)
    probabilite: Optional[float] = Field(None, ge=0, le=100)
    confiance: Optional[float] = Field(None, ge=0, le=100)
    est_valide: Optional[bool] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "rendement_estime": 4500.5,
                "confiance": 85.5,
                "est_valide": True
            }
        }


class PredictionResponse(PredictionBase):
    """Schéma pour la réponse d'une prédiction"""
    id: str
    intervalle_inferieur: Optional[float] = None
    intervalle_superieur: Optional[float] = None
    probabilite: Optional[float] = None
    confiance: Optional[float] = None
    est_valide: bool = True
    date_prediction: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "modele_id": "123e4567-e89b-12d3-a456-426614174001",
                "parcelle_id": "123e4567-e89b-12d3-a456-426614174002",
                "culture_id": "123e4567-e89b-12d3-a456-426614174003",
                "rendement_estime": 4500.5,
                "intervalle_inferieur": 3825.43,
                "intervalle_superieur": 5175.57,
                "probabilite": 85.0,
                "confiance": 85.0,
                "est_valide": True,
                "date_prediction": "2024-01-01T00:00:00",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }