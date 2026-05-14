# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import List

# # Importations relatives à votre structure
# from ....database import get_db
# from ....models.ia.prediction import Prediction
# from ....schemas.ia.prediction import PredictionCreate, PredictionResponse

# router = APIRouter()

# @router.patch("/{prediction_id}/recalculer-intervalles", response_model=PredictionResponse)
# def recalculate_intervals(
#     prediction_id: str, 
#     marge_erreur: float = 0.15, 
#     db: Session = Depends(get_db)
# ):
#     """
#     Recalcule dynamiquement les bornes de confiance.
#     La logique utilise la formule : $R \pm (R \times \text{marge})$
#     """
#     prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    
#     if not prediction or prediction.rendement_estime is None:
#         raise HTTPException(
#             status_code=404, 
#             detail="Données de rendement indisponibles pour le calcul"
#         )

#     # Calcul des bornes
#     delta = prediction.rendement_estime * marge_erreur
#     prediction.intervalle_inferieur = prediction.rendement_estime - delta
#     prediction.intervalle_superieur = prediction.rendement_estime + delta
    
#     # Ajustement de la confiance (plus la marge est large, plus la certitude est basse)
#     prediction.confiance = max(0.0, (1.0 - marge_erreur) * 100)
    
#     db.commit()
#     db.refresh(prediction)
#     return prediction

# @router.post("/{prediction_id}/valider-terrain", response_model=dict)
# def validate_with_real_data(
#     prediction_id: str, 
#     rendement_reel: float, 
#     db: Session = Depends(get_db)
# ):
#     """
#     Compare l'estimation IA avec la récolte réelle.
#     Vérifie si la réalité est comprise dans l'intervalle de confiance prédit.
#     """
#     prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    
#     if not prediction:
#         raise HTTPException(status_code=404, detail="Prédiction introuvable")

#     # Logique métier : calcul de la précision
#     ecart = abs(prediction.rendement_estime - rendement_reel)
#     dans_intervalle = (
#         prediction.intervalle_inferieur <= rendement_reel <= prediction.intervalle_superieur
#     )
    
#     # Invalidation automatique si l'écart est absurde (ex: > 80%)
#     if rendement_reel > 0 and (ecart / rendement_reel) > 0.8:
#         prediction.est_valide = False
    
#     db.commit()

#     return {
#         "id": prediction_id,
#         "succes_prediction": dans_intervalle,
#         "ecart_kg_ha": ecart,
#         "precision_relative": f"{100 - (ecart/rendement_reel*100):.2f}%" if rendement_reel > 0 else "N/A",
#         "statut_donnee": "Invalide (Ecart trop élevé)" if not prediction.est_valide else "Valide"
#     }


