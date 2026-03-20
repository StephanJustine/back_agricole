"""
Routes CRUD pour les mesures de croissance.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, datetime
import logging
import os
import uuid

from ...database import get_db
from ...models.mesure import Mesure
from ...models.culture import Culture
from ...models.parcelle import Parcelle
from ...models.user import User
from ...schemas.mesure import *
from ...core.dependencies import get_current_active_user
from ...core.pagination import paginate
from ...core.exceptions import NotFoundException, BadRequestException
from ...core.historique import HistoriqueService

logger = logging.getLogger(__name__)
router = APIRouter()


# LISTE DES MESURES
@router.get("/", response_model=MesureList)
async def get_mesures(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(20, ge=1, le=100, description="Nombre d'éléments par page"),
    culture_id: Optional[str] = Query(None, description="Filtrer par culture"),
    date_debut: Optional[date] = Query(None, description="Date de début"),
    date_fin: Optional[date] = Query(None, description="Date de fin"),
    sort_by: str = Query("date_mesure", description="Tri par champ"),
    sort_desc: bool = Query(True, description="Tri décroissant"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère la liste des mesures de l'utilisateur connecté.
    """
    # Jointure pour vérifier que les cultures appartiennent à l'utilisateur
    query = db.query(Mesure).join(Culture).join(Parcelle).filter(
        Parcelle.proprietaire_id == current_user.id
    )
    
    # Filtres
    if culture_id:
        query = query.filter(Mesure.culture_id == culture_id)
    if date_debut:
        query = query.filter(Mesure.date_mesure >= date_debut)
    if date_fin:
        query = query.filter(Mesure.date_mesure <= date_fin)
    
    # Tri - vérifier que l'attribut existe
    if hasattr(Mesure, sort_by):
        if sort_desc:
            query = query.order_by(getattr(Mesure, sort_by).desc())
        else:
            query = query.order_by(getattr(Mesure, sort_by).asc())
    else:
        # Fallback sur date_mesure
        if sort_desc:
            query = query.order_by(Mesure.date_mesure.desc())
        else:
            query = query.order_by(Mesure.date_mesure.asc())
    
    # Pagination
    result = paginate(query, page, size)
    
    # Construire les items
    items = []
    for mesure in result["items"]:
        items.append({
            "id": mesure.id,
            "culture_id": mesure.culture_id,
            "culture_nom": mesure.culture.variete if mesure.culture else None,
            "date_mesure": mesure.date_mesure,
            "hauteur_moyenne": mesure.hauteur_moyenne,
            "nb_feuilles_moyen": mesure.nb_feuilles_moyen,
            "nb_fleurs_moyen": mesure.nb_fleurs_moyen,
            "nb_gousses_moyen": mesure.nb_gousses_moyen,
            "diametre_tige": mesure.diametre_tige,
            "indice_vigueur": mesure.indice_vigueur,
            "couleur_feuillage": mesure.couleur_feuillage,
            "stress_hydrique": mesure.stress_hydrique,
            "photo_url": mesure.photo_url,
            "photos": mesure.photos if mesure.photos else [],
            "observations": mesure.observations,
            "age_culture": mesure.age_culture,
            "date_saisie": mesure.date_saisie,
            "created_at": mesure.created_at,
            "updated_at": mesure.updated_at,
            "created_by": mesure.created_by,
            "updated_by": mesure.updated_by,
            "extra_data": mesure.extra_data if mesure.extra_data else {},
            "tags": mesure.tags if mesure.tags else [],
            "version": mesure.version
        })
    
    return {
        "total": result["total"],
        "page": result["page"],
        "size": result["size"],
        "pages": result["pages"],
        "items": items
    }

