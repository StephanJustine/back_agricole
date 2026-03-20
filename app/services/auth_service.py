"""
Service d'authentification.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import Request, HTTPException, status

from ..models.user import User
from ..models.session import UserSession  # <-- IMPORTANT: Importer depuis session
from ..core.security import SecurityService
from ..core.email import EmailService as CoreEmailService
from ..core.historique import HistoriqueService as CoreHistoriqueService
from ..config import settings


class AuthService:
    """Service d'authentification."""
    
    @staticmethod
    def register(
        db: Session,
        email: str,
        nom: str,
        prenom: str,
        telephone: str,
        password: str,
        role: str = "producteur"
    ) -> User:
        """
        Inscription d'un nouvel utilisateur.
        """
        from ..models.enums import UserRole
        
        # Vérifier si l'email existe déjà
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cet email est déjà utilisé"
            )
        
        # Vérifier si le téléphone existe déjà
        existing_phone = db.query(User).filter(User.telephone == telephone).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ce numéro de téléphone est déjà utilisé"
            )
        
        # Créer l'utilisateur
        user = User(
            email=email,
            nom=nom,
            prenom=prenom,
            telephone=telephone,
            role=UserRole(role),
            hashed_password=SecurityService.get_password_hash(password),
            verification_token=SecurityService.generate_verification_token()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Enregistrer dans l'historique
        CoreHistoriqueService.log_action(
            db=db,
            user_id=user.id,
            action="REGISTER",
            entity_type="user",
            entity_id=user.id,
            description=f"Nouvel utilisateur inscrit: {user.email}"
        )
        
        return user
    
    @staticmethod
    def login(
        db: Session,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[User, str, str]:
        """
        Connexion utilisateur.
        """
        # Récupérer l'utilisateur
        user = db.query(User).filter(User.email == email).first()
        
        # Vérifier les identifiants
        if not user or not SecurityService.verify_password(password, user.hashed_password):
            CoreHistoriqueService.log_action(
                db=db,
                user_id=None,
                action="LOGIN_FAILED",
                entity_type="auth",
                description=f"Tentative de connexion échouée pour {email}",
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou mot de passe incorrect"
            )
        
        # Vérifier si le compte est actif
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Compte désactivé"
            )
        
        # Mettre à jour la dernière connexion
        user.derniere_connexion = datetime.utcnow()
        
        # Créer les tokens
        access_token = SecurityService.create_access_token({"sub": user.id})
        refresh_token = SecurityService.create_refresh_token({"sub": user.id})
        
        # Sauvegarder le refresh token
        user.refresh_token = refresh_token
        
        # Créer la session
        session = UserSession(
            user_id=user.id,
            token=access_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        db.add(session)
        
        db.commit()
        
        # Enregistrer dans l'historique
        CoreHistoriqueService.log_action(
            db=db,
            user_id=user.id,
            action="LOGIN",
            entity_type="auth",
            entity_id=user.id,
            description=f"Connexion réussie: {user.email}",
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return user, access_token, refresh_token
    
    # ... autres méthodes ...