# api/v1/ia/predictions.py
"""
Routes pour les prédictions de rendement agricole.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import math

from app.database import get_db
from app.models.ia.prediction import Prediction
from app.models.ia.modele_ia import ModeleIA
from app.schemas.ia.prediction import PredictionCreate, PredictionResponse, PredictionUpdate
from app.core.dependencies import get_current_active_user
from app.core.permissions import require_roles
from app.models.enums import UserRole

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# RECALCULER LES INTERVALLES DE CONFIANCE
# ============================================================================
@router.patch("/{prediction_id}/recalculer-intervalles", response_model=PredictionResponse)
async def recalculate_intervals(
    prediction_id: str,
    marge_erreur: float = Query(0.15, ge=0.01, le=0.5, description="Marge d'erreur (1% à 50%)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RECALCULE DYNAMIQUEMENT LES BORNES DE CONFIANCE.
    
    Formule utilisée : R ± (R × marge_erreur)
    
    Arguments:
    - prediction_id: Identifiant unique de la prédiction
    - marge_erreur: Marge d'erreur à appliquer (défaut: 0.15 soit 15%)
    
    Retourne la prédiction mise à jour avec les nouveaux intervalles.
    """
    try:
        # 1. Validation de la marge d'erreur
        if not 0 < marge_erreur < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La marge d'erreur doit être comprise entre 0 et 1 (exclu)"
            )
        
        # 2. Récupération de la prédiction
        prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
        
        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prédiction {prediction_id} non trouvée"
            )
        
        # 3. Vérification des accès
        if hasattr(prediction, 'user_id') and prediction.user_id != current_user.id:
            if current_user.role not in [UserRole.ADMIN, UserRole.TECHNICIEN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez pas accès à cette prédiction"
                )
        
        # 4. Vérification du rendement estimé
        if prediction.rendement_estime is None or prediction.rendement_estime <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Données de rendement indisponibles ou invalides pour le calcul"
            )
        
        # 5. Calcul des bornes (arrondi à 2 décimales)
        delta = round(prediction.rendement_estime * marge_erreur, 2)
        prediction.intervalle_inferieur = round(max(0, prediction.rendement_estime - delta), 2)
        prediction.intervalle_superieur = round(prediction.rendement_estime + delta, 2)
        
        # 6. Ajustement du niveau de confiance
        prediction.confiance = round(max(0.0, (1.0 - marge_erreur) * 100), 2)
        
        # 7. Mise à jour des timestamps
        prediction.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(prediction)
        
        logger.info(f"✅ Intervalles recalculés | Prédiction: {prediction_id} | Marge: {marge_erreur} | Par: {current_user.email}")
        
        return prediction
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur recalcul_intervals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du recalcul: {str(e)}"
        )


