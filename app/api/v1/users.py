"""
Routes CRUD pour les utilisateurs.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status, Request  # <-- Ajout de Request
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from ...database import get_db
from ...models.user import User
from ...models.enums import UserRole
from ...schemas.user import *
from ...core.dependencies import get_current_active_user, get_current_admin_user
from ...core.permissions import require_roles
from ...core.pagination import paginate
from ...core.exceptions import NotFoundException, BadRequestException
from ...core.security import SecurityService
from ...core.historique import HistoriqueService
from ...services.user_service import UserService

router = APIRouter()


# ========================
# LISTE DES UTILISATEURS
# ========================
@router.get("/", response_model=UserList)
async def get_users(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(20, ge=1, le=100, description="Nombre d'éléments par page"),
    role: Optional[UserRole] = Query(None, description="Filtrer par rôle"),
    search: Optional[str] = Query(None, description="Recherche par nom, prénom, email"),
    is_active: Optional[bool] = Query(None, description="Filtrer par statut actif"),
    sort_by: str = Query("created_at", description="Tri par champ"),
    sort_desc: bool = Query(False, description="Tri décroissant"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère la liste des utilisateurs avec pagination et filtres.
    """
    query = db.query(User)
    
    # Filtre par rôle
    if role:
        query = query.filter(User.role == role)
    
    # Filtre par statut actif
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # Recherche par nom, prénom, email
    if search:
        query = query.filter(
            (User.nom.ilike(f"%{search}%")) |
            (User.prenom.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (User.telephone.ilike(f"%{search}%"))
        )
    
    # Tri
    if sort_desc:
        query = query.order_by(getattr(User, sort_by).desc())
    else:
        query = query.order_by(getattr(User, sort_by).asc())
    
    # Pagination
    result = paginate(query, page, size)
    
    return {
        "total": result["total"],
        "page": result["page"],
        "size": result["size"],
        "pages": result["pages"],
        "items": result["items"]
    }


# ========================
# INFORMATIONS DE L'UTILISATEUR CONNECTÉ
# ========================
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les informations de l'utilisateur connecté.
    """
    return current_user


# ========================
# STATISTIQUES DE L'UTILISATEUR CONNECTÉ
# ========================
@router.get("/me/stats")
async def get_current_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les statistiques de l'utilisateur connecté.
    """
    stats = UserService.get_user_statistics(db, current_user.id)
    return stats


# ========================
# ACTIVITÉ DE L'UTILISATEUR CONNECTÉ
# ========================
@router.get("/me/activity")
async def get_current_user_activity(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère l'activité récente de l'utilisateur connecté.
    """
    activity = UserService.get_user_activity(db, current_user.id, limit)
    return {"activity": activity, "count": len(activity)}


# ========================
# SESSIONS DE L'UTILISATEUR CONNECTÉ
# ========================
@router.get("/me/sessions")
async def get_current_user_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les sessions actives de l'utilisateur connecté.
    """
    from ...models.session import UserSession
    
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).order_by(UserSession.created_at.desc()).all()
    
    return {
        "sessions": [
            {
                "id": s.id,
                "created_at": s.created_at,
                "expires_at": s.expires_at,
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
                "is_expired": s.is_expired()
            }
            for s in sessions
        ]
    }


# ========================
# METTRE À JOUR L'UTILISATEUR CONNECTÉ
# ========================
@router.put("/me", response_model=UserResponse)
async def update_current_user(
    request: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Met à jour les informations de l'utilisateur connecté.
    """
    update_data = request.model_dump(exclude_unset=True)
    old_data = {
        "nom": current_user.nom,
        "prenom": current_user.prenom,
        "telephone": current_user.telephone,
        "adresse": current_user.adresse,
        "photo_url": current_user.photo_url
    }
    
    for key, value in update_data.items():
        if hasattr(current_user, key):
            setattr(current_user, key, value)
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    # Enregistrer dans l'historique
    HistoriqueService.log_update(
        db=db,
        user_id=current_user.id,
        entity_type="user",
        entity_id=current_user.id,
        old_data=old_data,
        new_data=update_data
    )
    
    return current_user


# ========================
# CHANGER LE MOT DE PASSE (CONNECTÉ)
# ========================
@router.post("/me/change-password")
async def change_my_password(
    current_password: str,
    new_password: str,
    confirm_password: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Change le mot de passe de l'utilisateur connecté.
    """
    # Vérifier la confirmation
    if new_password != confirm_password:
        raise BadRequestException("Les mots de passe ne correspondent pas")
    
    # Vérifier l'ancien mot de passe
    if not SecurityService.verify_password(current_password, current_user.hashed_password):
        raise BadRequestException("Mot de passe actuel incorrect")
    
    # Mettre à jour le mot de passe
    current_user.hashed_password = SecurityService.get_password_hash(new_password)
    db.commit()
    
    # Enregistrer dans l'historique
    HistoriqueService.log_action(
        db=db,
        user_id=current_user.id,
        action="CHANGE_PASSWORD",
        entity_type="user",
        entity_id=current_user.id,
        description="Mot de passe modifié"
    )
    
    return {"message": "Mot de passe changé avec succès"}


# ========================
# RÉVOQUER TOUTES LES SESSIONS (SAUF ACTUELLE)
# ========================
@router.post("/me/revoke-sessions")
async def revoke_other_sessions(
    request: Request,  # <-- Request est maintenant importé
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Révoque toutes les sessions sauf la session actuelle.
    """
    from ...models.session import UserSession
    
    auth_header = request.headers.get("Authorization")
    current_token = auth_header.replace("Bearer ", "") if auth_header else None
    
    # Révoquer les autres sessions
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).all()
    
    revoked_count = 0
    for session in sessions:
        if session.token != current_token:
            session.is_active = False
            session.is_revoked = True
            revoked_count += 1
    
    db.commit()
    
    # Enregistrer dans l'historique
    HistoriqueService.log_action(
        db=db,
        user_id=current_user.id,
        action="REVOKE_SESSIONS",
        entity_type="user",
        entity_id=current_user.id,
        description=f"{revoked_count} sessions révoquées"
    )
    
    return {"message": f"{revoked_count} sessions révoquées"}


# ========================
# RÉCUPÉRER UN UTILISATEUR PAR ID
# ========================
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère un utilisateur par son ID.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("Utilisateur non trouvé")
    
    return user


# ========================
# STATISTIQUES D'UN UTILISATEUR (ADMIN)
# ========================
@router.get("/{user_id}/stats")
@require_roles([UserRole.ADMIN])
async def get_user_stats(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les statistiques d'un utilisateur (admin uniquement).
    """
    stats = UserService.get_user_statistics(db, user_id)
    return stats


# ========================
# METTRE À JOUR UN UTILISATEUR (ADMIN)
# ========================
@router.put("/{user_id}", response_model=UserResponse)
@require_roles([UserRole.ADMIN])
async def update_user(
    user_id: str,
    request: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Met à jour un utilisateur (admin uniquement).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("Utilisateur non trouvé")
    
    update_data = request.model_dump(exclude_unset=True)
    old_data = {
        "nom": user.nom,
        "prenom": user.prenom,
        "telephone": user.telephone,
        "role": user.role,
        "is_active": user.is_active,
        "adresse": user.adresse
    }
    
    for key, value in update_data.items():
        if hasattr(user, key):
            setattr(user, key, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    # Enregistrer dans l'historique
    HistoriqueService.log_update(
        db=db,
        user_id=current_user.id,
        entity_type="user",
        entity_id=user.id,
        old_data=old_data,
        new_data=update_data
    )
    
    return user


# ========================
# CHANGER LE RÔLE D'UN UTILISATEUR (ADMIN)
# ========================
@router.patch("/{user_id}/role", response_model=UserResponse)
@require_roles([UserRole.ADMIN])
async def change_user_role(
    user_id: str,
    role: UserRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Change le rôle d'un utilisateur (admin uniquement).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("Utilisateur non trouvé")
    
    # Ne pas changer son propre rôle
    if user.id == current_user.id:
        raise BadRequestException("Vous ne pouvez pas changer votre propre rôle")
    
    old_role = user.role
    user.role = role
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    # Enregistrer dans l'historique
    HistoriqueService.log_action(
        db=db,
        user_id=current_user.id,
        action="CHANGE_ROLE",
        entity_type="user",
        entity_id=user.id,
        description=f"Rôle changé de {old_role} à {role}"
    )
    
    return user


# ========================
# ACTIVER/DÉSACTIVER UN UTILISATEUR (ADMIN)
# ========================
@router.patch("/{user_id}/toggle-active", response_model=UserResponse)
@require_roles([UserRole.ADMIN])
async def toggle_user_active(
    user_id: str,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Active ou désactive un utilisateur (admin uniquement).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("Utilisateur non trouvé")
    
    # Ne pas désactiver son propre compte
    if user.id == current_user.id and not is_active:
        raise BadRequestException("Vous ne pouvez pas désactiver votre propre compte")
    
    user.is_active = is_active
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    # Enregistrer dans l'historique
    status = "activé" if is_active else "désactivé"
    HistoriqueService.log_action(
        db=db,
        user_id=current_user.id,
        action="TOGGLE_ACTIVE",
        entity_type="user",
        entity_id=user.id,
        description=f"Utilisateur {status}"
    )
    
    return user


# ========================
# SUPPRIMER UN UTILISATEUR (ADMIN)
# ========================
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_roles([UserRole.ADMIN])
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Supprime un utilisateur (admin uniquement).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("Utilisateur non trouvé")
    
    # Ne pas se supprimer soi-même
    if user.id == current_user.id:
        raise BadRequestException("Vous ne pouvez pas supprimer votre propre compte")
    
    # Enregistrer dans l'historique avant suppression
    HistoriqueService.log_action(
        db=db,
        user_id=current_user.id,
        action="DELETE_USER",
        entity_type="user",
        entity_id=user.id,
        description=f"Utilisateur supprimé: {user.email} ({user.nom} {user.prenom})"
    )
    
    db.delete(user)
    db.commit()


# ========================
# RÉINITIALISER LE MOT DE PASSE D'UN UTILISATEUR (ADMIN)
# ========================
@router.post("/{user_id}/reset-password")
@require_roles([UserRole.ADMIN])
async def admin_reset_password(
    user_id: str,
    new_password: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Réinitialise le mot de passe d'un utilisateur (admin uniquement).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("Utilisateur non trouvé")
    
    # Générer un mot de passe temporaire si non fourni
    if not new_password:
        new_password = SecurityService.generate_temp_password()
    
    # Mettre à jour le mot de passe
    user.hashed_password = SecurityService.get_password_hash(new_password)
    user.reset_password_token = None
    user.reset_password_expires = None
    db.commit()
    
    # Enregistrer dans l'historique
    HistoriqueService.log_action(
        db=db,
        user_id=current_user.id,
        action="ADMIN_RESET_PASSWORD",
        entity_type="user",
        entity_id=user.id,
        description=f"Mot de passe réinitialisé par admin"
    )
    
    return {
        "message": "Mot de passe réinitialisé avec succès",
        "new_password": new_password if not new_password else "***"
    }


# ========================
# EXPORTER LA LISTE DES UTILISATEURS (ADMIN)
# ========================
@router.get("/export/csv")
@require_roles([UserRole.ADMIN])
async def export_users_csv(
    role: Optional[UserRole] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Exporte la liste des utilisateurs au format CSV (admin uniquement).
    """
    import csv
    from fastapi.responses import StreamingResponse
    import io
    
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    
    users = query.all()
    
    # Créer le fichier CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # En-têtes
    writer.writerow([
        "ID", "Email", "Nom", "Prénom", "Téléphone", "Rôle", 
        "Actif", "Vérifié", "Date inscription", "Dernière connexion"
    ])
    
    # Données
    for user in users:
        writer.writerow([
            user.id,
            user.email,
            user.nom,
            user.prenom,
            user.telephone,
            user.role.value if hasattr(user.role, 'value') else user.role,
            "Oui" if user.is_active else "Non",
            "Oui" if user.is_verified else "Non",
            user.date_inscription.strftime("%Y-%m-%d %H:%M") if user.date_inscription else "",
            user.derniere_connexion.strftime("%Y-%m-%d %H:%M") if user.derniere_connexion else ""
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users_export.csv"}
    )