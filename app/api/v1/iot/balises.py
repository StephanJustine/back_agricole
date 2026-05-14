# from fastapi import APIRouter, HTTPException, Depends, status
# from sqlalchemy.orm import Session
# from typing import List

# # Importation de vos schémas et modèles
# # Note : Ajustez les imports selon votre structure de dossiers réelle
# from ....database import get_db
# from ....schemas.iot.balise_gps import BaliseGPSCreate, BaliseGPSUpdate, BaliseGPSResponse
# from ....models.iot.balise_gps import BaliseGPS

# router = APIRouter()

# @router.post("/", response_model=BaliseGPSResponse, status_code=status.HTTP_201_CREATED)
# def create_balise(obj_in: BaliseGPSCreate, db: Session = Depends(get_db)):
#     """
#     Crée une nouvelle balise GPS.
#     """
#     # Vérifier si le code existe déjà
#     existing_balise = db.query(BaliseGPS).filter(BaliseGPS.code == obj_in.code).first()
#     if existing_balise:
#         raise HTTPException(status_code=400, detail="Ce code de balise existe déjà.")
    
#     db_balise = BaliseGPS(**obj_in.dict())
#     db.add(db_balise)
#     db.commit()
#     db.refresh(db_balise)
#     return db_balise

# @router.get("/", response_model=List[BaliseGPSResponse])
# def read_balises(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     """
#     Récupère la liste de toutes les balises.
#     """
#     balises = db.query(BaliseGPS).offset(skip).limit(limit).all()
#     return balises

# @router.get("/{balise_id}", response_model=BaliseGPSResponse)
# def read_balise(balise_id: str, db: Session = Depends(get_db)):
#     """
#     Récupère une balise spécifique par son ID (UUID).
#     """
#     balise = db.query(BaliseGPS).filter(BaliseGPS.id == balise_id).first()
#     if not balise:
#         raise HTTPException(status_code=404, detail="Balise non trouvée")
#     return balise

# @router.patch("/{balise_id}", response_model=BaliseGPSResponse)
# def update_balise(balise_id: str, obj_in: BaliseGPSUpdate, db: Session = Depends(get_db)):
#     """
#     Met à jour les données d'une balise (ex: mise à jour de position, batterie).
#     """
#     db_balise = db.query(BaliseGPS).filter(BaliseGPS.id == balise_id).first()
#     if not db_balise:
#         raise HTTPException(status_code=404, detail="Balise non trouvée")
    
#     update_data = obj_in.dict(exclude_unset=True)
#     for field, value in update_data.items():
#         setattr(db_balise, field, value)
    
#     # Logique métier optionnelle : mettre à jour 'derniere_mise_a_jour' automatiquement
#     # db_balise.derniere_mise_a_jour = datetime.now()

#     db.add(db_balise)
#     db.commit()
#     db.refresh(db_balise)
#     return db_balise

# @router.delete("/{balise_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_balise(balise_id: str, db: Session = Depends(get_db)):
#     """
#     Supprime une balise GPS.
#     """
#     db_balise = db.query(BaliseGPS).filter(BaliseGPS.id == balise_id).first()
#     if not db_balise:
#         raise HTTPException(status_code=404, detail="Balise non trouvée")
    
#     db.delete(db_balise)
#     db.commit()
#     return None

# api/v1/iot/balise_gps.py
"""
Routes pour les balises GPS.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import re

from app.database import get_db
from app.models.iot.balise_gps import BaliseGPS
from app.models.lot import Lot
from app.schemas.iot.balise_gps import (
    BaliseGPSCreate,
    BaliseGPSUpdate,
    BaliseGPSResponse
)
from app.core.dependencies import get_current_active_user
from app.core.permissions import require_roles
from app.models.enums import UserRole

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def valider_position(position: str) -> bool:
    """Valide le format de position (lat,lon)."""
    if not position:
        return True
    pattern = r'^-?\d{1,3}\.\d+,-?\d{1,3}\.\d+$'
    return bool(re.match(pattern, position))


def enregistrer_historique_positions(balise: BaliseGPS, nouvelle_position: str):
    """Enregistre la position dans l'historique."""
    if not balise.historique_positions:
        balise.historique_positions = []
    
    historique = {
        "position": nouvelle_position,
        "timestamp": datetime.utcnow().isoformat(),
        "vitesse": balise.vitesse,
        "cap": balise.cap,
        "batterie": balise.batterie
    }
    
    balise.historique_positions.append(historique)
    
    # Garder seulement les 100 dernières positions
    if len(balise.historique_positions) > 100:
        balise.historique_positions = balise.historique_positions[-100:]


