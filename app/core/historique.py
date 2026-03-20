# """
# Service d'historique.
# """
# from sqlalchemy.orm import Session
# from typing import Optional, Dict, Any
# from datetime import datetime
# import json

# from ..models.historique import Historique


# class HistoriqueService:
#     """Service pour enregistrer automatiquement les actions."""
    
#     @staticmethod
#     def log_action(
#         db: Session,
#         user_id: Optional[str],
#         action: str,
#         entity_type: str,
#         entity_id: Optional[str] = None,
#         details: Optional[Dict] = None,
#         description: Optional[str] = None,
#         ip_address: Optional[str] = None,
#         user_agent: Optional[str] = None
#     ) -> Historique:
#         """
#         Enregistre une action dans l'historique.
#         """
#         historique = Historique(
#             user_id=user_id,
#             action=action,
#             entity_type=entity_type,
#             entity_id=entity_id,
#             details=details or {},
#             description=description,
#             ip_address=ip_address,
#             user_agent=user_agent,
#             timestamp=datetime.utcnow()
#         )
        
#         db.add(historique)
#         db.commit()
        
#         return historique
    
#     @staticmethod
#     def log_create(
#         db: Session,
#         user_id: Optional[str],
#         entity_type: str,
#         entity_id: str,
#         data: Dict[str, Any],
#         description: Optional[str] = None,
#         ip_address: Optional[str] = None,
#         user_agent: Optional[str] = None
#     ) -> Historique:
#         """
#         Enregistre une création.
#         """
#         return HistoriqueService.log_action(
#             db=db,
#             user_id=user_id,
#             action="CREATE",
#             entity_type=entity_type,
#             entity_id=entity_id,
#             details={"data": data},
#             description=description or f"Création de {entity_type}",
#             ip_address=ip_address,
#             user_agent=user_agent
#         )
    
#     @staticmethod
#     def log_update(
#         db: Session,
#         user_id: Optional[str],
#         entity_type: str,
#         entity_id: str,
#         old_data: Dict[str, Any],
#         new_data: Dict[str, Any],
#         description: Optional[str] = None,
#         ip_address: Optional[str] = None,
#         user_agent: Optional[str] = None
#     ) -> Historique:
#         """
#         Enregistre une modification.
#         """
#         return HistoriqueService.log_action(
#             db=db,
#             user_id=user_id,
#             action="UPDATE",
#             entity_type=entity_type,
#             entity_id=entity_id,
#             details={"old": old_data, "new": new_data},
#             description=description or f"Modification de {entity_type}",
#             ip_address=ip_address,
#             user_agent=user_agent
#         )
    
#     @staticmethod
#     def log_delete(
#         db: Session,
#         user_id: Optional[str],
#         entity_type: str,
#         entity_id: str,
#         data: Dict[str, Any],
#         description: Optional[str] = None,
#         ip_address: Optional[str] = None,
#         user_agent: Optional[str] = None
#     ) -> Historique:
#         """
#         Enregistre une suppression.
#         """
#         return HistoriqueService.log_action(
#             db=db,
#             user_id=user_id,
#             action="DELETE",
#             entity_type=entity_type,
#             entity_id=entity_id,
#             details={"data": data},
#             description=description or f"Suppression de {entity_type}",
#             ip_address=ip_address,
#             user_agent=user_agent
#         )
    
#     @staticmethod
#     def log_login(
#         db: Session,
#         user_id: str,
#         success: bool,
#         description: Optional[str] = None,
#         ip_address: Optional[str] = None,
#         user_agent: Optional[str] = None
#     ) -> Historique:
#         """
#         Enregistre une tentative de connexion.
#         """
#         return HistoriqueService.log_action(
#             db=db,
#             user_id=user_id if success else None,
#             action="LOGIN",
#             entity_type="auth",
#             details={"success": success},
#             description=description or ("Connexion réussie" if success else "Tentative de connexion échouée"),
#             ip_address=ip_address,
#             user_agent=user_agent
#         )

"""
Service d'historique.
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime, date
import json

from ..models.historique import Historique


def json_serializer(obj):
    """
    Sérialise les objets non sérialisables par défaut.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class HistoriqueService:
    """Service pour enregistrer automatiquement les actions."""
    
    @staticmethod
    def _serialize_details(details: Optional[Dict]) -> Optional[Dict]:
        """
        Sérialise les détails pour le stockage JSON.
        """
        if details is None:
            return {}
        
        try:
            # Convertir les dates en string pour JSON
            return json.loads(json.dumps(details, default=json_serializer))
        except (TypeError, ValueError) as e:
            # En cas d'erreur, retourner un dict vide
            print(f"Erreur de sérialisation: {e}")
            return {}
    
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
        # Sérialiser les détails
        serialized_details = HistoriqueService._serialize_details(details)
        
        historique = Historique(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=serialized_details,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow()
        )
        
        db.add(historique)
        db.commit()
        db.refresh(historique)
        
        return historique
    
    @staticmethod
    def log_create(
        db: Session,
        user_id: Optional[str],
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Historique:
        """
        Enregistre une création.
        """
        return HistoriqueService.log_action(
            db=db,
            user_id=user_id,
            action="CREATE",
            entity_type=entity_type,
            entity_id=entity_id,
            details={"data": data},
            description=description or f"Création de {entity_type}",
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def log_update(
        db: Session,
        user_id: Optional[str],
        entity_type: str,
        entity_id: str,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Historique:
        """
        Enregistre une modification.
        """
        return HistoriqueService.log_action(
            db=db,
            user_id=user_id,
            action="UPDATE",
            entity_type=entity_type,
            entity_id=entity_id,
            details={"old": old_data, "new": new_data},
            description=description or f"Modification de {entity_type}",
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def log_delete(
        db: Session,
        user_id: Optional[str],
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Historique:
        """
        Enregistre une suppression.
        """
        return HistoriqueService.log_action(
            db=db,
            user_id=user_id,
            action="DELETE",
            entity_type=entity_type,
            entity_id=entity_id,
            details={"data": data},
            description=description or f"Suppression de {entity_type}",
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def log_login(
        db: Session,
        user_id: str,
        success: bool,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Historique:
        """
        Enregistre une tentative de connexion.
        """
        return HistoriqueService.log_action(
            db=db,
            user_id=user_id if success else None,
            action="LOGIN",
            entity_type="auth",
            details={"success": success},
            description=description or ("Connexion réussie" if success else "Tentative de connexion échouée"),
            ip_address=ip_address,
            user_agent=user_agent
        )