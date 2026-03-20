"""
Routes CRUD pour les maladies.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, datetime, timedelta
import logging

from ...database import get_db
from ...models.maladie import Maladie
from ...models.culture import Culture
from ...models.parcelle import Parcelle
from ...models.user import User
from ...models.enums import TypeMaladie
from ...schemas.maladie import *
from ...core.dependencies import get_current_active_user, get_current_admin_user
from ...core.pagination import paginate
from ...core.exceptions import NotFoundException, BadRequestException
from ...core.historique import HistoriqueService
from ...services.notification_service import NotificationService

logger = logging.getLogger(__name__)
router = APIRouter()


# ========================
# LISTE DES MALADIES
# ========================
@router.get("/", response_model=MaladieList)
async def get_maladies(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(20, ge=1, le=100, description="Nombre d'éléments par page"),
    culture_id: Optional[str] = Query(None, description="Filtrer par culture"),
    type: Optional[TypeMaladie] = Query(None, description="Filtrer par type"),
    est_resolu: Optional[bool] = Query(None, description="Filtrer par statut"),
    gravite_min: Optional[int] = Query(None, ge=1, le=5, description="Gravité minimale"),
    date_debut: Optional[date] = Query(None, description="Date de début"),
    date_fin: Optional[date] = Query(None, description="Date de fin"),
    sort_by: str = Query("date_detection", description="Tri par champ"),
    sort_desc: bool = Query(True, description="Tri décroissant"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère la liste des maladies de l'utilisateur connecté.
    """
    # Jointure pour vérifier que les cultures appartiennent à l'utilisateur
    query = db.query(Maladie).join(Culture).join(Parcelle).filter(
        Parcelle.proprietaire_id == current_user.id
    )
    
    # Filtres
    if culture_id:
        query = query.filter(Maladie.culture_id == culture_id)
    if type:
        query = query.filter(Maladie.type == type)
    if est_resolu is not None:
        query = query.filter(Maladie.est_resolu == est_resolu)
    if gravite_min:
        query = query.filter(Maladie.gravite >= gravite_min)
    if date_debut:
        query = query.filter(Maladie.date_detection >= date_debut)
    if date_fin:
        query = query.filter(Maladie.date_detection <= date_fin)
    
    # Tri
    if sort_desc:
        query = query.order_by(getattr(Maladie, sort_by).desc())
    else:
        query = query.order_by(getattr(Maladie, sort_by).asc())
    
    # Pagination
    result = paginate(query, page, size)
    
    # Construire les items
    items = []
    for maladie in result["items"]:
        items.append({
            "id": maladie.id,
            "culture_id": maladie.culture_id,
            "culture_nom": maladie.culture.variete if maladie.culture else None,
            "type": maladie.type,
            "date_detection": maladie.date_detection,
            "gravite": maladie.gravite,
            "surface_touchee": maladie.surface_touchee,
            "traitement_applique": maladie.traitement_applique,
            "date_traitement": maladie.date_traitement,
            "efficace": maladie.efficace,
            "est_resolu": maladie.est_resolu,
            "date_guerison": maladie.date_guerison,
            "observations": maladie.observations,
            "recommandations": maladie.recommandations,
            "photo_url": maladie.photo_url,
            "photos": maladie.photos if maladie.photos else [],
            "est_critique": maladie.est_critique,
            "niveau_alerte": maladie.niveau_alerte,
            "alerte_envoyee": maladie.alerte_envoyee,
            "created_at": maladie.created_at,
            "updated_at": maladie.updated_at,
            "created_by": maladie.created_by,
            "updated_by": maladie.updated_by,
            "extra_data": maladie.extra_data if maladie.extra_data else {},
            "tags": maladie.tags if maladie.tags else [],
            "version": maladie.version
        })
    
    return {
        "total": result["total"],
        "page": result["page"],
        "size": result["size"],
        "pages": result["pages"],
        "items": items
    }