def verifier_alertes(balise: BaliseGPS) -> List[str]:
    """Vérifie les conditions d'alerte et retourne la liste des alertes."""
    alertes = []
    
    # Alerte batterie faible
    if balise.batterie is not None and balise.batterie < 15:
        alertes.append(f"Batterie faible: {balise.batterie}%")
        balise.alerte = True
    
    # Alerte choc
    if balise.choc:
        alertes.append("Choc détecté sur la balise")
        balise.alerte = True
    
    # Alerte hors zone
    # À implémenter selon vos besoins
    
    # Alerte signal faible
    if balise.signal is not None and balise.signal < 20:
        alertes.append(f"Signal GPS faible: {balise.signal}%")
    
    return alertes


# ============================================================================
# CRÉER UNE BALISE GPS
# ============================================================================
@router.post("/", response_model=BaliseGPSResponse, status_code=status.HTTP_201_CREATED)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def create_balise(
    obj_in: BaliseGPSCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    CRÉE UNE NOUVELLE BALISE GPS.
    
    Args:
        obj_in: Données de la balise
        db: Session de base de données
        current_user: Utilisateur authentifié
    """
    try:
        # 1. Validation du code
        if not obj_in.code or not obj_in.code.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le code de la balise est requis"
            )
        
        # 2. Vérifier si le code existe déjà
        existing = db.query(BaliseGPS).filter(BaliseGPS.code == obj_in.code).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Une balise avec le code '{obj_in.code}' existe déjà"
            )
        
        # 3. Validation du format de position
        if obj_in.position and not valider_position(obj_in.position):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format de position invalide. Utilisez 'latitude,longitude' (ex: -17.8333,48.4167)"
            )
        
        # 4. Validation du lot si fourni
        if obj_in.lot_id:
            lot = db.query(Lot).filter(Lot.id == obj_in.lot_id).first()
            if not lot:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Lot avec l'ID '{obj_in.lot_id}' non trouvé"
                )
        
        # 5. Création de la balise
        now = datetime.utcnow()
        
        balise = BaliseGPS(
            code=obj_in.code.upper().strip(),
            lot_id=obj_in.lot_id,
            modele=obj_in.modele,
            position=obj_in.position,
            derniere_mise_a_jour=now if obj_in.position else None,
            created_at=now,
            updated_at=now,
            created_by=current_user.id if hasattr(BaliseGPS, 'created_by') else None,
            historique_positions=[],
            alertes=[]
        )
        
        db.add(balise)
        db.commit()
        db.refresh(balise)
        
        logger.info(f"✅ Balise GPS créée | ID: {balise.id} | Code: {balise.code} | Par: {current_user.email}")
        
        return balise
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur create_balise: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création: {str(e)}"
        )


# ============================================================================
# LISTER LES BALISES GPS
# ============================================================================
@router.get("/", response_model=List[BaliseGPSResponse])
async def read_balises(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=500, description="Nombre maximum d'éléments"),
    code: Optional[str] = Query(None, description="Filtrer par code"),
    lot_id: Optional[str] = Query(None, description="Filtrer par lot"),
    alerte: Optional[bool] = Query(None, description="Filtrer par alerte"),
    batterie_min: Optional[float] = Query(None, ge=0, le=100, description="Batterie minimum (%)"),
    position_connue: Optional[bool] = Query(None, description="Position connue (oui/non)"),
    search: Optional[str] = Query(None, description="Recherche dans code et modèle"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE LA LISTE DES BALISES GPS AVEC FILTRES.
    """
    try:
        query = db.query(BaliseGPS)
        
        # Filtres
        if code:
            query = query.filter(BaliseGPS.code.ilike(f"%{code}%"))
        if lot_id:
            query = query.filter(BaliseGPS.lot_id == lot_id)
        if alerte is not None:
            query = query.filter(BaliseGPS.alerte == alerte)
        if batterie_min is not None:
            query = query.filter(BaliseGPS.batterie >= batterie_min)
        if position_connue is not None:
            if position_connue:
                query = query.filter(BaliseGPS.position.isnot(None))
            else:
                query = query.filter(BaliseGPS.position.is_(None))
        if search:
            query = query.filter(
                (BaliseGPS.code.ilike(f"%{search}%")) |
                (BaliseGPS.modele.ilike(f"%{search}%"))
            )
        
        # Tri par date de mise à jour décroissante
        balises = query.order_by(BaliseGPS.derniere_mise_a_jour.desc()).offset(skip).limit(limit).all()
        
        logger.info(f"📊 Liste des balises | Total: {len(balises)}")
        
        return balises
        
    except Exception as e:
        logger.error(f"❌ Erreur read_balises: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# RÉCUPÉRER UNE BALISE PAR ID
# ============================================================================
@router.get("/{balise_id}", response_model=BaliseGPSResponse)
async def read_balise(
    balise_id: str,
    include_history: bool = Query(False, description="Inclure l'historique des positions"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE UNE BALISE SPÉCIFIQUE PAR SON ID.
    """
    try:
        balise = db.query(BaliseGPS).filter(BaliseGPS.id == balise_id).first()
        
        if not balise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Balise avec l'ID '{balise_id}' non trouvée"
            )
        
        # Optionnellement, ne pas retourner tout l'historique
        if not include_history:
            balise.historique_positions = []
        
        return balise
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur read_balise: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# METTRE À JOUR UNE BALISE (POSITION, BATTRIE, ETC.)
# ============================================================================
@router.patch("/{balise_id}", response_model=BaliseGPSResponse)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def update_balise(
    balise_id: str,
    obj_in: BaliseGPSUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    MET À JOUR LES DONNÉES D'UNE BALISE (POSITION, BATTERIE, ALERTES).
    """
    try:
        balise = db.query(BaliseGPS).filter(BaliseGPS.id == balise_id).first()
        
        if not balise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Balise avec l'ID '{balise_id}' non trouvée"
            )
        
        # Mise à jour des champs
        update_data = obj_in.model_dump(exclude_unset=True)
        position_changed = False
        old_position = balise.position
        
        for field, value in update_data.items():
            if hasattr(balise, field) and value is not None:
                # Validation spéciale pour position
                if field == "position":
                    if not valider_position(value):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Format de position invalide. Utilisez 'latitude,longitude'"
                        )
                    position_changed = True
                    # Sauvegarder l'ancienne position
                    if old_position:
                        balise.derniere_position = old_position
                
                # Validation batterie
                if field == "batterie" and (value < 0 or value > 100):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="La batterie doit être comprise entre 0 et 100%"
                    )
                
                # Validation signal
                if field == "signal" and (value < 0 or value > 100):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Le signal doit être compris entre 0 et 100%"
                    )
                
                setattr(balise, field, value)
        
        # Si la position a changé, enregistrer dans l'historique
        if position_changed and balise.position:
            balise.derniere_mise_a_jour = datetime.utcnow()
            enregistrer_historique_positions(balise, balise.position)
        
        # Vérifier les alertes
        nouvelles_alertes = verifier_alertes(balise)
        if nouvelles_alertes:
            for alerte in nouvelles_alertes:
                balise.alertes.append({
                    "message": alerte,
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "warning"
                })
            # Garder seulement les 50 dernières alertes
            if len(balise.alertes) > 50:
                balise.alertes = balise.alertes[-50:]
        
        # Mise à jour du lot si changé
        if "lot_id" in update_data and update_data["lot_id"]:
            lot = db.query(Lot).filter(Lot.id == balise.lot_id).first()
            if not lot:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Lot avec l'ID '{balise.lot_id}' non trouvé"
                )
        
        balise.updated_at = datetime.utcnow()
        if hasattr(BaliseGPS, 'updated_by'):
            balise.updated_by = current_user.id
        
        db.commit()
        db.refresh(balise)
        
        logger.info(f"✏️ Balise mise à jour | ID: {balise_id} | Position: {position_changed} | Par: {current_user.email}")
        
        return balise
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur update_balise: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


