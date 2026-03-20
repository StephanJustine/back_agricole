# """
# Routes CRUD pour les travaux du sol.
# """
# from fastapi import APIRouter, Depends, Query, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import Optional
# from datetime import date, datetime
# import logging

# from ...database import get_db
# from ...models.travail_sol import TravailSol
# from ...models.parcelle import Parcelle
# from ...models.user import User
# from ...models.enums import TypeTravail
# from ...schemas.travail_sol import *
# from ...core.dependencies import get_current_active_user
# from ...core.pagination import paginate
# from ...core.exceptions import NotFoundException, BadRequestException
# from ...core.historique import HistoriqueService

# logger = logging.getLogger(__name__)
# router = APIRouter()


# # ========================
# # LISTE DES TRAVAUX
# # ========================
# @router.get("/", response_model=TravailSolList)
# async def get_travaux(
#     page: int = Query(1, ge=1, description="Numéro de page"),
#     size: int = Query(20, ge=1, le=100, description="Nombre d'éléments par page"),
#     parcelle_id: Optional[str] = Query(None, description="Filtrer par parcelle"),
#     type: Optional[TypeTravail] = Query(None, description="Filtrer par type"),
#     date_debut: Optional[date] = Query(None, description="Date de début"),
#     date_fin: Optional[date] = Query(None, description="Date de fin"),
#     sort_by: str = Query("date", description="Tri par champ"),
#     sort_desc: bool = Query(True, description="Tri décroissant"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ):
#     """
#     Récupère la liste des travaux de l'utilisateur connecté.
#     """
#     # Jointure pour vérifier que les parcelles appartiennent à l'utilisateur
#     query = db.query(TravailSol).join(Parcelle).filter(
#         Parcelle.proprietaire_id == current_user.id
#     )
    
#     # Filtres
#     if parcelle_id:
#         query = query.filter(TravailSol.parcelle_id == parcelle_id)
#     if type:
#         query = query.filter(TravailSol.type == type)
#     if date_debut:
#         query = query.filter(TravailSol.date >= date_debut)
#     if date_fin:
#         query = query.filter(TravailSol.date <= date_fin)
    
#     # Tri
#     if sort_desc:
#         query = query.order_by(getattr(TravailSol, sort_by).desc())
#     else:
#         query = query.order_by(getattr(TravailSol, sort_by).asc())
    
#     # Pagination
#     result = paginate(query, page, size)
    
#     # Construire les items
#     items = []
#     for travail in result["items"]:
#         items.append({
#             "id": travail.id,
#             "parcelle_id": travail.parcelle_id,
#             "parcelle_nom": travail.parcelle.nom if travail.parcelle else None,
#             "date": travail.date,
#             "type": travail.type,
#             "description": travail.description,
#             "profondeur": travail.profondeur,
#             "produit": travail.produit,
#             "dose": travail.dose,
#             "cout_intrants": travail.cout_intrants,
#             "cout_main_oeuvre": travail.cout_main_oeuvre,
#             "cout_total": travail.cout_total,
#             "observations": travail.observations,
#             "responsable": travail.responsable,
#             "created_at": travail.created_at,
#             "updated_at": travail.updated_at,
#             "created_by": travail.created_by,
#             "updated_by": travail.updated_by,
#             "extra_data": travail.extra_data if travail.extra_data else {},
#             "tags": travail.tags if travail.tags else [],
#             "version": travail.version
#         })
    
#     return {
#         "total": result["total"],
#         "page": result["page"],
#         "size": result["size"],
#         "pages": result["pages"],
#         "items": items
#     }


# # ========================
# # CRÉER UN TRAVAIL
# # ========================
# @router.post("/", response_model=TravailSolResponse, status_code=status.HTTP_201_CREATED)
# async def create_travail(
#     request: TravailSolCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ):
#     """
#     Enregistre un nouveau travail du sol.
#     """
#     try:
#         logger.info(f"=== ENREGISTREMENT TRAVAIL ===")
#         logger.info(f"Utilisateur: {current_user.email}")
#         logger.info(f"Données reçues: {request.model_dump()}")
        