# ========================
# CRÉER UN SIGNALEMENT DE MALADIE
# ========================
@router.post("/", response_model=MaladieResponse, status_code=status.HTTP_201_CREATED)
async def create_maladie(
    request: MaladieCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Crée un signalement de maladie.
    """
    try:
        logger.info(f"=== SIGNALEMENT MALADIE ===")
        logger.info(f"Utilisateur: {current_user.email}")
        logger.info(f"Données reçues: {request.model_dump()}")
        
        # Vérifier que la culture existe et appartient à l'utilisateur
        culture = db.query(Culture).join(Parcelle).filter(
            Culture.id == request.culture_id,
            Parcelle.proprietaire_id == current_user.id
        ).first()
        
        if not culture:
            raise NotFoundException("Culture non trouvée ou non autorisée")
        
        # Vérifier que la culture n'est pas terminée
        if culture.date_fin_reelle:
            raise BadRequestException("Impossible d'ajouter une maladie à une culture terminée")
        
        # Créer la maladie
        maladie = Maladie(
            culture_id=request.culture_id,
            type=request.type,
            date_detection=request.date_detection,
            gravite=request.gravite,
            surface_touchee=request.surface_touchee,
            traitement_applique=request.traitement_applique,
            date_traitement=request.date_traitement,
            observations=request.observations,
            recommandations=request.recommandations,
            photo_url=request.photo_url
        )
        
        # Ajouter des recommandations automatiques basées sur le type
        if not maladie.recommandations:
            maladie.recommandations = get_recommandation_auto(request.type, request.gravite)
        
        # Sauvegarder
        db.add(maladie)
        db.commit()
        db.refresh(maladie)
        
        # Mettre à jour la santé de la culture
        culture.sante = max(1, culture.sante - (maladie.gravite // 2))
        
        # Envoyer une alerte si maladie grave
        if maladie.est_critique:
            background_tasks.add_task(
                send_alerte_maladie,
                maladie_id=maladie.id,
                culture=culture,
                parcelle=culture.parcelle,
                maladie_type=maladie.type,
                gravite=maladie.gravite,
                user_email=current_user.email
            )
            maladie.marquer_alerte_envoyee()
            db.commit()
        
        logger.info(f"✅ Maladie signalée: {maladie.type} (Gravité: {maladie.gravite})")
        
        # Enregistrer dans l'historique
        HistoriqueService.log_create(
            db=db,
            user_id=current_user.id,
            entity_type="maladie",
            entity_id=maladie.id,
            data=request.model_dump()
        )
        
        return maladie
        
    except BadRequestException:
        raise
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur création maladie: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


# ========================
# RÉCUPÉRER UNE MALADIE
# ========================
@router.get("/{maladie_id}", response_model=MaladieDetailResponse)
async def get_maladie(
    maladie_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les détails d'une maladie.
    """
    maladie = db.query(Maladie).join(Culture).join(Parcelle).filter(
        Maladie.id == maladie_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not maladie:
        raise NotFoundException("Maladie non trouvée")
    
    return maladie


# ========================
# METTRE À JOUR UNE MALADIE
# ========================
@router.put("/{maladie_id}", response_model=MaladieResponse)
async def update_maladie(
    maladie_id: str,
    request: MaladieUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Met à jour une maladie.
    """
    maladie = db.query(Maladie).join(Culture).join(Parcelle).filter(
        Maladie.id == maladie_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not maladie:
        raise NotFoundException("Maladie non trouvée")
    
    update_data = request.model_dump(exclude_unset=True)
    old_data = {
        "gravite": maladie.gravite,
        "traitement_applique": maladie.traitement_applique,
        "est_resolu": maladie.est_resolu
    }
    
    for key, value in update_data.items():
        if hasattr(maladie, key):
            setattr(maladie, key, value)
    
    # Si la maladie est marquée comme résolue
    if request.est_resolu and not maladie.est_resolu:
        maladie.marquer_resolu()
    
    maladie.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(maladie)
    
    # Enregistrer dans l'historique
    HistoriqueService.log_update(
        db=db,
        user_id=current_user.id,
        entity_type="maladie",
        entity_id=maladie.id,
        old_data=old_data,
        new_data=update_data
    )
    
    return maladie


# ========================
# SUPPRIMER UNE MALADIE
# ========================
@router.delete("/{maladie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_maladie(
    maladie_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Supprime une maladie.
    """
    maladie = db.query(Maladie).join(Culture).join(Parcelle).filter(
        Maladie.id == maladie_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not maladie:
        raise NotFoundException("Maladie non trouvée")
    
    db.delete(maladie)
    db.commit()
    
    return None


# ========================
# ALERTES MALADIES (Admin)
# ========================
@router.get("/alertes/non-traitees", response_model=List[AlerteMaladie])
async def get_alertes_non_traitees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Récupère les alertes de maladies non traitées (admin uniquement).
    """
    maladies = db.query(Maladie).join(Culture).join(Parcelle).filter(
        Maladie.gravite >= 4,
        Maladie.est_resolu == False,
        Maladie.alerte_envoyee == True
    ).order_by(Maladie.gravite.desc(), Maladie.date_detection.desc()).all()
    
    result = []
    for maladie in maladies:
        result.append({
            "maladie_id": maladie.id,
            "culture_id": maladie.culture_id,
            "culture_nom": maladie.culture.variete if maladie.culture else None,
            "parcelle_nom": maladie.culture.parcelle.nom if maladie.culture else None,
            "type": maladie.type,
            "gravite": maladie.gravite,
            "niveau_alerte": maladie.niveau_alerte,
            "surface_touchee": maladie.surface_touchee,
            "message": get_message_alerte(maladie.type, maladie.gravite),
            "recommandations": maladie.recommandations,
            "date_detection": maladie.date_detection
        })
    
    return result


# ========================
# STATISTIQUES DES MALADIES
# ========================
@router.get("/stats/summary")
async def get_maladies_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les statistiques des maladies.
    """
    maladies = db.query(Maladie).join(Culture).join(Parcelle).filter(
        Parcelle.proprietaire_id == current_user.id
    ).all()
    
    stats = {
        "total": len(maladies),
        "actives": sum(1 for m in maladies if not m.est_resolu),
        "resolues": sum(1 for m in maladies if m.est_resolu),
        "critiques": sum(1 for m in maladies if m.est_critique and not m.est_resolu),
        "par_type": {},
        "par_gravite": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    }
    
    for maladie in maladies:
        # Par type
        type_key = maladie.type.value if hasattr(maladie.type, 'value') else str(maladie.type)
        stats["par_type"][type_key] = stats["par_type"].get(type_key, 0) + 1
        
        # Par gravité
        stats["par_gravite"][maladie.gravite] = stats["par_gravite"].get(maladie.gravite, 0) + 1
    
    return stats


# ========================
# AJOUTER UNE PHOTO
# ========================
@router.post("/{maladie_id}/photos")
async def add_photo(
    maladie_id: str,
    photo_url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Ajoute une photo à une maladie.
    """
    maladie = db.query(Maladie).join(Culture).join(Parcelle).filter(
        Maladie.id == maladie_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not maladie:
        raise NotFoundException("Maladie non trouvée")
    
    if not maladie.photos:
        maladie.photos = []
    
    maladie.photos.append(photo_url)
    if not maladie.photo_url:
        maladie.photo_url = photo_url
    
    db.commit()
    
    return {"message": "Photo ajoutée", "photos": maladie.photos}


# ========================
# FONCTIONS UTILITAIRES
# ========================

def get_recommandation_auto(type_maladie: TypeMaladie, gravite: int) -> str:
    """Génère des recommandations automatiques basées sur le type de maladie."""
    recommendations = {
        TypeMaladie.ROSETTE: {
            1: "Surveiller l'évolution. Éliminer les plants isolés touchés.",
            3: "Arracher et brûler les plants touchés. Appliquer un insecticide contre les pucerons.",
            5: "Arracher immédiatement tous les plants touchés. Désinfecter le matériel. Rotation culturale."
        },
        TypeMaladie.CERCOSPORIOSE: {
            1: "Surveiller l'humidité. Aérer la culture.",
            3: "Appliquer un fongicide à base de cuivre. Espacer les arrosages.",
            5: "Traitement fongicide systémique. Éliminer les résidus après récolte."
        },
        TypeMaladie.FLAETRISSEMENT: {
            1: "Réduire l'humidité. Surveiller l'arrosage.",
            3: "Appliquer un traitement bactéricide. Éviter l'irrigation par aspersion.",
            5: "Arracher les plants atteints. Rotation culturale obligatoire."
        },
        TypeMaladie.POURRITURE: {
            1: "Améliorer le drainage. Réduire l'arrosage.",
            3: "Appliquer un fongicide. Aérer le sol.",
            5: "Arracher les plants. Traiter le sol. Rotation culturale."
        },
        TypeMaladie.AUTRE: {
            1: "Surveiller l'évolution. Consulter un technicien.",
            3: "Consulter un technicien. Prendre des photos.",
            5: "URGENT: Contacter immédiatement un technicien."
        }
    }
    
    rec = recommendations.get(type_maladie, recommendations[TypeMaladie.AUTRE])
    
    if gravite >= 4:
        return rec.get(5, rec.get(3, rec.get(1, "")))
    elif gravite >= 3:
        return rec.get(3, rec.get(1, ""))
    else:
        return rec.get(1, "")

def get_message_alerte(type_maladie: TypeMaladie, gravite: int) -> str:
    """Génère un message d'alerte."""
    messages = {
        TypeMaladie.ROSETTE: "⚠️ ALERTE ROUGE: Rosette détectée. Virus très contagieux!",
        TypeMaladie.CERCOSPORIOSE: "⚠️ ALERTE: Cercosporiose détectée. Risque de propagation rapide.",
        TypeMaladie.FLAETRISSEMENT: "⚠️ ALERTE: Flétrissement bactérien. Danger pour toute la parcelle!",
        TypeMaladie.POURRITURE: "⚠️ ALERTE: Pourriture racinaire. Risque de perte de récolte.",
        TypeMaladie.CARENCE: "⚠️ ALERTE: Carence nutritionnelle. Action rapide nécessaire.",
        TypeMaladie.AUTRE: "⚠️ ALERTE: Maladie détectée. Intervention nécessaire."
    }
    
    base_message = messages.get(type_maladie, messages[TypeMaladie.AUTRE])
    
    if gravite >= 5:
        return f"🔴 {base_message} ACTION IMMÉDIATE REQUISE!"
    elif gravite >= 4:
        return f"🟠 {base_message} Intervention urgente!"
    else:
        return f"🟡 {base_message} Surveillance nécessaire."


async def send_alerte_maladie(
    maladie_id: str,
    culture,
    parcelle,
    maladie_type: TypeMaladie,
    gravite: int,
    user_email: str
):
    """
    Envoie une alerte pour une maladie grave.
    """
    try:
        # Log de l'alerte
        logger.warning(f"🔴 ALERTE MALADIE GRAVE!")
        logger.warning(f"   Parcelle: {parcelle.nom}")
        logger.warning(f"   Culture: {culture.variete}")
        logger.warning(f"   Maladie: {maladie_type}")
        logger.warning(f"   Gravité: {gravite}/5")
        
        # Ici, vous pouvez ajouter:
        # - Envoi d'email aux techniciens
        # - Envoi de notification push
        # - SMS d'alerte
        # - Création d'un ticket d'intervention
        
        # Pour l'instant, on logge seulement
        logger.info(f"✅ Alerte enregistrée pour la maladie {maladie_id}")
        
    except Exception as e:
        logger.error(f"Erreur envoi alerte: {e}")