# ============================================================================
# SUPPRIMER UNE BALISE
# ============================================================================
@router.delete("/{balise_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_roles([UserRole.ADMIN])
async def delete_balise(
    balise_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    SUPPRIME UNE BALISE GPS (ADMIN UNIQUEMENT).
    """
    try:
        balise = db.query(BaliseGPS).filter(BaliseGPS.id == balise_id).first()
        
        if not balise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Balise avec l'ID '{balise_id}' non trouvée"
            )
        
        logger.info(f"🗑️ Balise supprimée | Code: {balise.code} | Par: {current_user.email}")
        
        db.delete(balise)
        db.commit()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur delete_balise: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )


# ============================================================================
# METTRE À JOUR LA POSITION D'UNE BALISE (ENDPOINT SPÉCIFIQUE)
# ============================================================================
@router.post("/{balise_id}/position", response_model=BaliseGPSResponse)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def update_position(
    balise_id: str,
    latitude: float,
    longitude: float,
    vitesse: Optional[float] = None,
    cap: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    MET À JOUR SPÉCIFIQUEMENT LA POSITION D'UNE BALISE.
    """
    try:
        balise = db.query(BaliseGPS).filter(BaliseGPS.id == balise_id).first()
        
        if not balise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Balise avec l'ID '{balise_id}' non trouvée"
            )
        
        # Validation des coordonnées
        if not (-90 <= latitude <= 90):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La latitude doit être comprise entre -90 et 90"
            )
        
        if not (-180 <= longitude <= 180):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La longitude doit être comprise entre -180 et 180"
            )
        
        # Sauvegarder l'ancienne position
        if balise.position:
            balise.derniere_position = balise.position
        
        # Nouvelle position
        nouvelle_position = f"{latitude},{longitude}"
        balise.position = nouvelle_position
        balise.derniere_mise_a_jour = datetime.utcnow()
        
        if vitesse is not None:
            balise.vitesse = vitesse
        if cap is not None:
            balise.cap = cap
        
        # Enregistrer dans l'historique
        enregistrer_historique_positions(balise, nouvelle_position)
        
        # Réinitialiser l'alerte choc si nécessaire
        if balise.choc:
            balise.choc = False
            balise.alerte = False
        
        balise.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(balise)
        
        logger.info(f"📍 Position mise à jour | Balise: {balise.code} | Lat: {latitude}, Lon: {longitude}")
        
        return balise
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur update_position: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


# ============================================================================
# STATISTIQUES DES BALISES
# ============================================================================
@router.get("/statistiques/resume", response_model=Dict[str, Any])
async def get_balises_statistiques(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE UN RÉSUMÉ STATISTIQUE DES BALISES GPS.
    """
    try:
        from sqlalchemy import func
        
        total = db.query(func.count(BaliseGPS.id)).scalar() or 0
        total_alertes = db.query(func.count(BaliseGPS.id)).filter(BaliseGPS.alerte == True).scalar() or 0
        total_position_connue = db.query(func.count(BaliseGPS.id)).filter(BaliseGPS.position.isnot(None)).scalar() or 0
        batterie_moyenne = db.query(func.avg(BaliseGPS.batterie)).scalar() or 0
        
        result = {
            "total_balises": total,
            "alertes_actives": total_alertes,
            "position_connue": total_position_connue,
            "position_inconnue": total - total_position_connue,
            "batterie_moyenne": round(float(batterie_moyenne), 1),
            "taux_alerte": round((total_alertes / total * 100), 1) if total > 0 else 0
        }
        
        logger.info(f"📊 Statistiques balises consultées")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur get_balises_statistiques: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul des statistiques: {str(e)}"
        )