from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# Importations locales (ajustez les chemins selon votre structure de dossier)
from ....database import get_db  # Supposant que vous avez une fonction de session
from ....models.iot.capteur import Capteur
from ....schemas.iot.capteur import CapteurCreate, CapteurUpdate, CapteurResponse

router = APIRouter()

@router.post("/", response_model=CapteurResponse, status_code=status.HTTP_201_CREATED)
def create_capteur(capteur: CapteurCreate, db: Session = Depends(get_db)):
    """
    Crée un nouveau capteur IoT dans la base de données.
    """
    db_capteur = Capteur(**capteur.dict())
    db.add(db_capteur)
    db.commit()
    db.refresh(db_capteur)
    return db_capteur

@router.get("/", response_model=List[CapteurResponse])
def read_capteurs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Récupère la liste de tous les capteurs avec pagination.
    """
    capteurs = db.query(Capteur).offset(skip).limit(limit).all()
    return capteurs

@router.get("/{capteur_id}", response_model=CapteurResponse)
def read_capteur(capteur_id: str, db: Session = Depends(get_db)):
    """
    Récupère un capteur spécifique par son ID.
    """
    db_capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()
    if not db_capteur:
        raise HTTPException(status_code=404, detail="Capteur non trouvé")
    return db_capteur

@router.patch("/{capteur_id}", response_model=CapteurResponse)
def update_capteur(capteur_id: str, capteur_update: CapteurUpdate, db: Session = Depends(get_db)):
    """
    Met à jour partiellement les informations d'un capteur.
    """
    db_query = db.query(Capteur).filter(Capteur.id == capteur_id)
    db_capteur = db_query.first()
    
    if not db_capteur:
        raise HTTPException(status_code=404, detail="Capteur non trouvé")
    
    # On extrait les données envoyées en excluant les valeurs non définies (None)
    update_data = capteur_update.dict(exclude_unset=True)
    
    db_query.update(update_data, synchronize_session=False)
    db.commit()
    db.refresh(db_capteur)
    return db_capteur

@router.delete("/{capteur_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_capteur(capteur_id: str, db: Session = Depends(get_db)):
    """
    Supprime un capteur de la base de données.
    """
    db_capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()
    if not db_capteur:
        raise HTTPException(status_code=404, detail="Capteur non trouvé")
    
    db.delete(db_capteur)
    db.commit()
    return None