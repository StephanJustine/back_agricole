from functools import wraps
from typing import List, Callable
from fastapi import HTTPException, status

from ..models.enums import UserRole

def has_permission(user_role: UserRole, required_roles: List[UserRole]) -> bool:
    """
    Vérifie si l'utilisateur a la permission requise.
    """
    # Hiérarchie des rôles
    hierarchy = {
        UserRole.PRODUCTEUR: 1,
        UserRole.COLLECTEUR: 2,
        UserRole.TECHNICIEN: 3,
        UserRole.COMMERCIAL: 3,
        UserRole.TRANSFORMATEUR: 4,
        UserRole.ADMIN: 10,
        UserRole.SUPER_ADMIN: 100
    }
    
    user_level = hierarchy.get(user_role, 0)
    
    for role in required_roles:
        if user_level >= hierarchy.get(role, 0):
            return True
    
    return False

def require_roles(roles: List[UserRole]):
    """
    Décorateur pour exiger certains rôles.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Récupérer l'utilisateur depuis le contexte
            user = kwargs.get('current_user')
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentification requise"
                )
            
            if not has_permission(user.role, roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez pas les permissions nécessaires"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator