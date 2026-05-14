# from pydantic import BaseModel, Field
# from typing import Optional, Dict
# from datetime import datetime

# from ..base import BaseSchema, BaseResponseSchema
# from ...models.enums import StatusEntrainement

# class EntrainementBase(BaseSchema):
#     modele_id: str
#     dataset_id: str

# class EntrainementCreate(EntrainementBase):
#     params: Optional[Dict] = None

# class EntrainementUpdate(BaseSchema):
#     status: Optional[StatusEntrainement] = None
#     precision: Optional[float] = None
#     rappel: Optional[float] = None
#     f1_score: Optional[float] = None
#     logs: Optional[str] = None

# class EntrainementResponse(BaseResponseSchema, EntrainementBase):
#     date_debut: datetime
#     date_fin: Optional[datetime]
#     precision: Optional[float]
#     rappel: Optional[float]
#     f1_score: Optional[float]
#     mae: Optional[float]
#     rmse: Optional[float]
#     r2: Optional[float]
#     params: Dict
#     logs: Optional[str]
#     status: StatusEntrainement
#     duree: Optional[float]  # minutes

# schemas/ia/entrainement.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.enums import StatusEntrainement


class EntrainementBase(BaseModel):
    """Schéma de base pour les entraînements"""
    modele_id: str = Field(..., description="ID du modèle IA")
    dataset_id: str = Field(..., description="ID du dataset")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Paramètres d'entraînement")


class EntrainementCreate(EntrainementBase):
    """Schéma pour la création"""
    precision: Optional[float] = Field(None, ge=0, le=1)
    rappel: Optional[float] = Field(None, ge=0, le=1)
    f1_score: Optional[float] = Field(None, ge=0, le=1)
    mae: Optional[float] = Field(None, ge=0)
    rmse: Optional[float] = Field(None, ge=0)
    r2: Optional[float] = Field(None, ge=0, le=1)


class EntrainementUpdate(BaseModel):
    """Schéma pour la mise à jour"""
    precision: Optional[float] = Field(None, ge=0, le=1)
    rappel: Optional[float] = Field(None, ge=0, le=1)
    f1_score: Optional[float] = Field(None, ge=0, le=1)
    mae: Optional[float] = Field(None, ge=0)
    rmse: Optional[float] = Field(None, ge=0)
    r2: Optional[float] = Field(None, ge=0, le=1)
    params: Optional[Dict[str, Any]] = None
    logs: Optional[str] = None
    status: Optional[StatusEntrainement] = None


class EntrainementResponse(EntrainementBase):
    """Schéma pour la réponse"""
    id: str
    date_debut: datetime
    date_fin: Optional[datetime] = None
    precision: Optional[float] = None
    rappel: Optional[float] = None
    f1_score: Optional[float] = None
    mae: Optional[float] = None
    rmse: Optional[float] = None
    r2: Optional[float] = None
    logs: Optional[str] = None
    status: StatusEntrainement
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EntrainementListResponse(BaseModel):
    """Schéma pour la liste paginée"""
    total: int
    page: int
    size: int
    pages: int
    items: List[EntrainementResponse]