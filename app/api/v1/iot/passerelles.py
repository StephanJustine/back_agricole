from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# Importez vos modèles, schémas et la fonction de session DB
# (Ajustez les chemins d'import selon votre structure de dossier)
from ....database import get_db  # Supposant que vous avez un get_db dans votre config base
from ....models.iot.passerelle import Passerelle
from ....schemas.iot.passerelle import PasserelleCreate, PasserelleUpdate, PasserelleResponse

router = APIRouter()

@router.post("/", response_model=PasserelleResponse, status_code=status.HTTP_201_CREATED)
def create_passerelle(obj_in: PasserelleCreate, db: Session = Depends(get_db)):
    """
    Enregistre une nouvelle passerelle IoT.
    """
    # Vérification si l'adresse MAC existe déjà
    existing = db.query(Passerelle).filter(Passerelle.adresse_mac == obj_in.adresse_mac).first()
    if existing:
        raise HTTPException(status_code=400, detail="Cette adresse MAC est déjà enregistrée.")
    
    db_obj = Passerelle(**obj_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/", response_model=List[PasserelleResponse])
def read_passerelles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Liste toutes les passerelles avec pagination.
    """
    return db.query(Passerelle).offset(skip).limit(limit).all()

@router.get("/{passerelle_id}", response_model=PasserelleResponse)
def read_passerelle(passerelle_id: int, db: Session = Depends(get_db)):
    """
    Récupère les détails d'une passerelle spécifique.
    """
    db_obj = db.query(Passerelle).filter(Passerelle.id == passerelle_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Passerelle non trouvée")
    return db_obj

@router.patch("/{passerelle_id}", response_model=PasserelleResponse)
def update_passerelle(passerelle_id: int, obj_in: PasserelleUpdate, db: Session = Depends(get_db)):
    """
    Met à jour partiellement les informations d'une passerelle.
    """
    db_obj = db.query(Passerelle).filter(Passerelle.id == passerelle_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Passerelle non trouvée")
    
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.delete("/{passerelle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_passerelle(passerelle_id: int, db: Session = Depends(get_db)):
    """
    Supprime une passerelle du système.
    """
    db_obj = db.query(Passerelle).filter(Passerelle.id == passerelle_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Passerelle non trouvée")
    
    db.delete(db_obj)
    db.commit()
    return None