# api/v1/ia/entrainements.py
"""
Routes pour les entraînements de modèles IA.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.database import get_db
from app.models.ia.entrainement import Entrainement
from app.models.ia.modele_ia import ModeleIA
from app.models.ia.dataset import Dataset
from app.schemas.ia.entrainement import (
    EntrainementCreate,
    EntrainementUpdate,
    EntrainementResponse,
    EntrainementListResponse
)
from app.core.dependencies import get_current_active_user
from app.core.permissions import require_roles
from app.models.enums import UserRole, StatusEntrainement

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def valider_modele(modele_id: str, db: Session) -> Optional[ModeleIA]:
    """Vérifie si le modèle existe et est actif."""
    modele = db.query(ModeleIA).filter(
        ModeleIA.id == modele_id,
        ModeleIA.est_actif == True
    ).first()
    return modele


# def valider_dataset(dataset_id: str, db: Session) -> Optional[Dataset]:
#     """Vérifie si le dataset existe et est actif."""
#     dataset = db.query(Dataset).filter(
#         Dataset.id == dataset_id,
#         Dataset.est_actif == True
#     ).first()
#     return dataset


def calculer_metriques_performance(entrainement: Entrainement) -> Dict[str, Any]:
    """Calcule les métriques de performance de l'entraînement."""
    metriques = {}
    
    if entrainement.precision is not None:
        metriques["precision"] = entrainement.precision
    if entrainement.rappel is not None:
        metriques["rappel"] = entrainement.rappel
    if entrainement.f1_score is not None:
        metriques["f1_score"] = entrainement.f1_score
    if entrainement.mae is not None:
        metriques["mae"] = entrainement.mae
    if entrainement.rmse is not None:
        metriques["rmse"] = entrainement.rmse
    if entrainement.r2 is not None:
        metriques["r2"] = entrainement.r2
    
    # Calculer la qualité globale (moyenne des métriques principales)
    notes = []
    if entrainement.precision:
        notes.append(entrainement.precision)
    if entrainement.rappel:
        notes.append(entrainement.rappel)
    if entrainement.f1_score:
        notes.append(entrainement.f1_score)
    
    if notes:
        metriques["qualite_globale"] = round(sum(notes) / len(notes), 3)
    
    return metriques


# ============================================================================
# CRÉER UN ENTRAÎNEMENT
# ============================================================================
# @router.post("/", response_model=EntrainementResponse, status_code=status.HTTP_201_CREATED)
# @require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
# async def create_entrainement(
#     obj_in: EntrainementCreate,
#     background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db),
#     current_user = Depends(get_current_active_user)
# ):
#     """
#     CRÉE UN NOUVEL ENTRAÎNEMENT POUR UN MODÈLE IA.
    
#     Args:
#         obj_in: Données de l'entraînement
#         background_tasks: Tâches asynchrones
#         db: Session de base de données
#         current_user: Utilisateur authentifié
        
#     Returns:
#         EntrainementResponse: L'entraînement créé
#     """
#     try:
#         # --------------------------------------------------------------------
#         # 1. Validation du modèle
#         # --------------------------------------------------------------------
#         modele = valider_modele(obj_in.modele_id, db)
#         if not modele:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail=f"Modèle IA avec l'ID '{obj_in.modele_id}' non trouvé ou inactif"
#             )
        
#         # --------------------------------------------------------------------
#         # 2. Validation du dataset
#         # --------------------------------------------------------------------
#         dataset = valider_dataset(obj_in.dataset_id, db)
#         if not dataset:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail=f"Dataset avec l'ID '{obj_in.dataset_id}' non trouvé ou inactif"
#             )
        
#         # --------------------------------------------------------------------
#         # 3. Vérifier qu'il n'y a pas d'entraînement en cours pour ce modèle
#         # --------------------------------------------------------------------
#         entrainement_en_cours = db.query(Entrainement).filter(
#             Entrainement.modele_id == obj_in.modele_id,
#             Entrainement.status == StatusEntrainement.EN_COURS
#         ).first()
        
#         if entrainement_en_cours:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail=f"Un entraînement est déjà en cours pour ce modèle (ID: {entrainement_en_cours.id})"
#             )
        
#         # --------------------------------------------------------------------
#         # 4. Création de l'entraînement
#         # --------------------------------------------------------------------
#         now = datetime.utcnow()
        
#         entrainement = Entrainement(
#             modele_id=obj_in.modele_id,
#             dataset_id=obj_in.dataset_id,
#             date_debut=now,
#             status=StatusEntrainement.EN_COURS,
#             params=obj_in.params or {},
#             logs=f"Entraînement démarré le {now.isoformat()} par {current_user.email}"
#         )
        
