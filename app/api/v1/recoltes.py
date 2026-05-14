"""
Routes CRUD pour les récoltes.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, datetime
import logging

from ...database import get_db
from ...models.recolte import Recolte
from ...models.culture import Culture
from ...models.parcelle import Parcelle
from ...models.user import User
from ...models.enums import TypeParcelle, QualiteRecolte
from ...schemas.recolte import *
from ...core.dependencies import get_current_active_user
from ...core.pagination import paginate
from ...core.exceptions import NotFoundException, BadRequestException
from ...core.historique import HistoriqueService

logger = logging.getLogger(__name__)
router = APIRouter()


# ========================
# LISTE DES RÉCOLTES
# ========================
@router.get("/", response_model=RecolteList)
async def get_recoltes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    culture_id: Optional[str] = None,
    parcelle_id: Optional[str] = None,
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
    qualite: Optional[QualiteRecolte] = None,
    sort_by: str = Query("date_debut", description="Tri par champ"),
    sort_desc: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère la liste des récoltes de l'utilisateur connecté.
    """
    query = db.query(Recolte).join(Culture).join(Parcelle).filter(
        Parcelle.proprietaire_id == current_user.id
    )
    
    if culture_id:
        query = query.filter(Recolte.culture_id == culture_id)
    if parcelle_id:
        query = query.filter(Parcelle.id == parcelle_id)
    if date_debut:
        query = query.filter(Recolte.date_debut >= date_debut)
    if date_fin:
        query = query.filter(Recolte.date_debut <= date_fin)
    if qualite:
        query = query.filter(Recolte.qualite == qualite)
    
    if sort_desc:
        query = query.order_by(getattr(Recolte, sort_by).desc())
    else:
        query = query.order_by(getattr(Recolte, sort_by).asc())
    
    result = paginate(query, page, size)
    
    items = []
    for recolte in result["items"]:
        # Calculer le rendement si superficie disponible
        parcelle = recolte.culture.parcelle if recolte.culture else None
        superficie = parcelle.superficie if parcelle else 0
        recolte.calculer_rendement(superficie)
        
        items.append({
            "id": recolte.id,
            "code": recolte.code,
            "culture_id": recolte.culture_id,
            "culture_nom": recolte.culture.variete if recolte.culture else None,
            "parcelle_nom": parcelle.nom if parcelle else None,
            "parcelle_type": parcelle.type.value if parcelle else None,
            "date_debut": recolte.date_debut,
            "date_fin": recolte.date_fin,
            "poids_frais": recolte.poids_frais,
            "poids_sec": recolte.poids_sec,
            "humidite": recolte.humidite,
            "qualite": recolte.qualite,
            "taux_gousses_vides": recolte.taux_gousses_vides,
            "taux_gousses_abimees": recolte.taux_gousses_abimees,
            "taux_impuretes": recolte.taux_impuretes,
            "poids_100_gousses": recolte.poids_100_gousses,
            "poids_100_graines": recolte.poids_100_graines,
            "nb_gousses_par_plant": recolte.nb_gousses_par_plant,
            "nb_sacs": recolte.nb_sacs,
            "observations": recolte.observations,
            "photos": recolte.photos if recolte.photos else [],
            "rendement_kg_ha": recolte.rendement_kg_ha,
            "perte_poids": recolte.perte_poids,
            "qualite_note": recolte.qualite_note,
            "created_at": recolte.created_at,
            "updated_at": recolte.updated_at,
            "created_by": recolte.created_by,
            "updated_by": recolte.updated_by,
            "extra_data": recolte.extra_data if recolte.extra_data else {},
            "tags": recolte.tags if recolte.tags else [],
            "version": recolte.version
        })
    
    return {
        "total": result["total"],
        "page": result["page"],
        "size": result["size"],
        "pages": result["pages"],
        "items": items
    }


