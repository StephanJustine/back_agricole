
"""
Routes CRUD pour les parcelles.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional,  List
from datetime import datetime
import logging

from ...database import get_db
from ...models.parcelle import Parcelle
from ...models.user import User
from ...models.enums import TypeParcelle
from ...schemas.parcelle import *
from ...core.dependencies import get_current_active_user
from ...core.pagination import paginate
from ...core.exceptions import NotFoundException, BadRequestException
from ...core.historique import HistoriqueService

logger = logging.getLogger(__name__)
router = APIRouter()

# LISTE DES PARCELLES
@router.get("/", response_model=ParcelleList)
async def get_parcelles(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(20, ge=1, le=100, description="Nombre d'éléments par page"),
    type: Optional[TypeParcelle] = Query(None, description="Filtrer par type"),
    region: Optional[str] = Query(None, description="Filtrer par région"),
    search: Optional[str] = Query(None, description="Recherche par nom"),
    is_active: Optional[bool] = Query(None, description="Filtrer par statut"),
    sort_by: str = Query("created_at", description="Tri par champ"),
    sort_desc: bool = Query(False, description="Tri décroissant"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère la liste des parcelles de l'utilisateur connecté.
    """
    query = db.query(Parcelle).filter(Parcelle.proprietaire_id == current_user.id)
    
    # Filtres
    if type:
        query = query.filter(Parcelle.type == type)
    if region:
        query = query.filter(Parcelle.region.ilike(f"%{region}%"))
    if is_active is not None:
        query = query.filter(Parcelle.is_active == is_active)
    if search:
        query = query.filter(Parcelle.nom.ilike(f"%{search}%"))
    
    # Tri
    if sort_desc:
        query = query.order_by(getattr(Parcelle, sort_by).desc())
    else:
        query = query.order_by(getattr(Parcelle, sort_by).asc())
    
    # Pagination
    result = paginate(query, page, size)
    
    # Construire les items avec les propriétés calculées
    items = []
    for parcelle in result["items"]:
        item_dict = {
            "id": parcelle.id,
            "nom": parcelle.nom,
            "code": parcelle.code,
            "superficie": parcelle.superficie,
            "type": parcelle.type,
            "region": parcelle.region,
            "commune": parcelle.commune,
            "lieu_dit": parcelle.lieu_dit,
            "coord_gps": parcelle.coord_gps,
            "latitude": parcelle.latitude if hasattr(parcelle, 'latitude') else None,
            "longitude": parcelle.longitude if hasattr(parcelle, 'longitude') else None,
            "altitude": parcelle.altitude,
            "type_sol": parcelle.type_sol,
            "exposition": parcelle.exposition,
            "pente": parcelle.pente,
            "proprietaire_id": parcelle.proprietaire_id,
            "proprietaire_nom": f"{current_user.prenom} {current_user.nom}",
            "is_active": parcelle.is_active,
            "is_cultivee": parcelle.is_cultivee if hasattr(parcelle, 'is_cultivee') else False,
            "photo_principale": parcelle.photo_principale,
            "photos": parcelle.photos if parcelle.photos else [],
            "notes": parcelle.notes,
            "created_at": parcelle.created_at,
            "updated_at": parcelle.updated_at,
            "created_by": parcelle.created_by,
            "updated_by": parcelle.updated_by,
            "extra_data": parcelle.extra_data if parcelle.extra_data else {},
            "tags": parcelle.tags if parcelle.tags else [],
            "version": parcelle.version
        }
        items.append(item_dict)
    
    return {
        "total": result["total"],
        "page": result["page"],
        "size": result["size"],
        "pages": result["pages"],
        "items": items
    }