# ============================================================================
# CRÉER UNE PRÉDICTION
# ============================================================================
@router.post("/", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def create_prediction(
    request: PredictionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    CRÉE UNE NOUVELLE PRÉDICTION DE RENDEMENT.
    
    Cette route permet aux administrateurs et techniciens de créer une prédiction
    basée sur un modèle IA.
    
    Étapes:
    1. Validation du modèle IA (existence et état actif)
    2. Validation des relations (parcelle, culture si fournies)
    3. Création de la prédiction
    4. Calcul automatique des intervalles de confiance
    5. Sauvegarde en base de données
    """
    try:
        # --------------------------------------------------------------------
        # 1. Validation du modèle IA
        # --------------------------------------------------------------------
        modele = db.query(ModeleIA).filter(ModeleIA.id == request.modele_id).first()
        if not modele:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Modèle IA avec l'ID '{request.modele_id}' non trouvé"
            )
        
        if not modele.est_actif:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le modèle IA n'est pas actif. Veuillez contacter un administrateur."
            )
        
        if not modele.est_pret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le modèle IA n'est pas encore prêt à l'emploi."
            )
        
        # --------------------------------------------------------------------
        # 2. Validation de la parcelle (si fournie)
        # --------------------------------------------------------------------
        if request.parcelle_id:
            from app.models.parcelle import Parcelle
            parcelle = db.query(Parcelle).filter(Parcelle.id == request.parcelle_id).first()
            if not parcelle:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parcelle avec l'ID '{request.parcelle_id}' non trouvée"
                )
        
        # --------------------------------------------------------------------
        # 3. Validation de la culture (si fournie)
        # --------------------------------------------------------------------
        if request.culture_id:
            from app.models.culture import Culture
            culture = db.query(Culture).filter(Culture.id == request.culture_id).first()
            if not culture:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Culture avec l'ID '{request.culture_id}' non trouvée"
                )
        
        # --------------------------------------------------------------------
        # 4. Validation du rendement estimé
        # --------------------------------------------------------------------
        if request.rendement_estime is not None and request.rendement_estime < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le rendement estimé ne peut pas être négatif"
            )
        
        # --------------------------------------------------------------------
        # 5. Préparation des données
        # --------------------------------------------------------------------
        prediction_data = {
            "modele_id": request.modele_id,
            "parcelle_id": request.parcelle_id,
            "culture_id": request.culture_id,
            "rendement_estime": request.rendement_estime,
            "probabilite": request.probabilite,
            "facteurs_influents": request.facteurs_influents or {},
            "donnees_utilisees": request.donnees_utilisees or {},
            "date_prediction": datetime.utcnow(),
            "est_valide": True
        }
        
        # Ajout de l'utilisateur créateur si le champ existe
        if hasattr(Prediction, 'created_by'):
            prediction_data['created_by'] = current_user.id
        
        # --------------------------------------------------------------------
        # 6. Création de l'objet Prediction
        # --------------------------------------------------------------------
        prediction = Prediction(**prediction_data)
        
        # --------------------------------------------------------------------
        # 7. Calcul des intervalles de confiance
        # --------------------------------------------------------------------
        if request.rendement_estime and request.rendement_estime > 0:
            marge = request.marge_precision if request.marge_precision else 0.15
            delta = round(request.rendement_estime * marge, 2)
            prediction.intervalle_inferieur = round(max(0, request.rendement_estime - delta), 2)
            prediction.intervalle_superieur = round(request.rendement_estime + delta, 2)
            prediction.confiance = round((1 - marge) * 100, 2)
        
        # --------------------------------------------------------------------
        # 8. Sauvegarde en base
        # --------------------------------------------------------------------
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        
        logger.info(f"✅ Prédiction créée | ID: {prediction.id} | Modèle: {request.modele_id} | Par: {current_user.email}")
        
        return prediction
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur create_prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création: {str(e)}"
        )


# ============================================================================
# LISTER LES PRÉDICTIONS
# ============================================================================
@router.get("/", response_model=List[PredictionResponse])
async def get_predictions(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer (pagination)"),
    limit: int = Query(100, ge=1, le=500, description="Nombre maximum d'éléments à retourner"),
    modele_id: Optional[str] = Query(None, description="Filtrer par ID du modèle IA"),
    parcelle_id: Optional[str] = Query(None, description="Filtrer par ID de la parcelle"),
    culture_id: Optional[str] = Query(None, description="Filtrer par ID de la culture"),
    est_valide: Optional[bool] = Query(None, description="Filtrer par validité (true/false)"),
    date_debut: Optional[datetime] = Query(None, description="Filtrer après cette date"),
    date_fin: Optional[datetime] = Query(None, description="Filtrer avant cette date"),
    rendement_min: Optional[float] = Query(None, ge=0, description="Rendement minimum (kg/ha)"),
    rendement_max: Optional[float] = Query(None, ge=0, description="Rendement maximum (kg/ha)"),
    confiance_min: Optional[float] = Query(None, ge=0, le=100, description="Confiance minimum (%)"),
    trier_par: str = Query("date_prediction", description="Champ de tri (date_prediction, rendement_estime, confiance)"),
    ordre_desc: bool = Query(True, description="Tri décroissant (true) ou croissant (false)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE LA LISTE DES PRÉDICTIONS AVEC FILTRES AVANCÉS.
    
    Permet de filtrer les prédictions selon plusieurs critères:
    - Par modèle IA, parcelle, culture
    - Par période (date_debut, date_fin)
    - Par rendement (min, max)
    - Par niveau de confiance
    - Par validité
    
    Arguments:
    - skip: Pagination - nombre d'éléments à ignorer
    - limit: Pagination - nombre maximum d'éléments
    - trier_par: Champ utilisé pour le tri
    - ordre_desc: True pour décroissant, False pour croissant
    """
    try:
        # Construction de la requête de base
        query = db.query(Prediction)
        
        # --------------------------------------------------------------------
        # Application des filtres
        # --------------------------------------------------------------------
        if modele_id:
            query = query.filter(Prediction.modele_id == modele_id)
        if parcelle_id:
            query = query.filter(Prediction.parcelle_id == parcelle_id)
        if culture_id:
            query = query.filter(Prediction.culture_id == culture_id)
        if est_valide is not None:
            query = query.filter(Prediction.est_valide == est_valide)
        if date_debut:
            query = query.filter(Prediction.date_prediction >= date_debut)
        if date_fin:
            query = query.filter(Prediction.date_prediction <= date_fin)
        if rendement_min:
            query = query.filter(Prediction.rendement_estime >= rendement_min)
        if rendement_max:
            query = query.filter(Prediction.rendement_estime <= rendement_max)
        if confiance_min:
            query = query.filter(Prediction.confiance >= confiance_min)
        
        # --------------------------------------------------------------------
        # Application du tri
        # --------------------------------------------------------------------
        champ_tri = getattr(Prediction, trier_par, Prediction.date_prediction)
        if ordre_desc:
            query = query.order_by(champ_tri.desc())
        else:
            query = query.order_by(champ_tri.asc())
        
        # --------------------------------------------------------------------
        # Pagination et exécution
        # --------------------------------------------------------------------
        total = query.count()
        predictions = query.offset(skip).limit(limit).all()
        
        logger.info(f"📊 Liste des prédictions | Total: {total} | Affichées: {len(predictions)} | Par: {current_user.email}")
        
        # Ajout des métadonnées de pagination dans les en-têtes (optionnel)
        # response.headers["X-Total-Count"] = str(total)
        
        return predictions
        
    except Exception as e:
        logger.error(f"❌ Erreur get_predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des prédictions: {str(e)}"
        )


# ============================================================================
# RÉCUPÉRER UNE PRÉDICTION PAR ID
# ============================================================================
@router.get("/{prediction_id}", response_model=PredictionResponse)
async def get_prediction(
    prediction_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE UNE PRÉDICTION SPÉCIFIQUE PAR SON IDENTIFIANT UNIQUE.
    
    Arguments:
    - prediction_id: Identifiant UUID de la prédiction
    
    Retourne les détails complets de la prédiction si elle existe.
    """
    try:
        # Récupération de la prédiction
        prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
        
        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prédiction avec l'ID '{prediction_id}' non trouvée"
            )
        
        # Vérification des accès (si champ user_id existe)
        if hasattr(prediction, 'user_id') and prediction.user_id != current_user.id:
            if current_user.role not in [UserRole.ADMIN, UserRole.TECHNICIEN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez pas accès à cette prédiction"
                )
        
        logger.info(f"📋 Consultation prédiction {prediction_id} par {current_user.email}")
        
        return prediction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur get_prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# VALIDER UNE PRÉDICTION AVEC DONNÉES TERRAIN
# ============================================================================
@router.post("/{prediction_id}/valider-terrain", response_model=Dict[str, Any])
async def validate_with_real_data(
    prediction_id: str,
    rendement_reel: float = Query(..., gt=0, description="Rendement réel mesuré (kg/ha)"),
    notes: Optional[str] = Query(None, max_length=500, description="Notes supplémentaires sur la validation"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    VALIDE UNE PRÉDICTION AVEC DES DONNÉES DE RÉCOLTE RÉELLES.
    
    Compare l'estimation du modèle IA avec le rendement réel mesuré sur le terrain.
    
    Critères de validation:
    - Succès: Le rendement réel est dans l'intervalle de confiance
    - Partiel: Le rendement réel est hors intervalle mais écart < 80%
    - Invalide: Écart supérieur à 80%, la prédiction est marquée invalide
    
    Arguments:
    - prediction_id: Identifiant de la prédiction à valider
    - rendement_reel: Rendement réel mesuré en kg/ha
    - notes: Commentaires sur la validation
    
    Retourne un rapport détaillé de la validation.
    """
    try:
        # --------------------------------------------------------------------
        # 1. Validation des paramètres d'entrée
        # --------------------------------------------------------------------
        if rendement_reel <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le rendement réel doit être supérieur à 0 kg/ha"
            )
        
        if rendement_reel > 100000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le rendement réel semble trop élevé (maximum: 100000 kg/ha)"
            )
        
        # --------------------------------------------------------------------
        # 2. Récupération de la prédiction
        # --------------------------------------------------------------------
        prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
        
        if not prediction:
            logger.warning(f"⚠️ Prédiction {prediction_id} non trouvée")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prédiction avec l'ID '{prediction_id}' non trouvée"
            )
        
        # --------------------------------------------------------------------
        # 3. Vérification des accès
        # --------------------------------------------------------------------
        if hasattr(prediction, 'user_id') and prediction.user_id != current_user.id:
            if current_user.role not in [UserRole.ADMIN, UserRole.TECHNICIEN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez pas accès à cette prédiction"
                )
        
        # --------------------------------------------------------------------
        # 4. Vérification de l'existence du rendement estimé
        # --------------------------------------------------------------------
        if prediction.rendement_estime is None or prediction.rendement_estime <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rendement estimé non disponible pour cette prédiction"
            )
        
        # --------------------------------------------------------------------
        # 5. Calculs métriques de validation
        # --------------------------------------------------------------------
        ecart_absolu = round(abs(prediction.rendement_estime - rendement_reel), 2)
        ecart_relatif = round((ecart_absolu / rendement_reel) * 100, 2) if rendement_reel > 0 else 0
        
        # Vérification dans l'intervalle de confiance
        dans_intervalle = False
        if prediction.intervalle_inferieur is not None and prediction.intervalle_superieur is not None:
            dans_intervalle = prediction.intervalle_inferieur <= rendement_reel <= prediction.intervalle_superieur
        
        # Calcul de la précision relative
        precision = round((1 - min(1.0, ecart_absolu / rendement_reel)) * 100, 2) if rendement_reel > 0 else 0
        
        # --------------------------------------------------------------------
        # 6. Détermination du statut
        # --------------------------------------------------------------------
        statut_anterior = prediction.est_valide
        
        if ecart_relatif > 80:
            prediction.est_valide = False
            statut = "INVALIDE"
            message = f"❌ Écart de {ecart_relatif}% dépasse le seuil de 80% - Prédiction invalidée"
        elif dans_intervalle:
            statut = "SUCCÈS"
            message = f"✅ Prédiction validée - Le rendement réel ({rendement_reel} kg/ha) est dans l'intervalle de confiance"
        else:
            statut = "PARTIEL"
            message = f"⚠️ Validation partielle - Le rendement réel ({rendement_reel} kg/ha) est hors intervalle [{prediction.intervalle_inferieur}, {prediction.intervalle_superieur}]"
        
        # --------------------------------------------------------------------
        # 7. Sauvegarde des données de validation
        # --------------------------------------------------------------------
        if hasattr(prediction, 'rendement_reel'):
            prediction.rendement_reel = rendement_reel
        if hasattr(prediction, 'date_validation'):
            prediction.date_validation = datetime.utcnow()
        if hasattr(prediction, 'notes_validation'):
            prediction.notes_validation = notes
        
        prediction.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(prediction)
        
        # --------------------------------------------------------------------
        # 8. Construction de la réponse
        # --------------------------------------------------------------------
        result = {
            "id": prediction_id,
            "statut": statut,
            "succes": dans_intervalle,
            "est_valide": prediction.est_valide,
            "message": message,
            "metriques": {
                "rendement_estime": prediction.rendement_estime,
                "rendement_reel": rendement_reel,
                "ecart_absolu_kg_ha": ecart_absolu,
                "ecart_relatif_pct": ecart_relatif,
                "precision_pct": precision,
                "intervalle_inferieur": prediction.intervalle_inferieur,
                "intervalle_superieur": prediction.intervalle_superieur,
                "confiance_pct": prediction.confiance
            },
            "validation": {
                "date_validation": datetime.utcnow().isoformat(),
                "valide_par": current_user.email,
                "notes": notes
            }
        }
        
        logger.info(f"✅ Validation terrain | Prédiction: {prediction_id} | Statut: {statut} | Écart: {ecart_relatif}% | Par: {current_user.email}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur validate_with_real_data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la validation: {str(e)}"
        )