# ========================
# CRÉER UNE MESURE
# ========================
@router.post("/", response_model=MesureResponse, status_code=status.HTTP_201_CREATED)
async def create_mesure(
    request: MesureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Enregistre une nouvelle mesure de croissance.
    """
    try:
        logger.info(f"=== ENREGISTREMENT MESURE ===")
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
            raise BadRequestException("Impossible d'ajouter des mesures à une culture terminée")
        
        # Vérifier qu'il n'y a pas déjà une mesure pour cette date
        existing = db.query(Mesure).filter(
            Mesure.culture_id == request.culture_id,
            Mesure.date_mesure == request.date_mesure
        ).first()
        
        if existing:
            raise BadRequestException(f"Une mesure existe déjà pour le {request.date_mesure}")
        
        # Créer la mesure
        mesure = Mesure(
            culture_id=request.culture_id,
            date_mesure=request.date_mesure,
            hauteur_moyenne=request.hauteur_moyenne,
            nb_feuilles_moyen=request.nb_feuilles_moyen,
            nb_fleurs_moyen=request.nb_fleurs_moyen,
            nb_gousses_moyen=request.nb_gousses_moyen,
            diametre_tige=request.diametre_tige,
            indice_vigueur=request.indice_vigueur,
            couleur_feuillage=request.couleur_feuillage,
            stress_hydrique=request.stress_hydrique,
            photo_url=request.photo_url,
            observations=request.observations
        )
        
        # Sauvegarder
        db.add(mesure)
        db.commit()
        db.refresh(mesure)
        
        # Mettre à jour la santé de la culture
        if request.indice_vigueur:
            culture.sante = (culture.sante + request.indice_vigueur * 2) // 2
        
        logger.info(f"✅ Mesure enregistrée: {mesure.date_mesure} pour culture {culture.variete}")
        
        # Enregistrer dans l'historique
        HistoriqueService.log_create(
            db=db,
            user_id=current_user.id,
            entity_type="mesure",
            entity_id=mesure.id,
            data=request.model_dump()
        )
        
        # Construire la réponse
        return {
            "id": mesure.id,
            "culture_id": mesure.culture_id,
            "culture_nom": culture.variete,
            "date_mesure": mesure.date_mesure,
            "hauteur_moyenne": mesure.hauteur_moyenne,
            "nb_feuilles_moyen": mesure.nb_feuilles_moyen,
            "nb_fleurs_moyen": mesure.nb_fleurs_moyen,
            "nb_gousses_moyen": mesure.nb_gousses_moyen,
            "diametre_tige": mesure.diametre_tige,
            "indice_vigueur": mesure.indice_vigueur,
            "couleur_feuillage": mesure.couleur_feuillage,
            "stress_hydrique": mesure.stress_hydrique,
            "photo_url": mesure.photo_url,
            "photos": mesure.photos if mesure.photos else [],
            "observations": mesure.observations,
            "age_culture": mesure.age_culture,
            "date_saisie": mesure.date_saisie,
            "created_at": mesure.created_at,
            "updated_at": mesure.updated_at,
            "created_by": mesure.created_by,
            "updated_by": mesure.updated_by,
            "extra_data": mesure.extra_data if mesure.extra_data else {},
            "tags": mesure.tags if mesure.tags else [],
            "version": mesure.version
        }
        
    except BadRequestException:
        raise
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur création mesure: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


# ========================
# RÉCUPÉRER UNE MESURE
# ========================
@router.get("/{mesure_id}", response_model=MesureResponse)
async def get_mesure(
    mesure_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les détails d'une mesure.
    """
    mesure = db.query(Mesure).join(Culture).join(Parcelle).filter(
        Mesure.id == mesure_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not mesure:
        raise NotFoundException("Mesure non trouvée")
    
    return mesure


# ========================
# METTRE À JOUR UNE MESURE
# ========================
@router.put("/{mesure_id}", response_model=MesureResponse)
async def update_mesure(
    mesure_id: str,
    request: MesureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Met à jour une mesure existante.
    """
    mesure = db.query(Mesure).join(Culture).join(Parcelle).filter(
        Mesure.id == mesure_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not mesure:
        raise NotFoundException("Mesure non trouvée")
    
    update_data = request.model_dump(exclude_unset=True)
    old_data = {
        "hauteur_moyenne": mesure.hauteur_moyenne,
        "nb_feuilles_moyen": mesure.nb_feuilles_moyen,
        "indice_vigueur": mesure.indice_vigueur
    }
    
    for key, value in update_data.items():
        if hasattr(mesure, key):
            setattr(mesure, key, value)
    
    mesure.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(mesure)
    
    # Enregistrer dans l'historique
    HistoriqueService.log_update(
        db=db,
        user_id=current_user.id,
        entity_type="mesure",
        entity_id=mesure.id,
        old_data=old_data,
        new_data=update_data
    )
    
    return mesure


# ========================
# SUPPRIMER UNE MESURE
# ========================
@router.delete("/{mesure_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mesure(
    mesure_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Supprime une mesure.
    """
    mesure = db.query(Mesure).join(Culture).join(Parcelle).filter(
        Mesure.id == mesure_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not mesure:
        raise NotFoundException("Mesure non trouvée")
    
    db.delete(mesure)
    db.commit()
    
    return None


# ========================
# GRAPHIQUE DE CROISSANCE
# ========================
@router.get("/graphique/{culture_id}", response_model=GraphiqueCroissance)
async def get_croissance_graphique(
    culture_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les données pour le graphique de croissance d'une culture.
    """
    # Vérifier que la culture appartient à l'utilisateur
    culture = db.query(Culture).join(Parcelle).filter(
        Culture.id == culture_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not culture:
        raise NotFoundException("Culture non trouvée ou non autorisée")
    
    # Récupérer toutes les mesures de la culture, triées par date
    mesures = db.query(Mesure).filter(
        Mesure.culture_id == culture_id
    ).order_by(Mesure.date_mesure.asc()).all()
    
    # Préparer les données pour le graphique
    dates = []
    hauteurs = []
    feuilles = []
    fleurs = []
    gousses = []
    vigueur = []
    
    for mesure in mesures:
        dates.append(mesure.date_mesure.strftime("%Y-%m-%d"))
        hauteurs.append(mesure.hauteur_moyenne or 0)
        feuilles.append(mesure.nb_feuilles_moyen or 0)
        fleurs.append(mesure.nb_fleurs_moyen or 0)
        gousses.append(mesure.nb_gousses_moyen or 0)
        vigueur.append(mesure.indice_vigueur or 0)
    
    return {
        "dates": dates,
        "hauteurs": hauteurs,
        "feuilles": feuilles,
        "fleurs": fleurs,
        "gousses": gousses,
        "vigueur": vigueur
    }


# ========================
# AJOUTER UNE PHOTO
# ========================
@router.post("/{mesure_id}/photo")
async def add_photo(
    mesure_id: str,
    photo_url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Ajoute une photo à une mesure.
    """
    mesure = db.query(Mesure).join(Culture).join(Parcelle).filter(
        Mesure.id == mesure_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not mesure:
        raise NotFoundException("Mesure non trouvée")
    
    if not mesure.photos:
        mesure.photos = []
    
    mesure.photos.append(photo_url)
    if not mesure.photo_url:
        mesure.photo_url = photo_url
    
    db.commit()
    
    return {"message": "Photo ajoutée", "photos": mesure.photos}


# ========================
# SUPPRIMER UNE PHOTO
# ========================
@router.delete("/{mesure_id}/photo/{photo_index}")
async def delete_photo(
    mesure_id: str,
    photo_index: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Supprime une photo d'une mesure.
    """
    mesure = db.query(Mesure).join(Culture).join(Parcelle).filter(
        Mesure.id == mesure_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not mesure:
        raise NotFoundException("Mesure non trouvée")
    
    if not mesure.photos or photo_index >= len(mesure.photos):
        raise NotFoundException("Photo non trouvée")
    
    removed = mesure.photos.pop(photo_index)
    
    if mesure.photo_url == removed and mesure.photos:
        mesure.photo_url = mesure.photos[0]
    elif not mesure.photos:
        mesure.photo_url = None
    
    db.commit()
    
    return {"message": "Photo supprimée", "photos": mesure.photos}


# ========================
# DERNIÈRE MESURE D'UNE CULTURE
# ========================
@router.get("/culture/{culture_id}/derniere", response_model=Optional[MesureResponse])
async def get_derniere_mesure(
    culture_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère la dernière mesure d'une culture.
    """
    culture = db.query(Culture).join(Parcelle).filter(
        Culture.id == culture_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not culture:
        raise NotFoundException("Culture non trouvée")
    
    mesure = db.query(Mesure).filter(
        Mesure.culture_id == culture_id
    ).order_by(Mesure.date_mesure.desc()).first()
    
    return mesure


# ========================
# STATISTIQUES DES MESURES
# ========================
@router.get("/stats/summary")
async def get_mesures_stats(
    culture_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les statistiques des mesures.
    """
    query = db.query(Mesure).join(Culture).join(Parcelle).filter(
        Parcelle.proprietaire_id == current_user.id
    )
    
    if culture_id:
        query = query.filter(Mesure.culture_id == culture_id)
    
    mesures = query.all()
    
    if not mesures:
        return {
            "total": 0,
            "hauteur_max": None,
            "hauteur_moyenne": None,
            "nb_mesures": 0
        }
    
    hauteurs = [m.hauteur_moyenne for m in mesures if m.hauteur_moyenne]
    
    return {
        "total": len(mesures),
        "hauteur_max": max(hauteurs) if hauteurs else None,
        "hauteur_moyenne": sum(hauteurs) / len(hauteurs) if hauteurs else None,
        "nb_mesures": len(mesures),
        "cultures_suivies": len(set(m.culture_id for m in mesures))
    }