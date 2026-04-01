from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# Import de vos schémas et modèles
# Adaptez les imports selon votre structure de dossiers
from ....database import get_db
from ....schemas.iot.drone import DroneCreate, DroneResponse
from ....models.iot.drone import Drone

router = APIRouter()

@router.post("/", response_model=DroneResponse, status_code=status.HTTP_201_CREATED)
def create_drone_mission(drone_in: DroneCreate, db: Session = Depends(get_db)):
    """
    Enregistre une nouvelle mission de drone.
    """
    # Vérification si le numéro de série existe déjà
    if drone_in.numero_serie:
        db_drone = db.query(Drone).filter(Drone.numero_serie == drone_in.numero_serie).first()
        if db_drone:
            raise HTTPException(status_code=400, detail="Ce numéro de série existe déjà.")
    
    new_drone = Drone(**drone_in.model_dump())
    db.add(new_drone)
    db.commit()
    db.refresh(new_drone)
    return new_drone

@router.get("/", response_model=List[DroneResponse])
def read_drones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Récupère la liste de toutes les missions de drones.
    """
    drones = db.query(Drone).offset(skip).limit(limit).all()
    return drones

@router.get("/{drone_id}", response_model=DroneResponse)
def read_drone_by_id(drone_id: int, db: Session = Depends(get_db)):
    """
    Récupère les détails d'une mission spécifique par son ID.
    """
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Mission de drone non trouvée.")
    return drone

@router.delete("/{drone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_drone(drone_id: int, db: Session = Depends(get_db)):
    """
    Supprime une mission de drone de la base de données.
    """
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Mission non trouvée.")
    
    db.delete(drone)
    db.commit()
    return None