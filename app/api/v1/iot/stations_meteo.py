from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# Import de votre utilitaire de session DB
from ....database import get_db 
# On importe les modèles et schémas que vous avez fournis
# Note : Ajustez les imports selon votre structure de dossiers
from ....models.iot.station_meteo import StationMeteo
from ....schemas.iot.station_meteo import (
    StationMeteoCreate, 
    StationMeteoUpdate, 
    StationMeteoResponse
)

router = APIRouter()

## --- ROUTES CRUD ---

@router.post("/", response_model=StationMeteoResponse, status_code=status.HTTP_201_CREATED)
def create_station(station_in: StationMeteoCreate, db: Session = Depends(get_db)):
    """
    Enregistre une nouvelle station météo liée à une parcelle.
    """
    # Vérification de l'unicité de la parcelle (contrainte unique=True dans le modèle)
    db_station = db.query(StationMeteo).filter(StationMeteo.parcelle_id == station_in.parcelle_id).first()
    if db_station:
        raise HTTPException(
            status_code=400, 
            detail="Une station météo est déjà configurée pour cette parcelle."
        )
    
    new_station = StationMeteo(**station_in.model_dump())
    db.add(new_station)
    db.commit()
    db.refresh(new_station)
    return new_station


@router.get("/", response_model=List[StationMeteoResponse])
def read_all_stations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Liste toutes les stations avec pagination.
    """
    return db.query(StationMeteo).offset(skip).limit(limit).all()


@router.get("/{parcelle_id}", response_model=StationMeteoResponse)
def read_station(parcelle_id: str, db: Session = Depends(get_db)):
    """
    Récupère les détails d'une station par l'ID de sa parcelle.
    """
    station = db.query(StationMeteo).filter(StationMeteo.parcelle_id == parcelle_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station météo introuvable.")
    return station


@router.patch("/{parcelle_id}", response_model=StationMeteoResponse)
def update_station(
    parcelle_id: str, 
    station_update: StationMeteoUpdate, 
    db: Session = Depends(get_db)
):
    """
    Mise à jour partielle des données (température, vent, prévisions JSON, etc.).
    """
    db_station = db.query(StationMeteo).filter(StationMeteo.parcelle_id == parcelle_id).first()
    if not db_station:
        raise HTTPException(status_code=404, detail="Station météo introuvable.")

    # On récupère uniquement les champs envoyés dans la requête
    update_data = station_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_station, key, value)

    db.commit()
    db.refresh(db_station)
    return db_station


@router.delete("/{parcelle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_station(parcelle_id: str, db: Session = Depends(get_db)):
    """
    Supprime la station météo d'une parcelle.
    """
    db_station = db.query(StationMeteo).filter(StationMeteo.parcelle_id == parcelle_id).first()
    if not db_station:
        raise HTTPException(status_code=404, detail="Station météo introuvable.")
    
    db.delete(db_station)
    db.commit()
    return None