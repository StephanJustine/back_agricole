from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

# Importation de vos schémas et modèles
# Note : Ajustez les imports selon votre structure de dossiers réelle
from ....database import get_db
from ....schemas.iot.balise_gps import BaliseGPSCreate, BaliseGPSUpdate, BaliseGPSResponse
from ....models.iot.balise_gps import BaliseGPS

router = APIRouter()

@router.post("/", response_model=BaliseGPSResponse, status_code=status.HTTP_201_CREATED)
def create_balise(obj_in: BaliseGPSCreate, db: Session = Depends(get_db)):
    """
    Crée une nouvelle balise GPS.
    """
    # Vérifier si le code existe déjà
    existing_balise = db.query(BaliseGPS).filter(BaliseGPS.code == obj_in.code).first()
    if existing_balise:
        raise HTTPException(status_code=400, detail="Ce code de balise existe déjà.")
    
    db_balise = BaliseGPS(**obj_in.dict())
    db.add(db_balise)
    db.commit()
    db.refresh(db_balise)
    return db_balise

@router.get("/", response_model=List[BaliseGPSResponse])
def read_balises(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Récupère la liste de toutes les balises.
    """
    balises = db.query(BaliseGPS).offset(skip).limit(limit).all()
    return balises

@router.get("/{balise_id}", response_model=BaliseGPSResponse)
def read_balise(balise_id: str, db: Session = Depends(get_db)):
    """
    Récupère une balise spécifique par son ID (UUID).
    """
    balise = db.query(BaliseGPS).filter(BaliseGPS.id == balise_id).first()
    if not balise:
        raise HTTPException(status_code=404, detail="Balise non trouvée")
    return balise

@router.patch("/{balise_id}", response_model=BaliseGPSResponse)
def update_balise(balise_id: str, obj_in: BaliseGPSUpdate, db: Session = Depends(get_db)):
    """
    Met à jour les données d'une balise (ex: mise à jour de position, batterie).
    """
    db_balise = db.query(BaliseGPS).filter(BaliseGPS.id == balise_id).first()
    if not db_balise:
        raise HTTPException(status_code=404, detail="Balise non trouvée")
    
    update_data = obj_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_balise, field, value)
    
    # Logique métier optionnelle : mettre à jour 'derniere_mise_a_jour' automatiquement
    # db_balise.derniere_mise_a_jour = datetime.now()

    db.add(db_balise)
    db.commit()
    db.refresh(db_balise)
    return db_balise

@router.delete("/{balise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_balise(balise_id: str, db: Session = Depends(get_db)):
    """
    Supprime une balise GPS.
    """
    db_balise = db.query(BaliseGPS).filter(BaliseGPS.id == balise_id).first()
    if not db_balise:
        raise HTTPException(status_code=404, detail="Balise non trouvée")
    
    db.delete(db_balise)
    db.commit()
    return None