#         # Ajouter les métriques si fournies
#         if obj_in.precision is not None:
#             entrainement.precision = obj_in.precision
#         if obj_in.rappel is not None:
#             entrainement.rappel = obj_in.rappel
#         if obj_in.f1_score is not None:
#             entrainement.f1_score = obj_in.f1_score
#         if obj_in.mae is not None:
#             entrainement.mae = obj_in.mae
#         if obj_in.rmse is not None:
#             entrainement.rmse = obj_in.rmse
#         if obj_in.r2 is not None:
#             entrainement.r2 = obj_in.r2
        
#         if hasattr(Entrainement, 'created_by'):
#             entrainement.created_by = current_user.id
        
#         db.add(entrainement)
#         db.commit()
#         db.refresh(entrainement)
        
#         # --------------------------------------------------------------------
#         # 4. Démarrer l'entraînement en arrière-plan
#         # --------------------------------------------------------------------
#         background_tasks.add_task(
#             executer_entrainement,
#             entrainement.id,
#             obj_in.modele_id,
#             obj_in.dataset_id,
#             obj_in.params or {}
#         )
        
#         logger.info(f"✅ Entraînement créé | ID: {entrainement.id} | Modèle: {modele.nom} | Par: {current_user.email}")
        
#         return entrainement
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         db.rollback()
#         logger.error(f"❌ Erreur create_entrainement: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur lors de la création: {str(e)}"
#         )

