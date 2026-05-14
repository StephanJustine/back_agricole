# from pydantic import BaseModel, Field
# from typing import Optional, List, Dict
# from datetime import datetime

# from ..base import BaseSchema, BaseResponseSchema
# from ...models.enums import TypeModeleIA

# class ModeleIABase(BaseSchema):
#     nom: str = Field(..., min_length=2, max_length=100)
#     type: TypeModeleIA
#     version: str = Field(..., min_length=1, max_length=20)
#     framework: Optional[str] = None
#     description: Optional[str] = None

# class ModeleIACreate(ModeleIABase):
#     path: Optional[str] = None
#     parametres: Optional[Dict] = None

# class ModeleIAUpdate(BaseSchema):
#     nom: Optional[str] = None
#     version: Optional[str] = None
#     metriques: Optional[Dict] = None
#     est_actif: Optional[bool] = None
#     description: Optional[str] = None

# class ModeleIAResponse(BaseResponseSchema, ModeleIABase):
#     metriques: Optional[Dict] = None
#     parametres: Optional[Dict] = None
#     est_actif: bool
#     est_pret: bool
#     taille: Optional[str] = None


# schemas/ia/modele_ia.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.enums import TypeModeleIA


class ModeleIABase(BaseModel):
    """Schéma de base pour un modèle IA"""
    nom: str = Field(..., min_length=1, max_length=255)
    type: TypeModeleIA
    version: str = Field(..., min_length=1, max_length=50)
    framework: Optional[str] = Field(None, max_length=100)
    path: Optional[str] = Field(None, max_length=500)  # Au lieu de chemin_modele
    taille: Optional[str] = Field(None, max_length=50)
    metriques: Optional[Dict[str, Any]] = Field(default_factory=dict)
    parametres: Optional[Dict[str, Any]] = Field(default_factory=dict)
    est_actif: bool = True
    est_pret: bool = False
    description: Optional[str] = None


class ModeleIACreate(ModeleIABase):
    """Schéma pour la création d'un modèle IA"""
    pass


class ModeleIAUpdate(BaseModel):
    """Schéma pour la mise à jour d'un modèle IA"""
    nom: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[TypeModeleIA] = None
    version: Optional[str] = Field(None, min_length=1, max_length=50)
    framework: Optional[str] = Field(None, max_length=100)
    path: Optional[str] = Field(None, max_length=500)
    taille: Optional[str] = Field(None, max_length=50)
    metriques: Optional[Dict[str, Any]] = None
    parametres: Optional[Dict[str, Any]] = None
    est_actif: Optional[bool] = None
    est_pret: Optional[bool] = None
    description: Optional[str] = None


class ModeleIAResponse(ModeleIABase):
    """Schéma pour la réponse d'un modèle IA"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True