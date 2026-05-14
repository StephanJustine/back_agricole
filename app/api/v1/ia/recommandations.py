# from fastapi import APIRouter, Depends, HTTPException, status, Query
# from sqlalchemy.orm import Session
# from typing import List
# from datetime import datetime

# # Importations des dépendances et modèles
# from ....database import get_db 
# from ....models.ia.recommandation import Recommandation
# from ....schemas.ia.recommandation import (
#     RecommandationCreate, 
#     RecommandationResponse, 
#     RecommandationUpdate
# )

# router = APIRouter()

# @router.post("/", response_model=RecommandationResponse, status_code=status.HTTP_201_CREATED)
# def create_recommandation(obj_in: RecommandationCreate, db: Session = Depends(get_db)):
#     """
#     **Création d'une recommandation avec analyse de criticité.**
    
#     Logique appliquée :
#     1. Scan du message pour détecter des mots-clés d'urgence.
#     2. Injection de métadonnées système dans le champ JSON 'details'.
#     3. Initialisation de la date d'émission au format UTC.
#     """
#     # Analyse sémantique simplifiée pour ajuster la priorité automatiquement
#     urgences = ["gel", "sécheresse", "pucerons", "mildiou", "tempête"]
#     message_content = obj_in.message.lower()
    
#     priorite_finale = obj_in.priorite
#     if any(mot in message_content for mot in urgences):
#         # On force la priorité à 1 (Urgent) si un risque agronomique est détecté
#         priorite_finale = 1 

#     # Préparation des données pour SQLAlchemy
#     # On sépare 'details' pour s'assurer qu'il contient au moins la source
#     extra_info = obj_in.details or {}
#     extra_info["source"] = "moteur_agronomique_v1"

#     db_obj = Recommandation(
#         type=obj_in.type,
#         parcelle_id=obj_in.parcelle_id,
#         culture_id=obj_in.culture_id,
#         titre=obj_in.titre,
#         message=obj_in.message,
#         priorite=priorite_finale,
#         details=extra_info,
#         date_emission=datetime.utcnow()
#     )
    
#     db.add(db_obj)
#     db.commit()
#     db.refresh(db_obj)
#     return db_obj

# @router.patch("/{recommandation_id}/statut", response_model=RecommandationResponse)
# def update_recommandation_status(
#     recommandation_id: str, 
#     obj_in: RecommandationUpdate, 
#     db: Session = Depends(get_db)
# ):
#     """
#     **Mise à jour intelligente du cycle de vie d'une recommandation.**
    
#     Logique de transition d'état :
#     - Si 'est_lue' passe à True : on enregistre l'horodatage précis.
#     - Si 'est_appliquee' passe à True : cela valide l'action de l'agriculteur sur le terrain.
#     - Une recommandation appliquée est automatiquement marquée comme lue.
#     """
#     db_obj = db.query(Recommandation).filter(Recommandation.id == recommandation_id).first()
#     if not db_obj:
#         raise HTTPException(status_code=404, detail="Recommandation non trouvée")

#     now = datetime.utcnow()
#     update_data = obj_in.dict(exclude_unset=True)

#     # Règle métier : Si appliquée, alors forcément lue
#     if update_data.get("est_appliquee"):
#         db_obj.est_appliquee = True
#         db_obj.date_action = now
#         db_obj.est_lue = True
#         if not db_obj.date_lecture:
#             db_obj.date_lecture = now
            
#     # Gestion de la lecture simple
#     if update_data.get("est_lue") and not db_obj.est_lue:
#         db_obj.est_lue = True
#         db_obj.date_lecture = now

#     db.commit()
#     db.refresh(db_obj)
#     return db_obj

# @router.get("/dashboard/urgences", response_model=List[RecommandationResponse])
# def get_priorite_dashboard(db: Session = Depends(get_db)):
#     """
#     **Extraction des alertes pour le tableau de bord.**
    
#     Récupère uniquement les recommandations de priorité 1 (Urgent) 
#     qui n'ont pas encore été traitées par l'utilisateur.
#     """
#     return db.query(Recommandation).filter(
#         Recommandation.priorite == 1,
#         Recommandation.est_appliquee == False
#     ).order_by(Recommandation.date_emission.desc()).all()

# @router.delete("/{recommandation_id}", status_code=status.HTTP_204_NO_CONTENT)
# def archive_recommandation(recommandation_id: str, db: Session = Depends(get_db)):
#     """
#     **Suppression (ou archivage) d'une recommandation.**
    
