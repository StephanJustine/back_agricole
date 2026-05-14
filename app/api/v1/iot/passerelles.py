# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import List

# # Importez vos modèles, schémas et la fonction de session DB
# # (Ajustez les chemins d'import selon votre structure de dossier)
# from ....database import get_db  # Supposant que vous avez un get_db dans votre config base
# from ....models.iot.passerelle import Passerelle
# from ....schemas.iot.passerelle import PasserelleCreate, PasserelleUpdate, PasserelleResponse

# router = APIRouter()

# @router.post("/", response_model=PasserelleResponse, status_code=status.HTTP_201_CREATED)
# def create_passerelle(obj_in: PasserelleCreate, db: Session = Depends(get_db)):
#     """
#     Enregistre une nouvelle passerelle IoT.
#     """
#     # Vérification si l'adresse MAC existe déjà
#     existing = db.query(Passerelle).filter(Passerelle.adresse_mac == obj_in.adresse_mac).first()
#     if existing:
#         raise HTTPException(status_code=400, detail="Cette adresse MAC est déjà enregistrée.")
    
#     db_obj = Passerelle(**obj_in.model_dump())
#     db.add(db_obj)
#     db.commit()
#     db.refresh(db_obj)
#     return db_obj

# @router.get("/", response_model=List[PasserelleResponse])
# def read_passerelles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     """
#     Liste toutes les passerelles avec pagination.
#     """
#     return db.query(Passerelle).offset(skip).limit(limit).all()

# @router.get("/{passerelle_id}", response_model=PasserelleResponse)
# def read_passerelle(passerelle_id: int, db: Session = Depends(get_db)):
#     """
#     Récupère les détails d'une passerelle spécifique.
#     """
#     db_obj = db.query(Passerelle).filter(Passerelle.id == passerelle_id).first()
#     if not db_obj:
#         raise HTTPException(status_code=404, detail="Passerelle non trouvée")
#     return db_obj

# @router.patch("/{passerelle_id}", response_model=PasserelleResponse)
# def update_passerelle(passerelle_id: int, obj_in: PasserelleUpdate, db: Session = Depends(get_db)):
#     """
#     Met à jour partiellement les informations d'une passerelle.
#     """
#     db_obj = db.query(Passerelle).filter(Passerelle.id == passerelle_id).first()
#     if not db_obj:
#         raise HTTPException(status_code=404, detail="Passerelle non trouvée")
    
#     update_data = obj_in.model_dump(exclude_unset=True)
#     for field, value in update_data.items():
#         setattr(db_obj, field, value)
    
#     db.commit()
#     db.refresh(db_obj)
#     return db_obj

# @router.delete("/{passerelle_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_passerelle(passerelle_id: int, db: Session = Depends(get_db)):
#     """
#     Supprime une passerelle du système.
#     """
#     db_obj = db.query(Passerelle).filter(Passerelle.id == passerelle_id).first()
#     if not db_obj:
#         raise HTTPException(status_code=404, detail="Passerelle non trouvée")
    
#     db.delete(db_obj)
#     db.commit()
#     return None

# api/v1/iot/passerelles.py
"""
Routes pour les passerelles IoT.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import re

from app.database import get_db
from app.models.iot.passerelle import Passerelle
from app.schemas.iot.passerelle import (
    PasserelleCreate,
    PasserelleUpdate,
    PasserelleResponse
)
from app.core.dependencies import get_current_active_user
from app.core.permissions import require_roles
from app.models.enums import UserRole, StatusPasserelle

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def valider_adresse_mac(adresse_mac: str) -> bool:
    """Valide le format d'une adresse MAC."""
    pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
    return bool(re.match(pattern, adresse_mac))


def valider_adresse_ip(adresse_ip: str) -> bool:
    """Valide le format d'une adresse IP."""
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, adresse_ip):
        return False
    parts = adresse_ip.split('.')
    return all(0 <= int(part) <= 255 for part in parts)


def valider_localisation(localisation: str) -> bool:
    """Valide le format de localisation (lat,lon)."""
    if not localisation:
        return True
    pattern = r'^-?\d{1,3}\.\d+,-?\d{1,3}\.\d+$'
    return bool(re.match(pattern, localisation))


