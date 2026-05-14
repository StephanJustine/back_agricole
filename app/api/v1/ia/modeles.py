# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import Optional

# from ....database import get_db
# from ....models.ia.modele_ia import ModeleIA
# from ....schemas.ia.modele_ia import *
# from ....core.dependencies import get_current_active_user
# from ....core.permissions import require_roles
# from ....models.enums import UserRole

# router = APIRouter()

# @router.get("/", response_model=List[ModeleIAResponse])
# async def get_modeles(
#     type: Optional[TypeModeleIA] = None,
#     actif: Optional[bool] = None,
#     db: Session = Depends(get_db),
#     current_user = Depends(get_current_active_user)
# ):
#     """Récupère la liste des modèles IA."""
#     query = db.query(ModeleIA)
    
#     if type:
#         query = query.filter(ModeleIA.type == type)
#     if actif is not None:
#         query = query.filter(ModeleIA.est_actif == actif)
    
#     return query.all()

# @router.get("/{modele_id}", response_model=ModeleIAResponse)
# async def get_modele(
#     modele_id: str,
#     db: Session = Depends(get_db),
#     current_user = Depends(get_current_active_user)
# ):
#     """Récupère un modèle IA par son ID."""
#     modele = db.query(ModeleIA).filter(ModeleIA.id == modele_id).first()
#     if not modele:
#         raise HTTPException(status_code=404, detail="Modèle non trouvé")
#     return modele

# @router.post("/", response_model=ModeleIAResponse, status_code=status.HTTP_201_CREATED)
# @require_roles([UserRole.ADMIN])
# async def create_modele(
#     request: ModeleIACreate,
#     db: Session = Depends(get_db),
#     current_user = Depends(get_current_active_user)
# ):
#     """Crée un nouveau modèle IA."""
#     modele = ModeleIA(**request.model_dump())
#     db.add(modele)
#     db.commit()
#     db.refresh(modele)
#     return modele

# @router.put("/{modele_id}", response_model=ModeleIAResponse)
# @require_roles([UserRole.ADMIN])
# async def update_modele(
#     modele_id: str,
#     request: ModeleIAUpdate,
#     db: Session = Depends(get_db),
#     current_user = Depends(get_current_active_user)
# ):
#     """Met à jour un modèle IA."""
#     modele = db.query(ModeleIA).filter(ModeleIA.id == modele_id).first()
#     if not modele:
#         raise HTTPException(status_code=404, detail="Modèle non trouvé")
    
#     update_data = request.model_dump(exclude_unset=True)
#     for key, value in update_data.items():
#         setattr(modele, key, value)
    
#     db.commit()
#     db.refresh(modele)
#     return modele

# @router.delete("/{modele_id}", status_code=status.HTTP_204_NO_CONTENT)
# @require_roles([UserRole.ADMIN])
# async def delete_modele(
#     modele_id: str,
#     db: Session = Depends(get_db),
#     current_user = Depends(get_current_active_user)
# ):
#     """Supprime un modèle IA."""
#     modele = db.query(ModeleIA).filter(ModeleIA.id == modele_id).first()
#     if not modele:
#         raise HTTPException(status_code=404, detail="Modèle non trouvé")
    
#     db.delete(modele)
#     db.commit()


# api/v1/ia/modeles.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.models.ia.modele_ia import ModeleIA
from app.schemas.ia.modele_ia import (
    ModeleIACreate,
    ModeleIAUpdate,
    ModeleIAResponse
)
from app.core.dependencies import get_current_active_user
from app.core.permissions import require_roles
from app.models.enums import UserRole, TypeModeleIA

router = APIRouter()


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
    
    modeles = query.all()
    return modeles


@router.get("/{modele_id}", response_model=ModeleIAResponse)
async def get_modele(
    modele_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Récupère un modèle IA par son ID."""
    modele = db.query(ModeleIA).filter(ModeleIA.id == modele_id).first()
    if not modele:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modèle non trouvé"
        )
    return modele


@router.post("/", response_model=ModeleIAResponse, status_code=status.HTTP_201_CREATED)
@require_roles([UserRole.ADMIN])
async def create_modele(
    request: ModeleIACreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Crée un nouveau modèle IA."""
    try:
        # Vérifier si un modèle avec le même nom existe déjà
        existing = db.query(ModeleIA).filter(ModeleIA.nom == request.nom).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Un modèle avec le nom '{request.nom}' existe déjà"
            )
        
        # Création du modèle avec les champs du modèle existant
        modele = ModeleIA(
            nom=request.nom,
            type=request.type,
            version=request.version,
            framework=request.framework,
            path=request.path,
            taille=request.taille,
            metriques=request.metriques or {},
            parametres=request.parametres or {},
            est_actif=request.est_actif,
            est_pret=request.est_pret,
            description=request.description
        )
        
        db.add(modele)
        db.commit()
        db.refresh(modele)
        return modele
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création: {str(e)}"
        )


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modèle non trouvé"
        )
    
    # Mettre à jour uniquement les champs fournis
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(modele, key):
            setattr(modele, key, value)
    
    try:
        db.commit()
        db.refresh(modele)
        return modele
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modèle non trouvé"
        )
    
    try:
        db.delete(modele)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )

@router.patch("/{modele_id}/activate", response_model=ModeleIAResponse)
@require_roles([UserRole.ADMIN])
async def activate_modele(
    modele_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Active ou désactive un modèle IA."""
    modele = db.query(ModeleIA).filter(ModeleIA.id == modele_id).first()
    if not modele:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modèle non trouvé"
        )
    
    modele.est_actif = not modele.est_actif
    db.commit()
    db.refresh(modele)
    return modele


@router.patch("/{modele_id}/ready", response_model=ModeleIAResponse)
@require_roles([UserRole.ADMIN])
async def set_modele_ready(
    modele_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Marque un modèle comme prêt à l'emploi."""
    modele = db.query(ModeleIA).filter(ModeleIA.id == modele_id).first()
    if not modele:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modèle non trouvé"
        )
    
    modele.est_pret = True
    db.commit()
    db.refresh(modele)
    return modele