# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import List

# # Importations locales (ajustez les chemins selon votre structure de dossier)
# from ....database import get_db  # Supposant que vous avez une fonction de session
# from ....models.iot.capteur import Capteur
# from ....schemas.iot.capteur import CapteurCreate, CapteurUpdate, CapteurResponse

# router = APIRouter()

# @router.post("/", response_model=CapteurResponse, status_code=status.HTTP_201_CREATED)
# def create_capteur(capteur: CapteurCreate, db: Session = Depends(get_db)):
#     """
#     Crée un nouveau capteur IoT dans la base de données.
#     """
#     db_capteur = Capteur(**capteur.dict())
#     db.add(db_capteur)
#     db.commit()
#     db.refresh(db_capteur)
#     return db_capteur

# @router.get("/", response_model=List[CapteurResponse])
# def read_capteurs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     """
#     Récupère la liste de tous les capteurs avec pagination.
#     """
#     capteurs = db.query(Capteur).offset(skip).limit(limit).all()
#     return capteurs

# @router.get("/{capteur_id}", response_model=CapteurResponse)
# def read_capteur(capteur_id: str, db: Session = Depends(get_db)):
#     """
#     Récupère un capteur spécifique par son ID.
#     """
#     db_capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()
#     if not db_capteur:
#         raise HTTPException(status_code=404, detail="Capteur non trouvé")
#     return db_capteur

# @router.patch("/{capteur_id}", response_model=CapteurResponse)
# def update_capteur(capteur_id: str, capteur_update: CapteurUpdate, db: Session = Depends(get_db)):
#     """
#     Met à jour partiellement les informations d'un capteur.
#     """
#     db_query = db.query(Capteur).filter(Capteur.id == capteur_id)
#     db_capteur = db_query.first()
    
#     if not db_capteur:
#         raise HTTPException(status_code=404, detail="Capteur non trouvé")
    
#     # On extrait les données envoyées en excluant les valeurs non définies (None)
#     update_data = capteur_update.dict(exclude_unset=True)
    
#     db_query.update(update_data, synchronize_session=False)
#     db.commit()
#     db.refresh(db_capteur)
#     return db_capteur

# @router.delete("/{capteur_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_capteur(capteur_id: str, db: Session = Depends(get_db)):
#     """
#     Supprime un capteur de la base de données.
#     """
#     db_capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()
#     if not db_capteur:
#         raise HTTPException(status_code=404, detail="Capteur non trouvé")
    
#     db.delete(db_capteur)
#     db.commit()
#     return None

# api/v1/iot/capteurs.py
"""
Routes pour les capteurs IoT.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.database import get_db
from app.models.iot.capteur import Capteur
from app.models.iot.passerelle import Passerelle
from app.models.parcelle import Parcelle
from app.schemas.iot.capteur import (
    CapteurCreate,
    CapteurUpdate,
    CapteurResponse
)
from app.core.dependencies import get_current_active_user
from app.core.permissions import require_roles
from app.models.enums import UserRole, TypeCapteur

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def valider_capteur_code(code: str, db: Session, exclude_id: str = None) -> bool:
    """Vérifie si le code du capteur est unique."""
    query = db.query(Capteur).filter(Capteur.code == code)
    if exclude_id:
        query = query.filter(Capteur.id != exclude_id)
    return query.first() is None


def verifier_seuils_alerte(capteur: Capteur, valeur: float) -> Optional[str]:
    """Vérifie si la valeur dépasse les seuils d'alerte."""
    if capteur.seuil_alerte_bas and valeur < capteur.seuil_alerte_bas:
        return f"Valeur {valeur} inférieure au seuil bas {capteur.seuil_alerte_bas}"
    if capteur.seuil_alerte_haut and valeur > capteur.seuil_alerte_haut:
        return f"Valeur {valeur} supérieure au seuil haut {capteur.seuil_alerte_haut}"
    return None