# ========================
# CRÉER UNE RÉCOLTE
# ========================
@router.post("/", response_model=RecolteResponse, status_code=status.HTTP_201_CREATED)
async def create_recolte(
    request: RecolteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Enregistre une nouvelle récolte.
    """
    try:
        logger.info(f"=== ENREGISTREMENT RÉCOLTE ===")
        logger.info(f"Utilisateur: {current_user.email}")
        
        # Vérifier que la culture existe et appartient à l'utilisateur
        culture = db.query(Culture).join(Parcelle).filter(
            Culture.id == request.culture_id,
            Parcelle.proprietaire_id == current_user.id
        ).first()
        
        if not culture:
            raise NotFoundException("Culture non trouvée ou non autorisée")
        
        # Vérifier qu'une récolte n'existe pas déjà pour cette culture
        existing = db.query(Recolte).filter(Recolte.culture_id == request.culture_id).first()
        if existing:
            raise BadRequestException("Une récolte existe déjà pour cette culture")
        
        # Créer la récolte
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
        
        # Calculer le rendement
        parcelle = culture.parcelle
        recolte.calculer_rendement(parcelle.superficie)
        
        # Générer un code
        recolte.generate_code()
        
        # Terminer la culture
        culture.terminer()
        
        db.add(recolte)
        db.commit()
        db.refresh(recolte)
        
        logger.info(f"✅ Récolte enregistrée: {recolte.code} - {recolte.poids_sec} kg")
        
        # Enregistrer dans l'historique
        HistoriqueService.log_create(
            db=db,
            user_id=current_user.id,
            entity_type="recolte",
            entity_id=recolte.id,
            data=request.model_dump()
        )
        
        return {
            "id": recolte.id,
            "code": recolte.code,
            "culture_id": recolte.culture_id,
            "culture_nom": culture.variete,
            "parcelle_nom": parcelle.nom,
            "parcelle_type": parcelle.type.value if hasattr(parcelle.type, 'value') else parcelle.type,
            "date_debut": recolte.date_debut,
            "date_fin": recolte.date_fin,
            "poids_frais": recolte.poids_frais,
            "poids_sec": recolte.poids_sec,
            "humidite": recolte.humidite,
            "qualite": recolte.qualite,
            "taux_gousses_vides": recolte.taux_gousses_vides,
            "taux_gousses_abimees": recolte.taux_gousses_abimees,
            "taux_impuretes": recolte.taux_impuretes,
            "poids_100_gousses": recolte.poids_100_gousses,
            "poids_100_graines": recolte.poids_100_graines,
            "nb_gousses_par_plant": recolte.nb_gousses_par_plant,
            "nb_sacs": recolte.nb_sacs,
            "observations": recolte.observations,
            "photos": recolte.photos if recolte.photos else [],
            "rendement_kg_ha": recolte.rendement_kg_ha,
            "perte_poids": recolte.perte_poids,
            "qualite_note": recolte.qualite_note,
            "created_at": recolte.created_at,
            "updated_at": recolte.updated_at,
            "created_by": recolte.created_by,
            "updated_by": recolte.updated_by,
            "extra_data": recolte.extra_data if recolte.extra_data else {},
            "tags": recolte.tags if recolte.tags else [],
            "version": recolte.version
        }
        
    except BadRequestException:
        raise
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur création récolte: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )

# ========================
# CRÉER UNE RÉCOLTE BULK
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

    for index, request in enumerate(requests):
        try:
            # ========================
            # 1. Vérifier culture
            # ========================
            culture = db.query(Culture).join(Parcelle).filter(
                Culture.id == request.culture_id,
                Parcelle.proprietaire_id == current_user.id
            ).first()

            if not culture:
                errors.append({
                    "index": index,
                    "error": "Culture non trouvée ou non autorisée"
                })
                continue

            # ========================
            # 2. vérifier récolte existante
            # ========================
            existing = db.query(Recolte).filter(
                Recolte.culture_id == request.culture_id
            ).first()

            if existing:
                errors.append({
                    "index": index,
                    "error": "Récolte déjà existante"
                })
                continue

            # ========================
            # 3. CREATE RÉCOLTE
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

            parcelle = culture.parcelle

            recolte.calculer_rendement(parcelle.superficie)
            recolte.generate_code()
            culture.terminer()

            db.add(recolte)
            db.commit()
            db.refresh(recolte)

            created.append({
                "id": recolte.id,
                "code": recolte.code,
                "culture_id": recolte.culture_id,
                "poids_sec": recolte.poids_sec,
                "rendement": recolte.rendement_kg_ha
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
# RÉCUPÉRER UNE RÉCOLTE
# ========================
@router.get("/{recolte_id}", response_model=RecolteDetailResponse)
async def get_recolte(
    recolte_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les détails d'une récolte.
    """
    recolte = db.query(Recolte).join(Culture).join(Parcelle).filter(
        Recolte.id == recolte_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not recolte:
        raise NotFoundException("Récolte non trouvée")
    
    parcelle = recolte.culture.parcelle
    recolte.calculer_rendement(parcelle.superficie)
    
    return recolte


# ========================
# METTRE À JOUR UNE RÉCOLTE
# ========================
@router.put("/{recolte_id}", response_model=RecolteResponse)
async def update_recolte(
    recolte_id: str,
    request: RecolteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Met à jour une récolte.
    """
    recolte = db.query(Recolte).join(Culture).join(Parcelle).filter(
        Recolte.id == recolte_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not recolte:
        raise NotFoundException("Récolte non trouvée")
    
    update_data = request.model_dump(exclude_unset=True)
    parcelle = recolte.culture.parcelle
    
    for key, value in update_data.items():
        if hasattr(recolte, key):
            setattr(recolte, key, value)
    
    # Recalculer le rendement
    recolte.calculer_rendement(parcelle.superficie)
    
    recolte.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(recolte)
    
    return recolte


# ========================
# SUPPRIMER UNE RÉCOLTE
# ========================
@router.delete("/{recolte_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recolte(
    recolte_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Supprime une récolte.
    """
    recolte = db.query(Recolte).join(Culture).join(Parcelle).filter(
        Recolte.id == recolte_id,
        Parcelle.proprietaire_id == current_user.id
    ).first()
    
    if not recolte:
        raise NotFoundException("Récolte non trouvée")
    
    db.delete(recolte)
    db.commit()
    
    return None


# ========================
# COMPARAISON PARCELLES AMÉLIORÉES VS TRADITIONNELLES
# ========================
@router.get("/comparaison/amelioration-vs-traditionnelle")
async def comparer_rendements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Compare les rendements entre parcelles améliorées et traditionnelles.
    """
    # Récupérer toutes les récoltes de l'utilisateur
    recoltes = db.query(Recolte).join(Culture).join(Parcelle).filter(
        Parcelle.proprietaire_id == current_user.id
    ).all()
    
    amelioration = []
    traditionnelle = []
    
    for recolte in recoltes:
        parcelle = recolte.culture.parcelle
        if parcelle.type == TypeParcelle.AMELIOREE:
            amelioration.append(recolte)
        else:
            traditionnelle.append(recolte)
    
    # Calculer les moyennes
    def calculer_stats(recoltes_list):
        if not recoltes_list:
            return {
                "nombre": 0,
                "rendement_moyen": 0,
                "poids_sec_moyen": 0,
                "qualite_moyenne": 0,
                "taux_gousses_vides_moyen": 0,
                "taux_gousses_abimees_moyen": 0
            }
        
        rendements = [r.rendement_kg_ha or 0 for r in recoltes_list]
        poids_secs = [r.poids_sec or 0 for r in recoltes_list]
        qualites = [r.qualite_note for r in recoltes_list]
        taux_vides = [r.taux_gousses_vides or 0 for r in recoltes_list]
        taux_abimees = [r.taux_gousses_abimees or 0 for r in recoltes_list]
        
        return {
            "nombre": len(recoltes_list),
            "rendement_moyen": sum(rendements) / len(rendements) if rendements else 0,
            "poids_sec_moyen": sum(poids_secs) / len(poids_secs) if poids_secs else 0,
            "qualite_moyenne": sum(qualites) / len(qualites) if qualites else 0,
            "taux_gousses_vides_moyen": sum(taux_vides) / len(taux_vides) if taux_vides else 0,
            "taux_gousses_abimees_moyen": sum(taux_abimees) / len(taux_abimees) if taux_abimees else 0
        }
    
    stats_amelioration = calculer_stats(amelioration)
    stats_traditionnelle = calculer_stats(traditionnelle)
    
    # Calculer les écarts
    ecart = {
        "rendement": stats_amelioration["rendement_moyen"] - stats_traditionnelle["rendement_moyen"],
        "rendement_pourcentage": ((stats_amelioration["rendement_moyen"] - stats_traditionnelle["rendement_moyen"]) / stats_traditionnelle["rendement_moyen"] * 100) if stats_traditionnelle["rendement_moyen"] > 0 else 0,
        "qualite": stats_amelioration["qualite_moyenne"] - stats_traditionnelle["qualite_moyenne"],
        "gousses_vides": stats_traditionnelle["taux_gousses_vides_moyen"] - stats_amelioration["taux_gousses_vides_moyen"],
        "gousses_abimees": stats_traditionnelle["taux_gousses_abimees_moyen"] - stats_amelioration["taux_gousses_abimees_moyen"]
    }
    
    # Analyse
    analyse = ""
    if ecart["rendement"] > 0:
        analyse = f"Les parcelles améliorées ont un rendement supérieur de {ecart['rendement']:.0f} kg/ha (+{ecart['rendement_pourcentage']:.1f}%). "
        if ecart["qualite"] > 0:
            analyse += f"La qualité est également meilleure. "
        if ecart["gousses_vides"] > 0:
            analyse += f"Moins de gousses vides (-{ecart['gousses_vides']:.1f}%). "
    elif ecart["rendement"] < 0:
        analyse = f"Les parcelles traditionnelles ont un meilleur rendement. À analyser les pratiques culturales."
    else:
        analyse = "Rendements équivalents entre les deux types de parcelles."
    
    return {
        "amelioration": stats_amelioration,
        "traditionnelle": stats_traditionnelle,
        "ecart": ecart,
        "analyse": analyse
    }


# ========================
# STATISTIQUES DES RÉCOLTES
# ========================
@router.get("/stats/summary")
async def get_recoltes_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les statistiques des récoltes.
    """
    recoltes = db.query(Recolte).join(Culture).join(Parcelle).filter(
        Parcelle.proprietaire_id == current_user.id
    ).all()
    
    if not recoltes:
        return {
            "total": 0,
            "poids_total": 0,
            "rendement_moyen": 0,
            "par_qualite": {},
            "par_type_parcelle": {}
        }
    
    par_qualite = {}
    par_type_parcelle = {}
    poids_total = 0
    rendements = []
    
    for recolte in recoltes:
        parcelle = recolte.culture.parcelle
        qualite_key = recolte.qualite.value if hasattr(recolte.qualite, 'value') else str(recolte.qualite)
        type_key = parcelle.type.value if hasattr(parcelle.type, 'value') else str(parcelle.type)
        
        par_qualite[qualite_key] = par_qualite.get(qualite_key, 0) + 1
        par_type_parcelle[type_key] = par_type_parcelle.get(type_key, 0) + 1
        poids_total += recolte.poids_sec or recolte.poids_frais or 0
        rendements.append(recolte.rendement_kg_ha or 0)
    
    return {
        "total": len(recoltes),
        "poids_total": poids_total,
        "rendement_moyen": sum(rendements) / len(rendements) if rendements else 0,
        "rendement_max": max(rendements) if rendements else 0,
        "rendement_min": min(rendements) if rendements else 0,
        "par_qualite": par_qualite,
        "par_type_parcelle": par_type_parcelle
    }