# Version plus simple sans vérification d'état
def valider_dataset(dataset_id: str, db: Session) -> Optional[Dataset]:
    """Vérifie si le dataset existe."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    return dataset  # Retourne même si inactif, juste vérifie l'existence


@router.post("/", response_model=EntrainementResponse, status_code=status.HTTP_201_CREATED)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def create_entrainement(
    obj_in: EntrainementCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    try:
        # Vérifier l'existence du modèle
        modele = db.query(ModeleIA).filter(ModeleIA.id == obj_in.modele_id).first()
        if not modele:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Modèle IA non trouvé"
            )
        
        # Vérifier l'existence du dataset
        dataset = db.query(Dataset).filter(Dataset.id == obj_in.dataset_id).first()
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dataset non trouvé"
            )
        
        # Créer l'entraînement
        entrainement = Entrainement(
            modele_id=obj_in.modele_id,
            dataset_id=obj_in.dataset_id,
            date_debut=datetime.utcnow(),
            status=StatusEntrainement.EN_COURS,
            params=obj_in.params or {}
        )
        
        db.add(entrainement)
        db.commit()
        db.refresh(entrainement)
        
        return entrainement
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}"
        )
        
# ============================================================================
# LANCER UN ENTRAÎNEMENT (ASYNC)
# ============================================================================
async def executer_entrainement(
    entrainement_id: str,
    modele_id: str,
    dataset_id: str,
    params: Dict[str, Any]
):
    """
    Exécute l'entraînement du modèle en arrière-plan.
    Cette fonction simule l'entraînement - à adapter selon vos besoins.
    """
    try:
        logger.info(f"🚀 Démarrage de l'entraînement {entrainement_id}")
        
        # Simuler une tâche longue
        import asyncio
        await asyncio.sleep(5)  # Simulation d'entraînement
        
        # Ici, vous intégreriez votre logique d'entraînement réel
        # Par exemple:
        # - Charger le dataset
        # - Entraîner le modèle
        # - Calculer les métriques
        # - Sauvegarder le modèle entraîné
        
        # Simulation de résultats
        resultats = {
            "precision": 0.85,
            "rappel": 0.82,
            "f1_score": 0.83,
            "mae": 0.15,
            "rmse": 0.22,
            "r2": 0.78
        }
        
        # Mettre à jour l'entraînement dans la base
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            entrainement = db.query(Entrainement).filter(Entrainement.id == entrainement_id).first()
            if entrainement:
                entrainement.status = StatusEntrainement.TERMINE
                entrainement.date_fin = datetime.utcnow()
                entrainement.precision = resultats["precision"]
                entrainement.rappel = resultats["rappel"]
                entrainement.f1_score = resultats["f1_score"]
                entrainement.mae = resultats["mae"]
                entrainement.rmse = resultats["rmse"]
                entrainement.r2 = resultats["r2"]
                entrainement.logs += f"\nEntraînement terminé le {datetime.utcnow().isoformat()}\n"
                entrainement.logs += f"Résultats: {resultats}"
                db.commit()
                logger.info(f"✅ Entraînement {entrainement_id} terminé avec succès")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution de l'entraînement {entrainement_id}: {e}")
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            entrainement = db.query(Entrainement).filter(Entrainement.id == entrainement_id).first()
            if entrainement:
                entrainement.status = StatusEntrainement.ECHEC
                entrainement.date_fin = datetime.utcnow()
                entrainement.logs += f"\nERREUR: {str(e)}\n"
                db.commit()
        finally:
            db.close()


# ============================================================================
# LISTER LES ENTRAÎNEMENTS
# ============================================================================
@router.get("/", response_model=List[EntrainementResponse])
async def get_entrainements(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=500, description="Nombre maximum d'éléments"),
    modele_id: Optional[str] = Query(None, description="Filtrer par modèle IA"),
    dataset_id: Optional[str] = Query(None, description="Filtrer par dataset"),
    status: Optional[StatusEntrainement] = Query(None, description="Filtrer par statut"),
    date_debut: Optional[datetime] = Query(None, description="Date début"),
    date_fin: Optional[datetime] = Query(None, description="Date fin"),
    precision_min: Optional[float] = Query(None, ge=0, le=1, description="Précision minimum"),
    trier_par: str = Query("date_debut", description="Champ de tri"),
    ordre_desc: bool = Query(True, description="Tri décroissant"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE LA LISTE DES ENTRAÎNEMENTS AVEC FILTRES.
    """
    try:
        query = db.query(Entrainement)
        
        # Filtres
        if modele_id:
            query = query.filter(Entrainement.modele_id == modele_id)
        if dataset_id:
            query = query.filter(Entrainement.dataset_id == dataset_id)
        if status:
            query = query.filter(Entrainement.status == status)
        if date_debut:
            query = query.filter(Entrainement.date_debut >= date_debut)
        if date_fin:
            query = query.filter(Entrainement.date_debut <= date_fin)
        if precision_min:
            query = query.filter(Entrainement.precision >= precision_min)
        
        # Tri
        champ_tri = getattr(Entrainement, trier_par, Entrainement.date_debut)
        if ordre_desc:
            query = query.order_by(champ_tri.desc())
        else:
            query = query.order_by(champ_tri.asc())
        
        total = query.count()
        entrainements = query.offset(skip).limit(limit).all()
        
        logger.info(f"📊 Liste des entraînements | Total: {total} | Affichés: {len(entrainements)}")
        
        return entrainements
        
    except Exception as e:
        logger.error(f"❌ Erreur get_entrainements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# RÉCUPÉRER UN ENTRAÎNEMENT PAR ID
# ============================================================================
@router.get("/{entrainement_id}", response_model=EntrainementResponse)
async def get_entrainement(
    entrainement_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE UN ENTRAÎNEMENT SPÉCIFIQUE.
    """
    try:
        entrainement = db.query(Entrainement).filter(Entrainement.id == entrainement_id).first()
        
        if not entrainement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entraînement avec l'ID '{entrainement_id}' non trouvé"
            )
        
        return entrainement
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur get_entrainement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# METTRE À JOUR UN ENTRAÎNEMENT
# ============================================================================
@router.put("/{entrainement_id}", response_model=EntrainementResponse)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def update_entrainement(
    entrainement_id: str,
    obj_in: EntrainementUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    MET À JOUR UN ENTRAÎNEMENT EXISTANT.
    """
    try:
        entrainement = db.query(Entrainement).filter(Entrainement.id == entrainement_id).first()
        
        if not entrainement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entraînement avec l'ID '{entrainement_id}' non trouvé"
            )
        
        # Mise à jour des champs
        update_data = obj_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(entrainement, key) and value is not None:
                setattr(entrainement, key, value)
        
        # Si le statut passe à TERMINE, ajouter date_fin
        if obj_in.status == StatusEntrainement.TERMINE and not entrainement.date_fin:
            entrainement.date_fin = datetime.utcnow()
        
        # Si le statut passe à ECHEC, ajouter date_fin et log
        if obj_in.status == StatusEntrainement.ECHEC and not entrainement.date_fin:
            entrainement.date_fin = datetime.utcnow()
            entrainement.logs = (entrainement.logs or "") + f"\nÉchec de l'entraînement le {datetime.utcnow().isoformat()}\n"
        
        entrainement.updated_at = datetime.utcnow()
        if hasattr(Entrainement, 'updated_by'):
            entrainement.updated_by = current_user.id
        
        db.commit()
        db.refresh(entrainement)
        
        logger.info(f"✏️ Entraînement mis à jour | ID: {entrainement_id} | Status: {entrainement.status}")
        
        return entrainement
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur update_entrainement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


# ============================================================================
# SUPPRIMER UN ENTRAÎNEMENT
# ============================================================================
@router.delete("/{entrainement_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_roles([UserRole.ADMIN])
async def delete_entrainement(
    entrainement_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    SUPPRIME UN ENTRAÎNEMENT (ADMIN UNIQUEMENT).
    """
    try:
        entrainement = db.query(Entrainement).filter(Entrainement.id == entrainement_id).first()
        
        if not entrainement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entraînement avec l'ID '{entrainement_id}' non trouvé"
            )
        
        db.delete(entrainement)
        db.commit()
        
        logger.info(f"🗑️ Entraînement supprimé | ID: {entrainement_id} | Par: {current_user.email}")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur delete_entrainement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )


# ============================================================================
# ARRÊTER UN ENTRAÎNEMENT
# ============================================================================
@router.post("/{entrainement_id}/stop", response_model=EntrainementResponse)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def stop_entrainement(
    entrainement_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    ARRÊTE UN ENTRAÎNEMENT EN COURS.
    """
    try:
        entrainement = db.query(Entrainement).filter(Entrainement.id == entrainement_id).first()
        
        if not entrainement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entraînement avec l'ID '{entrainement_id}' non trouvé"
            )
        
        if entrainement.status != StatusEntrainement.EN_COURS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"L'entraînement n'est pas en cours (statut actuel: {entrainement.status})"
            )
        
        entrainement.status = StatusEntrainement.ANNULE
        entrainement.date_fin = datetime.utcnow()
        entrainement.logs = (entrainement.logs or "") + f"\nEntraînement arrêté par {current_user.email} le {datetime.utcnow().isoformat()}\n"
        entrainement.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(entrainement)
        
        logger.info(f"⏹️ Entraînement arrêté | ID: {entrainement_id} | Par: {current_user.email}")
        
        return entrainement
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur stop_entrainement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'arrêt: {str(e)}"
        )


