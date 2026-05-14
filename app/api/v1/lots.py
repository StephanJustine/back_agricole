"""
Routes CRUD pour les lots.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, datetime
import logging

from ...database import get_db
from ...models.lot import Lot
from ...models.recolte import Recolte
from ...models.culture import Culture  # <-- IMPORT AJOUTÉ
from ...models.parcelle import Parcelle
from ...models.user import User
from ...models.enums import TypeLot
from ...schemas.lot import *
from ...core.dependencies import get_current_active_user
from ...core.pagination import paginate
from ...core.exceptions import NotFoundException, BadRequestException
from ...core.historique import HistoriqueService
from ...schemas.recolte import RecolteCreate

logger = logging.getLogger(__name__)
router = APIRouter()


# ========================
# LISTE DES LOTS
# ========================
@router.get("/", response_model=LotList)
async def get_lots(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    type: Optional[TypeLot] = Query(None, description="Filtrer par type"),
    code: Optional[str] = Query(None, description="Filtrer par code"),
    est_disponible: Optional[bool] = Query(None, description="Filtrer par disponibilité"),
    date_debut: Optional[date] = Query(None, description="Date de début"),
    date_fin: Optional[date] = Query(None, description="Date de fin"),
    sort_by: str = Query("date_production", description="Tri par champ"),
    sort_desc: bool = Query(True, description="Tri décroissant"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère la liste des lots de l'utilisateur connecté.
    """
    # Requête simplifiée - on récupère d'abord les IDs des récoltes de l'utilisateur
    parcelles_ids = [p.id for p in db.query(Parcelle.id).filter(
        Parcelle.proprietaire_id == current_user.id
    ).all()]
    
    recoltes_ids = []
    if parcelles_ids:
        cultures_ids = [c.id for c in db.query(Culture.id).filter(
            Culture.parcelle_id.in_(parcelles_ids)
        ).all()]
        if cultures_ids:
            recoltes_ids = [r.id for r in db.query(Recolte.id).filter(
                Recolte.culture_id.in_(cultures_ids)
            ).all()]
    
    query = db.query(Lot)
    if recoltes_ids:
        query = query.filter(
            (Lot.recolte_id.in_(recoltes_ids)) | (Lot.recolte_id.is_(None))
        )
    else:
        query = query.filter(Lot.recolte_id.is_(None))
    
    if type:
        query = query.filter(Lot.type == type)
    if code:
        query = query.filter(Lot.code.ilike(f"%{code}%"))
    if est_disponible is not None:
        if est_disponible:
            query = query.filter(Lot.quantite_restante > 0, Lot.est_epuise == False)
        else:
            query = query.filter((Lot.quantite_restante == 0) | (Lot.est_epuise == True))
    if date_debut:
        query = query.filter(Lot.date_production >= date_debut)
    if date_fin:
        query = query.filter(Lot.date_production <= date_fin)
    
    if sort_desc:
        query = query.order_by(getattr(Lot, sort_by).desc())
    else:
        query = query.order_by(getattr(Lot, sort_by).asc())
    
    result = paginate(query, page, size)
    
    items = []
    for lot in result["items"]:
        items.append({
            "id": lot.id,
            "code": lot.code,
            "type": lot.type,
            "recolte_id": lot.recolte_id,
            "parcelle_source": lot.parcelle_source,
            "quantite_initiale": lot.quantite_initiale,
            "quantite_restante": lot.quantite_restante,
            "unite": lot.unite,
            "date_production": lot.date_production,
            "date_peremption": lot.date_peremption,
            "qualite": lot.qualite,
            "certificats": lot.certificats,
            "est_transformable": lot.est_transformable,
            "est_vendu": lot.est_vendu,
            "est_epuise": lot.est_epuise,
            "notes": lot.notes,
            "quantite_utilisee": lot.quantite_utilisee,
            "taux_utilisation": lot.taux_utilisation,
            "est_disponible": lot.est_disponible,
            "created_at": lot.created_at,
            "updated_at": lot.updated_at,
            "created_by": lot.created_by,
            "updated_by": lot.updated_by,
            "extra_data": lot.extra_data if lot.extra_data else {},
            "tags": lot.tags if lot.tags else [],
            "version": lot.version
        })
    
    return {
        "total": result["total"],
        "page": result["page"],
        "size": result["size"],
        "pages": result["pages"],
        "items": items
    }


