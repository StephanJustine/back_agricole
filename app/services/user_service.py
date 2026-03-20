"""
Service de gestion des utilisateurs.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status

from ..models.user import User
from ..models.session import UserSession  # <-- IMPORTANT: Importer UserSession
from ..models.parcelle import Parcelle
from ..models.culture import Culture
from ..models.recolte import Recolte
from ..models.transformation import Transformation
from ..models.vente import Vente
from ..models.historique import Historique
from ..core.security import SecurityService
from ..core.historique import HistoriqueService
from ..models.enums import UserRole


class UserService:
    """Service de gestion des utilisateurs."""
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Récupère un utilisateur par son ID."""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Récupère un utilisateur par son email."""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_telephone(db: Session, telephone: str) -> Optional[User]:
        """Récupère un utilisateur par son téléphone."""
        return db.query(User).filter(User.telephone == telephone).first()
    
    @staticmethod
    def get_users(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """Récupère la liste des utilisateurs avec filtres."""
        query = db.query(User)
        
        if role:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if search:
            query = query.filter(
                or_(
                    User.nom.ilike(f"%{search}%"),
                    User.prenom.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.telephone.ilike(f"%{search}%")
                )
            )
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_user_statistics(db: Session, user_id: str) -> Dict[str, Any]:
        """Récupère les statistiques d'un utilisateur."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé"
            )
        
        stats = {
            "user_id": user_id,
            "nom": user.nom,
            "prenom": user.prenom,
            "role": user.role,
            "date_inscription": user.date_inscription,
            "derniere_connexion": user.derniere_connexion,
            "is_active": user.is_active,
            "is_verified": user.is_verified
        }
        
        # Statistiques selon le rôle
        if user.role == UserRole.PRODUCTEUR:
            nb_parcelles = db.query(Parcelle).filter(Parcelle.proprietaire_id == user_id).count()
            stats["nb_parcelles"] = nb_parcelles
            
            total_surface = db.query(Parcelle.superficie).filter(
                Parcelle.proprietaire_id == user_id
            ).all()
            stats["surface_totale"] = sum(s[0] for s in total_surface) if total_surface else 0
            
            cultures = db.query(Culture).join(Parcelle).filter(
                Parcelle.proprietaire_id == user_id,
                Culture.date_fin_reelle.is_(None)
            ).count()
            stats["cultures_en_cours"] = cultures
            
        elif user.role == UserRole.TRANSFORMATEUR:
            nb_transformations = db.query(Transformation).filter(
                Transformation.responsable_id == user_id
            ).count()
            stats["nb_transformations"] = nb_transformations
            
        elif user.role == UserRole.COMMERCIAL:
            nb_ventes = db.query(Vente).filter(Vente.commercial_id == user_id).count()
            stats["nb_ventes"] = nb_ventes
            
            ventes = db.query(Vente.montant_total).filter(Vente.commercial_id == user_id).all()
            stats["ca_total"] = sum(v[0] for v in ventes) if ventes else 0
        
        return stats
    
    @staticmethod
    def get_user_activity(db: Session, user_id: str, limit: int = 50) -> List[Dict]:
        """Récupère l'activité récente d'un utilisateur."""
        actions = db.query(Historique).filter(
            Historique.user_id == user_id
        ).order_by(Historique.timestamp.desc()).limit(limit).all()
        
        return [
            {
                "id": a.id,
                "action": a.action,
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "description": a.description,
                "timestamp": a.timestamp,
                "ip_address": a.ip_address
            }
            for a in actions
        ]
    
    @staticmethod
    def get_user_sessions(db: Session, user_id: str, limit: int = 20) -> List[Dict]:
        """Récupère les sessions d'un utilisateur."""
        sessions = db.query(UserSession).filter(
            UserSession.user_id == user_id
        ).order_by(UserSession.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": s.id,
                "created_at": s.created_at,
                "expires_at": s.expires_at,
                "last_activity": s.last_activity,
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
                "is_active": s.is_active,
                "is_expired": s.is_expired()
            }
            for s in sessions
        ]