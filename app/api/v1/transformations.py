"""
Routes CRUD pour les transformations (huile et savon).
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime, timedelta
import logging
import math

from ...database import get_db
from ...models.transformation import Transformation
from ...models.lot import Lot
from ...models.user import User
from ...models.enums import TypeTransformation, TypeLot
from ...schemas.transformation import *
from ...core.dependencies import get_current_active_user
from ...core.pagination import paginate
from ...core.exceptions import NotFoundException, BadRequestException
from ...core.historique import HistoriqueService

logger = logging.getLogger(__name__)
router = APIRouter()


# ========================
# CONSTANTES
# ========================
RENDEMENT_HUILE_MIN = 35  # %
RENDEMENT_HUILE_MAX = 45  # %
RENDEMENT_HUILE_MOYEN = 40  # %
DENSITE_HUILE_ARACHIDE = 0.92  # kg/L
INDICE_SAPONIFICATION = 0.136  # pour huile d'arachide


# ========================
# LISTE DES TRANSFORMATIONS
# ========================
@router.get("/", response_model=TransformationList)
async def get_transformations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    type: Optional[TypeTransformation] = Query(None, description="Filtrer par type"),
    lot_entree_id: Optional[str] = Query(None, description="Filtrer par lot entrant"),
    date_debut: Optional[date] = Query(None, description="Date de début"),
    date_fin: Optional[date] = Query(None, description="Date de fin"),
    sort_by: str = Query("date_transformation", description="Tri par champ"),
    sort_desc: bool = Query(True, description="Tri décroissant"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère la liste des transformations.
    """
    query = db.query(Transformation)
    
    if type:
        query = query.filter(Transformation.type == type)
    if lot_entree_id:
        query = query.filter(Transformation.lot_entree_id == lot_entree_id)
    if date_debut:
        query = query.filter(Transformation.date_transformation >= date_debut)
    if date_fin:
        query = query.filter(Transformation.date_transformation <= date_fin)
    
    if sort_desc:
        query = query.order_by(getattr(Transformation, sort_by).desc())
    else:
        query = query.order_by(getattr(Transformation, sort_by).asc())
    
    result = paginate(query, page, size)
    
    items = []
    for transfo in result["items"]:
        items.append({
            "id": transfo.id,
            "type": transfo.type,
            "lot_entree_id": transfo.lot_entree_id,
            "lot_entree_code": transfo.lot_entree.code if transfo.lot_entree else None,
            "lot_sortie_id": transfo.lot_sortie_id,
            "lot_sortie_code": transfo.lot_sortie.code if transfo.lot_sortie else None,
            "date_transformation": transfo.date_transformation,
            "responsable_id": transfo.responsable_id,
            "responsable_nom": f"{transfo.responsable.prenom} {transfo.responsable.nom}" if transfo.responsable else None,
            "quantite_entree": transfo.quantite_entree,
            "quantite_sortie": transfo.quantite_sortie,
            "rendement": transfo.rendement,
            "recette": transfo.recette,
            "observations": transfo.observations,
            "created_at": transfo.created_at,
            "updated_at": transfo.updated_at,
            "created_by": transfo.created_by,
            "updated_by": transfo.updated_by,
            "extra_data": transfo.extra_data if transfo.extra_data else {},
            "tags": transfo.tags if transfo.tags else [],
            "version": transfo.version
        })
    
    return {
        "total": result["total"],
        "page": result["page"],
        "size": result["size"],
        "pages": result["pages"],
        "items": items
    }


