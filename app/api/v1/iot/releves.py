# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import List

# # Import de la session de base de données (à adapter selon ton projet)
# from ....database import get_db 
# # Import des modèles et schémas
# from ....models.iot.releve import ReleveCapteur
# from ....schemas.iot.releve import ReleveCapteurCreate, ReleveCapteurResponse

# router = APIRouter()

# @router.post("/", response_model=ReleveCapteurResponse, status_code=status.HTTP_201_CREATED)
# def create_releve(releve: ReleveCapteurCreate, db: Session = Depends(get_db)):
#     """
#     Crée un nouveau relevé pour un capteur spécifique.
#     """
#     db_releve = ReleveCapteur(**releve.model_dump())
#     db.add(db_releve)
#     db.commit()
#     db.refresh(db_releve)
#     return db_releve

# @router.get("/", response_model=List[ReleveCapteurResponse])
# def read_releves(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     """
#     Récupère la liste des relevés (avec pagination).
#     """
#     releves = db.query(ReleveCapteur).offset(skip).limit(limit).all()
#     return releves

# @router.get("/{releve_id}", response_model=ReleveCapteurResponse)
# def read_releve(releve_id: int, db: Session = Depends(get_db)):
#     """
#     Récupère un relevé spécifique par son ID.
#     """
#     releve = db.query(ReleveCapteur).filter(ReleveCapteur.id == releve_id).first()
#     if not releve:
#         raise HTTPException(status_code=404, detail="Relevé non trouvé")
#     return releve

# @router.delete("/{releve_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_releve(releve_id: int, db: Session = Depends(get_db)):
#     """
#     Supprime un relevé.
#     """
#     releve = db.query(ReleveCapteur).filter(ReleveCapteur.id == releve_id).first()
#     if not releve:
#         raise HTTPException(status_code=404, detail="Relevé non trouvé")
    
#     db.delete(releve)
#     db.commit()
#     return None

# @router.get("/capteur/{capteur_id}", response_model=List[ReleveCapteurResponse])
# def read_releves_by_capteur(capteur_id: str, db: Session = Depends(get_db)):
#     return db.query(ReleveCapteur).filter(ReleveCapteur.capteur_id == capteur_id).all()