# ========================
# SCANNER UN CODE DE LOT
# ========================
@router.get("/scan/{code}", response_model=ScanLotResponse)
async def scan_lot(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Scanne un code de lot pour voir son origine et ses informations.
    """
    lot = db.query(Lot).filter(Lot.code == code).first()
    
    if not lot:
        raise NotFoundException(f"Lot avec le code {code} non trouvé")
    
    origine = lot.origine_complete
    
    return {
        "code": lot.code,
        "type": lot.type,
        "origine": origine,
        "quantite_restante": lot.quantite_restante,
        "unite": lot.unite,
        "date_production": lot.date_production,
        "date_peremption": lot.date_peremption,
        "qualite": lot.qualite,
        "est_disponible": lot.est_disponible
    }


# ========================
# CRÉER UN LOT MANUELLEMENT
# ========================
@router.post("/", response_model=LotResponse, status_code=status.HTTP_201_CREATED)
async def create_lot(
    request: LotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Crée un lot manuellement.
    """
    try:
        logger.info(f"=== CRÉATION LOT ===")
        logger.info(f"Utilisateur: {current_user.email}")
        logger.info(f"Données reçues: {request.model_dump()}")
        
        # Vérifier que la récolte existe si fournie
        if request.recolte_id:
            # Récupérer les parcelles de l'utilisateur
            parcelles_ids = [p.id for p in db.query(Parcelle.id).filter(
                Parcelle.proprietaire_id == current_user.id
            ).all()]
            
            if not parcelles_ids:
                raise NotFoundException("Récolte non trouvée ou non autorisée")
            
            # Récupérer les cultures liées à ces parcelles
            cultures_ids = [c.id for c in db.query(Culture.id).filter(
                Culture.parcelle_id.in_(parcelles_ids)
            ).all()]
            
            if not cultures_ids:
                raise NotFoundException("Récolte non trouvée ou non autorisée")
            
            # Vérifier la récolte
            recolte = db.query(Recolte).filter(
                Recolte.id == request.recolte_id,
                Recolte.culture_id.in_(cultures_ids)
            ).first()
            
            if not recolte:
                raise NotFoundException("Récolte non trouvée ou non autorisée")
        
        # Vérifier que la parcelle source existe si fournie
        if request.parcelle_source:
            parcelle = db.query(Parcelle).filter(
                Parcelle.id == request.parcelle_source,
                Parcelle.proprietaire_id == current_user.id
            ).first()
            
            if not parcelle:
                raise NotFoundException("Parcelle non trouvée ou non autorisée")
        
        # Créer le lot
        lot = Lot(
            type=request.type,
            recolte_id=request.recolte_id,
            parcelle_source=request.parcelle_source,
            quantite_initiale=request.quantite_initiale,
            quantite_restante=request.quantite_initiale,
            unite=request.unite,
            date_production=request.date_production,
            date_peremption=request.date_peremption,
            qualite=request.qualite,
            certificats=request.certificats,
            est_transformable=request.est_transformable,
            notes=request.notes
        )
        
        lot.generer_code()
        
        db.add(lot)
        db.commit()
        db.refresh(lot)
        
        logger.info(f"✅ Lot créé: {lot.code}")
        
        HistoriqueService.log_create(
            db=db,
            user_id=current_user.id,
            entity_type="lot",
            entity_id=lot.id,
            data=request.model_dump()
        )
        
        return lot
        
    except BadRequestException:
        raise
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur création lot: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


# ========================
# CRÉATION BULK LOT
# ========================
@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def create_recoltes_bulk(
    requests: List[RecolteCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Création multiple de récoltes (BULK).
    """

    created = []
    errors = []

    # ========================
    # cultures autorisées user (SET = plus rapide)
    # ========================
    cultures_ids = {
        c.id for c in db.query(Culture.id)
        .join(Parcelle)
        .filter(Parcelle.proprietaire_id == current_user.id)
        .all()
    }

    from datetime import date

    for index, request in enumerate(requests):
        try:

            # ========================
            # 1. validation culture
            # ========================
            if request.culture_id not in cultures_ids:
                errors.append({
                    "index": index,
                    "error": "Culture non autorisée"
                })
                continue

            # ========================
            # 2. validation dates
            # ========================
            if request.date_debut > date.today():
                errors.append({
                    "index": index,
                    "error": "Date début future interdite"
                })
                continue

            if request.date_fin and request.date_fin < request.date_debut:
                errors.append({
                    "index": index,
                    "error": "Date fin invalide"
                })
                continue

            # ========================
            # 3. validation qualité
            # ========================
            if request.qualite not in ["excellente", "bonne", "moyenne", "mauvaise"]:
                errors.append({
                    "index": index,
                    "error": "Qualité invalide"
                })
                continue

            # ========================
            # 4. duplicate check
            # ========================
            existing = db.query(Recolte).filter(
                Recolte.culture_id == request.culture_id
            ).first()

            if existing:
                errors.append({
                    "index": index,
                    "error": "Récolte déjà existante pour cette culture"
                })
                continue

            # ========================
            # 5. CREATE
            # ========================
            recolte = Recolte(
                culture_id=request.culture_id,
                date_debut=request.date_debut,
                date_fin=request.date_fin,
                poids_frais=request.poids_frais,
                poids_sec=request.poids_sec,
                humidite=request.humidite,
                qualite=request.qualite,
                taux_gousses_vides=request.taux_gousses_vides,
                taux_gousses_abimees=request.taux_gousses_abimees,
                taux_impuretes=request.taux_impuretes,
                poids_100_gousses=request.poids_100_gousses,
                poids_100_graines=request.poids_100_graines,
                nb_gousses_par_plant=request.nb_gousses_par_plant,
                nb_sacs=request.nb_sacs,
                observations=request.observations
            )

            # ========================
            # calculs métier
            # ========================
            recolte.calculer_rendement(recolte.poids_sec or 1)
            recolte.generate_code()

            db.add(recolte)
            db.commit()
            db.refresh(recolte)

            created.append({
                "id": recolte.id,
                "code": recolte.code,
                "culture_id": recolte.culture_id,
                "qualite": recolte.qualite
            })

        except Exception as e:
            db.rollback()
            errors.append({
                "index": index,
                "error": str(e)
            })

    return {
        "total_received": len(requests),
        "created": len(created),
        "failed": len(errors),
        "data": created,
        "errors": errors
    }
# ========================
# CRÉER UN LOT À PARTIR D'UNE RÉCOLTE
# ========================
@router.post("/from-recolte/{recolte_id}", response_model=LotResponse, status_code=status.HTTP_201_CREATED)
async def create_lot_from_recolte(
    recolte_id: str,
    request: LotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Crée un lot à partir d'une récolte.
    """
    try:
        # Vérifier que la récolte existe et appartient à l'utilisateur
        parcelles_ids = [p.id for p in db.query(Parcelle.id).filter(
            Parcelle.proprietaire_id == current_user.id
        ).all()]
        
        if not parcelles_ids:
            raise NotFoundException("Récolte non trouvée ou non autorisée")
        
        cultures_ids = [c.id for c in db.query(Culture.id).filter(
            Culture.parcelle_id.in_(parcelles_ids)
        ).all()]
        
        if not cultures_ids:
            raise NotFoundException("Récolte non trouvée ou non autorisée")
        
        recolte = db.query(Recolte).filter(
            Recolte.id == recolte_id,
            Recolte.culture_id.in_(cultures_ids)
        ).first()
        
        if not recolte:
            raise NotFoundException("Récolte non trouvée ou non autorisée")
        
        # Créer le lot
        lot = Lot(
            type=request.type,
            recolte_id=recolte_id,
            parcelle_source=recolte.culture.parcelle_id if recolte.culture else None,
            quantite_initiale=request.quantite_initiale,
            quantite_restante=request.quantite_initiale,
            unite=request.unite,
            date_production=request.date_production,
            date_peremption=request.date_peremption,
            qualite=request.qualite or (recolte.qualite.value if recolte.qualite else None),
            certificats=request.certificats,
            est_transformable=request.est_transformable,
            notes=request.notes
        )
        
        lot.generer_code()
        
        db.add(lot)
        db.commit()
        db.refresh(lot)
        
        logger.info(f"✅ Lot créé: {lot.code} à partir de récolte {recolte_id}")
        
        HistoriqueService.log_create(
            db=db,
            user_id=current_user.id,
            entity_type="lot",
            entity_id=lot.id,
            data=request.model_dump()
        )
        
        return lot
        
    except BadRequestException:
        raise
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur création lot: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


# ========================
# RÉCUPÉRER UN LOT
# ========================
@router.get("/{lot_id}", response_model=LotDetailResponse)
async def get_lot(
    lot_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les détails d'un lot.
    """
    # Récupérer les IDs des récoltes autorisées
    parcelles_ids = [p.id for p in db.query(Parcelle.id).filter(
        Parcelle.proprietaire_id == current_user.id
    ).all()]
    
    recoltes_ids = []
    if parcelles_ids:
        cultures_ids = [c.id for c in db.query(Culture.id).filter(
            Culture.parcelle_id.in_(parcelles_ids)
        ).all()]
        if cultures_ids:
            recoltes_ids = [r.id for r in db.query(Recolte.id).filter(
                Recolte.culture_id.in_(cultures_ids)
            ).all()]
    
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    
    if not lot:
        raise NotFoundException("Lot non trouvé")
    
    # Vérifier l'autorisation
    if lot.recolte_id and lot.recolte_id not in recoltes_ids:
        raise NotFoundException("Lot non trouvé")
    
    return lot


# ========================
# METTRE À JOUR UN LOT
# ========================
@router.put("/{lot_id}", response_model=LotResponse)
async def update_lot(
    lot_id: str,
    request: LotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Met à jour un lot.
    """
    # Récupérer les IDs des récoltes autorisées
    parcelles_ids = [p.id for p in db.query(Parcelle.id).filter(
        Parcelle.proprietaire_id == current_user.id
    ).all()]
    
    recoltes_ids = []
    if parcelles_ids:
        cultures_ids = [c.id for c in db.query(Culture.id).filter(
            Culture.parcelle_id.in_(parcelles_ids)
        ).all()]
        if cultures_ids:
            recoltes_ids = [r.id for r in db.query(Recolte.id).filter(
                Recolte.culture_id.in_(cultures_ids)
            ).all()]
    
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    
    if not lot:
        raise NotFoundException("Lot non trouvé")
    
    if lot.recolte_id and lot.recolte_id not in recoltes_ids:
        raise NotFoundException("Lot non trouvé")
    
    update_data = request.model_dump(exclude_unset=True)
    old_data = {
        "qualite": lot.qualite,
        "est_transformable": lot.est_transformable
    }
    
    for key, value in update_data.items():
        if hasattr(lot, key):
            setattr(lot, key, value)
    
    lot.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(lot)
    
    HistoriqueService.log_update(
        db=db,
        user_id=current_user.id,
        entity_type="lot",
        entity_id=lot.id,
        old_data=old_data,
        new_data=update_data
    )
    
    return lot


# ========================
# SUPPRIMER UN LOT
# ========================
@router.delete("/{lot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lot(
    lot_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Supprime un lot.
    """
    # Récupérer les IDs des récoltes autorisées
    parcelles_ids = [p.id for p in db.query(Parcelle.id).filter(
        Parcelle.proprietaire_id == current_user.id
    ).all()]
    
    recoltes_ids = []
    if parcelles_ids:
        cultures_ids = [c.id for c in db.query(Culture.id).filter(
            Culture.parcelle_id.in_(parcelles_ids)
        ).all()]
        if cultures_ids:
            recoltes_ids = [r.id for r in db.query(Recolte.id).filter(
                Recolte.culture_id.in_(cultures_ids)
            ).all()]
    
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    
    if not lot:
        raise NotFoundException("Lot non trouvé")
    
    if lot.recolte_id and lot.recolte_id not in recoltes_ids:
        raise NotFoundException("Lot non trouvé")
    
    db.delete(lot)
    db.commit()
    
    return None


# ========================
# STATISTIQUES DES LOTS
# ========================
@router.get("/stats/summary")
async def get_lots_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les statistiques des lots.
    """
    # Récupérer les IDs des récoltes autorisées
    parcelles_ids = [p.id for p in db.query(Parcelle.id).filter(
        Parcelle.proprietaire_id == current_user.id
    ).all()]
    
    recoltes_ids = []
    if parcelles_ids:
        cultures_ids = [c.id for c in db.query(Culture.id).filter(
            Culture.parcelle_id.in_(parcelles_ids)
        ).all()]
        if cultures_ids:
            recoltes_ids = [r.id for r in db.query(Recolte.id).filter(
                Recolte.culture_id.in_(cultures_ids)
            ).all()]
    
    query = db.query(Lot)
    if recoltes_ids:
        query = query.filter(
            (Lot.recolte_id.in_(recoltes_ids)) | (Lot.recolte_id.is_(None))
        )
    else:
        query = query.filter(Lot.recolte_id.is_(None))
    
    lots = query.all()
    
    if not lots:
        return {
            "total": 0,
            "total_quantite": 0,
            "par_type": {}
        }
    
    par_type = {}
    total_quantite = 0
    
    for lot in lots:
        type_key = lot.type.value if hasattr(lot.type, 'value') else str(lot.type)
        par_type[type_key] = par_type.get(type_key, 0) + 1
        par_type[f"{type_key}_quantite"] = par_type.get(f"{type_key}_quantite", 0) + lot.quantite_restante
        total_quantite += lot.quantite_restante
    
    return {
        "total": len(lots),
        "total_quantite": total_quantite,
        "lots_disponibles": sum(1 for l in lots if l.est_disponible),
        "lots_epuises": sum(1 for l in lots if l.est_epuise),
        "par_type": par_type
    }