def mettre_a_jour_statut_connectivite(passerelle: Passerelle):
    """Met à jour le statut de connectivité de la passerelle."""
    now = datetime.utcnow()
    
    # Si dernière connexion > 5 minutes, considérer déconnecté
    if passerelle.derniere_connexion:
        delta = (now - passerelle.derniere_connexion).total_seconds()
        if delta > 300:  # 5 minutes
            passerelle.est_connectee = False
            if passerelle.status == StatusPasserelle.ACTIVE:
                passerelle.status = StatusPasserelle.INACTIVE
    else:
        passerelle.est_connectee = False


# ============================================================================
# CRÉER UNE PASSERELLE
# ============================================================================
@router.post("/", response_model=PasserelleResponse, status_code=status.HTTP_201_CREATED)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def create_passerelle(
    obj_in: PasserelleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    CRÉE UNE NOUVELLE PASSERELLE IOT.
    
    Args:
        obj_in: Données de la passerelle
        db: Session de base de données
        current_user: Utilisateur authentifié
    """
    try:
        # 1. Validation du nom
        if not obj_in.nom or not obj_in.nom.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le nom de la passerelle est requis"
            )
        
        # 2. Validation de l'adresse MAC
        if not valider_adresse_mac(obj_in.adresse_mac):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format d'adresse MAC invalide. Utilisez le format XX:XX:XX:XX:XX:XX"
            )
        
        # 3. Vérifier si l'adresse MAC existe déjà
        existing = db.query(Passerelle).filter(
            Passerelle.adresse_mac == obj_in.adresse_mac
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Une passerelle avec l'adresse MAC '{obj_in.adresse_mac}' existe déjà"
            )
        
        # 4. Validation de la localisation
        if obj_in.localisation and not valider_localisation(obj_in.localisation):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format de localisation invalide. Utilisez 'latitude,longitude'"
            )
        
        # 5. Création de la passerelle
        now = datetime.utcnow()
        
        db_obj = Passerelle(
            nom=obj_in.nom.strip(),
            modele=obj_in.modele,
            adresse_mac=obj_in.adresse_mac.upper(),
            adresse_ip=obj_in.adresse_ip,
            firmware_version=obj_in.firmware_version,
            localisation=obj_in.localisation,
            adresse_physique=obj_in.adresse_physique,
            configuration=obj_in.configuration or {},
            notes=obj_in.notes,
            status=StatusPasserelle.ACTIVE,
            est_connectee=False,
            date_installation=now,
            created_at=now,
            updated_at=now,
            created_by=current_user.id if hasattr(Passerelle, 'created_by') else None
        )
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        logger.info(f"✅ Passerelle créée | ID: {db_obj.id} | Nom: {db_obj.nom} | MAC: {db_obj.adresse_mac} | Par: {current_user.email}")
        
        return db_obj
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur create_passerelle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création: {str(e)}"
        )


# ============================================================================
# LISTER LES PASSERELLES
# ============================================================================
@router.get("/", response_model=List[PasserelleResponse])
async def read_passerelles(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=500, description="Nombre maximum d'éléments"),
    nom: Optional[str] = Query(None, description="Filtrer par nom"),
    modele: Optional[str] = Query(None, description="Filtrer par modèle"),
    status: Optional[StatusPasserelle] = Query(None, description="Filtrer par statut"),
    est_connectee: Optional[bool] = Query(None, description="Filtrer par connectivité"),
    adresse_mac: Optional[str] = Query(None, description="Filtrer par adresse MAC"),
    recherche: Optional[str] = Query(None, description="Recherche dans nom, modèle, adresse MAC"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE LA LISTE DES PASSERELLES AVEC FILTRES ET PAGINATION.
    """
    try:
        query = db.query(Passerelle)
        
        # Filtres
        if nom:
            query = query.filter(Passerelle.nom.ilike(f"%{nom}%"))
        if modele:
            query = query.filter(Passerelle.modele.ilike(f"%{modele}%"))
        if status:
            query = query.filter(Passerelle.status == status)
        if est_connectee is not None:
            query = query.filter(Passerelle.est_connectee == est_connectee)
        if adresse_mac:
            query = query.filter(Passerelle.adresse_mac.ilike(f"%{adresse_mac}%"))
        if recherche:
            query = query.filter(
                (Passerelle.nom.ilike(f"%{recherche}%")) |
                (Passerelle.modele.ilike(f"%{recherche}%")) |
                (Passerelle.adresse_mac.ilike(f"%{recherche}%"))
            )
        
        # Mettre à jour le statut de connectivité avant d'afficher
        passerelles = query.order_by(Passerelle.date_installation.desc()).offset(skip).limit(limit).all()
        
        for passerelle in passerelles:
            mettre_a_jour_statut_connectivite(passerelle)
        
        logger.info(f"📊 Liste des passerelles | Total: {len(passerelles)}")
        
        return passerelles
        
    except Exception as e:
        logger.error(f"❌ Erreur read_passerelles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# RÉCUPÉRER UNE PASSERELLE PAR ID
# ============================================================================
@router.get("/{passerelle_id}", response_model=PasserelleResponse)
async def read_passerelle(
    passerelle_id: str,
    include_capteurs: bool = Query(False, description="Inclure la liste des capteurs"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE LES DÉTAILS D'UNE PASSERELLE SPÉCIFIQUE.
    """
    try:
        db_obj = db.query(Passerelle).filter(Passerelle.id == passerelle_id).first()
        
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Passerelle avec l'ID '{passerelle_id}' non trouvée"
            )
        
        # Mettre à jour le statut de connectivité
        mettre_a_jour_statut_connectivite(db_obj)
        
        # Optionnellement, charger les capteurs associés
        if include_capteurs and hasattr(db_obj, 'capteurs'):
            capteurs_data = []
            for capteur in db_obj.capteurs:
                capteurs_data.append({
                    "id": capteur.id,
                    "code": capteur.code,
                    "type": capteur.type.value if hasattr(capteur.type, 'value') else str(capteur.type),
                    "est_actif": capteur.est_actif,
                    "derniere_valeur": capteur.derniere_valeur,
                    "derniere_mise_a_jour": capteur.derniere_mise_a_jour
                })
            setattr(db_obj, 'capteurs_liste', capteurs_data)
        
        return db_obj
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur read_passerelle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# RÉCUPÉRER UNE PASSERELLE PAR ADRESSE MAC
# ============================================================================
@router.get("/mac/{adresse_mac}", response_model=PasserelleResponse)
async def read_passerelle_by_mac(
    adresse_mac: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE UNE PASSERELLE PAR SON ADRESSE MAC.
    """
    try:
        if not valider_adresse_mac(adresse_mac):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format d'adresse MAC invalide"
            )
        
        db_obj = db.query(Passerelle).filter(Passerelle.adresse_mac == adresse_mac.upper()).first()
        
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Passerelle avec l'adresse MAC '{adresse_mac}' non trouvée"
            )
        
        mettre_a_jour_statut_connectivite(db_obj)
        
        return db_obj
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur read_passerelle_by_mac: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


# ============================================================================
# METTRE À JOUR UNE PASSERELLE
# ============================================================================
@router.patch("/{passerelle_id}", response_model=PasserelleResponse)
@require_roles([UserRole.ADMIN, UserRole.TECHNICIEN])
async def update_passerelle(
    passerelle_id: str,
    obj_in: PasserelleUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    MET À JOUR PARTIELLEMENT LES INFORMATIONS D'UNE PASSERELLE.
    """
    try:
        db_obj = db.query(Passerelle).filter(Passerelle.id == passerelle_id).first()
        
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Passerelle avec l'ID '{passerelle_id}' non trouvée"
            )
        
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Validation spéciale pour l'adresse IP
        if "adresse_ip" in update_data and update_data["adresse_ip"]:
            if not valider_adresse_ip(update_data["adresse_ip"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Format d'adresse IP invalide"
                )
        
        # Mise à jour des champs
        for field, value in update_data.items():
            if hasattr(db_obj, field) and value is not None:
                setattr(db_obj, field, value)
        
        # Si la passerelle redevient active, mettre à jour la connexion
        if obj_in.status == StatusPasserelle.ACTIVE and db_obj.status != StatusPasserelle.ACTIVE:
            db_obj.est_connectee = True
            db_obj.derniere_connexion = datetime.utcnow()
        
        db_obj.updated_at = datetime.utcnow()
        if hasattr(Passerelle, 'updated_by'):
            db_obj.updated_by = current_user.id
        
        db.commit()
        db.refresh(db_obj)
        
        logger.info(f"✏️ Passerelle mise à jour | ID: {passerelle_id} | Par: {current_user.email}")
        
        return db_obj
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur update_passerelle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


# ============================================================================
# METTRE À JOUR LA CONNEXION D'UNE PASSERELLE
# ============================================================================
@router.post("/{passerelle_id}/heartbeat", response_model=PasserelleResponse)
async def passerelle_heartbeat(
    passerelle_id: str,
    adresse_ip: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    MET À JOUR LA DERNIÈRE CONNEXION D'UNE PASSERELLE (HEARTBEAT).
    """
    try:
        db_obj = db.query(Passerelle).filter(Passerelle.id == passerelle_id).first()
        
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Passerelle avec l'ID '{passerelle_id}' non trouvée"
            )
        
        # Mettre à jour la connexion
        db_obj.derniere_connexion = datetime.utcnow()
        db_obj.est_connectee = True
        
        if adresse_ip and valider_adresse_ip(adresse_ip):
            db_obj.adresse_ip = adresse_ip
        
        if db_obj.status != StatusPasserelle.ACTIVE:
            db_obj.status = StatusPasserelle.ACTIVE
        
        db_obj.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_obj)
        
        logger.info(f"💓 Heartbeat reçu | Passerelle: {db_obj.nom} | IP: {adresse_ip or 'inconnue'}")
        
        return db_obj
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur passerelle_heartbeat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


# ============================================================================
# SUPPRIMER UNE PASSERELLE
# ============================================================================
@router.delete("/{passerelle_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_roles([UserRole.ADMIN])
async def delete_passerelle(
    passerelle_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    SUPPRIME UNE PASSERELLE DU SYSTÈME (ADMIN UNIQUEMENT).
    """
    try:
        db_obj = db.query(Passerelle).filter(Passerelle.id == passerelle_id).first()
        
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Passerelle avec l'ID '{passerelle_id}' non trouvée"
            )
        
        # Compter les capteurs associés
        nb_capteurs = len(db_obj.capteurs) if hasattr(db_obj, 'capteurs') else 0
        
        logger.info(f"🗑️ Passerelle supprimée | ID: {passerelle_id} | Nom: {db_obj.nom} | Capteurs: {nb_capteurs} | Par: {current_user.email}")
        
        db.delete(db_obj)
        db.commit()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur delete_passerelle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )


# ============================================================================
# STATISTIQUES DES PASSERELLES
# ============================================================================
@router.get("/statistiques/resume", response_model=Dict[str, Any])
async def get_passerelles_statistiques(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    RÉCUPÈRE UN RÉSUMÉ STATISTIQUE DES PASSERELLES.
    """
    try:
        from sqlalchemy import func
        
        total = db.query(func.count(Passerelle.id)).scalar() or 0
        total_connectees = db.query(func.count(Passerelle.id)).filter(Passerelle.est_connectee == True).scalar() or 0
        total_inactives = db.query(func.count(Passerelle.id)).filter(Passerelle.status == StatusPasserelle.INACTIVE).scalar() or 0
        
        # Répartition par modèle
        repartition_modele = db.query(
            Passerelle.modele,
            func.count(Passerelle.id).label("total")
        ).filter(Passerelle.modele.isnot(None)).group_by(Passerelle.modele).all()
        
        # Moyenne de capteurs par passerelle
        # À implémenter selon votre structure
        
        result = {
            "total_passerelles": total,
            "connectees": total_connectees,
            "inactives": total_inactives,
            "taux_connectivite": round((total_connectees / total * 100), 1) if total > 0 else 0,
            "repartition_par_modele": [
                {"modele": item[0], "total": item[1]}
                for item in repartition_modele
            ]
        }
        
        logger.info(f"📊 Statistiques passerelles consultées")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur get_passerelles_statistiques: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul des statistiques: {str(e)}"
        )