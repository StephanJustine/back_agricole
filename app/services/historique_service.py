"""
Service de gestion de l'historique.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.historique import Historique
from ..core.historique import HistoriqueService as CoreHistoriqueService


class HistoriqueService:
    """Service de gestion de l'historique."""
    
    @staticmethod
    def log_action(
        db: Session,
        user_id: Optional[str],
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        details: Optional[Dict] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Historique:
        """
        Enregistre une action dans l'historique.
        """
        return CoreHistoriqueService.log_action(
            db=db,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def get_historique(
        db: Session,
        user_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Historique]:
        """
        Récupère l'historique avec filtres.
        """
        query = db.query(Historique)
        
        if user_id:
            query = query.filter(Historique.user_id == user_id)
        
        if entity_type:
            query = query.filter(Historique.entity_type == entity_type)
        
        if action:
            query = query.filter(Historique.action == action)
        
        if start_date:
            query = query.filter(Historique.timestamp >= start_date)
        
        if end_date:
            query = query.filter(Historique.timestamp <= end_date)
        
        return query.order_by(Historique.timestamp.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_historique_by_entity(
        db: Session,
        entity_type: str,
        entity_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Historique]:
        """
        Récupère l'historique d'une entité spécifique.
        """
        return db.query(Historique).filter(
            Historique.entity_type == entity_type,
            Historique.entity_id == entity_id
        ).order_by(Historique.timestamp.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def count_historique(
        db: Session,
        user_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        action: Optional[str] = None
    ) -> int:
        """
        Compte le nombre d'entrées dans l'historique.
        """
        query = db.query(Historique)
        
        if user_id:
            query = query.filter(Historique.user_id == user_id)
        
        if entity_type:
            query = query.filter(Historique.entity_type == entity_type)
        
        if action:
            query = query.filter(Historique.action == action)
        
        return query.count()