#     Note : En production, on préférera souvent un 'soft delete' (is_deleted=True) 
#     plutôt qu'une suppression physique pour garder l'historique agronomique.
#     """
#     db_obj = db.query(Recommandation).filter(Recommandation.id == recommandation_id).first()
#     if not db_obj:
#         raise HTTPException(status_code=404, detail="Recommandation introuvable")
    
#     db.delete(db_obj)
#     db.commit()
#     return None

# api/v1/ia/recommandations.py
"""
Routes pour les recommandations agronomiques.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import re

from app.database import get_db
from app.models.ia.recommandation import Recommandation
from app.models.parcelle import Parcelle
from app.models.culture import Culture
from app.models.user import User
from app.schemas.ia.recommandation import (
    RecommandationCreate, 
    RecommandationResponse, 
    RecommandationUpdate
)
from app.core.dependencies import get_current_active_user
from app.core.permissions import require_roles
from app.models.enums import UserRole, TypeRecommandation

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# CONSTANTES DE SÉCURITÉ
# ============================================================================
MOTS_URGENCE = {
    "gel": 1, "sécheresse": 1, "pucerons": 1, "mildiou": 1, 
    "tempête": 1, "inondation": 1, "maladie": 2, "ravageur": 2,
    "carence": 2, "fertilisation": 3, "arrosage": 3, "taille": 3
}
PRIORITE_MAX = 3
PRIORITE_MIN = 1


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def analyser_criticite(message: str) -> int:
    """
    Analyse le message et retourne la priorité basée sur les mots-clés.
    
    Args:
        message: Contenu du message à analyser
        
    Returns:
        Priorité calculée (1 = Urgent, 2 = Important, 3 = Normal)
    """
    message_lower = message.lower()
    
    # Recherche des mots d'urgence
    for mot in MOTS_URGENCE.keys():
        if mot in message_lower:
            return 1  # Urgent si mot d'urgence détecté
    
    # Détection de mentions de dates (ex: "demain", "ce soir")
    urgence_temporelle = re.search(r'(demain|ce soir|immédiatement|urgence|rapidement)', message_lower)
    if urgence_temporelle:
        return 2  # Important
    
    return 3  # Normal


def valider_parcelle(parcelle_id: str, db: Session) -> bool:
    """Vérifie si la parcelle existe et est active."""
    parcelle = db.query(Parcelle).filter(
        Parcelle.id == parcelle_id,
        Parcelle.is_active == True
    ).first()
    return parcelle is not None


def valider_culture(culture_id: Optional[str], db: Session) -> bool:
    """Vérifie si la culture existe et est active."""
    if not culture_id:
        return True
    culture = db.query(Culture).filter(
        Culture.id == culture_id,
        Culture.is_active == True
    ).first()
    return culture is not None

# ============================================================================
# CRÉER UNE RECOMMANDATION
# ============================================================================
@router.post("/", response_model=RecommandationResponse, status_code=status.HTTP_201_CREATED)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def create_recommandation(
    obj_in: RecommandationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    CRÉE UNE RECOMMANDATION AGRONOMIQUE AVEC ANALYSE DE CRITICITÉ.
    
    Cette route analyse automatiquement le message pour détecter les urgences
    et ajuster la priorité en conséquence.
    
    Logique appliquée :
    1. Validation des entrées (parcelle, culture)
    2. Analyse sémantique du message pour détection d'urgence
    3. Calcul automatique de la priorité
    4. Injection de métadonnées système
    5. Sauvegarde en base de données
    
    Args:
        obj_in: Données de la recommandation
        background_tasks: Tâches asynchrones (notifications)
        db: Session de base de données
        current_user: Utilisateur authentifié
        
    Returns:
        RecommandationResponse: La recommandation créée
    """
    try:
        # --------------------------------------------------------------------
        # 1. Validation des relations
        # --------------------------------------------------------------------
        parcelle = db.query(Parcelle).filter(
            Parcelle.id == obj_in.parcelle_id,
            Parcelle.is_active == True
        ).first()
        
        if not parcelle:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parcelle avec l'ID '{obj_in.parcelle_id}' non trouvée ou inactive"
            )
        
        # Validation de la culture si fournie
        if obj_in.culture_id:
            from app.models.culture import Culture
            culture = db.query(Culture).filter(
                Culture.id == obj_in.culture_id,
                Culture.is_active == True
            ).first()
            if not culture:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Culture avec l'ID '{obj_in.culture_id}' non trouvée ou inactive"
                )
        
        # --------------------------------------------------------------------
        # 2. Validation du message
        # --------------------------------------------------------------------
        if len(obj_in.message) > 2000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le message ne peut pas dépasser 2000 caractères"
            )
        
        if not obj_in.message or not obj_in.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le message ne peut pas être vide"
            )
        
        if not obj_in.titre or not obj_in.titre.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le titre ne peut pas être vide"
            )
        
        # --------------------------------------------------------------------
        # 3. Normalisation du type de recommandation
        # --------------------------------------------------------------------
        type_normalise = obj_in.type
        if isinstance(type_normalise, str):
            type_normalise = type_normalise.lower()
            # Mapping des valeurs
            mapping_types = {
                "irrigation": "arrosage",
                "irriguer": "arrosage",
                "water": "arrosage",
                "fertilizer": "fertilisation",
                "engrais": "fertilisation",
                "pest": "traitement",
                "pesticide": "traitement",
                "planning": "calendrier"
            }
            if type_normalise in mapping_types:
                type_normalise = mapping_types[type_normalise]
        
        # Vérifier que le type est valide
        types_valides = [t.value for t in TypeRecommandation]
        if type_normalise not in types_valides:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Type de recommandation invalide. Types acceptés: {', '.join(types_valides)}"
            )
        
        # --------------------------------------------------------------------
        # 4. Analyse de criticité
        # --------------------------------------------------------------------
        priorite_auto = analyser_criticite(obj_in.message)
        
        # La priorité explicite écrase l'auto-détection mais l'urgence absolue prime
        priorite_finale = obj_in.priorite
        if priorite_auto == 1:  # Urgence détectée
            priorite_finale = 1
        
        # S'assurer que la priorité est dans les limites
        priorite_finale = max(1, min(3, priorite_finale))
        
        # --------------------------------------------------------------------
        # 5. Préparation des métadonnées
        # --------------------------------------------------------------------
        extra_info = obj_in.details or {}
        extra_info.update({
            "source": "moteur_agronomique_v1",
            "created_by": current_user.email,
            "created_by_id": str(current_user.id),
            "created_by_role": current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
            "analyse_automatique": priorite_auto,
            "priorite_initiale": obj_in.priorite,
            "priorite_finale": priorite_finale,
            "version_api": "1.0",
            "parcelle_nom": parcelle.nom if hasattr(parcelle, 'nom') else None,
            "parcelle_code": parcelle.code if hasattr(parcelle, 'code') else None
        })
        
        # Ajouter les infos de culture si disponible
        if obj_in.culture_id and culture:
            extra_info["culture_nom"] = culture.nom if hasattr(culture, 'nom') else None
        
        # --------------------------------------------------------------------
        # 6. Création de l'objet
        # --------------------------------------------------------------------
        now = datetime.utcnow()
        
        db_obj = Recommandation(
            type=type_normalise,
            parcelle_id=obj_in.parcelle_id,
            culture_id=obj_in.culture_id,
            titre=obj_in.titre.strip(),
            message=obj_in.message.strip(),
            priorite=priorite_finale,
            details=extra_info,
            date_emission=now,
            created_at=now,
            updated_at=now,
            est_lue=False,
            est_appliquee=False
        )
        
        # Ajouter created_by si le champ existe
        if hasattr(Recommandation, 'created_by'):
            db_obj.created_by = current_user.id
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        # --------------------------------------------------------------------
        # 7. Notifications asynchrones (si priorité urgente)
        # --------------------------------------------------------------------
        if priorite_finale == 1:
            background_tasks.add_task(
                envoyer_notification_urgence, 
                db_obj.id, 
                obj_in.parcelle_id,
                parcelle.nom if hasattr(parcelle, 'nom') else obj_in.parcelle_id
            )
        
        logger.info(f"✅ Recommandation créée | ID: {db_obj.id} | Type: {type_normalise} | Priorité: {priorite_finale} | Par: {current_user.email}")
        
        return db_obj
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur create_recommandation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création: {str(e)}"
        )