#         # Vérifier que la parcelle existe et appartient à l'utilisateur
#         parcelle = db.query(Parcelle).filter(
#             Parcelle.id == request.parcelle_id,
#             Parcelle.proprietaire_id == current_user.id
#         ).first()
        
#         if not parcelle:
#             raise NotFoundException("Parcelle non trouvée ou non autorisée")
        
#         # Créer le travail
#         travail = TravailSol(
#             parcelle_id=request.parcelle_id,
#             date=request.date,
#             type=request.type,
#             description=request.description,
#             profondeur=request.profondeur,
#             produit=request.produit,
#             dose=request.dose,
#             cout_intrants=request.cout_intrants,
#             cout_main_oeuvre=request.cout_main_oeuvre,
#             observations=request.observations,
#             responsable=request.responsable
#         )
        
#         # Calculer le coût total
#         travail.calculer_cout_total()
        
#         # Sauvegarder
#         db.add(travail)
#         db.commit()
#         db.refresh(travail)
        
#         logger.info(f"✅ Travail enregistré: {travail.type} sur parcelle {parcelle.nom}")
        
#         # Enregistrer dans l'historique
#         HistoriqueService.log_create(
#             db=db,
#             user_id=current_user.id,
#             entity_type="travail_sol",
#             entity_id=travail.id,
#             data=request.model_dump()
#         )
        
#         # Construire la réponse
#         return {
#             "id": travail.id,
#             "parcelle_id": travail.parcelle_id,
#             "parcelle_nom": parcelle.nom,
#             "date": travail.date,
#             "type": travail.type,
#             "description": travail.description,
#             "profondeur": travail.profondeur,
#             "produit": travail.produit,
#             "dose": travail.dose,
#             "cout_intrants": travail.cout_intrants,
#             "cout_main_oeuvre": travail.cout_main_oeuvre,
#             "cout_total": travail.cout_total,
#             "observations": travail.observations,
#             "responsable": travail.responsable,
#             "created_at": travail.created_at,
#             "updated_at": travail.updated_at,
#             "created_by": travail.created_by,
#             "updated_by": travail.updated_by,
#             "extra_data": travail.extra_data if travail.extra_data else {},
#             "tags": travail.tags if travail.tags else [],
#             "version": travail.version
#         }
        
#     except BadRequestException:
#         raise
#     except NotFoundException:
#         raise
#     except Exception as e:
#         logger.error(f"❌ Erreur création travail: {e}")
#         import traceback
#         logger.error(traceback.format_exc())
#         db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur interne: {str(e)}"
#         )


# # ========================
# # RÉCUPÉRER UN TRAVAIL
# # ========================
# @router.get("/{travail_id}", response_model=TravailSolResponse)
# async def get_travail(
#     travail_id: str,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ):
#     """
#     Récupère les détails d'un travail.
#     """
#     travail = db.query(TravailSol).join(Parcelle).filter(
#         TravailSol.id == travail_id,
#         Parcelle.proprietaire_id == current_user.id
#     ).first()
    
#     if not travail:
#         raise NotFoundException("Travail non trouvé")
    
#     return travail


# # ========================
# # METTRE À JOUR UN TRAVAIL
# # ========================
# @router.put("/{travail_id}", response_model=TravailSolResponse)
# async def update_travail(
#     travail_id: str,
#     request: TravailSolUpdate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ):
#     """
#     Met à jour un travail existant.
#     """
#     travail = db.query(TravailSol).join(Parcelle).filter(
#         TravailSol.id == travail_id,
#         Parcelle.proprietaire_id == current_user.id
#     ).first()
    
#     if not travail:
#         raise NotFoundException("Travail non trouvé")
    
