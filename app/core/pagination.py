from typing import TypeVar, Generic, List
from pydantic import BaseModel
from sqlalchemy.orm import Query

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Réponse paginée."""
    total: int
    page: int
    size: int
    pages: int
    items: List[T]

def paginate(query: Query, page: int = 1, size: int = 20) -> tuple:
    """
    Pagine une requête SQLAlchemy.
    """
    # Calculer le nombre total
    total = query.count()
    
    # Calculer le nombre de pages
    pages = (total + size - 1) // size if total > 0 else 1
    
    # Ajuster la page
    page = max(1, min(page, pages))
    
    # Récupérer les items
    items = query.offset((page - 1) * size).limit(size).all()
    
    return {
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
        "items": items
    }