# api/v1/iot/releves.py
"""
Routes pour les relevés de capteurs IoT.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.models.iot.releve import ReleveCapteur
from app.models.iot.capteur import Capteur
from app.schemas.iot.releve import ReleveCapteurCreate, ReleveCapteurResponse
from app.core.dependencies import get_current_active_user
from app.core.permissions import require_roles
from app.models.enums import UserRole

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def valider_valeur_capteur(valeur: float, capteur: Capteur) -> tuple[bool, Optional[str]]:
    """
    Valide si la valeur est dans les plages acceptables du capteur.
    
    Returns:
        tuple: (est_valide, message_erreur)
    """
    if capteur.valeur_min is not None and valeur < capteur.valeur_min:
        return False, f"Valeur {valeur} inférieure au minimum {capteur.valeur_min}"
    
    if capteur.valeur_max is not None and valeur > capteur.valeur_max:
        return False, f"Valeur {valeur} supérieure au maximum {capteur.valeur_max}"
    
    return True, None


def verifier_alerte_seuil(capteur: Capteur, valeur: float) -> Optional[str]:
    """
    Vérifie si la valeur dépasse les seuils d'alerte.
    """
    if capteur.seuil_alerte_bas and valeur < capteur.seuil_alerte_bas:
        return f"Alerte basse: {valeur} < {capteur.seuil_alerte_bas}"
    
    if capteur.seuil_alerte_haut and valeur > capteur.seuil_alerte_haut:
        return f"Alerte haute: {valeur} > {capteur.seuil_alerte_haut}"
    
    return None


# ============================================================================
# CRÉER UN RELEVÉ
# ============================================================================
@router.post("/", response_model=ReleveCapteurResponse, status_code=status.HTTP_201_CREATED)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def create_releve(
    releve: ReleveCapteurCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    CRÉE UN NOUVEAU RELEVÉ POUR UN CAPTEUR SPÉCIFIQUE.
    
    Args:
        releve: Données du relevé
        db: Session de base de données
        current_user: Utilisateur authentifié
    """
    try:
        # 1. Vérifier que le capteur existe
        capteur = db.query(Capteur).filter(Capteur.id == releve.capteur_id).first()
        if not capteur:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Capteur avec l'ID '{releve.capteur_id}' non trouvé"
            )
        
        # 2. Vérifier que le capteur est actif
        if not capteur.est_actif:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Le capteur '{capteur.code}' est désactivé, impossible d'ajouter des relevés"
            )
        
        # 3. Valider la valeur par rapport aux plages du capteur
        est_valide, erreur = valider_valeur_capteur(releve.valeur, capteur)
        
        # 4. Vérifier les alertes
        alerte = verifier_alerte_seuil(capteur, releve.valeur)
        if alerte:
            logger.warning(f"⚠️ {alerte} | Capteur: {capteur.code}")
        
        # 5. Création du relevé
        now = datetime.utcnow()
        
        db_releve = ReleveCapteur(
            capteur_id=releve.capteur_id,
            valeur=releve.valeur,
            timestamp=now,
            batterie=releve.batterie,
            signal=releve.signal,
            temperature_interne=releve.temperature_interne,
            est_valide=est_valide,
            erreur=erreur if not est_valide else None,
            created_at=now,
            updated_at=now,
            created_by=current_user.id if hasattr(ReleveCapteur, 'created_by') else None
        )
        
        db.add(db_releve)
        db.commit()
        db.refresh(db_releve)
        
        # 6. Mettre à jour la dernière valeur du capteur
        capteur.derniere_valeur = releve.valeur
        capteur.derniere_mise_a_jour = now
        db.commit()
        
        logger.info(f"✅ Relevé créé | Capteur: {capteur.code} | Valeur: {releve.valeur} | Valide: {est_valide}")
        
        return db_releve
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur create_releve: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création: {str(e)}"
        )