#     update_data = request.model_dump(exclude_unset=True)
#     old_data = {
#         "type": travail.type,
#         "cout_intrants": travail.cout_intrants,
#         "cout_main_oeuvre": travail.cout_main_oeuvre,
#         "cout_total": travail.cout_total
#     }
    
#     for key, value in update_data.items():
#         if hasattr(travail, key):
#             setattr(travail, key, value)
    
#     # Recalculer le coût total si les coûts ont changé
#     if "cout_intrants" in update_data or "cout_main_oeuvre" in update_data:
#         travail.calculer_cout_total()
    
#     travail.updated_at = datetime.utcnow()
#     db.commit()
#     db.refresh(travail)
    
#     # Enregistrer dans l'historique
#     HistoriqueService.log_update(
#         db=db,
#         user_id=current_user.id,
#         entity_type="travail_sol",
#         entity_id=travail.id,
#         old_data=old_data,
#         new_data=update_data
#     )
    
#     return travail


# # ========================
# # SUPPRIMER UN TRAVAIL
# # ========================
# @router.delete("/{travail_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_travail(
#     travail_id: str,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ):
#     """
#     Supprime un travail.
#     """
#     travail = db.query(TravailSol).join(Parcelle).filter(
#         TravailSol.id == travail_id,
#         Parcelle.proprietaire_id == current_user.id
#     ).first()
    
#     if not travail:
#         raise NotFoundException("Travail non trouvé")
    
#     db.delete(travail)
#     db.commit()
    
#     return None


# # ========================
# # COÛTS PAR PARCELLE
# # ========================
# @router.get("/cout-par-parcelle/{parcelle_id}", response_model=CoutsParcelle)
# async def get_couts_parcelle(
#     parcelle_id: str,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ):
#     """
#     Récupère les coûts détaillés pour une parcelle.
#     """
#     # Vérifier que la parcelle appartient à l'utilisateur
#     parcelle = db.query(Parcelle).filter(
#         Parcelle.id == parcelle_id,
#         Parcelle.proprietaire_id == current_user.id
#     ).first()
    
#     if not parcelle:
#         raise NotFoundException("Parcelle non trouvée ou non autorisée")
    
#     # Récupérer tous les travaux de la parcelle
#     travaux = db.query(TravailSol).filter(
#         TravailSol.parcelle_id == parcelle_id
#     ).order_by(TravailSol.date.desc()).all()
    
#     # Calculer les coûts par type
#     couts_par_type = {}
#     total_couts = 0
    
#     for travail in travaux:
#         type_key = travail.type.value if hasattr(travail.type, 'value') else str(travail.type)
#         couts_par_type[type_key] = couts_par_type.get(type_key, 0) + (travail.cout_total or 0)
#         total_couts += (travail.cout_total or 0)
    
#     # Construire les détails
#     details = []
#     for travail in travaux:
#         details.append({
#             "id": travail.id,
#             "parcelle_id": travail.parcelle_id,
#             "parcelle_nom": parcelle.nom,
#             "date": travail.date,
#             "type": travail.type,
#             "description": travail.description,
#             "profondeur": travail.profondeur,
#             "produit": travail.produit,
#             "dose": travail.dose,
#             "cout_intrants": travail.cout_intrants,
#             "cout_main_oeuvre": travail.cout_main_oeuvre,
#             "cout_total": travail.cout_total,
#             "observations": travail.observations,
#             "responsable": travail.responsable,
#             "created_at": travail.created_at,
#             "updated_at": travail.updated_at,
#             "created_by": travail.created_by,
#             "updated_by": travail.updated_by,
#             "extra_data": travail.extra_data if travail.extra_data else {},
#             "tags": travail.tags if travail.tags else [],
#             "version": travail.version
#         })
    
#     return {
#         "parcelle_id": parcelle.id,
#         "parcelle_nom": parcelle.nom,
#         "total_couts": total_couts,
#         "par_type": couts_par_type,
#         "details": details
#     }


