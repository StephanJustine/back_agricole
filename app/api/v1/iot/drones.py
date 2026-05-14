# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import List

# # Import de vos schémas et modèles
# # Adaptez les imports selon votre structure de dossiers
# from ....database import get_db
# from ....schemas.iot.drone import DroneCreate, DroneResponse
# from ....models.iot.drone import Drone

# router = APIRouter()

# @router.post("/", response_model=DroneResponse, status_code=status.HTTP_201_CREATED)
# def create_drone_mission(drone_in: DroneCreate, db: Session = Depends(get_db)):
#     """
#     Enregistre une nouvelle mission de drone.
#     """
#     # Vérification si le numéro de série existe déjà
#     if drone_in.numero_serie:
#         db_drone = db.query(Drone).filter(Drone.numero_serie == drone_in.numero_serie).first()
#         if db_drone:
#             raise HTTPException(status_code=400, detail="Ce numéro de série existe déjà.")
    
#     new_drone = Drone(**drone_in.model_dump())
#     db.add(new_drone)
#     db.commit()
#     db.refresh(new_drone)
#     return new_drone

# @router.get("/", response_model=List[DroneResponse])
# def read_drones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     """
#     Récupère la liste de toutes les missions de drones.
#     """
#     drones = db.query(Drone).offset(skip).limit(limit).all()
#     return drones

# @router.get("/{drone_id}", response_model=DroneResponse)
# def read_drone_by_id(drone_id: int, db: Session = Depends(get_db)):
#     """
#     Récupère les détails d'une mission spécifique par son ID.
#     """
#     drone = db.query(Drone).filter(Drone.id == drone_id).first()
#     if not drone:
#         raise HTTPException(status_code=404, detail="Mission de drone non trouvée.")
#     return drone

# @router.delete("/{drone_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_drone(drone_id: int, db: Session = Depends(get_db)):
#     """
#     Supprime une mission de drone de la base de données.
#     """
#     drone = db.query(Drone).filter(Drone.id == drone_id).first()
#     if not drone:
#         raise HTTPException(status_code=404, detail="Mission non trouvée.")
    
#     db.delete(drone)
#     db.commit()
#     return None

# api/v1/iot/drones.py
"""
Routes pour les drones agricoles.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import json

from app.database import get_db
from app.models.iot.drone import Drone
from app.schemas.iot.drone import DroneCreate, DroneResponse
from app.core.dependencies import get_current_active_user
from app.core.permissions import require_roles
from app.models.enums import UserRole

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def valider_numero_serie(numero_serie: str) -> bool:
    """Valide le format du numéro de série."""
    if not numero_serie:
        return True
    # Format: DRONE-XXXX-XXXX
    import re
    pattern = r'^[A-Z0-9]{4,20}$'
    return bool(re.match(pattern, numero_serie.upper()))


def calculer_indices_agronomiques(images: List[str] = None) -> Dict[str, float]:
    """
    Calcule les indices agronomiques à partir des images.
    À adapter selon votre logique métier.
    """
    # Simulation - à remplacer par calcul réel
    import random
    return {
        "ndvi": round(random.uniform(0.2, 0.8), 3),
        "ndre": round(random.uniform(0.2, 0.8), 3),
        "norm": round(random.uniform(0.0, 1.0), 3)
    }


def analyser_zones_problemes(ndvi: float, ndre: float) -> List[Dict]:
    """
    Analyse les zones à problèmes en fonction des indices.
    """
    zones = []
    
    if ndvi < 0.3:
        zones.append({
            "type": "faible_vigueur",
            "severite": "critique",
            "surface_ha": 0.5,
            "recommandation": "Fertilisation urgente"
        })
    elif ndvi < 0.5:
        zones.append({
            "type": "vigueur_moyenne",
            "severite": "moderee",
            "surface_ha": 0.3,
            "recommandation": "Surveillance renforcée"
        })
    
    if ndre < 0.4:
        zones.append({
            "type": "stress_azote",
            "severite": "elevee",
            "surface_ha": 0.4,
            "recommandation": "Apport d'azote"
        })
    
    return zones


# ============================================================================
# CRÉER UNE MISSION DE DRONE
# ============================================================================
@router.post("/", response_model=DroneResponse, status_code=status.HTTP_201_CREATED)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def create_drone_mission(
    drone_in: DroneCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    ENREGISTRE UNE NOUVELLE MISSION DE DRONE.
    
    Args:
        drone_in: Données de la mission
        db: Session de base de données
        current_user: Utilisateur authentifié
    """
    try:
        # 1. Validation du modèle
        if not drone_in.modele or not drone_in.modele.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le modèle du drone est requis"
            )
        
        # 2. Validation du numéro de série (si fourni)
        if drone_in.numero_serie:
            if not valider_numero_serie(drone_in.numero_serie):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Format de numéro de série invalide. Utilisez alphanumérique (4-20 caractères)"
                )
            
            existing = db.query(Drone).filter(Drone.numero_serie == drone_in.numero_serie).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Un drone avec le numéro de série '{drone_in.numero_serie}' existe déjà"
                )
        
        # 3. Validation des paramètres de vol
        if drone_in.duree_vol is not None and drone_in.duree_vol <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La durée de vol doit être positive"
            )
        
        if drone_in.altitude is not None and (drone_in.altitude < 0 or drone_in.altitude > 400):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="L'altitude doit être comprise entre 0 et 400 mètres"
            )
        
        # 4. Création de la mission
        now = datetime.utcnow()
        
        # Calcul des indices agronomiques (simulation)
        indices = calculer_indices_agronomiques(drone_in.images)
        
        # Analyse des zones à problèmes
        zones_problemes = analyser_zones_problemes(indices["ndvi"], indices["ndre"])
        
        # Préparation des données
        drone_data = {
            "modele": drone_in.modele.strip(),
            "numero_serie": drone_in.numero_serie.upper() if drone_in.numero_serie else None,
            "date_mission": now,
            "duree_vol": drone_in.duree_vol,
            "altitude": drone_in.altitude,
            "vitesse": drone_in.vitesse,
            "plan_vol": drone_in.plan_vol or {},
            "zone_survolee": drone_in.zone_survolee or {},
            "surface_couverte": drone_in.surface_couverte,
            "images": drone_in.images or [],
            "videos": drone_in.videos or [],
            "indice_ndvi": indices["ndvi"],
            "indice_ndre": indices["ndre"],
            "indice_norm": indices["norm"],
            "zones_a_probleme": zones_problemes,
            "observations": drone_in.observations,
            "created_at": now,
            "updated_at": now,
            "created_by": current_user.id if hasattr(Drone, 'created_by') else None
        }
        
        db_drone = Drone(**drone_data)
        db.add(db_drone)
        db.commit()
        db.refresh(db_drone)
        
        logger.info(f"✅ Mission drone créée | ID: {db_drone.id} | Modèle: {db_drone.modele} | Par: {current_user.email}")
        
        return db_drone
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur create_drone_mission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création: {str(e)}"
        )


# ============================================================================
# LISTER LES MISSIONS DE DRONE
# ============================================================================
@router.get("/", response_model=List[DroneResponse])
async def read_drones(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=500, description="Nombre maximum d'éléments"),
    modele: Optional[str] = Query(None, description="Filtrer par modèle"),
    date_debut: Optional[datetime] = Query(None, description="Date de mission début"),
    date_fin: Optional[datetime] = Query(None, description="Date de mission fin"),
    ndvi_min: Optional[float] = Query(None, ge=0, le=1, description="NDVI minimum"),
    has_issues: Optional[bool] = Query(None, description="Avec zones à problèmes"),
    search: Optional[str] = Query(None, description="Recherche dans modèle et observations"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE LA LISTE DE TOUTES LES MISSIONS DE DRONE.
    """
    try:
        query = db.query(Drone)
        
        # Filtres
        if modele:
            query = query.filter(Drone.modele.ilike(f"%{modele}%"))
        if date_debut:
            query = query.filter(Drone.date_mission >= date_debut)
        if date_fin:
            query = query.filter(Drone.date_mission <= date_fin)
        if ndvi_min:
            query = query.filter(Drone.indice_ndvi >= ndvi_min)
        if has_issues is not None:
            if has_issues:
                query = query.filter(Drone.zones_a_probleme != [])
            else:
                query = query.filter(Drone.zones_a_probleme == [])
        if search:
            query = query.filter(
                (Drone.modele.ilike(f"%{search}%")) |
                (Drone.observations.ilike(f"%{search}%"))
            )
        
        drones = query.order_by(Drone.date_mission.desc()).offset(skip).limit(limit).all()
        
        logger.info(f"📊 Liste des missions drone | Total: {len(drones)}")
        
        return drones
        
    except Exception as e:
        logger.error(f"❌ Erreur read_drones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# RÉCUPÉRER UNE MISSION DE DRONE PAR ID
# ============================================================================
@router.get("/{drone_id}", response_model=DroneResponse)
async def read_drone_by_id(
    drone_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE LES DÉTAILS D'UNE MISSION SPÉCIFIQUE.
    """
    try:
        drone = db.query(Drone).filter(Drone.id == drone_id).first()
        
        if not drone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mission de drone avec l'ID '{drone_id}' non trouvée"
            )
        
        return drone
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur read_drone_by_id: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# RÉCUPÉRER LES MISSIONS PAR PÉRIODE
# ============================================================================
@router.get("/periode/", response_model=List[DroneResponse])
async def read_drones_by_period(
    date_debut: datetime = Query(..., description="Date de début"),
    date_fin: datetime = Query(..., description="Date de fin"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE LES MISSIONS DE DRONE SUR UNE PÉRIODE SPÉCIFIQUE.
    """
    try:
        if date_debut > date_fin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La date de début doit être antérieure à la date de fin"
            )
        
        drones = db.query(Drone).filter(
            Drone.date_mission >= date_debut,
            Drone.date_mission <= date_fin
        ).order_by(Drone.date_mission.desc()).all()
        
        logger.info(f"📅 Missions du {date_debut} au {date_fin}: {len(drones)} trouvées")
        
        return drones
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur read_drones_by_period: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# ANALYSER UNE ZONE SPÉCIFIQUE
# ============================================================================
@router.get("/{drone_id}/analyse-zone")
async def analyse_zone(
    drone_id: str,
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    ANALYSE UNE ZONE SPÉCIFIQUE D'UNE MISSION DE DRONE.
    """
    try:
        drone = db.query(Drone).filter(Drone.id == drone_id).first()
        
        if not drone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mission de drone avec l'ID '{drone_id}' non trouvée"
            )
        
        # Simulation d'analyse de zone
        analyse = {
            "coordonnees": {"lat": lat, "lon": lon},
            "indices": {
                "ndvi": drone.indice_ndvi,
                "ndre": drone.indice_ndre
            },
            "statut": "bon_etat" if drone.indice_ndvi and drone.indice_ndvi > 0.5 else "surveillance",
            "recommandations": [
                "Maintenir la surveillance",
                "Vérifier l'humidité du sol"
            ] if drone.indice_ndvi and drone.indice_ndvi > 0.5 else [
                "Fertilisation recommandée",
                "Arrosage supplémentaire"
            ]
        }
        
        logger.info(f"🔍 Analyse zone drone {drone_id} à {lat},{lon}")
        
        return analyse
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur analyse_zone: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse: {str(e)}"
        )


# ============================================================================
# SUPPRIMER UNE MISSION DE DRONE
# ============================================================================
@router.delete("/{drone_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_roles([UserRole.ADMIN])
async def delete_drone(
    drone_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    SUPPRIME UNE MISSION DE DRONE (ADMIN UNIQUEMENT).
    """
    try:
        drone = db.query(Drone).filter(Drone.id == drone_id).first()
        
        if not drone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mission de drone avec l'ID '{drone_id}' non trouvée"
            )
        
        logger.info(f"🗑️ Mission drone supprimée | ID: {drone_id} | Modèle: {drone.modele} | Par: {current_user.email}")
        
        db.delete(drone)
        db.commit()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur delete_drone: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )


# ============================================================================
# STATISTIQUES DES MISSIONS DE DRONE
# ============================================================================
# @router.get("/statistiques/resume", response_model=Dict[str, Any])
# async def get_drones_statistiques(
#     db: Session = Depends(get_db),
#     current_user = Depends(get_current_active_user)
# ):
#     """
#     RÉCUPÈRE UN RÉSUMÉ STATISTIQUE DES MISSIONS DE DRONE.
#     """
#     try:
#         from sqlalchemy import func
        
#         total = db.query(func.count(Drone.id)).scalar() or 0
        
#         # Moyenne NDVI
#         ndvi_moyen = db.query(func.avg(Drone.indice_ndvi)).scalar() or 0
        
#         # Missions avec problèmes
#         missions_problemes = db.query(func.count(Drone.id)).filter(Drone.zones_a_probleme != []).scalar() or 0
        
#         # Modèles les plus utilisés
#         modeles_utilises = db.query(
#             Drone.modele,
#             func.count(Drone.id).label("total")
#         ).group_by(Drone.modele).all()
        
#         # Surface totale couverte
#         surface_totale = db.query(func.sum(Drone.surface_couverte)).scalar() or 0
        
#         result = {
#             "total_missions": total,
#             "ndvi_moyen": round(float(ndvi_moyen), 3) if ndvi_moyen else None,
#             "missions_avec_problemes": missions_problemes,
#             "taux_problemes": round((missions_problemes / total * 100), 1) if total > 0 else 0,
#             "surface_totale_couverte_ha": round(float(surface_totale), 2) if surface_totale else 0,
#             "modeles_utilises": [
#                 {"modele": item[0], "missions": item[1]}
#                 for item in modeles_utilises
#             ]
#         }
        
#         logger.info(f"📊 Statistiques drones consultées")
        
#         return result
        
#     except Exception as e:
#         logger.error(f"❌ Erreur get_drones_statistiques: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur lors du calcul des statistiques: {str(e)}"
#         )

# api/v1/iot/drones.py - Version corrigée de la fonction statistiques

@router.get("/statistiques/resume", response_model=Dict[str, Any])
async def get_drones_statistiques(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE UN RÉSUMÉ STATISTIQUE DES MISSIONS DE DRONE.
    """
    try:
        from sqlalchemy import func
        from sqlalchemy import cast
        from sqlalchemy.types import String
        
        total = db.query(func.count(Drone.id)).scalar() or 0
        
        # Moyenne NDVI
        ndvi_moyen = db.query(func.avg(Drone.indice_ndvi)).scalar() or 0
        
        # Correction: Compter les missions avec zones à problèmes
        # Utiliser une approche différente pour PostgreSQL
        missions_problemes = 0
        if total > 0:
            # Récupérer tous les IDs des drones et compter ceux qui ont des zones problématiques
            all_drones = db.query(Drone.id, Drone.zones_a_probleme).all()
            missions_problemes = sum(1 for drone in all_drones if drone.zones_a_probleme and len(drone.zones_a_probleme) > 0)
        
        # Modèles les plus utilisés
        modeles_utilises = db.query(
            Drone.modele,
            func.count(Drone.id).label("total")
        ).group_by(Drone.modele).all()
        
        # Surface totale couverte
        surface_totale = db.query(func.sum(Drone.surface_couverte)).scalar() or 0
        
        # Missions par mois
        missions_par_mois = db.query(
            func.date_trunc('month', Drone.date_mission).label("mois"),
            func.count(Drone.id).label("total")
        ).group_by("mois").order_by("mois").limit(12).all()
        
        result = {
            "total_missions": total,
            "ndvi_moyen": round(float(ndvi_moyen), 3) if ndvi_moyen else None,
            "missions_avec_problemes": missions_problemes,
            "taux_problemes": round((missions_problemes / total * 100), 1) if total > 0 else 0,
            "surface_totale_couverte_ha": round(float(surface_totale), 2) if surface_totale else 0,
            "modeles_utilises": [
                {"modele": item[0], "missions": item[1]}
                for item in modeles_utilises
            ],
            "missions_par_mois": [
                {"mois": item[0].isoformat() if item[0] else None, "total": item[1]}
                for item in missions_par_mois
            ]
        }
        
        logger.info(f"📊 Statistiques drones consultées")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur get_drones_statistiques: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul des statistiques: {str(e)}"
        )