from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# Import de la session de base de données (à adapter selon ton projet)
from ....database import get_db 
# Import des modèles et schémas
from ....models.iot.releve import ReleveCapteur
from ....schemas.iot.releve import ReleveCapteurCreate, ReleveCapteurResponse

router = APIRouter()

@router.post("/", response_model=ReleveCapteurResponse, status_code=status.HTTP_201_CREATED)
def create_releve(releve: ReleveCapteurCreate, db: Session = Depends(get_db)):
    """
    Crée un nouveau relevé pour un capteur spécifique.
    """
    db_releve = ReleveCapteur(**releve.model_dump())
    db.add(db_releve)
    db.commit()
    db.refresh(db_releve)
    return db_releve

@router.get("/", response_model=List[ReleveCapteurResponse])
def read_releves(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Récupère la liste des relevés (avec pagination).
    """
    releves = db.query(ReleveCapteur).offset(skip).limit(limit).all()
    return releves

@router.get("/{releve_id}", response_model=ReleveCapteurResponse)
def read_releve(releve_id: int, db: Session = Depends(get_db)):
    """
    Récupère un relevé spécifique par son ID.
    """
    releve = db.query(ReleveCapteur).filter(ReleveCapteur.id == releve_id).first()
    if not releve:
        raise HTTPException(status_code=404, detail="Relevé non trouvé")
    return releve

@router.delete("/{releve_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_releve(releve_id: int, db: Session = Depends(get_db)):
    """
    Supprime un relevé.
    """
    releve = db.query(ReleveCapteur).filter(ReleveCapteur.id == releve_id).first()
    if not releve:
        raise HTTPException(status_code=404, detail="Relevé non trouvé")
    
    db.delete(releve)
    db.commit()
    return None

@router.get("/capteur/{capteur_id}", response_model=List[ReleveCapteurResponse])
def read_releves_by_capteur(capteur_id: str, db: Session = Depends(get_db)):
    return db.query(ReleveCapteur).filter(ReleveCapteur.capteur_id == capteur_id).all()