# ============================================================================
# FONCTIONS DE NOTIFICATION
# ============================================================================
async def envoyer_notification_urgence(recommandation_id: str, parcelle_id: str, parcelle_nom: str):
    """
    Envoie des notifications pour les recommandations urgentes.
    Cette fonction s'exécute en arrière-plan.
    
    Args:
        recommandation_id: ID de la recommandation
        parcelle_id: ID de la parcelle concernée
        parcelle_nom: Nom de la parcelle
    """
    try:
        # Simuler l'envoi de notification
        # À remplacer par un vrai service (email, SMS, push notification)
        logger.info(f"🔔 NOTIFICATION URGENTE")
        logger.info(f"   - Recommandation ID: {recommandation_id}")
        logger.info(f"   - Parcelle: {parcelle_nom} ({parcelle_id})")
        logger.info(f"   - Message: Alerte agronomique nécessitant une attention immédiate")
        
        # Exemple d'envoi d'email (à décommenter et configurer)
        # await EmailService.send_alerte_parcelle(
        #     parcelle_id=parcelle_id,
        #     sujet="Alerte agronomique urgente",
        #     message=f"Une recommandation urgente a été émise pour votre parcelle {parcelle_nom}"
        # )
        
    except Exception as e:
        logger.error(f"❌ Erreur notification: {e}")

        