# ============================================================================
# METTRE À JOUR UNE PRÉDICTION
# ============================================================================
@router.put("/{prediction_id}", response_model=PredictionResponse)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def update_prediction(
    prediction_id: str,
    request: PredictionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    MET À JOUR UNE PRÉDICTION EXISTANTE.
    
    Permet de modifier les champs d'une prédiction existante.
    Accessible uniquement aux administrateurs et techniciens.
    
    Arguments:
    - prediction_id: Identifiant de la prédiction à modifier
    - request: Données de mise à jour (tous les champs sont optionnels)
    """
    try:
        # Récupération de la prédiction
        prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
        
        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prédiction avec l'ID '{prediction_id}' non trouvée"
            )
        
        # Application des mises à jour
        update_data = request.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(prediction, key) and value is not None:
                setattr(prediction, key, value)
        
        # Mise à jour du timestamp
        prediction.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(prediction)
        
        logger.info(f"✏️ Prédiction mise à jour | ID: {prediction_id} | Par: {current_user.email}")
        
        return prediction
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur update_prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


# ============================================================================
# SUPPRIMER UNE PRÉDICTION
# ============================================================================
@router.delete("/{prediction_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_roles([UserRole.ADMIN])
async def delete_prediction(
    prediction_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    SUPPRIME UNE PRÉDICTION (ADMIN UNIQUEMENT).
    
    Supprime définitivement une prédiction de la base de données.
    Cette action est irréversible.
    
    Arguments:
    - prediction_id: Identifiant de la prédiction à supprimer
    """
    try:
        # Récupération de la prédiction
        prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
        
        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prédiction avec l'ID '{prediction_id}' non trouvée"
            )
        
        # Sauvegarde des infos pour le log avant suppression
        infos = {
            "id": prediction.id,
            "modele_id": prediction.modele_id,
            "rendement_estime": prediction.rendement_estime,
            "date_prediction": prediction.date_prediction.isoformat() if prediction.date_prediction else None
        }
        
        # Suppression
        db.delete(prediction)
        db.commit()
        
        logger.info(f"🗑️ Prédiction supprimée | ID: {prediction_id} | Infos: {infos} | Par: {current_user.email}")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur delete_prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )


# ============================================================================
# STATISTIQUES DES PRÉDICTIONS
# ============================================================================
@router.get("/statistiques/resume", response_model=Dict[str, Any])
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def get_predictions_statistiques(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE UN RÉSUMÉ STATISTIQUE DES PRÉDICTIONS.
    
    Fournit des indicateurs clés sur l'ensemble des prédictions:
    - Nombre total de prédictions
    - Taux de validité
    - Rendements moyens
    - Confiance moyenne
    - Répartition par modèle
    
    Accessible uniquement aux administrateurs et techniciens.
    """
    try:
        from sqlalchemy import func
        
        # Statistiques de base
        total = db.query(func.count(Prediction.id)).scalar() or 0
        total_valides = db.query(func.count(Prediction.id)).filter(Prediction.est_valide == True).scalar() or 0
        total_invalides = total - total_valides
        
        # Moyennes
        rendement_moyen = db.query(func.avg(Prediction.rendement_estime)).scalar() or 0
        confiance_moyenne = db.query(func.avg(Prediction.confiance)).scalar() or 0
        
        # Prédictions par modèle
        predictions_par_modele = db.query(
            Prediction.modele_id,
            func.count(Prediction.id).label("total")
        ).group_by(Prediction.modele_id).all()
        
        # Prédictions par mois
        predictions_par_mois = db.query(
            func.date_trunc('month', Prediction.date_prediction).label("mois"),
            func.count(Prediction.id).label("total")
        ).group_by("mois").order_by("mois").limit(12).all()
        
        result = {
            "total_predictions": total,
            "total_valides": total_valides,
            "total_invalides": total_invalides,
            "taux_validite": round((total_valides / total * 100), 2) if total > 0 else 0,
            "moyennes": {
                "rendement_estime_kg_ha": round(float(rendement_moyen), 2),
                "confiance_pct": round(float(confiance_moyenne), 2)
            },
            "repartition_par_modele": [
                {"modele_id": item[0], "total_predictions": item[1]}
                for item in predictions_par_modele
            ],
            "tendance_mensuelle": [
                {"mois": item[0].isoformat() if item[0] else None, "total": item[1]}
                for item in predictions_par_mois
            ]
        }
        
        logger.info(f"📊 Statistiques des prédictions consultées par {current_user.email}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur get_predictions_statistiques: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul des statistiques: {str(e)}"
        )