# ============================================================================
# LISTER LES RELEVÉS
# ============================================================================
@router.get("/", response_model=List[ReleveCapteurResponse])
async def read_releves(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments"),
    capteur_id: Optional[str] = Query(None, description="Filtrer par capteur"),
    date_debut: Optional[datetime] = Query(None, description="Date de début"),
    date_fin: Optional[datetime] = Query(None, description="Date de fin"),
    valeur_min: Optional[float] = Query(None, description="Valeur minimum"),
    valeur_max: Optional[float] = Query(None, description="Valeur maximum"),
    est_valide: Optional[bool] = Query(None, description="Filtrer par validité"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE LA LISTE DES RELEVÉS AVEC FILTRES ET PAGINATION.
    """
    try:
        query = db.query(ReleveCapteur)
        
        # Filtres
        if capteur_id:
            query = query.filter(ReleveCapteur.capteur_id == capteur_id)
        if date_debut:
            query = query.filter(ReleveCapteur.timestamp >= date_debut)
        if date_fin:
            query = query.filter(ReleveCapteur.timestamp <= date_fin)
        if valeur_min:
            query = query.filter(ReleveCapteur.valeur >= valeur_min)
        if valeur_max:
            query = query.filter(ReleveCapteur.valeur <= valeur_max)
        if est_valide is not None:
            query = query.filter(ReleveCapteur.est_valide == est_valide)
        
        releves = query.order_by(ReleveCapteur.timestamp.desc()).offset(skip).limit(limit).all()
        
        logger.info(f"📊 Liste des relevés | Total: {len(releves)}")
        
        return releves
        
    except Exception as e:
        logger.error(f"❌ Erreur read_releves: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# RÉCUPÉRER UN RELEVÉ PAR ID
# ============================================================================
@router.get("/{releve_id}", response_model=ReleveCapteurResponse)
async def read_releve(
    releve_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE UN RELEVÉ SPÉCIFIQUE PAR SON ID.
    """
    try:
        releve = db.query(ReleveCapteur).filter(ReleveCapteur.id == releve_id).first()
        
        if not releve:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Relevé avec l'ID '{releve_id}' non trouvé"
            )
        
        return releve
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur read_releve: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# RELEVÉS PAR CAPTEUR
# ============================================================================
@router.get("/capteur/{capteur_id}", response_model=List[ReleveCapteurResponse])
async def read_releves_by_capteur(
    capteur_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de relevés"),
    date_debut: Optional[datetime] = Query(None, description="Date de début"),
    date_fin: Optional[datetime] = Query(None, description="Date de fin"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE TOUS LES RELEVÉS D'UN CAPTEUR SPÉCIFIQUE.
    """
    try:
        # Vérifier que le capteur existe
        capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()
        if not capteur:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Capteur avec l'ID '{capteur_id}' non trouvé"
            )
        
        query = db.query(ReleveCapteur).filter(ReleveCapteur.capteur_id == capteur_id)
        
        if date_debut:
            query = query.filter(ReleveCapteur.timestamp >= date_debut)
        if date_fin:
            query = query.filter(ReleveCapteur.timestamp <= date_fin)
        
        releves = query.order_by(ReleveCapteur.timestamp.desc()).limit(limit).all()
        
        logger.info(f"📊 Relevés du capteur {capteur.code} | Total: {len(releves)}")
        
        return releves
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur read_releves_by_capteur: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# DERNIER RELEVÉ D'UN CAPTEUR
# ============================================================================
@router.get("/capteur/{capteur_id}/dernier", response_model=ReleveCapteurResponse)
async def read_last_releve(
    capteur_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE LE DERNIER RELEVÉ D'UN CAPTEUR.
    """
    try:
        # Vérifier que le capteur existe
        capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()
        if not capteur:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Capteur avec l'ID '{capteur_id}' non trouvé"
            )
        
        releve = db.query(ReleveCapteur).filter(
            ReleveCapteur.capteur_id == capteur_id
        ).order_by(ReleveCapteur.timestamp.desc()).first()
        
        if not releve:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucun relevé trouvé pour le capteur {capteur.code}"
            )
        
        return releve
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur read_last_releve: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# STATISTIQUES DES RELEVÉS D'UN CAPTEUR
# ============================================================================
@router.get("/capteur/{capteur_id}/statistiques", response_model=Dict[str, Any])
async def get_releves_statistiques(
    capteur_id: str,
    periode: str = Query("24h", regex="^(24h|7d|30d|all)$", description="Période d'analyse"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE LES STATISTIQUES DES RELEVÉS D'UN CAPTEUR.
    """
    try:
        from sqlalchemy import func
        
        # Vérifier que le capteur existe
        capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()
        if not capteur:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Capteur avec l'ID '{capteur_id}' non trouvé"
            )
        
        # Déterminer la date de début selon la période
        now = datetime.utcnow()
        if periode == "24h":
            date_debut = now - timedelta(hours=24)
        elif periode == "7d":
            date_debut = now - timedelta(days=7)
        elif periode == "30d":
            date_debut = now - timedelta(days=30)
        else:
            date_debut = None
        
        # Construire la requête
        query = db.query(ReleveCapteur).filter(ReleveCapteur.capteur_id == capteur_id)
        if date_debut:
            query = query.filter(ReleveCapteur.timestamp >= date_debut)
        
        # Calculer les statistiques
        total = query.count()
        
        stats = {
            "capteur_id": capteur_id,
            "capteur_code": capteur.code,
            "capteur_type": capteur.type.value if hasattr(capteur.type, 'value') else str(capteur.type),
            "periode": periode,
            "total_releves": total,
            "valeur_min": None,
            "valeur_max": None,
            "valeur_moyenne": None,
            "dernier_releve": None,
            "taux_validite": 0
        }
        
        if total > 0:
            # Valeur min, max, moyenne
            min_val = query.with_entities(func.min(ReleveCapteur.valeur)).scalar()
            max_val = query.with_entities(func.max(ReleveCapteur.valeur)).scalar()
            avg_val = query.with_entities(func.avg(ReleveCapteur.valeur)).scalar()
            
            # Dernier relevé
            dernier = query.order_by(ReleveCapteur.timestamp.desc()).first()
            
            # Nombre de relevés valides
            valides = query.filter(ReleveCapteur.est_valide == True).count()
            
            stats["valeur_min"] = round(float(min_val), 2) if min_val else None
            stats["valeur_max"] = round(float(max_val), 2) if max_val else None
            stats["valeur_moyenne"] = round(float(avg_val), 2) if avg_val else None
            stats["dernier_releve"] = {
                "valeur": dernier.valeur,
                "timestamp": dernier.timestamp.isoformat(),
                "est_valide": dernier.est_valide
            }
            stats["taux_validite"] = round((valides / total) * 100, 1)
        
        logger.info(f"📊 Statistiques du capteur {capteur.code} | Période: {periode} | Relevés: {total}")
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur get_releves_statistiques: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul des statistiques: {str(e)}"
        )


# ============================================================================
# SUPPRIMER UN RELEVÉ
# ============================================================================
@router.delete("/{releve_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_roles([UserRole.ADMIN])
async def delete_releve(
    releve_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    SUPPRIME UN RELEVÉ (ADMIN UNIQUEMENT).
    """
    try:
        releve = db.query(ReleveCapteur).filter(ReleveCapteur.id == releve_id).first()
        
        if not releve:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Relevé avec l'ID '{releve_id}' non trouvé"
            )
        
        logger.info(f"🗑️ Relevé supprimé | ID: {releve_id} | Capteur: {releve.capteur_id} | Valeur: {releve.valeur}")
        
        db.delete(releve)
        db.commit()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur delete_releve: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )


# ============================================================================
# SUPPRIMER LES RELEVÉS ANCIENS (ADMIN)
# ============================================================================
# api/v1/iot/releves.py - Version corrigée

@router.delete("/anciens/{jours}", status_code=status.HTTP_200_OK)
@require_roles([UserRole.ADMIN])
async def delete_old_releves(
    jours: int,  # Supprimer Query, c'est un paramètre de chemin
    capteur_id: Optional[str] = Query(None, description="ID du capteur (optionnel)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    SUPPRIME LES RELEVÉS PLUS VIEUX QUE N JOURS.
    
    Args:
        jours: Nombre de jours de conservation (dans l'URL)
        capteur_id: ID du capteur (optionnel, dans la query string)
    """
    try:
        # Validation du nombre de jours
        if jours < 1 or jours > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le nombre de jours doit être compris entre 1 et 365"
            )
        
        date_limite = datetime.utcnow() - timedelta(days=jours)
        
        query = db.query(ReleveCapteur).filter(ReleveCapteur.timestamp < date_limite)
        
        if capteur_id:
            # Vérifier que le capteur existe
            capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()
            if not capteur:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Capteur avec l'ID '{capteur_id}' non trouvé"
                )
            query = query.filter(ReleveCapteur.capteur_id == capteur_id)
        
        count = query.count()
        
        # Confirmation si beaucoup de relevés
        if count > 10000:
            logger.warning(f"⚠️ Suppression massive de {count} relevés pour {jours} jours")
        
        query.delete(synchronize_session=False)
        db.commit()
        
        logger.info(f"🗑️ Suppression des relevés anciens | {count} relevés supprimés | Jours: {jours}")
        
        return {
            "message": f"{count} relevés plus vieux que {jours} jours ont été supprimés",
            "jours_conservation": jours,
            "releves_supprimes": count,
            "capteur_id": capteur_id if capteur_id else "tous"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur delete_old_releves: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )