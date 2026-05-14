# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import List

# # Import de votre utilitaire de session DB
# from ....database import get_db 
# # On importe les modèles et schémas que vous avez fournis
# # Note : Ajustez les imports selon votre structure de dossiers
# from ....models.iot.station_meteo import StationMeteo
# from ....schemas.iot.station_meteo import (
#     StationMeteoCreate, 
#     StationMeteoUpdate, 
#     StationMeteoResponse
# )

# router = APIRouter()

# ## --- ROUTES CRUD ---

# @router.post("/", response_model=StationMeteoResponse, status_code=status.HTTP_201_CREATED)
# def create_station(station_in: StationMeteoCreate, db: Session = Depends(get_db)):
#     """
#     Enregistre une nouvelle station météo liée à une parcelle.
#     """
#     # Vérification de l'unicité de la parcelle (contrainte unique=True dans le modèle)
#     db_station = db.query(StationMeteo).filter(StationMeteo.parcelle_id == station_in.parcelle_id).first()
#     if db_station:
#         raise HTTPException(
#             status_code=400, 
#             detail="Une station météo est déjà configurée pour cette parcelle."
#         )
    
#     new_station = StationMeteo(**station_in.model_dump())
#     db.add(new_station)
#     db.commit()
#     db.refresh(new_station)
#     return new_station


# @router.get("/", response_model=List[StationMeteoResponse])
# def read_all_stations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     """
#     Liste toutes les stations avec pagination.
#     """
#     return db.query(StationMeteo).offset(skip).limit(limit).all()


# @router.get("/{parcelle_id}", response_model=StationMeteoResponse)
# def read_station(parcelle_id: str, db: Session = Depends(get_db)):
#     """
#     Récupère les détails d'une station par l'ID de sa parcelle.
#     """
#     station = db.query(StationMeteo).filter(StationMeteo.parcelle_id == parcelle_id).first()
#     if not station:
#         raise HTTPException(status_code=404, detail="Station météo introuvable.")
#     return station


# @router.patch("/{parcelle_id}", response_model=StationMeteoResponse)
# def update_station(
#     parcelle_id: str, 
#     station_update: StationMeteoUpdate, 
#     db: Session = Depends(get_db)
# ):
#     """
#     Mise à jour partielle des données (température, vent, prévisions JSON, etc.).
#     """
#     db_station = db.query(StationMeteo).filter(StationMeteo.parcelle_id == parcelle_id).first()
#     if not db_station:
#         raise HTTPException(status_code=404, detail="Station météo introuvable.")

#     # On récupère uniquement les champs envoyés dans la requête
#     update_data = station_update.model_dump(exclude_unset=True)
    
#     for key, value in update_data.items():
#         setattr(db_station, key, value)

#     db.commit()
#     db.refresh(db_station)
#     return db_station


# @router.delete("/{parcelle_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_station(parcelle_id: str, db: Session = Depends(get_db)):
#     """
#     Supprime la station météo d'une parcelle.
#     """
#     db_station = db.query(StationMeteo).filter(StationMeteo.parcelle_id == parcelle_id).first()
#     if not db_station:
#         raise HTTPException(status_code=404, detail="Station météo introuvable.")
    
#     db.delete(db_station)
#     db.commit()
#     return None
# api/v1/iot/stations_meteo.py
"""
Routes pour les stations météo.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.models.iot.station_meteo import StationMeteo
from app.models.parcelle import Parcelle
from app.schemas.iot.station_meteo import (
    StationMeteoCreate,
    StationMeteoUpdate,
    StationMeteoPut,
    StationMeteoResponse
)
from app.core.dependencies import get_current_active_user
from app.core.permissions import require_roles
from app.models.enums import UserRole

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def valider_temperature(temperature: float) -> bool:
    """Valide la température (-50°C à 60°C)."""
    return -50 <= temperature <= 60


def valider_humidite(humidite: float) -> bool:
    """Valide l'humidité (0% à 100%)."""
    return 0 <= humidite <= 100


def valider_pression(pression: float) -> bool:
    """Valide la pression (950 hPa à 1050 hPa)."""
    return 950 <= pression <= 1050


def valider_vent(vitesse: float) -> bool:
    """Valide la vitesse du vent (0 à 300 km/h)."""
    return 0 <= vitesse <= 300


def valider_uv(uv: float) -> bool:
    """Valide l'index UV (0 à 20)."""
    return 0 <= uv <= 20


def valider_pluie(pluie: float) -> bool:
    """Valide la pluie (0 à 1000 mm)."""
    return 0 <= pluie <= 1000


