# """
# Schémas Pydantic pour les travaux du sol.
# """
# from pydantic import BaseModel, Field
# from typing import Optional, List
# from datetime import date


# class TravailSolBase(BaseModel):
#     """Schéma de base pour un travail du sol."""
#     parcelle_id: str
#     date: date
#     type: str
#     description: Optional[str] = None
#     profondeur: Optional[float] = None
#     produit: Optional[str] = None
#     dose: Optional[float] = None
#     cout_intrants: Optional[float] = None
#     cout_main_oeuvre: Optional[float] = None
#     observations: Optional[str] = None
#     responsable: Optional[str] = None


# class TravailSolCreate(TravailSolBase):
#     """Schéma pour la création d'un travail."""
#     pass


# class TravailSolUpdate(BaseModel):
#     """Schéma pour la mise à jour d'un travail."""
#     date: Optional[date] = None
#     type: Optional[str] = None
#     description: Optional[str] = None
#     profondeur: Optional[float] = None
#     produit: Optional[str] = None
#     dose: Optional[float] = None
#     cout_intrants: Optional[float] = None
#     cout_main_oeuvre: Optional[float] = None
#     observations: Optional[str] = None
#     responsable: Optional[str] = None


# class TravailSolResponse(BaseModel):
#     """Schéma de réponse pour un travail."""
#     id: str
#     parcelle_id: str
#     parcelle_nom: Optional[str] = None
#     date: date
#     type: str
#     description: Optional[str]
#     profondeur: Optional[float]
#     produit: Optional[str]
#     dose: Optional[float]
#     cout_intrants: Optional[float]
#     cout_main_oeuvre: Optional[float]
#     cout_total: Optional[float]
#     observations: Optional[str]
#     responsable: Optional[str]
#     created_at: Optional[str] = None
#     updated_at: Optional[str] = None
    
#     class Config:
#         from_attributes = True


# class TravailSolList(BaseModel):
#     """Schéma pour la liste des travaux."""
#     total: int
#     page: int
#     size: int
#     pages: int
#     items: List[TravailSolResponse]


# class CoutsParcelle(BaseModel):
#     """Schéma pour les coûts par parcelle."""
#     parcelle_id: str
#     parcelle_nom: str
#     total_couts: float
#     par_type: dict
#     details: List[dict]


"""
Schémas Pydantic pour les travaux du sol.
"""
from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List
from datetime import date, datetime


class TravailSolBase(BaseModel):
    """Schéma de base pour un travail du sol."""
    parcelle_id: str
    date: date
    type: str
    description: Optional[str] = None
    profondeur: Optional[float] = None
    produit: Optional[str] = None
    dose: Optional[float] = None
    cout_intrants: Optional[float] = None
    cout_main_oeuvre: Optional[float] = None
    observations: Optional[str] = None
    responsable: Optional[str] = None


class TravailSolCreate(TravailSolBase):
    """Schéma pour la création d'un travail."""
    pass


class TravailSolUpdate(BaseModel):
    """Schéma pour la mise à jour d'un travail."""
    date: Optional[date] = None
    type: Optional[str] = None
    description: Optional[str] = None
    profondeur: Optional[float] = None
    produit: Optional[str] = None
    dose: Optional[float] = None
    cout_intrants: Optional[float] = None
    cout_main_oeuvre: Optional[float] = None
    observations: Optional[str] = None
    responsable: Optional[str] = None


class TravailSolResponse(BaseModel):
    """Schéma de réponse pour un travail."""
    id: str
    parcelle_id: str
    parcelle_nom: Optional[str] = None
    date: date
    type: str
    description: Optional[str]
    profondeur: Optional[float]
    produit: Optional[str]
    dose: Optional[float]
    cout_intrants: Optional[float]
    cout_main_oeuvre: Optional[float]
    cout_total: Optional[float]
    observations: Optional[str]
    responsable: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime) -> str:
        """Convertit datetime en string ISO."""
        return dt.isoformat()
    
    class Config:
        from_attributes = True


class TravailSolList(BaseModel):
    """Schéma pour la liste des travaux."""
    total: int
    page: int
    size: int
    pages: int
    items: List[TravailSolResponse]


class CoutsParcelle(BaseModel):
    """Schéma pour les coûts par parcelle."""
    parcelle_id: str
    parcelle_nom: str
    total_couts: float
    par_type: dict
    details: List[dict]