# ============================================================================
# STATISTIQUES DES ENTRAÎNEMENTS
# ============================================================================
@router.get("/statistiques/resume", response_model=Dict[str, Any])
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def get_entrainement_statistiques(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE UN RÉSUMÉ STATISTIQUE DES ENTRAÎNEMENTS.
    """
    try:
        from sqlalchemy import func
        
        # Statistiques de base
        total = db.query(func.count(Entrainement.id)).scalar() or 0
        total_termines = db.query(func.count(Entrainement.id)).filter(Entrainement.status == StatusEntrainement.TERMINE).scalar() or 0
        total_echoues = db.query(func.count(Entrainement.id)).filter(Entrainement.status == StatusEntrainement.ECHEC).scalar() or 0
        total_en_cours = db.query(func.count(Entrainement.id)).filter(Entrainement.status == StatusEntrainement.EN_COURS).scalar() or 0
        
        # Métriques moyennes (des entraînements terminés)
        precision_moyenne = db.query(func.avg(Entrainement.precision)).filter(Entrainement.status == StatusEntrainement.TERMINE).scalar() or 0
        rappel_moyen = db.query(func.avg(Entrainement.rappel)).filter(Entrainement.status == StatusEntrainement.TERMINE).scalar() or 0
        f1_moyen = db.query(func.avg(Entrainement.f1_score)).filter(Entrainement.status == StatusEntrainement.TERMINE).scalar() or 0
        
        # Entraînements par modèle
        entrainements_par_modele = db.query(
            Entrainement.modele_id,
            func.count(Entrainement.id).label("total")
        ).group_by(Entrainement.modele_id).all()
        
        result = {
            "total_entrainements": total,
            "statuts": {
                "termines": total_termines,
                "echoues": total_echoues,
                "en_cours": total_en_cours,
                "taux_succes": round((total_termines / total * 100), 2) if total > 0 else 0
            },
            "metriques_moyennes": {
                "precision": round(float(precision_moyenne), 3),
                "rappel": round(float(rappel_moyen), 3),
                "f1_score": round(float(f1_moyen), 3)
            },
            "entrainements_par_modele": [
                {"modele_id": item[0], "total": item[1]}
                for item in entrainements_par_modele
            ],
            "dernier_entrainement": None
        }
        
        # Dernier entraînement
        dernier = db.query(Entrainement).order_by(Entrainement.date_debut.desc()).first()
        if dernier:
            result["dernier_entrainement"] = {
                "id": dernier.id,
                "status": dernier.status,
                "date_debut": dernier.date_debut.isoformat() if dernier.date_debut else None,
                "precision": dernier.precision
            }
        
        logger.info(f"📊 Statistiques des entraînements consultées par {current_user.email}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur get_entrainement_statistiques: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul des statistiques: {str(e)}"
        )