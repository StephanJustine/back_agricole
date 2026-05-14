"""
Routes CRUD pour les cultures.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional,List
from datetime import date, datetime
import logging

from ...database import get_db
from ...models.culture import Culture
from ...models.parcelle import Parcelle
from ...models.user import User
from ...models.enums import StadeCulture
from ...schemas.culture import *
from ...core.dependencies import get_current_active_user
from ...core.pagination import paginate
from ...core.exceptions import NotFoundException, BadRequestException
from ...core.historique import HistoriqueService

logger = logging.getLogger(__name__)
router = APIRouter()


# ========================
# LISTE DES CULTURES
# ========================
@router.get("/", response_model=CultureList)
async def get_cultures(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(20, ge=1, le=100, description="Nombre d'éléments par page"),
    parcelle_id: Optional[str] = Query(None, description="Filtrer par parcelle"),
    stade: Optional[StadeCulture] = Query(None, description="Filtrer par stade"),
    search: Optional[str] = Query(None, description="Recherche par variété"),
    is_active: Optional[bool] = Query(None, description="Filtrer par cultures actives"),
    sort_by: str = Query("created_at", description="Tri par champ"),
    sort_desc: bool = Query(False, description="Tri décroissant"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère la liste des cultures de l'utilisateur connecté.
    """
    # Jointure avec parcelle pour filtrer par utilisateur
    query = db.query(Culture).join(Parcelle).filter(
        Parcelle.proprietaire_id == current_user.id
    )
    
    # Filtres
    if parcelle_id:
        query = query.filter(Culture.parcelle_id == parcelle_id)
    if stade:
        query = query.filter(Culture.stade == stade)
    if is_active is not None:
        if is_active:
            query = query.filter(Culture.date_fin_reelle.is_(None))
        else:
            query = query.filter(Culture.date_fin_reelle.isnot(None))
    if search:
        query = query.filter(Culture.variete.ilike(f"%{search}%"))
    
    # Tri
    if sort_desc:
        query = query.order_by(getattr(Culture, sort_by).desc())
    else:
        query = query.order_by(getattr(Culture, sort_by).asc())
    
    # Pagination
    result = paginate(query, page, size)
    
    # Construire les items
    items = []
    for culture in result["items"]:
        # Mettre à jour le stade automatiquement
        culture.update_stade()
        
        items.append({
            "id": culture.id,
            "code": culture.code,
            "parcelle_id": culture.parcelle_id,
            "parcelle_nom": culture.parcelle.nom if culture.parcelle else None,
            "date_debut": culture.date_debut,
            "date_fin_prevue": culture.date_fin_prevue,
            "date_fin_reelle": culture.date_fin_reelle,
            "variete": culture.variete,
            "type_semence": culture.type_semence,
            "densite_semis": culture.densite_semis,
            "ecartement_lignes": culture.ecartement_lignes,
            "ecartement_poquets": culture.ecartement_poquets,
            "stade": culture.stade,
            "sante": culture.sante,
            "vigueur": culture.vigueur,
            "observations": culture.observations,
            "photos": culture.photos if culture.photos else [],
            "duree_ecoulee": culture.duree_ecoulee,
            "progression": culture.progression,
            "jours_restants": culture.jours_restants,
            "stade_description": culture.stade_description,
            "created_at": culture.created_at,
            "updated_at": culture.updated_at,
            "created_by": culture.created_by,
            "updated_by": culture.updated_by,
            "extra_data": culture.extra_data if culture.extra_data else {},
            "tags": culture.tags if culture.tags else [],
            "version": culture.version
        })
    
    return {
        "total": result["total"],
        "page": result["page"],
        "size": result["size"],
        "pages": result["pages"],
        "items": items
    }


