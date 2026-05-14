# api/v1/ia/datasets.py
"""
Routes pour les jeux de données (datasets).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import json
import os

from app.database import get_db
from app.models.ia.dataset import Dataset
from app.schemas.ia.dataset import (
    DatasetCreate,
    DatasetUpdate,
    DatasetResponse,
    # DatasetListResponse
)

from app.core.dependencies import get_current_active_user
from app.core.permissions import require_roles
from app.models.enums import UserRole, SourceDataset

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def calculer_statistiques_dataset(db: Session, dataset_id: str) -> Dict[str, Any]:
    """Calcule les statistiques d'un dataset."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        return {}
    
    stats = {
        "nb_echantillons": dataset.nb_echantillons,
        "nb_features": len(dataset.features) if dataset.features else 0,
        "nb_labels": len(dataset.labels) if dataset.labels else 0,
        "taille": dataset.taille,
        "date_creation": dataset.date_creation.isoformat() if dataset.date_creation else None
    }
    
    return stats


# ============================================================================
# CRÉER UN DATASET
# ============================================================================
@router.post("/", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def create_dataset(
    obj_in: DatasetCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    CRÉE UN NOUVEAU JEU DE DONNÉES (DATASET).
    
    Args:
        obj_in: Données du dataset
        db: Session de base de données
        current_user: Utilisateur authentifié
        
    Returns:
        DatasetResponse: Le dataset créé
    """
    try:
        # --------------------------------------------------------------------
        # 1. Validation des données
        # --------------------------------------------------------------------
        if not obj_in.nom or not obj_in.nom.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le nom du dataset est requis"
            )
        
        # Vérifier si un dataset avec le même nom existe déjà
        existing = db.query(Dataset).filter(Dataset.nom == obj_in.nom).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Un dataset avec le nom '{obj_in.nom}' existe déjà"
            )
        
        # --------------------------------------------------------------------
        # 2. Préparation des données
        # --------------------------------------------------------------------
        now = datetime.utcnow()
        
        dataset = Dataset(
            nom=obj_in.nom.strip(),
            source=obj_in.source,
            date_creation=now,
            nb_echantillons=obj_in.nb_echantillons or 0,
            features=obj_in.features or [],
            labels=obj_in.labels or [],
            url_data=obj_in.url_data,
            taille=obj_in.taille,
            description=obj_in.description,
            created_at=now,
            updated_at=now,
            created_by=current_user.id if hasattr(Dataset, 'created_by') else None
        )
        
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        logger.info(f"✅ Dataset créé | ID: {dataset.id} | Nom: {dataset.nom} | Par: {current_user.email}")
        
        return dataset
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur create_dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création: {str(e)}"
        )


# ============================================================================
# LISTER LES DATASETS
# ============================================================================
@router.get("/", response_model=List[DatasetResponse])
async def get_datasets(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=500, description="Nombre maximum d'éléments"),
    nom: Optional[str] = Query(None, description="Filtrer par nom"),
    source: Optional[SourceDataset] = Query(None, description="Filtrer par source"),
    min_echantillons: Optional[int] = Query(None, ge=0, description="Nombre minimum d'échantillons"),
    date_debut: Optional[datetime] = Query(None, description="Date de création début"),
    date_fin: Optional[datetime] = Query(None, description="Date de création fin"),
    recherche: Optional[str] = Query(None, description="Recherche dans nom et description"),
    trier_par: str = Query("date_creation", description="Champ de tri"),
    ordre_desc: bool = Query(True, description="Tri décroissant"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE LA LISTE DES DATASETS AVEC FILTRES.
    """
    try:
        query = db.query(Dataset)
        
        # Filtres
        if nom:
            query = query.filter(Dataset.nom.ilike(f"%{nom}%"))
        if source:
            query = query.filter(Dataset.source == source)
        if min_echantillons:
            query = query.filter(Dataset.nb_echantillons >= min_echantillons)
        if date_debut:
            query = query.filter(Dataset.date_creation >= date_debut)
        if date_fin:
            query = query.filter(Dataset.date_creation <= date_fin)
        if recherche:
            query = query.filter(
                (Dataset.nom.ilike(f"%{recherche}%")) |
                (Dataset.description.ilike(f"%{recherche}%"))
            )
        
        # Tri
        champ_tri = getattr(Dataset, trier_par, Dataset.date_creation)
        if ordre_desc:
            query = query.order_by(champ_tri.desc())
        else:
            query = query.order_by(champ_tri.asc())
        
        total = query.count()
        datasets = query.offset(skip).limit(limit).all()
        
        logger.info(f"📊 Liste des datasets | Total: {total} | Affichés: {len(datasets)}")
        
        return datasets
        
    except Exception as e:
        logger.error(f"❌ Erreur get_datasets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# RÉCUPÉRER UN DATASET PAR ID
# ============================================================================
@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    include_stats: bool = Query(False, description="Inclure les statistiques détaillées"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE UN DATASET SPÉCIFIQUE PAR SON ID.
    """
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset avec l'ID '{dataset_id}' non trouvé"
            )
        
        # Ajouter les statistiques si demandé
        if include_stats:
            stats = calculer_statistiques_dataset(db, dataset_id)
            setattr(dataset, 'statistiques', stats)
        
        return dataset
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur get_dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# METTRE À JOUR UN DATASET
# ============================================================================
@router.put("/{dataset_id}", response_model=DatasetResponse)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def update_dataset(
    dataset_id: str,
    obj_in: DatasetUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    MET À JOUR UN DATASET EXISTANT.
    """
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset avec l'ID '{dataset_id}' non trouvé"
            )
        
        # Mise à jour des champs
        update_data = obj_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(dataset, key) and value is not None:
                setattr(dataset, key, value)
        
        dataset.updated_at = datetime.utcnow()
        if hasattr(Dataset, 'updated_by'):
            dataset.updated_by = current_user.id
        
        db.commit()
        db.refresh(dataset)
        
        logger.info(f"✏️ Dataset mis à jour | ID: {dataset_id} | Nom: {dataset.nom} | Par: {current_user.email}")
        
        return dataset
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur update_dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


# ============================================================================
# SUPPRIMER UN DATASET
# ============================================================================
@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_roles([UserRole.ADMIN])
async def delete_dataset(
    dataset_id: str,
    suppression_fichier: bool = Query(False, description="Supprimer également le fichier associé"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    SUPPRIME UN DATASET (ADMIN UNIQUEMENT).
    
    Args:
        dataset_id: ID du dataset à supprimer
        suppression_fichier: Si True, supprime aussi le fichier associé
    """
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset avec l'ID '{dataset_id}' non trouvé"
            )
        
        # Supprimer le fichier associé si demandé
        if suppression_fichier and dataset.url_data:
            try:
                if os.path.exists(dataset.url_data):
                    os.remove(dataset.url_data)
                    logger.info(f"🗑️ Fichier associé supprimé: {dataset.url_data}")
            except Exception as e:
                logger.warning(f"Impossible de supprimer le fichier {dataset.url_data}: {e}")
        
        db.delete(dataset)
        db.commit()
        
        logger.info(f"🗑️ Dataset supprimé | ID: {dataset_id} | Nom: {dataset.nom} | Par: {current_user.email}")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur delete_dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )


# ============================================================================
# STATISTIQUES D'UN DATASET
# ============================================================================
@router.get("/{dataset_id}/statistiques", response_model=Dict[str, Any])
async def get_dataset_statistiques(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE LES STATISTIQUES DÉTAILLÉES D'UN DATASET.
    """
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset avec l'ID '{dataset_id}' non trouvé"
            )
        
        stats = {
            "id": dataset.id,
            "nom": dataset.nom,
            "source": dataset.source.value if hasattr(dataset.source, 'value') else str(dataset.source),
            "date_creation": dataset.date_creation.isoformat() if dataset.date_creation else None,
            "nb_echantillons": dataset.nb_echantillons,
            "nb_features": len(dataset.features) if dataset.features else 0,
            "features": dataset.features,
            "nb_labels": len(dataset.labels) if dataset.labels else 0,
            "labels": dataset.labels,
            "taille": dataset.taille,
            "url_data": dataset.url_data,
            "description": dataset.description
        }
        
        logger.info(f"📈 Statistiques du dataset {dataset_id} consultées")
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur get_dataset_statistiques: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )


# ============================================================================
# IMPORTATION DE DONNÉES (CSV/JSON)
# ============================================================================
@router.post("/import", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def import_dataset(
    nom: str = Query(..., description="Nom du dataset"),
    source: SourceDataset = Query(SourceDataset.TERRAIN, description="Source des données"),
    fichier_url: str = Query(..., description="URL ou chemin du fichier"),
    description: Optional[str] = Query(None, description="Description"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    IMPORTE UN DATASET À PARTIR D'UN FICHIER (CSV, JSON, etc.).
    """
    try:
        # Vérifier si le fichier existe
        if not os.path.exists(fichier_url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Le fichier '{fichier_url}' n'existe pas"
            )
        
        # Obtenir la taille du fichier
        taille = os.path.getsize(fichier_url)
        taille_mb = f"{taille / (1024*1024):.2f} MB"
        
        # Simuler la détection de la structure
        # Dans un cas réel, vous analyseriez le fichier pour extraire features/labels
        features = ["feature_1", "feature_2", "feature_3"]
        labels = ["label"]
        nb_echantillons = 1000  # À calculer réellement
        
        # Créer le dataset
        now = datetime.utcnow()
        dataset = Dataset(
            nom=nom,
            source=source,
            date_creation=now,
            nb_echantillons=nb_echantillons,
            features=features,
            labels=labels,
            url_data=fichier_url,
            taille=taille_mb,
            description=description,
            created_at=now,
            updated_at=now,
            created_by=current_user.id if hasattr(Dataset, 'created_by') else None
        )
        
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        logger.info(f"📁 Dataset importé | ID: {dataset.id} | Fichier: {fichier_url}")
        
        return dataset
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur import_dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'importation: {str(e)}"
        )


# ============================================================================
# EXPORTER UN DATASET
# ============================================================================
@router.get("/{dataset_id}/export")
async def export_dataset(
    dataset_id: str,
    format: str = Query("json", regex="^(json|csv)$", description="Format d'exportation"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    EXPORTE UN DATASET AU FORMAT JSON OU CSV.
    """
    from fastapi.responses import JSONResponse, StreamingResponse
    import io
    import csv
    
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset avec l'ID '{dataset_id}' non trouvé"
            )
        
        # Préparer les données à exporter
        export_data = {
            "id": dataset.id,
            "nom": dataset.nom,
            "source": dataset.source.value if hasattr(dataset.source, 'value') else str(dataset.source),
            "date_creation": dataset.date_creation.isoformat() if dataset.date_creation else None,
            "nb_echantillons": dataset.nb_echantillons,
            "features": dataset.features,
            "labels": dataset.labels,
            "taille": dataset.taille,
            "description": dataset.description
        }
        
        if format == "json":
            return JSONResponse(content=export_data)
        
        else:  # format CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Écrire les en-têtes
            writer.writerow(["Champ", "Valeur"])
            
            # Écrire les données
            for key, value in export_data.items():
                if isinstance(value, list):
                    value = json.dumps(value)
                writer.writerow([key, value])
            
            output.seek(0)
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={dataset.nom}.csv"}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur export_dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'exportation: {str(e)}"
        )