# CRÉER UNE PARCELLE
@router.post("/", response_model=ParcelleResponse, status_code=status.HTTP_201_CREATED)
async def create_parcelle(
    request: ParcelleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Crée une nouvelle parcelle.
    
    - **nom**: Nom de la parcelle (obligatoire)
    - **superficie**: Surface en hectares (obligatoire)
    - **type**: Type de parcelle (amelioree/traditionnelle)
    - **coord_gps**: Coordonnées GPS au format "latitude,longitude" (optionnel)
    """
    try:
        logger.info(f"=== CRÉATION PARCELLE ===")
        logger.info(f"Utilisateur: {current_user.email} (ID: {current_user.id})")
        logger.info(f"Données reçues: {request.model_dump()}")
        
        # Validation des données requises
        if not request.nom or not request.nom.strip():
            raise BadRequestException("Le nom de la parcelle est requis")
        
        if not request.superficie or request.superficie <= 0:
            raise BadRequestException("La superficie doit être supérieure à 0")
        
        if not request.type:
            raise BadRequestException("Le type de parcelle est requis (amelioree/traditionnelle)")
        
        # Vérifier si une parcelle avec le même nom existe déjà pour cet utilisateur
        existing = db.query(Parcelle).filter(
            Parcelle.proprietaire_id == current_user.id,
            Parcelle.nom.ilike(request.nom.strip())
        ).first()
        
        if existing:
            logger.warning(f"Parcelle dupliquée détectée: {request.nom}")
            raise BadRequestException(f"Une parcelle nommée '{request.nom}' existe déjà")
        
        # Créer la parcelle
        parcelle = Parcelle(
            nom=request.nom.strip(),
            superficie=request.superficie,
            type=request.type,
            region=request.region.strip() if request.region else None,
            commune=request.commune.strip() if request.commune else None,
            lieu_dit=request.lieu_dit.strip() if request.lieu_dit else None,
            coord_gps=request.coord_gps.strip() if request.coord_gps else None,
            altitude=request.altitude,
            type_sol=request.type_sol.strip() if request.type_sol else None,
            exposition=request.exposition.strip() if request.exposition else None,
            pente=request.pente.strip() if request.pente else None,
            notes=request.notes.strip() if request.notes else None,
            proprietaire_id=current_user.id
        )
        
        # Générer un code unique
        parcelle.generate_code()
        
        # Sauvegarder en base
        db.add(parcelle)
        db.commit()
        db.refresh(parcelle)
        
        logger.info(f"✅ Parcelle créée avec succès: {parcelle.nom} (ID: {parcelle.id}, Code: {parcelle.code})")
        
        # Enregistrer dans l'historique (sans le paramètre description)
        HistoriqueService.log_create(
            db=db,
            user_id=current_user.id,
            entity_type="parcelle",
            entity_id=parcelle.id,
            data=request.model_dump()
            # Le paramètre description est optionnel, on ne le passe pas
        )
        
        # Construire la réponse
        response_data = {
            "id": parcelle.id,
            "nom": parcelle.nom,
            "code": parcelle.code,
            "superficie": parcelle.superficie,
            "type": parcelle.type,
            "region": parcelle.region,
            "commune": parcelle.commune,
            "lieu_dit": parcelle.lieu_dit,
            "coord_gps": parcelle.coord_gps,
            "latitude": parcelle.latitude if hasattr(parcelle, 'latitude') else None,
            "longitude": parcelle.longitude if hasattr(parcelle, 'longitude') else None,
            "altitude": parcelle.altitude,
            "type_sol": parcelle.type_sol,
            "exposition": parcelle.exposition,
            "pente": parcelle.pente,
            "notes": parcelle.notes,
            "proprietaire_id": parcelle.proprietaire_id,
            "proprietaire_nom": f"{current_user.prenom} {current_user.nom}",
            "is_active": parcelle.is_active,
            "is_cultivee": parcelle.is_cultivee if hasattr(parcelle, 'is_cultivee') else False,
            "photo_principale": parcelle.photo_principale,
            "photos": parcelle.photos if parcelle.photos else [],
            "created_at": parcelle.created_at,
            "updated_at": parcelle.updated_at,
            "created_by": parcelle.created_by,
            "updated_by": parcelle.updated_by,
            "extra_data": parcelle.extra_data if parcelle.extra_data else {},
            "tags": parcelle.tags if parcelle.tags else [],
            "version": parcelle.version
        }
        
        return response_data
        
    except BadRequestException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur inattendue lors de la création de la parcelle: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne du serveur: {str(e)}"
        )


# CRÉER UNE PARCELLE BULK
@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def create_parcelles_bulk(
    parcelles: List[ParcelleCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Crée plusieurs parcelles en une fois.
    """

    created = []

    for request in parcelles:

        parcelle = Parcelle(
            nom=request.nom.strip(),
            superficie=request.superficie,
            type=request.type,
            region=request.region.strip() if request.region else None,
            commune=request.commune.strip() if request.commune else None,
            lieu_dit=request.lieu_dit.strip() if request.lieu_dit else None,
            coord_gps=request.coord_gps.strip() if request.coord_gps else None,
            altitude=request.altitude,
            type_sol=request.type_sol.strip() if request.type_sol else None,
            exposition=request.exposition.strip() if request.exposition else None,
            pente=request.pente.strip() if request.pente else None,
            notes=request.notes.strip() if request.notes else None,
            proprietaire_id=current_user.id
        )

        parcelle.generate_code()

        db.add(parcelle)
        created.append(parcelle)

    db.commit()

    for p in created:
        db.refresh(p)

    return created 

# ========================
# RÉCUPÉRER UNE PARCELLE
# ========================
@router.get("/{parcelle_id}", response_model=ParcelleDetailResponse)
async def get_parcelle(
    parcelle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les détails d'une parcelle.
    """
    parcelle = db.query(Parcelle).filter(
        Parcelle.id == parcelle_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not parcelle:
        raise NotFoundException("Parcelle non trouvée")
    
    # Construire la réponse avec les détails
    result = {
        "id": parcelle.id,
        "nom": parcelle.nom,
        "code": parcelle.code,
        "superficie": parcelle.superficie,
        "type": parcelle.type,
        "region": parcelle.region,
        "commune": parcelle.commune,
        "lieu_dit": parcelle.lieu_dit,
        "coord_gps": parcelle.coord_gps,
        "latitude": parcelle.latitude,
        "longitude": parcelle.longitude,
        "altitude": parcelle.altitude,
        "type_sol": parcelle.type_sol,
        "exposition": parcelle.exposition,
        "pente": parcelle.pente,
        "proprietaire_id": parcelle.proprietaire_id,
        "proprietaire_nom": f"{current_user.prenom} {current_user.nom}",
        "is_active": parcelle.is_active,
        "is_cultivee": parcelle.is_cultivee,
        "photo_principale": parcelle.photo_principale,
        "photos": parcelle.photos,
        "notes": parcelle.notes,
        "created_at": parcelle.created_at,
        "updated_at": parcelle.updated_at,
        "created_by": parcelle.created_by,
        "updated_by": parcelle.updated_by,
        "extra_data": parcelle.extra_data,
        "tags": parcelle.tags,
        "version": parcelle.version,
        "culture_actuelle": None,
        "analyses_sol": [],
        "travaux": [],
        "cultures": [],
        "capteurs": [],
        "predictions": [],
        "recommandations": []
    }
    
    # Ajouter la culture actuelle si elle existe
    if parcelle.culture_actuelle:
        result["culture_actuelle"] = {
            "id": parcelle.culture_actuelle.id,
            "variete": parcelle.culture_actuelle.variete,
            "date_debut": parcelle.culture_actuelle.date_debut,
            "stade": parcelle.culture_actuelle.stade,
            "sante": parcelle.culture_actuelle.sante
        }
    
    return result


# ========================
# METTRE À JOUR UNE PARCELLE
# ========================
@router.put("/{parcelle_id}", response_model=ParcelleResponse)
async def update_parcelle(
    parcelle_id: str,
    request: ParcelleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Met à jour une parcelle existante.
    """
    parcelle = db.query(Parcelle).filter(
        Parcelle.id == parcelle_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not parcelle:
        raise NotFoundException("Parcelle non trouvée")
    
    update_data = request.model_dump(exclude_unset=True)
    old_data = {
        "nom": parcelle.nom,
        "type": parcelle.type,
        "superficie": parcelle.superficie,
        "coord_gps": parcelle.coord_gps,
        "region": parcelle.region,
        "commune": parcelle.commune
    }
    
    for key, value in update_data.items():
        if hasattr(parcelle, key):
            if isinstance(value, str):
                value = value.strip() if value else None
            setattr(parcelle, key, value)
    
    parcelle.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(parcelle)
    
    # Enregistrer dans l'historique
    HistoriqueService.log_update(
        db=db,
        user_id=current_user.id,
        entity_type="parcelle",
        entity_id=parcelle.id,
        old_data=old_data,
        new_data=update_data
    )
    
    # Construire la réponse
    return {
        "id": parcelle.id,
        "nom": parcelle.nom,
        "code": parcelle.code,
        "superficie": parcelle.superficie,
        "type": parcelle.type,
        "region": parcelle.region,
        "commune": parcelle.commune,
        "lieu_dit": parcelle.lieu_dit,
        "coord_gps": parcelle.coord_gps,
        "latitude": parcelle.latitude,
        "longitude": parcelle.longitude,
        "altitude": parcelle.altitude,
        "type_sol": parcelle.type_sol,
        "exposition": parcelle.exposition,
        "pente": parcelle.pente,
        "notes": parcelle.notes,
        "proprietaire_id": parcelle.proprietaire_id,
        "is_active": parcelle.is_active,
        "is_cultivee": parcelle.is_cultivee,
        "photo_principale": parcelle.photo_principale,
        "photos": parcelle.photos,
        "created_at": parcelle.created_at,
        "updated_at": parcelle.updated_at,
        "created_by": parcelle.created_by,
        "updated_by": parcelle.updated_by,
        "extra_data": parcelle.extra_data,
        "tags": parcelle.tags,
        "version": parcelle.version
    }


# ========================
# SUPPRIMER UNE PARCELLE
# ========================
@router.delete("/{parcelle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parcelle(
    parcelle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Supprime une parcelle (soft delete).
    """
    parcelle = db.query(Parcelle).filter(
        Parcelle.id == parcelle_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not parcelle:
        raise NotFoundException("Parcelle non trouvée")
    
    # Vérifier s'il y a des cultures en cours
    if parcelle.culture_actuelle:
        raise BadRequestException("Impossible de supprimer une parcelle avec une culture en cours")
    
    parcelle.soft_delete()
    db.commit()
    
    # Enregistrer dans l'historique
    HistoriqueService.log_delete(
        db=db,
        user_id=current_user.id,
        entity_type="parcelle",
        entity_id=parcelle.id,
        data={"nom": parcelle.nom, "superficie": parcelle.superficie}
    )
    
    return None


# ========================
# STATISTIQUES DES PARCELLES
# ========================
@router.get("/stats/summary")
async def get_parcelles_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les statistiques des parcelles de l'utilisateur.
    """
    parcelles = db.query(Parcelle).filter(Parcelle.proprietaire_id == current_user.id).all()
    
    stats = {
        "total": len(parcelles),
        "superficie_totale": sum(p.superficie for p in parcelles),
        "superficie_moyenne": sum(p.superficie for p in parcelles) / len(parcelles) if parcelles else 0,
        "par_type": {},
        "par_region": {},
        "actives": sum(1 for p in parcelles if p.is_active),
        "cultivees": sum(1 for p in parcelles if p.is_cultivee)
    }
    
    for parcelle in parcelles:
        # Par type
        type_key = parcelle.type.value if hasattr(parcelle.type, 'value') else str(parcelle.type)
        stats["par_type"][type_key] = stats["par_type"].get(type_key, 0) + 1
        
        # Par région
        if parcelle.region:
            stats["par_region"][parcelle.region] = stats["par_region"].get(parcelle.region, 0) + 1
    
    return stats


# ========================
# AJOUTER UNE PHOTO À UNE PARCELLE
# ========================
@router.post("/{parcelle_id}/photos")
async def add_parcelle_photo(
    parcelle_id: str,
    photo_url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Ajoute une photo à une parcelle.
    """
    parcelle = db.query(Parcelle).filter(
        Parcelle.id == parcelle_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not parcelle:
        raise NotFoundException("Parcelle non trouvée")
    
    if not parcelle.photos:
        parcelle.photos = []
    
    parcelle.photos.append(photo_url)
    if not parcelle.photo_principale:
        parcelle.photo_principale = photo_url
    
    db.commit()
    
    return {"message": "Photo ajoutée", "photos": parcelle.photos}


# ========================
# SUPPRIMER UNE PHOTO
# ========================
@router.delete("/{parcelle_id}/photos/{photo_index}")
async def delete_parcelle_photo(
    parcelle_id: str,
    photo_index: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Supprime une photo d'une parcelle.
    """
    parcelle = db.query(Parcelle).filter(
        Parcelle.id == parcelle_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not parcelle:
        raise NotFoundException("Parcelle non trouvée")
    
    if not parcelle.photos or photo_index >= len(parcelle.photos):
        raise NotFoundException("Photo non trouvée")
    
    removed = parcelle.photos.pop(photo_index)
    
    # Si c'était la photo principale, mettre la première disponible
    if parcelle.photo_principale == removed and parcelle.photos:
        parcelle.photo_principale = parcelle.photos[0]
    elif not parcelle.photos:
        parcelle.photo_principale = None
    
    db.commit()
    
    return {"message": "Photo supprimée", "photos": parcelle.photos}


# ========================
# ROUTE DE DIAGNOSTIC (optionnelle)
# ========================
@router.post("/diagnostic")
async def diagnostic_parcelle(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Route de diagnostic pour tester la connexion et les données.
    """
    try:
        body = await request.body()
        return {
            "status": "ok",
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "nom": current_user.nom,
                "prenom": current_user.prenom
            },
            "request": {
                "body": body.decode("utf-8") if body else None,
                "headers": dict(request.headers)
            }
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}