def valider_direction_vent(direction: Optional[str]) -> bool:
    """Valide la direction du vent."""
    if direction is None:
        return True
    directions_valides = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "NNE", "ENE", "ESE", "SSE", "SSW", "WSW", "WNW", "NNW"]
    return direction.upper() in directions_valides


# ============================================================================
# CRÉER UNE STATION MÉTÉO
# ============================================================================
@router.post("/", response_model=StationMeteoResponse, status_code=status.HTTP_201_CREATED)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def create_station(
    station_in: StationMeteoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    ENREGISTRE UNE NOUVELLE STATION MÉTÉO LIÉE À UNE PARCELLE.
    """
    try:
        # 1. Vérifier que la parcelle existe
        parcelle = db.query(Parcelle).filter(Parcelle.id == station_in.parcelle_id).first()
        if not parcelle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parcelle avec l'ID '{station_in.parcelle_id}' non trouvée"
            )
        
        # 2. Vérifier qu'une station n'existe pas déjà pour cette parcelle
        existing = db.query(StationMeteo).filter(
            StationMeteo.parcelle_id == station_in.parcelle_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Une station météo existe déjà pour la parcelle '{parcelle.nom}'. Utilisez PATCH ou PUT pour la mettre à jour."
            )
        
        # 3. Validation des valeurs
        if station_in.temperature is not None and not valider_temperature(station_in.temperature):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La température doit être comprise entre -50°C et 60°C"
            )
        
        if station_in.humidite is not None and not valider_humidite(station_in.humidite):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="L'humidité doit être comprise entre 0% et 100%"
            )
        
        if station_in.pression is not None and not valider_pression(station_in.pression):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La pression doit être comprise entre 950 hPa et 1050 hPa"
            )
        
        if station_in.vent_moyen is not None and not valider_vent(station_in.vent_moyen):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La vitesse du vent doit être comprise entre 0 et 300 km/h"
            )
        
        # 4. Création de la station
        now = datetime.utcnow()
        
        db_station = StationMeteo(
            parcelle_id=station_in.parcelle_id,
            temperature=station_in.temperature,
            humidite=station_in.humidite,
            pression=station_in.pression,
            pluie_24h=station_in.pluie_24h,
            vent_moyen=station_in.vent_moyen,
            date_maj=now,
            created_at=now,
            updated_at=now,
            created_by=current_user.id if hasattr(StationMeteo, 'created_by') else None
        )
        
        db.add(db_station)
        db.commit()
        db.refresh(db_station)
        
        logger.info(f"✅ Station météo créée | Parcelle: {parcelle.nom} | Par: {current_user.email}")
        
        return db_station
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur create_station: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création: {str(e)}"
        )


# ============================================================================
# LISTER LES STATIONS MÉTÉO
# ============================================================================
@router.get("/", response_model=List[StationMeteoResponse])
async def read_all_stations(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=500, description="Nombre maximum d'éléments"),
    parcelle_id: Optional[str] = Query(None, description="Filtrer par parcelle"),
    temperature_min: Optional[float] = Query(None, description="Température minimum"),
    temperature_max: Optional[float] = Query(None, description="Température maximum"),
    humidite_min: Optional[float] = Query(None, ge=0, le=100, description="Humidité minimum"),
    avec_previsions: bool = Query(False, description="Inclure les prévisions"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    LISTE TOUTES LES STATIONS MÉTÉO AVEC PAGINATION ET FILTRES.
    """
    try:
        query = db.query(StationMeteo)
        
        # Filtres
        if parcelle_id:
            query = query.filter(StationMeteo.parcelle_id == parcelle_id)
        if temperature_min is not None:
            query = query.filter(StationMeteo.temperature >= temperature_min)
        if temperature_max is not None:
            query = query.filter(StationMeteo.temperature <= temperature_max)
        if humidite_min is not None:
            query = query.filter(StationMeteo.humidite >= humidite_min)
        
        stations = query.order_by(StationMeteo.date_maj.desc()).offset(skip).limit(limit).all()
        
        # Optionnellement, nettoyer les prévisions si non demandées
        if not avec_previsions:
            for station in stations:
                station.previsions = {}
        
        logger.info(f"📊 Liste des stations météo | Total: {len(stations)}")
        
        return stations
        
    except Exception as e:
        logger.error(f"❌ Erreur read_all_stations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# RÉCUPÉRER UNE STATION PAR PARCELLE
# ============================================================================
@router.get("/{parcelle_id}", response_model=StationMeteoResponse)
async def read_station(
    parcelle_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE LES DÉTAILS D'UNE STATION PAR L'ID DE SA PARCELLE.
    """
    try:
        station = db.query(StationMeteo).filter(StationMeteo.parcelle_id == parcelle_id).first()
        
        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Station météo non trouvée pour la parcelle {parcelle_id}"
            )
        
        return station
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur read_station: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# METTRE À JOUR UNE STATION MÉTÉO (PATCH - PARTIEL)
# ============================================================================
@router.patch("/{parcelle_id}", response_model=StationMeteoResponse)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def update_station_partial(
    parcelle_id: str,
    station_update: StationMeteoUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    MET À JOUR PARTIELLEMENT LES DONNÉES D'UNE STATION MÉTÉO (PATCH).
    Seuls les champs fournis sont mis à jour.
    """
    try:
        db_station = db.query(StationMeteo).filter(StationMeteo.parcelle_id == parcelle_id).first()
        
        if not db_station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Station météo non trouvée pour la parcelle {parcelle_id}"
            )
        
        update_data = station_update.model_dump(exclude_unset=True)
        
        # Validations des valeurs
        if "temperature" in update_data and update_data["temperature"] is not None:
            if not valider_temperature(update_data["temperature"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La température doit être comprise entre -50°C et 60°C"
                )
        
        if "humidite" in update_data and update_data["humidite"] is not None:
            if not valider_humidite(update_data["humidite"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="L'humidité doit être comprise entre 0% et 100%"
                )
        
        if "pression" in update_data and update_data["pression"] is not None:
            if not valider_pression(update_data["pression"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La pression doit être comprise entre 950 hPa et 1050 hPa"
                )
        
        if "vent_moyen" in update_data and update_data["vent_moyen"] is not None:
            if not valider_vent(update_data["vent_moyen"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La vitesse du vent doit être comprise entre 0 et 300 km/h"
                )
        
        if "vent_rafale" in update_data and update_data["vent_rafale"] is not None:
            if not valider_vent(update_data["vent_rafale"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La rafale de vent doit être comprise entre 0 et 300 km/h"
                )
        
        if "uv" in update_data and update_data["uv"] is not None:
            if not valider_uv(update_data["uv"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="L'index UV doit être compris entre 0 et 20"
                )
        
        if "pluie_24h" in update_data and update_data["pluie_24h"] is not None:
            if not valider_pluie(update_data["pluie_24h"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La pluie doit être comprise entre 0 et 1000 mm"
                )
        
        if "direction_vent" in update_data and update_data["direction_vent"] is not None:
            if not valider_direction_vent(update_data["direction_vent"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Direction du vent invalide. Valeurs acceptées: N, NE, E, SE, S, SW, W, NW"
                )
        
        # Mise à jour
        for key, value in update_data.items():
            if hasattr(db_station, key) and value is not None:
                setattr(db_station, key, value)
        
        db_station.date_maj = datetime.utcnow()
        db_station.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_station)
        
        logger.info(f"✏️ Station météo mise à jour (PATCH) | Parcelle: {parcelle_id} | Par: {current_user.email}")
        
        return db_station
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur update_station_partial: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


# ============================================================================
# METTRE À JOUR COMPLÈTE UNE STATION MÉTÉO (PUT)
# ============================================================================
@router.put("/{parcelle_id}", response_model=StationMeteoResponse)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def update_station_full(
    parcelle_id: str,
    station_update: StationMeteoPut,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    MET À JOUR COMPLÈTEMENT UNE STATION MÉTÉO (PUT).
    Tous les champs sont requis (remplacement complet).
    """
    try:
        db_station = db.query(StationMeteo).filter(StationMeteo.parcelle_id == parcelle_id).first()
        
        if not db_station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Station météo non trouvée pour la parcelle {parcelle_id}"
            )
        
        # Validation des valeurs
        if station_update.temperature is not None and not valider_temperature(station_update.temperature):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La température doit être comprise entre -50°C et 60°C"
            )
        
        if station_update.humidite is not None and not valider_humidite(station_update.humidite):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="L'humidité doit être comprise entre 0% et 100%"
            )
        
        if station_update.pression is not None and not valider_pression(station_update.pression):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La pression doit être comprise entre 950 hPa et 1050 hPa"
            )
        
        if station_update.vent_moyen is not None and not valider_vent(station_update.vent_moyen):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La vitesse du vent doit être comprise entre 0 et 300 km/h"
            )
        
        if station_update.vent_rafale is not None and not valider_vent(station_update.vent_rafale):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La rafale de vent doit être comprise entre 0 et 300 km/h"
            )
        
        if station_update.uv is not None and not valider_uv(station_update.uv):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="L'index UV doit être compris entre 0 et 20"
            )
        
        if station_update.direction_vent is not None and not valider_direction_vent(station_update.direction_vent):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Direction du vent invalide"
            )
        
        # Mise à jour complète
        db_station.temperature = station_update.temperature
        db_station.temperature_min = station_update.temperature_min
        db_station.temperature_max = station_update.temperature_max
        db_station.humidite = station_update.humidite
        db_station.pression = station_update.pression
        db_station.pluie_24h = station_update.pluie_24h
        db_station.pluie_mensuelle = station_update.pluie_mensuelle
        db_station.vent_moyen = station_update.vent_moyen
        db_station.vent_rafale = station_update.vent_rafale
        db_station.direction_vent = station_update.direction_vent
        db_station.luminosite = station_update.luminosite
        db_station.uv = station_update.uv
        db_station.previsions = station_update.previsions or {}
        
        db_station.date_maj = datetime.utcnow()
        db_station.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_station)
        
        logger.info(f"✏️ Station météo mise à jour (PUT) | Parcelle: {parcelle_id} | Par: {current_user.email}")
        
        return db_station
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur update_station_full: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


# ============================================================================
# SUPPRIMER UNE STATION MÉTÉO
# ============================================================================
@router.delete("/{parcelle_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_roles([UserRole.ADMIN])
async def delete_station(
    parcelle_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    SUPPRIME LA STATION MÉTÉO D'UNE PARCELLE (ADMIN UNIQUEMENT).
    """
    try:
        db_station = db.query(StationMeteo).filter(StationMeteo.parcelle_id == parcelle_id).first()
        
        if not db_station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Station météo non trouvée pour la parcelle {parcelle_id}"
            )
        
        logger.info(f"🗑️ Station météo supprimée | Parcelle: {parcelle_id} | Par: {current_user.email}")
        
        db.delete(db_station)
        db.commit()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur delete_station: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )


# ============================================================================
# METTRE À JOUR LES PRÉVISIONS MÉTÉO
# ============================================================================
@router.post("/{parcelle_id}/previsions", response_model=StationMeteoResponse)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def update_previsions(
    parcelle_id: str,
    previsions: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    MET À JOUR LES PRÉVISIONS MÉTÉO D'UNE STATION.
    """
    try:
        db_station = db.query(StationMeteo).filter(StationMeteo.parcelle_id == parcelle_id).first()
        
        if not db_station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Station météo non trouvée pour la parcelle {parcelle_id}"
            )
        
        db_station.previsions = previsions
        db_station.date_maj = datetime.utcnow()
        db_station.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_station)
        
        logger.info(f"📡 Prévisions mises à jour | Parcelle: {parcelle_id}")
        
        return db_station
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur update_previsions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


# ============================================================================
# STATISTIQUES MÉTÉO
# ============================================================================
@router.get("/statistiques/resume", response_model=Dict[str, Any])
async def get_meteo_statistiques(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE UN RÉSUMÉ STATISTIQUE DES STATIONS MÉTÉO.
    """
    try:
        from sqlalchemy import func
        
        total = db.query(func.count(StationMeteo.id)).scalar() or 0
        
        # Moyennes
        temp_moyenne = db.query(func.avg(StationMeteo.temperature)).scalar() or 0
        humidite_moyenne = db.query(func.avg(StationMeteo.humidite)).scalar() or 0
        pression_moyenne = db.query(func.avg(StationMeteo.pression)).scalar() or 0
        pluie_totale = db.query(func.sum(StationMeteo.pluie_24h)).scalar() or 0
        
        # Extrêmes
        temp_min = db.query(func.min(StationMeteo.temperature)).scalar()
        temp_max = db.query(func.max(StationMeteo.temperature)).scalar()
        
        result = {
            "total_stations": total,
            "moyennes": {
                "temperature": round(float(temp_moyenne), 1),
                "humidite": round(float(humidite_moyenne), 1),
                "pression": round(float(pression_moyenne), 1)
            },
            "extremes": {
                "temperature_min": round(float(temp_min), 1) if temp_min else None,
                "temperature_max": round(float(temp_max), 1) if temp_max else None
            },
            "pluie_24h_totale_mm": round(float(pluie_totale), 1),
            "date_consultation": datetime.utcnow().isoformat()
        }
        
        logger.info(f"📊 Statistiques météo consultées")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur get_meteo_statistiques: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul des statistiques: {str(e)}"
        )