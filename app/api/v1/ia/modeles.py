from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from ....database import get_db
from ....models.ia.modele_ia import ModeleIA
from ....schemas.ia.modele_ia import *
from ....core.dependencies import get_current_active_user
from ....core.permissions import require_roles
from ....models.enums import UserRole

router = APIRouter(prefix="/modeles-ia", tags=["IA - Modèles"])

@router.get("/", response_model=List[ModeleIAResponse])
async def get_modeles(
    type: Optional[TypeModeleIA] = None,
    actif: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Récupère la liste des modèles IA."""
    query = db.query(ModeleIA)
    
    if type:
        query = query.filter(ModeleIA.type == type)
    if actif is not None:
        query = query.filter(ModeleIA.est_actif == actif)
    
    return query.all()

@router.get("/{modele_id}", response_model=ModeleIAResponse)
async def get_modele(
    modele_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Récupère un modèle IA par son ID."""
    modele = db.query(ModeleIA).filter(ModeleIA.id == modele_id).first()
    if not modele:
        raise HTTPException(status_code=404, detail="Modèle non trouvé")
    return modele

@router.post("/", response_model=ModeleIAResponse, status_code=status.HTTP_201_CREATED)
@require_roles([UserRole.ADMIN])
async def create_modele(
    request: ModeleIACreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Crée un nouveau modèle IA."""
    modele = ModeleIA(**request.model_dump())
    db.add(modele)
    db.commit()
    db.refresh(modele)
    return modele

@router.put("/{modele_id}", response_model=ModeleIAResponse)
@require_roles([UserRole.ADMIN])
async def update_modele(
    modele_id: str,
    request: ModeleIAUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Met à jour un modèle IA."""
    modele = db.query(ModeleIA).filter(ModeleIA.id == modele_id).first()
    if not modele:
        raise HTTPException(status_code=404, detail="Modèle non trouvé")
    
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(modele, key, value)
    
    db.commit()
    db.refresh(modele)
    return modele

@router.delete("/{modele_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_roles([UserRole.ADMIN])
async def delete_modele(
    modele_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Supprime un modèle IA."""
    modele = db.query(ModeleIA).filter(ModeleIA.id == modele_id).first()
    if not modele:
        raise HTTPException(status_code=404, detail="Modèle non trouvé")
    
    db.delete(modele)
    db.commit()