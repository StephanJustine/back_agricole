"""
Dépendances pour l'authentification.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime  # <-- IMPORTANT: Ajouter l'import datetime
import logging

from ..database import get_db
from ..models.user import User
from ..models.session import UserSession
from .security import SecurityService
from .exceptions import UnauthorizedException

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Récupère l'utilisateur actuel à partir du token.
    """
    try:
        payload = SecurityService.decode_token(token)
        if not payload or payload.get("type") != "access":
            logger.warning("Token invalide ou type incorrect")
            raise UnauthorizedException("Token invalide")
        
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token sans user_id")
            raise UnauthorizedException("Token invalide")
        
        # Vérifier que la session est active
        session = db.query(UserSession).filter(
            UserSession.token == token,
            UserSession.is_active == True
        ).first()
        
        if not session:
            logger.warning(f"Session non trouvée pour le token")
            raise UnauthorizedException("Session invalide")
        
        if session.is_expired():
            logger.warning(f"Session expirée pour le token")
            raise UnauthorizedException("Session expirée")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"Utilisateur non trouvé: {user_id}")
            raise UnauthorizedException("Utilisateur non trouvé")
        
        if not user.is_active:
            logger.warning(f"Compte désactivé: {user.email}")
            raise UnauthorizedException("Compte désactivé")
        
        # Mettre à jour la dernière activité
        session.last_activity = datetime.utcnow()
        db.commit()
        
        return user
        
    except UnauthorizedException:
        raise
    except Exception as e:
        logger.error(f"Erreur dans get_current_user: {e}")
        raise UnauthorizedException("Erreur d'authentification")


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Récupère l'utilisateur actuel et vérifie qu'il est actif.
    """
    if not current_user.is_active:
        raise UnauthorizedException("Compte désactivé")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Récupère l'utilisateur actuel et vérifie qu'il est admin.
    """
    from ..models.enums import UserRole
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs"
        )
    return current_user


async def get_current_super_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Récupère l'utilisateur actuel et vérifie qu'il est super admin.
    """
    from ..models.enums import UserRole
    
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux super administrateurs"
        )
    return current_user