# ========================
# DÉMARRER UNE CULTURE
# ========================
@router.post("/", response_model=CultureResponse, status_code=status.HTTP_201_CREATED)
async def create_culture(
    request: CultureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Démarre une nouvelle culture sur une parcelle.
    """
    try:
        logger.info(f"=== DÉMARRAGE CULTURE ===")
        logger.info(f"Utilisateur: {current_user.email}")
        logger.info(f"Données reçues: {request.model_dump()}")
        
        # Vérifier que la parcelle existe et appartient à l'utilisateur
        parcelle = db.query(Parcelle).filter(
            Parcelle.id == request.parcelle_id,
            Parcelle.proprietaire_id == current_user.id
        ).first()
        
        if not parcelle:
            raise NotFoundException("Parcelle non trouvée ou non autorisée")
        
        # Vérifier si une culture est déjà en cours sur cette parcelle
        existing_culture = db.query(Culture).filter(
            Culture.parcelle_id == request.parcelle_id,
            Culture.date_fin_reelle.is_(None)
        ).first()
        
        if existing_culture:
            raise BadRequestException(
                f"Une culture est déjà en cours sur cette parcelle (démarrée le {existing_culture.date_debut})"
            )
        
        # Créer la culture
        culture = Culture(
            parcelle_id=request.parcelle_id,
            date_debut=request.date_debut,
            variete=request.variete.strip(),
            type_semence=request.type_semence.strip() if request.type_semence else None,
            densite_semis=request.densite_semis,
            ecartement_lignes=request.ecartement_lignes,
            ecartement_poquets=request.ecartement_poquets,
            observations=request.observations.strip() if request.observations else None,
            sante=10,
            vigueur=10,
            stade=StadeCulture.SEMIS
        )
        
        # Générer un code unique
        culture.generate_code()
        
        # Sauvegarder
        db.add(culture)
        db.commit()
        db.refresh(culture)
        
        # NE PAS MODIFIER is_cultivee DIRECTEMENT
        # is_cultivee est une propriété calculée basée sur culture_actuelle
        # Il n'est pas nécessaire de la définir manuellement
        
        logger.info(f"✅ Culture démarrée: {culture.variete} sur parcelle {parcelle.nom} (ID: {culture.id})")
        
        # Enregistrer dans l'historique
        HistoriqueService.log_create(
            db=db,
            user_id=current_user.id,
            entity_type="culture",
            entity_id=culture.id,
            data=request.model_dump()
        )
        
        # Construire la réponse
        return {
            "id": culture.id,
            "code": culture.code,
            "parcelle_id": culture.parcelle_id,
            "parcelle_nom": parcelle.nom,
            "date_debut": culture.date_debut,
            "date_fin_prevue": culture.date_fin_prevue,
            "date_fin_reelle": culture.date_fin_reelle,
            "variete": culture.variete,
            "type_semence": culture.type_semence,
            "densite_semis": culture.densite_semis,
            "ecartement_lignes": culture.ecartement_lignes,
            "ecartement_poquets": culture.ecartement_poquets,
            "stade": culture.stade,
            "sante": culture.sante,
            "vigueur": culture.vigueur,
            "observations": culture.observations,
            "photos": culture.photos if culture.photos else [],
            "duree_ecoulee": culture.duree_ecoulee,
            "progression": culture.progression,
            "jours_restants": culture.jours_restants,
            "stade_description": culture.stade_description,
            "created_at": culture.created_at,
            "updated_at": culture.updated_at,
            "created_by": culture.created_by,
            "updated_by": culture.updated_by,
            "extra_data": culture.extra_data if culture.extra_data else {},
            "tags": culture.tags if culture.tags else [],
            "version": culture.version
        }
        
    except BadRequestException:
        raise
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur création culture: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


# ========================
# DÉMARRER DES CULTURES (BULK)
# ========================

@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def create_cultures_bulk(
    requests: List[CultureBulkCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Création multiple de cultures (BULK INSERT)
    VERSION SANS UUID (ID STRING)
    """

    created_cultures = []
    errors = []

    today = datetime.utcnow().date()

    for index, request in enumerate(requests):

        try:
            # =========================
            # 1. PARCELLE (STRING ID)
            # =========================
            parcelle_id = request.parcelle_id.strip()

            parcelle = db.query(Parcelle).filter(
                Parcelle.id == parcelle_id,
                Parcelle.proprietaire_id == current_user.id
            ).first()

            if not parcelle:
                errors.append({
                    "index": index,
                    "error": "Parcelle non trouvée"
                })
                continue

            # =========================
            # 2. CULTURE ACTIVE CHECK
            # =========================
            existing = db.query(Culture).filter(
                Culture.parcelle_id == parcelle_id,
                Culture.date_fin_reelle.is_(None)
            ).first()

            if existing:
                errors.append({
                    "index": index,
                    "error": "Culture déjà active sur cette parcelle"
                })
                continue

            # =========================
            # 3. VALIDATION METIER
            # =========================
            if request.densite_semis < 50000:
                errors.append({
                    "index": index,
                    "error": "densite_semis doit être >= 50000"
                })
                continue

            # date format safe check
            try:
                date_debut = datetime.strptime(
                    request.date_debut, "%Y-%m-%d"
                ).date()
            except:
                errors.append({
                    "index": index,
                    "error": "Format date invalide (YYYY-MM-DD)"
                })
                continue

            # ❌ pas dans le futur
            if date_debut > today:
                errors.append({
                    "index": index,
                    "error": "date_debut ne peut pas être dans le futur"
                })
                continue

            # =========================
            # 4. CREATE CULTURE
            # =========================
            culture = Culture(
                parcelle_id=parcelle_id,
                date_debut=date_debut,
                variete=request.variete.strip(),
                type_semence=request.type_semence.strip() if request.type_semence else None,
                densite_semis=request.densite_semis,
                ecartement_lignes=request.ecartement_lignes,
                ecartement_poquets=request.ecartement_poquets,
                observations=request.observations.strip() if request.observations else None,
                sante=10,
                vigueur=10,
                stade=StadeCulture.SEMIS
            )

            culture.generate_code()

            db.add(culture)
            db.flush()  # important pour récupérer ID sans commit immédiat

            created_cultures.append({
                "id": culture.id,
                "code": culture.code,
                "parcelle_id": culture.parcelle_id,
                "variete": culture.variete,
                "stade": culture.stade
            })

        except Exception as e:
            errors.append({
                "index": index,
                "error": str(e)
            })

    # =========================
    # COMMIT GLOBAL (PERF)
    # =========================
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return {
            "total_received": len(requests),
            "created": 0,
            "failed": len(requests),
            "data": [],
            "errors": [{"error": "DB commit error", "detail": str(e)}]
        }

    return {
        "total_received": len(requests),
        "created": len(created_cultures),
        "failed": len(errors),
        "data": created_cultures,
        "errors": errors
    }
# ========================
# RÉCUPÉRER UNE CULTURE
# ========================
@router.get("/{culture_id}", response_model=CultureDetailResponse)
async def get_culture(
    culture_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les détails d'une culture.
    """
    culture = db.query(Culture).join(Parcelle).filter(
        Culture.id == culture_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not culture:
        raise NotFoundException("Culture non trouvée")
    
    # Mettre à jour le stade
    culture.update_stade()
    
    # Construire la réponse
    result = {
        "id": culture.id,
        "code": culture.code,
        "parcelle_id": culture.parcelle_id,
        "parcelle_nom": culture.parcelle.nom if culture.parcelle else None,
        "date_debut": culture.date_debut,
        "date_fin_prevue": culture.date_fin_prevue,
        "date_fin_reelle": culture.date_fin_reelle,
        "variete": culture.variete,
        "type_semence": culture.type_semence,
        "densite_semis": culture.densite_semis,
        "ecartement_lignes": culture.ecartement_lignes,
        "ecartement_poquets": culture.ecartement_poquets,
        "stade": culture.stade,
        "sante": culture.sante,
        "vigueur": culture.vigueur,
        "observations": culture.observations,
        "photos": culture.photos if culture.photos else [],
        "duree_ecoulee": culture.duree_ecoulee,
        "progression": culture.progression,
        "jours_restants": culture.jours_restants,
        "stade_description": culture.stade_description,
        "created_at": culture.created_at,
        "updated_at": culture.updated_at,
        "created_by": culture.created_by,
        "updated_by": culture.updated_by,
        "extra_data": culture.extra_data if culture.extra_data else {},
        "tags": culture.tags if culture.tags else [],
        "version": culture.version,
        "mesures": [],
        "maladies": [],
        "recolte": None
    }
    
    return result


# ========================
# METTRE À JOUR UNE CULTURE
# ========================
@router.put("/{culture_id}", response_model=CultureResponse)
async def update_culture(
    culture_id: str,
    request: CultureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Met à jour une culture.
    """
    culture = db.query(Culture).join(Parcelle).filter(
        Culture.id == culture_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not culture:
        raise NotFoundException("Culture non trouvée")
    
    update_data = request.model_dump(exclude_unset=True)
    old_data = {
        "stade": culture.stade,
        "sante": culture.sante,
        "vigueur": culture.vigueur
    }
    
    for key, value in update_data.items():
        if hasattr(culture, key):
            setattr(culture, key, value)
    
    culture.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(culture)
    
    # Enregistrer dans l'historique
    HistoriqueService.log_update(
        db=db,
        user_id=current_user.id,
        entity_type="culture",
        entity_id=culture.id,
        old_data=old_data,
        new_data=update_data
    )
    
    return culture


# ========================
# TERMINER UNE CULTURE
# ========================
@router.post("/{culture_id}/terminer")
async def terminer_culture(
    culture_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Termine une culture (après récolte).
    """
    culture = db.query(Culture).join(Parcelle).filter(
        Culture.id == culture_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not culture:
        raise NotFoundException("Culture non trouvée")
    
    if culture.date_fin_reelle:
        raise BadRequestException("Cette culture est déjà terminée")
    
    culture.terminer()
    db.commit()
    
    # Enregistrer dans l'historique
    HistoriqueService.log_action(
        db=db,
        user_id=current_user.id,
        action="TERMINER",
        entity_type="culture",
        entity_id=culture.id,
        description=f"Culture {culture.variete} terminée"
    )
    
    return {"message": "Culture terminée avec succès"}


# ========================
# CULTURE ACTUELLE D'UNE PARCELLE
# ========================
@router.get("/parcelle/{parcelle_id}/actuelle", response_model=Optional[CultureResponse])
async def get_culture_actuelle(
    parcelle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère la culture actuelle d'une parcelle.
    """
    # Vérifier la parcelle
    parcelle = db.query(Parcelle).filter(
        Parcelle.id == parcelle_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not parcelle:
        raise NotFoundException("Parcelle non trouvée")
    
    culture = parcelle.culture_actuelle
    
    if not culture:
        return None
    
    return culture


# ========================
# STATISTIQUES DES CULTURES
# ========================
@router.get("/stats/summary")
async def get_cultures_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les statistiques des cultures.
    """
    cultures = db.query(Culture).join(Parcelle).filter(
        Parcelle.proprietaire_id == current_user.id
    ).all()
    
    stats = {
        "total": len(cultures),
        "en_cours": sum(1 for c in cultures if c.date_fin_reelle is None),
        "terminees": sum(1 for c in cultures if c.date_fin_reelle is not None),
        "par_stade": {},
        "par_variete": {},
        "sante_moyenne": 0,
        "vigueur_moyenne": 0
    }
    
    sante_total = 0
    vigueur_total = 0
    
    for culture in cultures:
        # Par stade
        stade_key = culture.stade.value if hasattr(culture.stade, 'value') else str(culture.stade)
        stats["par_stade"][stade_key] = stats["par_stade"].get(stade_key, 0) + 1
        
        # Par variété
        stats["par_variete"][culture.variete] = stats["par_variete"].get(culture.variete, 0) + 1
        
        sante_total += culture.sante
        vigueur_total += culture.vigueur
    
    if cultures:
        stats["sante_moyenne"] = round(sante_total / len(cultures), 1)
        stats["vigueur_moyenne"] = round(vigueur_total / len(cultures), 1)
    
    return stats