# ============================================================================
# METTRE À JOUR LE STATUT D'UNE RECOMMANDATION
# ============================================================================
@router.patch("/{recommandation_id}/statut", response_model=RecommandationResponse)
async def update_recommandation_status(
    recommandation_id: str,
    obj_in: RecommandationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    MET À JOUR LE STATUT D'UNE RECOMMANDATION.
    
    Gère le cycle de vie des recommandations agricoles.
    
    Logique de transition :
    - Lecture : enregistre la date et l'utilisateur
    - Application : valide l'action terrain et enregistre l'horodatage
    - Une recommandation appliquée est automatiquement marquée comme lue
    """
    try:
        # Récupération de la recommandation
        db_obj = db.query(Recommandation).filter(Recommandation.id == recommandation_id).first()
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recommandation avec l'ID '{recommandation_id}' non trouvée"
            )
        
        now = datetime.utcnow()
        update_data = obj_in.model_dump(exclude_unset=True)
        modifications = []
        
        # Règle métier : Application = Lecture automatique
        if update_data.get("est_appliquee", False):
            if not db_obj.est_appliquee:
                db_obj.est_appliquee = True
                db_obj.date_action = now
                modifications.append("appliquée")
                
                details = db_obj.details or {}
                details["appliquee_par"] = current_user.email
                details["appliquee_le"] = now.isoformat()
                db_obj.details = details
            
            if not db_obj.est_lue:
                db_obj.est_lue = True
                db_obj.date_lecture = now
                modifications.append("lue")
        
        # Gestion de la lecture seule
        if update_data.get("est_lue", False) and not db_obj.est_lue:
            db_obj.est_lue = True
            db_obj.date_lecture = now
            modifications.append("lue")
            
            details = db_obj.details or {}
            details["lue_par"] = current_user.email
            details["lue_le"] = now.isoformat()
            db_obj.details = details
        
        db_obj.updated_at = now
        db_obj.updated_by = current_user.id
        
        db.commit()
        db.refresh(db_obj)
        
        if modifications:
            logger.info(f"📝 Recommandation {recommandation_id} modifiée: {', '.join(modifications)} | Par: {current_user.email}")
        
        return db_obj
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur update_recommandation_status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


# ============================================================================
# TABLEAU DE BORD - ALERTES URGENTES
# ============================================================================
@router.get("/dashboard/urgences", response_model=List[RecommandationResponse])
async def get_priorite_dashboard(
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum d'alertes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE LES ALERTES URGENTES POUR LE TABLEAU DE BORD.
    
    Retourne uniquement les recommandations de priorité 1 (urgentes)
    qui n'ont pas encore été traitées.
    """
    try:
        query = db.query(Recommandation).filter(
            Recommandation.priorite == 1,
            Recommandation.est_appliquee == False
        )
        
        # Si l'utilisateur n'est pas admin, filtrer par ses parcelles
        if current_user.role != UserRole.ADMIN:
            parcelles_ids = [p.id for p in current_user.parcelles] if hasattr(current_user, 'parcelles') else []
            if parcelles_ids:
                query = query.filter(Recommandation.parcelle_id.in_(parcelles_ids))
        
        urgences = query.order_by(
            Recommandation.date_emission.desc()
        ).limit(limit).all()
        
        logger.info(f"🚨 Dashboard | {len(urgences)} urgences actives")
        
        return urgences
        
    except Exception as e:
        logger.error(f"❌ Erreur get_priorite_dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des urgences"
        )


# ============================================================================
# LISTER LES RECOMMANDATIONS
# ============================================================================
@router.get("/", response_model=List[RecommandationResponse])
async def get_recommandations(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=500, description="Nombre maximum d'éléments"),
    parcelle_id: Optional[str] = Query(None, description="Filtrer par parcelle"),
    type_recommandation: Optional[TypeRecommandation] = Query(None, description="Filtrer par type"),
    priorite: Optional[int] = Query(None, ge=1, le=3, description="Filtrer par priorité"),
    est_lue: Optional[bool] = Query(None, description="Filtrer par statut de lecture"),
    est_appliquee: Optional[bool] = Query(None, description="Filtrer par statut d'application"),
    date_debut: Optional[datetime] = Query(None, description="Date début"),
    date_fin: Optional[datetime] = Query(None, description="Date fin"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE LA LISTE DES RECOMMANDATIONS AVEC FILTRES.
    """
    try:
        query = db.query(Recommandation)
        
        # Filtres
        if parcelle_id:
            query = query.filter(Recommandation.parcelle_id == parcelle_id)
        if type_recommandation:
            query = query.filter(Recommandation.type == type_recommandation)
        if priorite:
            query = query.filter(Recommandation.priorite == priorite)
        if est_lue is not None:
            query = query.filter(Recommandation.est_lue == est_lue)
        if est_appliquee is not None:
            query = query.filter(Recommandation.est_appliquee == est_appliquee)
        if date_debut:
            query = query.filter(Recommandation.date_emission >= date_debut)
        if date_fin:
            query = query.filter(Recommandation.date_emission <= date_fin)
        
        # Restriction par parcelles pour les non-admins
        if current_user.role != UserRole.ADMIN:
            parcelles_ids = [p.id for p in current_user.parcelles] if hasattr(current_user, 'parcelles') else []
            if parcelles_ids:
                query = query.filter(Recommandation.parcelle_id.in_(parcelles_ids))
            else:
                return []
        
        recommandations = query.order_by(
            Recommandation.priorite.asc(),
            Recommandation.date_emission.desc()
        ).offset(skip).limit(limit).all()
        
        logger.info(f"📋 Liste recommandations | Affichées: {len(recommandations)}")
        
        return recommandations
        
    except Exception as e:
        logger.error(f"❌ Erreur get_recommandations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des recommandations"
        )


# ============================================================================
# RÉCUPÉRER UNE RECOMMANDATION PAR ID
# ============================================================================
@router.get("/{recommandation_id}", response_model=RecommandationResponse)
async def get_recommandation(
    recommandation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE UNE RECOMMANDATION SPÉCIFIQUE.
    """
    try:
        recommandation = db.query(Recommandation).filter(Recommandation.id == recommandation_id).first()
        
        if not recommandation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recommandation avec l'ID '{recommandation_id}' non trouvée"
            )
        
        # Vérification des accès
        if current_user.role != UserRole.ADMIN:
            parcelles_ids = [p.id for p in current_user.parcelles] if hasattr(current_user, 'parcelles') else []
            if recommandation.parcelle_id not in parcelles_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez pas accès à cette recommandation"
                )
        
        return recommandation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur get_recommandation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# SUPPRIMER UNE RECOMMANDATION (ADMIN)