# # ========================
# # COÛTS TOTAUX PAR PARCELLE (RÉSUMÉ)
# # ========================
# @router.get("/cout-total-parcelles")
# async def get_couts_totaux_parcelles(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ):
#     """
#     Récupère les coûts totaux pour toutes les parcelles de l'utilisateur.
#     """
#     # Récupérer toutes les parcelles de l'utilisateur
#     parcelles = db.query(Parcelle).filter(
#         Parcelle.proprietaire_id == current_user.id
#     ).all()
    
#     resultats = []
#     total_general = 0
    
#     for parcelle in parcelles:
#         # Récupérer les travaux de la parcelle
#         travaux = db.query(TravailSol).filter(
#             TravailSol.parcelle_id == parcelle.id
#         ).all()
        
#         total_parcelle = sum(t.cout_total or 0 for t in travaux)
#         total_general += total_parcelle
        
#         resultats.append({
#             "parcelle_id": parcelle.id,
#             "parcelle_nom": parcelle.nom,
#             "superficie": parcelle.superficie,
#             "cout_total": total_parcelle,
#             "cout_par_hectare": total_parcelle / parcelle.superficie if parcelle.superficie > 0 else 0,
#             "nb_travaux": len(travaux)
#         })
    
#     return {
#         "parcelles": resultats,
#         "total_general": total_general,
#         "nombre_parcelles": len(parcelles)
#     }


# # ========================
# # STATISTIQUES DES TRAVAUX
# # ========================
# @router.get("/stats/summary")
# async def get_travaux_stats(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ):
#     """
#     Récupère les statistiques des travaux.
#     """
#     travaux = db.query(TravailSol).join(Parcelle).filter(
#         Parcelle.proprietaire_id == current_user.id
#     ).all()
    
#     if not travaux:
#         return {
#             "total": 0,
#             "total_couts": 0,
#             "par_type": {},
#             "par_mois": {}
#         }
    
#     # Statistiques par type
#     par_type = {}
#     # Statistiques par mois
#     par_mois = {}
#     total_couts = 0
    
#     for travail in travaux:
#         type_key = travail.type.value if hasattr(travail.type, 'value') else str(travail.type)
#         par_type[type_key] = par_type.get(type_key, 0) + 1
        
#         mois_key = travail.date.strftime("%Y-%m")
#         par_mois[mois_key] = par_mois.get(mois_key, 0) + (travail.cout_total or 0)
        
#         total_couts += (travail.cout_total or 0)
    
#     return {
#         "total": len(travaux),
#         "total_couts": total_couts,
#         "cout_moyen": total_couts / len(travaux) if travaux else 0,
#         "par_type": par_type,
#         "par_mois": par_mois
#     }


# # ========================
# # TRAVAUX RÉCENTS
# # ========================
# @router.get("/recents")
# async def get_travaux_recents(
#     limit: int = Query(10, ge=1, le=50, description="Nombre de travaux à afficher"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ):
#     """
#     Récupère les travaux les plus récents.
#     """
#     travaux = db.query(TravailSol).join(Parcelle).filter(
#         Parcelle.proprietaire_id == current_user.id
#     ).order_by(TravailSol.date.desc()).limit(limit).all()
    
#     resultats = []
#     for travail in travaux:
#         resultats.append({
#             "id": travail.id,
#             "parcelle_nom": travail.parcelle.nom if travail.parcelle else None,
#             "date": travail.date,
#             "type": travail.type,
#             "description": travail.description,
#             "cout_total": travail.cout_total,
#             "responsable": travail.responsable
#         })
    
#     return resultats