# ============================================================================
# CRÉER UN CAPTEUR
# ============================================================================
@router.post("/", response_model=CapteurResponse, status_code=status.HTTP_201_CREATED)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def create_capteur(
    capteur: CapteurCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    CRÉE UN NOUVEAU CAPTEUR IOT.
    
    Args:
        capteur: Données du capteur
        db: Session de base de données
        current_user: Utilisateur authentifié
    """
    try:
        # 1. Validation de la passerelle
        passerelle = db.query(Passerelle).filter(Passerelle.id == capteur.passerelle_id).first()
        if not passerelle:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Passerelle avec l'ID '{capteur.passerelle_id}' non trouvée"
            )
        
        # 2. Validation de la parcelle si fournie
        if capteur.parcelle_id:
            parcelle = db.query(Parcelle).filter(Parcelle.id == capteur.parcelle_id).first()
            if not parcelle:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parcelle avec l'ID '{capteur.parcelle_id}' non trouvée"
                )
        
        # 3. Validation du code unique
        if capteur.code:
            if not valider_capteur_code(capteur.code, db):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Le code '{capteur.code}' est déjà utilisé par un autre capteur"
                )
        
        # 4. Validation des seuils
        if capteur.seuil_alerte_bas and capteur.seuil_alerte_haut:
            if capteur.seuil_alerte_bas >= capteur.seuil_alerte_haut:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Le seuil bas doit être inférieur au seuil haut"
                )
        
        # 5. Création du capteur
        now = datetime.utcnow()
        
        db_capteur = Capteur(
            passerelle_id=capteur.passerelle_id,
            parcelle_id=capteur.parcelle_id,
            code=capteur.code,
            type=capteur.type,
            reference=capteur.reference,
            precision=capteur.precision,
            unite=capteur.unite,
            seuil_alerte_bas=capteur.seuil_alerte_bas,
            seuil_alerte_haut=capteur.seuil_alerte_haut,
            configuration=capteur.configuration or {},
            date_installation=now,
            est_actif=True,
            created_at=now,
            updated_at=now,
            created_by=current_user.id if hasattr(Capteur, 'created_by') else None
        )
        
        db.add(db_capteur)
        db.commit()
        db.refresh(db_capteur)
        
        logger.info(f"✅ Capteur créé | ID: {db_capteur.id} | Type: {capteur.type} | Par: {current_user.email}")
        
        return db_capteur
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur create_capteur: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création: {str(e)}"
        )


# ============================================================================
# LISTER LES CAPTEURS
# ============================================================================
@router.get("/", response_model=List[CapteurResponse])
async def read_capteurs(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=500, description="Nombre maximum d'éléments"),
    passerelle_id: Optional[str] = Query(None, description="Filtrer par passerelle"),
    parcelle_id: Optional[str] = Query(None, description="Filtrer par parcelle"),
    type: Optional[TypeCapteur] = Query(None, description="Filtrer par type de capteur"),
    est_actif: Optional[bool] = Query(None, description="Filtrer par statut actif"),
    code: Optional[str] = Query(None, description="Filtrer par code"),
    recherche: Optional[str] = Query(None, description="Recherche dans code et référence"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE LA LISTE DE TOUS LES CAPTEURS AVEC FILTRES.
    """
    try:
        query = db.query(Capteur)
        
        # Filtres
        if passerelle_id:
            query = query.filter(Capteur.passerelle_id == passerelle_id)
        if parcelle_id:
            query = query.filter(Capteur.parcelle_id == parcelle_id)
        if type:
            query = query.filter(Capteur.type == type)
        if est_actif is not None:
            query = query.filter(Capteur.est_actif == est_actif)
        if code:
            query = query.filter(Capteur.code.ilike(f"%{code}%"))
        if recherche:
            query = query.filter(
                (Capteur.code.ilike(f"%{recherche}%")) |
                (Capteur.reference.ilike(f"%{recherche}%"))
            )
        
        capteurs = query.order_by(Capteur.date_installation.desc()).offset(skip).limit(limit).all()
        
        logger.info(f"📊 Liste des capteurs | Total: {len(capteurs)}")
        
        return capteurs
        
    except Exception as e:
        logger.error(f"❌ Erreur read_capteurs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# RÉCUPÉRER UN CAPTEUR PAR ID
# ============================================================================
@router.get("/{capteur_id}", response_model=CapteurResponse)
async def read_capteur(
    capteur_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE UN CAPTEUR SPÉCIFIQUE PAR SON ID.
    """
    try:
        db_capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()
        
        if not db_capteur:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Capteur avec l'ID '{capteur_id}' non trouvé"
            )
        
        return db_capteur
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur read_capteur: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# METTRE À JOUR UN CAPTEUR
# ============================================================================
@router.patch("/{capteur_id}", response_model=CapteurResponse)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def update_capteur(
    capteur_id: str,
    capteur_update: CapteurUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    MET À JOUR PARTIELLEMENT LES INFORMATIONS D'UN CAPTEUR.
    """
    try:
        db_capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()
        
        if not db_capteur:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Capteur avec l'ID '{capteur_id}' non trouvé"
            )
        
        update_data = capteur_update.model_dump(exclude_unset=True)
        
        # Vérifier l'unicité du code si modifié
        if "code" in update_data and update_data["code"]:
            if not valider_capteur_code(update_data["code"], db, capteur_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Le code '{update_data['code']}' est déjà utilisé par un autre capteur"
                )
        
        # Vérifier la cohérence des seuils
        nouveau_seuil_bas = update_data.get("seuil_alerte_bas", db_capteur.seuil_alerte_bas)
        nouveau_seuil_haut = update_data.get("seuil_alerte_haut", db_capteur.seuil_alerte_haut)
        
        if nouveau_seuil_bas is not None and nouveau_seuil_haut is not None:
            if nouveau_seuil_bas >= nouveau_seuil_haut:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Le seuil bas doit être inférieur au seuil haut"
                )
        
        # Mise à jour
        for field, value in update_data.items():
            if hasattr(db_capteur, field):
                setattr(db_capteur, field, value)
        
        db_capteur.updated_at = datetime.utcnow()
        if hasattr(Capteur, 'updated_by'):
            db_capteur.updated_by = current_user.id
        
        db.commit()
        db.refresh(db_capteur)
        
        logger.info(f"✏️ Capteur mis à jour | ID: {capteur_id} | Par: {current_user.email}")
        
        return db_capteur
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur update_capteur: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


# ============================================================================
# METTRE À JOUR LA DERNIÈRE VALEUR D'UN CAPTEUR
# ============================================================================
@router.post("/{capteur_id}/valeur", response_model=CapteurResponse)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def update_capteur_valeur(
    capteur_id: str,
    valeur: float = Query(..., description="Nouvelle valeur mesurée"),
    timestamp: Optional[datetime] = Query(None, description="Horodatage de la mesure"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    MET À JOUR LA DERNIÈRE VALEUR MESURÉE PAR LE CAPTEUR.
    """
    try:
        db_capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()
        
        if not db_capteur:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Capteur avec l'ID '{capteur_id}' non trouvé"
            )
        
        # Vérifier si le capteur est actif
        if not db_capteur.est_actif:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ce capteur est désactivé, impossible de mettre à jour la valeur"
            )
        
        # Vérifier les seuils
        alerte = verifier_seuils_alerte(db_capteur, valeur)
        if alerte:
            logger.warning(f"⚠️ Alerte capteur {capteur_id}: {alerte}")
            # Optionnel: enregistrer l'alerte
        
        # Mettre à jour la valeur
        db_capteur.derniere_valeur = valeur
        db_capteur.derniere_mise_a_jour = timestamp or datetime.utcnow()
        
        # Mettre à jour min/max
        if db_capteur.valeur_min is None or valeur < db_capteur.valeur_min:
            db_capteur.valeur_min = valeur
        if db_capteur.valeur_max is None or valeur > db_capteur.valeur_max:
            db_capteur.valeur_max = valeur
        
        db_capteur.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_capteur)
        
        logger.info(f"📊 Valeur capteur mise à jour | ID: {capteur_id} | Valeur: {valeur}")
        
        return db_capteur
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur update_capteur_valeur: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


# ============================================================================
# SUPPRIMER UN CAPTEUR
# ============================================================================
@router.delete("/{capteur_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_roles([UserRole.ADMIN])
async def delete_capteur(
    capteur_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    SUPPRIME UN CAPTEUR DE LA BASE DE DONNÉES (ADMIN UNIQUEMENT).
    """
    try:
        db_capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()
        
        if not db_capteur:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Capteur avec l'ID '{capteur_id}' non trouvé"
            )
        
        logger.info(f"🗑️ Capteur supprimé | ID: {capteur_id} | Code: {db_capteur.code} | Par: {current_user.email}")
        
        db.delete(db_capteur)
        db.commit()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur delete_capteur: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )


# ============================================================================
# STATISTIQUES DES CAPTEURS
# ============================================================================
@router.get("/statistiques/resume", response_model=Dict[str, Any])
async def get_capteurs_statistiques(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE UN RÉSUMÉ STATISTIQUE DES CAPTEURS.
    """
    try:
        from sqlalchemy import func
        
        total = db.query(func.count(Capteur.id)).scalar() or 0
        total_actifs = db.query(func.count(Capteur.id)).filter(Capteur.est_actif == True).scalar() or 0
        total_inactifs = total - total_actifs
        
        # Répartition par type
        repartition_type = db.query(
            Capteur.type,
            func.count(Capteur.id).label("total")
        ).group_by(Capteur.type).all()
        
        # Capteurs avec alertes potentielles (dernière valeur hors seuil)
        capteurs_alerte = 0
        # À implémenter selon vos besoins
        
        result = {
            "total_capteurs": total,
            "actifs": total_actifs,
            "inactifs": total_inactifs,
            "taux_activite": round((total_actifs / total * 100), 1) if total > 0 else 0,
            "repartition_par_type": [
                {"type": item[0].value if hasattr(item[0], 'value') else str(item[0]), "total": item[1]}
                for item in repartition_type
            ]
        }
        
        logger.info(f"📊 Statistiques capteurs consultées")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur get_capteurs_statistiques: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul des statistiques: {str(e)}"
        )