"""
Service de gestion des tokens.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from ..config import settings
from ..core.security import SecurityService
from ..models.user import User
from ..models.session import UserSession  # <-- IMPORTANT: Importer depuis session


class TokenService:
    """Service de gestion des tokens."""
    
    @staticmethod
    def create_tokens(user_id: str) -> Dict[str, Any]:
        """
        Crée les tokens d'accès et de rafraîchissement.
        """
        access_token = SecurityService.create_access_token({"sub": user_id})
        refresh_token = SecurityService.create_refresh_token({"sub": user_id})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    @staticmethod
    def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Vérifie un token d'accès.
        """
        payload = SecurityService.decode_token(token)
        if not payload or payload.get("type") != "access":
            return None
        return payload
    
    @staticmethod
    def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Vérifie un token de rafraîchissement.
        """
        payload = SecurityService.decode_token(token)
        if not payload or payload.get("type") != "refresh":
            return None
        return payload
    
    @staticmethod
    def revoke_user_sessions(
        db: Session,
        user_id: str,
        except_token: Optional[str] = None
    ) -> int:
        """
        Révoque toutes les sessions d'un utilisateur.
        """
        query = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        )
        
        if except_token:
            query = query.filter(UserSession.token != except_token)
        
        sessions = query.all()
        for session in sessions:
            session.is_active = False
            session.is_revoked = True
        
        db.commit()
        
        return len(sessions)
    
    @staticmethod
    def clean_expired_sessions(db: Session) -> int:
        """
        Nettoie les sessions expirées.
        """
        expired = db.query(UserSession).filter(
            UserSession.expires_at < datetime.utcnow(),
            UserSession.is_active == True
        ).all()
        
        for session in expired:
            session.is_active = False
        
        db.commit()
        
        return len(expired)
    
    @staticmethod
    def get_session_by_token(
        db: Session,
        token: str
    ) -> Optional[UserSession]:
        """
        Récupère une session par son token.
        """
        return db.query(UserSession).filter(
            UserSession.token == token,
            UserSession.is_active == True
        ).first()