# ============================================================================
@router.delete("/{recommandation_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_roles([UserRole.ADMIN])
async def archive_recommandation(
    recommandation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    SUPPRIME UNE RECOMMANDATION - ADMIN UNIQUEMENT.
    """
    try:
        recommandation = db.query(Recommandation).filter(Recommandation.id == recommandation_id).first()
        
        if not recommandation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recommandation avec l'ID '{recommandation_id}' non trouvée"
            )
        
        db.delete(recommandation)
        db.commit()
        
        logger.info(f"🗑️ Recommandation supprimée | ID: {recommandation_id} | Par: {current_user.email}")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur archive_recommandation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )


# ============================================================================
# FONCTIONS DE NOTIFICATION
# ============================================================================
async def envoyer_notification_urgence(recommandation_id: str, db: Session):
    """
    Envoie des notifications pour les recommandations urgentes.
    Cette fonction s'exécute en arrière-plan.
    """
    try:
        recommandation = db.query(Recommandation).filter(Recommandation.id == recommandation_id).first()
        if not recommandation:
            return
        
        parcelle = db.query(Parcelle).filter(Parcelle.id == recommandation.parcelle_id).first()
        if not parcelle:
            return
        
        logger.info(f"🔔 NOTIFICATION URGENTE | Parcelle: {parcelle.nom if hasattr(parcelle, 'nom') else parcelle.id} | Message: {recommandation.titre}")
        
    except Exception as e:
        logger.error(f"❌ Erreur notification: {e}")