"""
Routes CRUD pour les travaux du sol.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime
import logging

from ...database import get_db
from ...models.travail_sol import TravailSol
from ...models.parcelle import Parcelle
from ...models.user import User
from ...models.enums import TypeTravail
from ...schemas.travail_sol import *
from ...core.dependencies import get_current_active_user
from ...core.pagination import paginate
from ...core.exceptions import NotFoundException, BadRequestException
from ...core.historique import HistoriqueService

logger = logging.getLogger(__name__)
router = APIRouter()


# ========================
# LISTE DES TRAVAUX
# ========================
@router.get("/", response_model=TravailSolList)
async def get_travaux(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(20, ge=1, le=100, description="Nombre d'éléments par page"),
    parcelle_id: Optional[str] = Query(None, description="Filtrer par parcelle"),
    type: Optional[TypeTravail] = Query(None, description="Filtrer par type"),
    date_debut: Optional[date] = Query(None, description="Date de début"),
    date_fin: Optional[date] = Query(None, description="Date de fin"),
    sort_by: str = Query("date", description="Tri par champ"),
    sort_desc: bool = Query(True, description="Tri décroissant"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère la liste des travaux de l'utilisateur connecté.
    """
    query = db.query(TravailSol).join(Parcelle).filter(
        Parcelle.proprietaire_id == current_user.id
    )
    
    if parcelle_id:
        query = query.filter(TravailSol.parcelle_id == parcelle_id)
    if type:
        query = query.filter(TravailSol.type == type)
    if date_debut:
        query = query.filter(TravailSol.date >= date_debut)
    if date_fin:
        query = query.filter(TravailSol.date <= date_fin)
    
    if sort_desc:
        query = query.order_by(getattr(TravailSol, sort_by).desc())
    else:
        query = query.order_by(getattr(TravailSol, sort_by).asc())
    
    result = paginate(query, page, size)
    
    items = []
    for travail in result["items"]:
        items.append({
            "id": travail.id,
            "parcelle_id": travail.parcelle_id,
            "parcelle_nom": travail.parcelle.nom if travail.parcelle else None,
            "date": travail.date,
            "type": travail.type,
            "description": travail.description,
            "profondeur": travail.profondeur,
            "produit": travail.produit,
            "dose": travail.dose,
            "cout_intrants": travail.cout_intrants,
            "cout_main_oeuvre": travail.cout_main_oeuvre,
            "cout_total": travail.cout_total,
            "observations": travail.observations,
            "responsable": travail.responsable,
            "created_at": travail.created_at,
            "updated_at": travail.updated_at,
            "created_by": travail.created_by,
            "updated_by": travail.updated_by,
            "extra_data": travail.extra_data if travail.extra_data else {},
            "tags": travail.tags if travail.tags else [],
            "version": travail.version
        })
    
    return {
        "total": result["total"],
        "page": result["page"],
        "size": result["size"],
        "pages": result["pages"],
        "items": items
    }


