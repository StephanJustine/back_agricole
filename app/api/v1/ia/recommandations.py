from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

# Importations des dépendances et modèles
from ....database import get_db 
from ....models.ia.recommandation import Recommandation
from ....schemas.ia.recommandation import (
    RecommandationCreate, 
    RecommandationResponse, 
    RecommandationUpdate
)

router = APIRouter()

@router.post("/", response_model=RecommandationResponse, status_code=status.HTTP_201_CREATED)
def create_recommandation(obj_in: RecommandationCreate, db: Session = Depends(get_db)):
    """
    **Création d'une recommandation avec analyse de criticité.**
    
    Logique appliquée :
    1. Scan du message pour détecter des mots-clés d'urgence.
    2. Injection de métadonnées système dans le champ JSON 'details'.
    3. Initialisation de la date d'émission au format UTC.
    """
    # Analyse sémantique simplifiée pour ajuster la priorité automatiquement
    urgences = ["gel", "sécheresse", "pucerons", "mildiou", "tempête"]
    message_content = obj_in.message.lower()
    
    priorite_finale = obj_in.priorite
    if any(mot in message_content for mot in urgences):
        # On force la priorité à 1 (Urgent) si un risque agronomique est détecté
        priorite_finale = 1 

    # Préparation des données pour SQLAlchemy
    # On sépare 'details' pour s'assurer qu'il contient au moins la source
    extra_info = obj_in.details or {}
    extra_info["source"] = "moteur_agronomique_v1"

    db_obj = Recommandation(
        type=obj_in.type,
        parcelle_id=obj_in.parcelle_id,
        culture_id=obj_in.culture_id,
        titre=obj_in.titre,
        message=obj_in.message,
        priorite=priorite_finale,
        details=extra_info,
        date_emission=datetime.utcnow()
    )
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.patch("/{recommandation_id}/statut", response_model=RecommandationResponse)
def update_recommandation_status(
    recommandation_id: str, 
    obj_in: RecommandationUpdate, 
    db: Session = Depends(get_db)
):
    """
    **Mise à jour intelligente du cycle de vie d'une recommandation.**
    
    Logique de transition d'état :
    - Si 'est_lue' passe à True : on enregistre l'horodatage précis.
    - Si 'est_appliquee' passe à True : cela valide l'action de l'agriculteur sur le terrain.
    - Une recommandation appliquée est automatiquement marquée comme lue.
    """
    db_obj = db.query(Recommandation).filter(Recommandation.id == recommandation_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Recommandation non trouvée")

    now = datetime.utcnow()
    update_data = obj_in.dict(exclude_unset=True)

    # Règle métier : Si appliquée, alors forcément lue
    if update_data.get("est_appliquee"):
        db_obj.est_appliquee = True
        db_obj.date_action = now
        db_obj.est_lue = True
        if not db_obj.date_lecture:
            db_obj.date_lecture = now
            
    # Gestion de la lecture simple
    if update_data.get("est_lue") and not db_obj.est_lue:
        db_obj.est_lue = True
        db_obj.date_lecture = now

    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/dashboard/urgences", response_model=List[RecommandationResponse])
def get_priorite_dashboard(db: Session = Depends(get_db)):
    """
    **Extraction des alertes pour le tableau de bord.**
    
    Récupère uniquement les recommandations de priorité 1 (Urgent) 
    qui n'ont pas encore été traitées par l'utilisateur.
    """
    return db.query(Recommandation).filter(
        Recommandation.priorite == 1,
        Recommandation.est_appliquee == False
    ).order_by(Recommandation.date_emission.desc()).all()

@router.delete("/{recommandation_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_recommandation(recommandation_id: str, db: Session = Depends(get_db)):
    """
    **Suppression (ou archivage) d'une recommandation.**
    
    Note : En production, on préférera souvent un 'soft delete' (is_deleted=True) 
    plutôt qu'une suppression physique pour garder l'historique agronomique.
    """
    db_obj = db.query(Recommandation).filter(Recommandation.id == recommandation_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Recommandation introuvable")
    
    db.delete(db_obj)
    db.commit()
    return None