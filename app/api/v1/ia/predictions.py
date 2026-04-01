from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# Importations relatives à votre structure
from ....database import get_db
from ....models.ia.prediction import Prediction
from ....schemas.ia.prediction import PredictionCreate, PredictionResponse

router = APIRouter()

@router.patch("/{prediction_id}/recalculer-intervalles", response_model=PredictionResponse)
def recalculate_intervals(
    prediction_id: str, 
    marge_erreur: float = 0.15, 
    db: Session = Depends(get_db)
):
    """
    Recalcule dynamiquement les bornes de confiance.
    La logique utilise la formule : $R \pm (R \times \text{marge})$
    """
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    
    if not prediction or prediction.rendement_estime is None:
        raise HTTPException(
            status_code=404, 
            detail="Données de rendement indisponibles pour le calcul"
        )

    # Calcul des bornes
    delta = prediction.rendement_estime * marge_erreur
    prediction.intervalle_inferieur = prediction.rendement_estime - delta
    prediction.intervalle_superieur = prediction.rendement_estime + delta
    
    # Ajustement de la confiance (plus la marge est large, plus la certitude est basse)
    prediction.confiance = max(0.0, (1.0 - marge_erreur) * 100)
    
    db.commit()
    db.refresh(prediction)
    return prediction

@router.post("/{prediction_id}/valider-terrain", response_model=dict)
def validate_with_real_data(
    prediction_id: str, 
    rendement_reel: float, 
    db: Session = Depends(get_db)
):
    """
    Compare l'estimation IA avec la récolte réelle.
    Vérifie si la réalité est comprise dans l'intervalle de confiance prédit.
    """
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Prédiction introuvable")

    # Logique métier : calcul de la précision
    ecart = abs(prediction.rendement_estime - rendement_reel)
    dans_intervalle = (
        prediction.intervalle_inferieur <= rendement_reel <= prediction.intervalle_superieur
    )
    
    # Invalidation automatique si l'écart est absurde (ex: > 80%)
    if rendement_reel > 0 and (ecart / rendement_reel) > 0.8:
        prediction.est_valide = False
    
    db.commit()

    return {
        "id": prediction_id,
        "succes_prediction": dans_intervalle,
        "ecart_kg_ha": ecart,
        "precision_relative": f"{100 - (ecart/rendement_reel*100):.2f}%" if rendement_reel > 0 else "N/A",
        "statut_donnee": "Invalide (Ecart trop élevé)" if not prediction.est_valide else "Valide"
    }