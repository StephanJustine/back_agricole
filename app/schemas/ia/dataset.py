# schemas/ia/dataset.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.enums import SourceDataset


class DatasetBase(BaseModel):
    """Schéma de base pour les datasets"""
    nom: str = Field(..., min_length=1, max_length=255)
    source: SourceDataset = SourceDataset.TERRAIN
    nb_echantillons: int = Field(0, ge=0)
    features: List[str] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)
    url_data: Optional[str] = Field(None, max_length=500)
    taille: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=1000)


class DatasetCreate(DatasetBase):
    """Schéma pour la création"""
    pass


class DatasetUpdate(BaseModel):
    """Schéma pour la mise à jour"""
    nom: Optional[str] = Field(None, min_length=1, max_length=255)
    source: Optional[SourceDataset] = None
    nb_echantillons: Optional[int] = Field(None, ge=0)
    features: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    url_data: Optional[str] = Field(None, max_length=500)
    taille: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=1000)


class DatasetResponse(DatasetBase):
    """Schéma pour la réponse"""
    id: str
    date_creation: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True