# ========================
# COÛTS TOTAUX PAR PARCELLE (RÉSUMÉ) - À PLACER AVANT /{travail_id}
# ========================
@router.get("/cout-total-parcelles")
async def get_couts_totaux_parcelles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les coûts totaux pour toutes les parcelles de l'utilisateur.
    """
    try:
        parcelles = db.query(Parcelle).filter(
            Parcelle.proprietaire_id == current_user.id
        ).all()
        
        resultats = []
        total_general = 0
        
        for parcelle in parcelles:
            travaux = db.query(TravailSol).filter(
                TravailSol.parcelle_id == parcelle.id
            ).all()
            
            total_parcelle = sum(t.cout_total or 0 for t in travaux)
            total_general += total_parcelle
            
            resultats.append({
                "parcelle_id": parcelle.id,
                "parcelle_nom": parcelle.nom,
                "superficie": parcelle.superficie,
                "cout_total": total_parcelle,
                "cout_par_hectare": total_parcelle / parcelle.superficie if parcelle.superficie > 0 else 0,
                "nb_travaux": len(travaux)
            })
        
        return {
            "parcelles": resultats,
            "total_general": total_general,
            "nombre_parcelles": len(parcelles)
        }
        
    except Exception as e:
        logger.error(f"Erreur get_couts_totaux_parcelles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}"
        )


# ========================
# COÛTS PAR PARCELLE
# ========================
@router.get("/cout-par-parcelle/{parcelle_id}", response_model=CoutsParcelle)
async def get_couts_parcelle(
    parcelle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les coûts détaillés pour une parcelle.
    """
    parcelle = db.query(Parcelle).filter(
        Parcelle.id == parcelle_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not parcelle:
        raise NotFoundException("Parcelle non trouvée ou non autorisée")
    
    travaux = db.query(TravailSol).filter(
        TravailSol.parcelle_id == parcelle_id
    ).order_by(TravailSol.date.desc()).all()
    
    couts_par_type = {}
    total_couts = 0
    
    for travail in travaux:
        type_key = travail.type.value if hasattr(travail.type, 'value') else str(travail.type)
        couts_par_type[type_key] = couts_par_type.get(type_key, 0) + (travail.cout_total or 0)
        total_couts += (travail.cout_total or 0)
    
    details = []
    for travail in travaux:
        details.append({
            "id": travail.id,
            "parcelle_id": travail.parcelle_id,
            "parcelle_nom": parcelle.nom,
            "date": travail.date,
            "type": travail.type,
            "description": travail.description,
            "profondeur": travail.profondeur,
            "produit": travail.produit,
            "dose": travail.dose,
            "cout_intrants": travail.cout_intrants,
            "cout_main_oeuvre": travail.cout_main_oeuvre,
            "cout_total": travail.cout_total,
            "observations": travail.observations,
            "responsable": travail.responsable
        })
    
    return {
        "parcelle_id": parcelle.id,
        "parcelle_nom": parcelle.nom,
        "total_couts": total_couts,
        "par_type": couts_par_type,
        "details": details
    }


# ========================
# STATISTIQUES DES TRAVAUX
# ========================
@router.get("/stats/summary")
async def get_travaux_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les statistiques des travaux.
    """
    travaux = db.query(TravailSol).join(Parcelle).filter(
        Parcelle.proprietaire_id == current_user.id
    ).all()
    
    if not travaux:
        return {
            "total": 0,
            "total_couts": 0,
            "par_type": {},
            "par_mois": {}
        }
    
    par_type = {}
    par_mois = {}
    total_couts = 0
    
    for travail in travaux:
        type_key = travail.type.value if hasattr(travail.type, 'value') else str(travail.type)
        par_type[type_key] = par_type.get(type_key, 0) + 1
        
        mois_key = travail.date.strftime("%Y-%m")
        par_mois[mois_key] = par_mois.get(mois_key, 0) + (travail.cout_total or 0)
        
        total_couts += (travail.cout_total or 0)
    
    return {
        "total": len(travaux),
        "total_couts": total_couts,
        "cout_moyen": total_couts / len(travaux) if travaux else 0,
        "par_type": par_type,
        "par_mois": par_mois
    }


# ========================
# TRAVAUX RÉCENTS
# ========================
@router.get("/recents")
async def get_travaux_recents(
    limit: int = Query(10, ge=1, le=50, description="Nombre de travaux à afficher"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les travaux les plus récents.
    """
    travaux = db.query(TravailSol).join(Parcelle).filter(
        Parcelle.proprietaire_id == current_user.id
    ).order_by(TravailSol.date.desc()).limit(limit).all()
    
    resultats = []
    for travail in travaux:
        resultats.append({
            "id": travail.id,
            "parcelle_nom": travail.parcelle.nom if travail.parcelle else None,
            "date": travail.date,
            "type": travail.type,
            "description": travail.description,
            "cout_total": travail.cout_total,
            "responsable": travail.responsable
        })
    
    return resultats


# ========================
# CRÉER UN TRAVAIL
# ========================
@router.post("/", response_model=TravailSolResponse, status_code=status.HTTP_201_CREATED)
async def create_travail(
    request: TravailSolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Enregistre un nouveau travail du sol.
    """
    try:
        logger.info(f"=== ENREGISTREMENT TRAVAIL ===")
        logger.info(f"Utilisateur: {current_user.email}")
        logger.info(f"Données reçues: {request.model_dump()}")
        
        parcelle = db.query(Parcelle).filter(
            Parcelle.id == request.parcelle_id,
            Parcelle.proprietaire_id == current_user.id
        ).first()
        
        if not parcelle:
            raise NotFoundException("Parcelle non trouvée ou non autorisée")
        
        travail = TravailSol(
            parcelle_id=request.parcelle_id,
            date=request.date,
            type=request.type,
            description=request.description,
            profondeur=request.profondeur,
            produit=request.produit,
            dose=request.dose,
            cout_intrants=request.cout_intrants,
            cout_main_oeuvre=request.cout_main_oeuvre,
            observations=request.observations,
            responsable=request.responsable
        )
        
        travail.calculer_cout_total()
        
        db.add(travail)
        db.commit()
        db.refresh(travail)
        
        logger.info(f"✅ Travail enregistré: {travail.type} sur parcelle {parcelle.nom}")
        
        HistoriqueService.log_create(
            db=db,
            user_id=current_user.id,
            entity_type="travail_sol",
            entity_id=travail.id,
            data=request.model_dump()
        )
        
        return {
            "id": travail.id,
            "parcelle_id": travail.parcelle_id,
            "parcelle_nom": parcelle.nom,
            "date": travail.date,
            "type": travail.type,
            "description": travail.description,
            "profondeur": travail.profondeur,
            "produit": travail.produit,
            "dose": travail.dose,
            "cout_intrants": travail.cout_intrants,
            "cout_main_oeuvre": travail.cout_main_oeuvre,
            "cout_total": travail.cout_total,
            "observations": travail.observations,
            "responsable": travail.responsable,
            "created_at": travail.created_at,
            "updated_at": travail.updated_at,
            "created_by": travail.created_by,
            "updated_by": travail.updated_by,
            "extra_data": travail.extra_data if travail.extra_data else {},
            "tags": travail.tags if travail.tags else [],
            "version": travail.version
        }
        
    except BadRequestException:
        raise
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur création travail: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


# ========================
# METTRE À JOUR UN TRAVAIL
# ========================
@router.put("/{travail_id}", response_model=TravailSolResponse)
async def update_travail(
    travail_id: str,
    request: TravailSolUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Met à jour un travail existant.
    """
    travail = db.query(TravailSol).join(Parcelle).filter(
        TravailSol.id == travail_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not travail:
        raise NotFoundException("Travail non trouvé")
    
    update_data = request.model_dump(exclude_unset=True)
    old_data = {
        "type": travail.type,
        "cout_intrants": travail.cout_intrants,
        "cout_main_oeuvre": travail.cout_main_oeuvre,
        "cout_total": travail.cout_total
    }
    
    for key, value in update_data.items():
        if hasattr(travail, key):
            setattr(travail, key, value)
    
    if "cout_intrants" in update_data or "cout_main_oeuvre" in update_data:
        travail.calculer_cout_total()
    
    travail.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(travail)
    
    HistoriqueService.log_update(
        db=db,
        user_id=current_user.id,
        entity_type="travail_sol",
        entity_id=travail.id,
        old_data=old_data,
        new_data=update_data
    )
    
    return travail


# ========================
# SUPPRIMER UN TRAVAIL
# ========================
@router.delete("/{travail_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_travail(
    travail_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Supprime un travail.
    """
    travail = db.query(TravailSol).join(Parcelle).filter(
        TravailSol.id == travail_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not travail:
        raise NotFoundException("Travail non trouvé")
    
    db.delete(travail)
    db.commit()
    
    return None


# ========================
# RÉCUPÉRER UN TRAVAIL PAR ID - À PLACER EN DERNIER
# ========================
@router.get("/{travail_id}", response_model=TravailSolResponse)
async def get_travail(
    travail_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les détails d'un travail.
    """
    travail = db.query(TravailSol).join(Parcelle).filter(
        TravailSol.id == travail_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not travail:
        raise NotFoundException("Travail non trouvé")
    
    return travail