# ========================
# CALCULER RECETTE SAVON
# ========================
@router.post("/calculer-savon", response_model=CalculSavonResponse)
async def calculer_recette_savon(
    request: RecetteSavon,
    current_user: User = Depends(get_current_active_user)
):
    """
    Calcule les quantités nécessaires pour la fabrication de savon.
    """
    # Validation des entrées
    if request.huile_l <= 0:
        raise BadRequestException("La quantité d'huile doit être positive")
    
    if request.surgraissage < 0 or request.surgraissage > 20:
        raise BadRequestException("Le surgraissage doit être entre 0% et 20%")
    
    # Calculs
    huile_kg = request.huile_l * DENSITE_HUILE_ARACHIDE
    
    # Soude nécessaire (NaOH)
    soude_kg = huile_kg * INDICE_SAPONIFICATION * (1 - request.surgraissage / 100)
    
    # Eau: 25-30% du poids de l'huile
    eau_kg = huile_kg * 0.28
    
    # Poids total et nombre de savons (poids moyen 100g)
    poids_total = huile_kg + soude_kg + eau_kg
    nb_savons = math.floor(poids_total / 0.1)  # 100g par savon
    
    result = {
        "huile_kg": round(huile_kg, 2),
        "soude_kg": round(soude_kg, 2),
        "eau_kg": round(eau_kg, 2),
        "poids_total": round(poids_total, 2),
        "nb_savons": nb_savons,
        "surgraissage": request.surgraissage
    }
    
    if request.additifs:
        result["additifs"] = request.additifs
    if request.parfum:
        result["parfum"] = request.parfum
    
    logger.info(f"Calcul recette savon: {request.huile_l}L → {nb_savons} savons")
    
    return result


# ========================
# TRANSFORMATION EN HUILE
# ========================
@router.post("/huile", response_model=TransformationResponse, status_code=status.HTTP_201_CREATED)
async def transformer_en_huile(
    request: TransformationHuileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Transforme un lot d'arachide en huile.
    """
    try:
        logger.info(f"=== TRANSFORMATION EN HUILE ===")
        logger.info(f"Utilisateur: {current_user.email}")
        
        # Vérifier que le lot entrant existe
        lot_entree = db.query(Lot).filter(Lot.id == request.lot_entree_id).first()
        if not lot_entree:
            raise NotFoundException("Lot entrant non trouvé")
        
        # Vérifier le type de lot
        if lot_entree.type not in [TypeLot.ARACHIDE_BRUTE, TypeLot.ARACHIDE_DECORTIQUEE]:
            raise BadRequestException(
                f"Le lot entrant doit être de l'arachide (brute ou décortiquée). "
                f"Type actuel: {lot_entree.type}"
            )
        
        # Vérifier la quantité disponible
        if lot_entree.quantite_restante < request.quantite_entree:
            raise BadRequestException(
                f"Quantité insuffisante. Disponible: {lot_entree.quantite_restante} {lot_entree.unite}"
            )
        
        # Vérifier que la quantité d'huile produite est réaliste
        rendement_calcule = (request.quantite_sortie / request.quantite_entree) * 100
        if rendement_calcule < RENDEMENT_HUILE_MIN or rendement_calcule > RENDEMENT_HUILE_MAX:
            logger.warning(
                f"Rendement anormal: {rendement_calcule:.1f}% "
                f"(normal: {RENDEMENT_HUILE_MIN}-{RENDEMENT_HUILE_MAX}%)"
            )
        
        # Créer le lot d'huile
        lot_huile = Lot(
            type=TypeLot.HUILE,
            parcelle_source=lot_entree.parcelle_source,
            quantite_initiale=request.quantite_sortie,
            quantite_restante=request.quantite_sortie,
            unite="L",
            date_production=request.date_transformation,
            date_peremption=datetime.now().date() + timedelta(days=365),  # 1 an
            qualite=request.qualite if hasattr(request, 'qualite') else "bonne",
            est_transformable=False
        )
        lot_huile.generer_code()
        
        db.add(lot_huile)
        db.flush()
        
        # Créer la transformation
        transformation = Transformation(
            type=TypeTransformation.HUILE,
            lot_entree_id=request.lot_entree_id,
            lot_sortie_id=lot_huile.id,
            date_transformation=request.date_transformation,
            responsable_id=current_user.id,
            quantite_entree=request.quantite_entree,
            quantite_sortie=request.quantite_sortie,
            observations=request.observations
        )
        transformation.calculer_rendement()
        
        db.add(transformation)
        
        # Réduire le stock du lot entrant
        lot_entree.reduire_stock(request.quantite_entree)
        
        db.commit()
        db.refresh(transformation)
        db.refresh(lot_huile)
        
        logger.info(
            f"✅ Transformation en huile: {request.quantite_entree} kg → "
            f"{request.quantite_sortie} L (Rendement: {transformation.rendement:.1f}%)"
        )
        
        HistoriqueService.log_create(
            db=db,
            user_id=current_user.id,
            entity_type="transformation",
            entity_id=transformation.id,
            data=request.model_dump()
        )
        
        return {
            "id": transformation.id,
            "type": transformation.type,
            "lot_entree_id": transformation.lot_entree_id,
            "lot_entree_code": lot_entree.code,
            "lot_sortie_id": lot_huile.id,
            "lot_sortie_code": lot_huile.code,
            "date_transformation": transformation.date_transformation,
            "responsable_id": current_user.id,
            "responsable_nom": f"{current_user.prenom} {current_user.nom}",
            "quantite_entree": transformation.quantite_entree,
            "quantite_sortie": transformation.quantite_sortie,
            "rendement": transformation.rendement,
            "recette": None,
            "observations": transformation.observations,
            "created_at": transformation.created_at,
            "updated_at": transformation.updated_at,
            "created_by": transformation.created_by,
            "updated_by": transformation.updated_by,
            "extra_data": transformation.extra_data if transformation.extra_data else {},
            "tags": transformation.tags if transformation.tags else [],
            "version": transformation.version
        }
        
    except BadRequestException:
        raise
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur transformation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


# # ========================
# # TRANSFORMATION EN SAVON
# # ========================
# @router.post("/savon", response_model=TransformationResponse, status_code=status.HTTP_201_CREATED)
# async def transformer_en_savon(
#     request: TransformationSavonCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ):
#     """
#     Transforme un lot d'huile en savon.
#     """
#     try:
#         logger.info(f"=== TRANSFORMATION EN SAVON ===")
#         logger.info(f"Utilisateur: {current_user.email}")
        
#         # Vérifier que le lot entrant existe
#         lot_entree = db.query(Lot).filter(Lot.id == request.lot_entree_id).first()
#         if not lot_entree:
#             raise NotFoundException("Lot entrant non trouvé")
        
#         # Vérifier le type de lot
#         if lot_entree.type != TypeLot.HUILE:
#             raise BadRequestException(
#                 f"Le lot entrant doit être de l'huile. Type actuel: {lot_entree.type}"
#             )
        
#         # Calculer les quantités de la recette
#         huile_kg = request.recette.huile_l * DENSITE_HUILE_ARACHIDE
        
#         # Vérifier la quantité d'huile disponible
#         if lot_entree.quantite_restante < huile_kg:
#             raise BadRequestException(
#                 f"Quantité d'huile insuffisante. "
#                 f"Disponible: {lot_entree.quantite_restante} kg, "
#                 f"Nécessaire: {huile_kg} kg"
#             )
        
#         # Calculs de saponification
#         soude_kg = huile_kg * INDICE_SAPONIFICATION * (1 - request.recette.surgraissage / 100)
#         eau_kg = huile_kg * 0.28
#         poids_total = huile_kg + soude_kg + eau_kg
        
#         # Nombre de savons
#         if request.quantite_sortie:
#             nb_savons = request.quantite_sortie
#         else:
#             nb_savons = math.floor(poids_total / 0.1)  # 100g par savon
        
#         # Vérifier que le nombre de savons est réaliste
#         if nb_savons <= 0:
#             raise BadRequestException("La quantité d'huile est insuffisante pour produire au moins un savon")
        
#         # Créer le lot de savons
#         lot_savon = Lot(
#             type=TypeLot.SAVON,
#             parcelle_source=lot_entree.parcelle_source,
#             quantite_initiale=nb_savons,
#             quantite_restante=nb_savons,
#             unite="piece",
#             date_production=request.date_transformation,
#             date_peremption=datetime.now().date() + timedelta(days=730),  # 2 ans
#             qualite="excellente",
#             est_transformable=False
#         )
#         lot_savon.generer_code()
        
#         db.add(lot_savon)
#         db.flush()
        
#         # Créer la transformation
#         recette_complete = {
#             "huile_l": request.recette.huile_l,
#             "huile_kg": round(huile_kg, 2),
#             "soude_kg": round(soude_kg, 2),
#             "eau_kg": round(eau_kg, 2),
#             "poids_total": round(poids_total, 2),
#             "surgraissage": request.recette.surgraissage,
#             "additifs": request.recette.additifs if request.recette.additifs else [],
#             "parfum": request.recette.parfum if request.recette.parfum else None,
#             "nb_savons_calcules": nb_savons
#         }
        
#         transformation = Transformation(
#             type=TypeTransformation.SAVON,
#             lot_entree_id=request.lot_entree_id,
#             lot_sortie_id=lot_savon.id,
#             date_transformation=request.date_transformation,
#             responsable_id=current_user.id,
#             quantite_entree=huile_kg,
#             quantite_sortie=nb_savons,
#             recette=recette_complete,
#             observations=request.observations
#         )
#         transformation.calculer_rendement()
        
#         db.add(transformation)
        
#         # Réduire le stock du lot entrant
#         lot_entree.reduire_stock(huile_kg)
        
#         db.commit()
#         db.refresh(transformation)
#         db.refresh(lot_savon)
        
#         logger.info(
#             f"✅ Transformation en savon: {request.recette.huile_l} L → {nb_savons} savons "
#             f"(Rendement: {transformation.rendement:.1f} savons/kg)"
#         )
        
#         HistoriqueService.log_create(
#             db=db,
#             user_id=current_user.id,
#             entity_type="transformation",
#             entity_id=transformation.id,
#             data=request.model_dump()
#         )
        
#         return {
#             "id": transformation.id,
#             "type": transformation.type,
#             "lot_entree_id": transformation.lot_entree_id,
#             "lot_entree_code": lot_entree.code,
#             "lot_sortie_id": lot_savon.id,
#             "lot_sortie_code": lot_savon.code,
#             "date_transformation": transformation.date_transformation,
#             "responsable_id": current_user.id,
#             "responsable_nom": f"{current_user.prenom} {current_user.nom}",
#             "quantite_entree": transformation.quantite_entree,
#             "quantite_sortie": transformation.quantite_sortie,
#             "rendement": transformation.rendement,
#             "recette": transformation.recette,
#             "observations": transformation.observations,
#             "created_at": transformation.created_at,
#             "updated_at": transformation.updated_at,
#             "created_by": transformation.created_by,
#             "updated_by": transformation.updated_by,
#             "extra_data": transformation.extra_data if transformation.extra_data else {},
#             "tags": transformation.tags if transformation.tags else [],
#             "version": transformation.version
#         }
        
#     except BadRequestException:
#         raise
#     except NotFoundException:
#         raise
#     except Exception as e:
#         logger.error(f"❌ Erreur transformation: {e}")
#         import traceback
#         logger.error(traceback.format_exc())
#         db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur interne: {str(e)}"
#         )

# ========================
# TRANSFORMATION EN SAVON
# ========================
@router.post("/savon", response_model=TransformationResponse, status_code=status.HTTP_201_CREATED)
async def transformer_en_savon(
    request: TransformationSavonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Transforme un lot d'huile en savon.
    """
    try:
        logger.info(f"=== TRANSFORMATION EN SAVON ===")
        logger.info(f"Utilisateur: {current_user.email}")
        
        # Vérifier que le lot entrant existe
        lot_entree = db.query(Lot).filter(Lot.id == request.lot_entree_id).first()
        if not lot_entree:
            raise NotFoundException("Lot entrant non trouvé")
        
        # Vérifier le type de lot
        if lot_entree.type != TypeLot.HUILE:
            raise BadRequestException(
                f"Le lot entrant doit être de l'huile. Type actuel: {lot_entree.type}"
            )
        
        # Calculer les quantités de la recette
        huile_kg = request.recette.huile_l * DENSITE_HUILE_ARACHIDE
        
        # Vérifier la quantité d'huile disponible
        if lot_entree.quantite_restante < huile_kg:
            raise BadRequestException(
                f"Quantité d'huile insuffisante. "
                f"Disponible: {lot_entree.quantite_restante} kg, "
                f"Nécessaire: {huile_kg} kg"
            )
        
        # Calculs de saponification
        soude_kg = huile_kg * INDICE_SAPONIFICATION * (1 - request.recette.surgraissage / 100)
        eau_kg = huile_kg * 0.28
        poids_total = huile_kg + soude_kg + eau_kg
        
        # Nombre de savons
        if request.quantite_sortie:
            nb_savons = request.quantite_sortie
        else:
            nb_savons = math.floor(poids_total / 0.1)  # 100g par savon
        
        # Vérifier que le nombre de savons est réaliste
        if nb_savons <= 0:
            raise BadRequestException("La quantité d'huile est insuffisante pour produire au moins un savon")
        
        # Créer le lot de savons
        lot_savon = Lot(
            type=TypeLot.SAVON,
            parcelle_source=lot_entree.parcelle_source,
            quantite_initiale=nb_savons,
            quantite_restante=nb_savons,
            unite="piece",
            date_production=request.date_transformation,
            date_peremption=datetime.now().date() + timedelta(days=730),  # 2 ans
            qualite="excellente",
            est_transformable=False
        )
        lot_savon.generer_code()
        
        db.add(lot_savon)
        db.flush()
        
        # Créer la transformation avec recette en dictionnaire
        recette_complete = {
            "huile_l": request.recette.huile_l,
            "huile_kg": round(huile_kg, 2),
            "soude_kg": round(soude_kg, 2),
            "eau_kg": round(eau_kg, 2),
            "poids_total": round(poids_total, 2),
            "surgraissage": request.recette.surgraissage,
            "additifs": request.recette.additifs if request.recette.additifs else [],
            "parfum": request.recette.parfum if request.recette.parfum else None,
            "nb_savons_calcules": nb_savons
        }
        
        transformation = Transformation(
            type=TypeTransformation.SAVON,
            lot_entree_id=request.lot_entree_id,
            lot_sortie_id=lot_savon.id,
            date_transformation=request.date_transformation,
            responsable_id=current_user.id,
            quantite_entree=huile_kg,
            quantite_sortie=nb_savons,
            recette=recette_complete,  # Assurez-vous que c'est un dictionnaire, pas une string
            observations=request.observations
        )
        transformation.calculer_rendement()
        
        db.add(transformation)
        
        # Réduire le stock du lot entrant
        lot_entree.reduire_stock(huile_kg)
        
        db.commit()
        db.refresh(transformation)
        db.refresh(lot_savon)
        
        logger.info(
            f"✅ Transformation en savon: {request.recette.huile_l} L → {nb_savons} savons "
            f"(Rendement: {transformation.rendement:.1f} savons/kg)"
        )
        
        HistoriqueService.log_create(
            db=db,
            user_id=current_user.id,
            entity_type="transformation",
            entity_id=transformation.id,
            data=request.model_dump()
        )
        
        return {
            "id": transformation.id,
            "type": transformation.type,
            "lot_entree_id": transformation.lot_entree_id,
            "lot_entree_code": lot_entree.code,
            "lot_sortie_id": lot_savon.id,
            "lot_sortie_code": lot_savon.code,
            "date_transformation": transformation.date_transformation,
            "responsable_id": current_user.id,
            "responsable_nom": f"{current_user.prenom} {current_user.nom}",
            "quantite_entree": transformation.quantite_entree,
            "quantite_sortie": transformation.quantite_sortie,
            "rendement": transformation.rendement,
            "recette": transformation.recette,  # C'est déjà un dictionnaire
            "observations": transformation.observations,
            "created_at": transformation.created_at,
            "updated_at": transformation.updated_at,
            "created_by": transformation.created_by,
            "updated_by": transformation.updated_by,
            "extra_data": transformation.extra_data if transformation.extra_data else {},
            "tags": transformation.tags if transformation.tags else [],
            "version": transformation.version
        }
        
    except BadRequestException:
        raise
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur transformation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )

# ========================
# RÉCUPÉRER UNE TRANSFORMATION
# ========================
@router.get("/{transformation_id}", response_model=TransformationResponse)
async def get_transformation(
    transformation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les détails d'une transformation.
    """
    transformation = db.query(Transformation).filter(
        Transformation.id == transformation_id
    ).first()
    
    if not transformation:
        raise NotFoundException("Transformation non trouvée")
    
    return transformation


# ========================
# STATISTIQUES DES TRANSFORMATIONS
# ========================
@router.get("/stats/summary")
async def get_transformations_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les statistiques des transformations.
    """
    transformations = db.query(Transformation).all()
    
    if not transformations:
        return {
            "total": 0,
            "total_huile": 0,
            "total_savon": 0,
            "total_huile_produite": 0,
            "total_savon_produit": 0,
            "total_arachide_transformee": 0,
            "rendement_moyen_huile": 0,
            "rendement_min_huile": 0,
            "rendement_max_huile": 0
        }
    
    transformations_huile = [t for t in transformations if t.type == TypeTransformation.HUILE]
    transformations_savon = [t for t in transformations if t.type == TypeTransformation.SAVON]
    
    rendements_huile = [t.rendement for t in transformations_huile if t.rendement]
    
    stats = {
        "total": len(transformations),
        "total_huile": len(transformations_huile),
        "total_savon": len(transformations_savon),
        "total_huile_produite": sum(t.quantite_sortie for t in transformations_huile if t.quantite_sortie),
        "total_savon_produit": sum(t.quantite_sortie for t in transformations_savon if t.quantite_sortie),
        "total_arachide_transformee": sum(t.quantite_entree for t in transformations_huile),
        "rendement_moyen_huile": sum(rendements_huile) / len(rendements_huile) if rendements_huile else 0,
        "rendement_min_huile": min(rendements_huile) if rendements_huile else 0,
        "rendement_max_huile": max(rendements_huile) if rendements_huile else 0,
        "savons_par_litre": sum(t.quantite_sortie for t in transformations_savon) / sum(t.quantite_entree for t in transformations_savon) if transformations_savon else 0
    }
    
    return stats


# ========================
# RENDEMENT PAR LOT D'ARACHIDE
# ========================
@router.get("/rendement/lot/{lot_id}")
async def get_rendement_par_lot(
    lot_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère le rendement pour un lot d'arachide spécifique.
    """
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise NotFoundException("Lot non trouvé")
    
    transformations = db.query(Transformation).filter(
        Transformation.lot_entree_id == lot_id,
        Transformation.type == TypeTransformation.HUILE
    ).all()
    
    if not transformations:
        return {
            "lot_id": lot_id,
            "lot_code": lot.code,
            "quantite_arachide": lot.quantite_initiale,
            "quantite_utilisee": lot.quantite_utilisee,
            "huile_produite": 0,
            "rendement": 0
        }
    
    huile_produite = sum(t.quantite_sortie for t in transformations)
    rendement = (huile_produite / lot.quantite_utilisee) * 100 if lot.quantite_utilisee > 0 else 0
    
    return {
        "lot_id": lot_id,
        "lot_code": lot.code,
        "quantite_arachide": lot.quantite_initiale,
        "quantite_utilisee": lot.quantite_utilisee,
        "huile_produite": huile_produite,
        "rendement": round(rendement, 2),
        "transformations": [
            {
                "id": t.id,
                "date": t.date_transformation,
                "quantite_entree": t.quantite_entree,
                "quantite_sortie": t.quantite_sortie,
                "rendement": t.rendement
            }
            for t in transformations
        ]
    }