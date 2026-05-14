# """
# Classe de base pour tous les schémas Pydantic.
# """
# from pydantic import BaseModel, ConfigDict, Field
# from datetime import datetime
# from typing import Optional, Any, Dict, List


# class BaseSchema(BaseModel):
#     """
#     Classe de base pour tous les schémas Pydantic.
#     """
#     model_config = ConfigDict(
#         from_attributes=True,
#         populate_by_name=True,
#         arbitrary_types_allowed=True,
#         json_encoders={
#             datetime: lambda v: v.isoformat()
#         }
#     )


# class BaseResponseSchema(BaseSchema):
#     """
#     Schéma de réponse de base avec les champs communs.
#     """
#     id: str
#     created_at: datetime
#     updated_at: datetime
#     is_active: bool = True
    
#     # Champs optionnels
#     created_by: Optional[str] = None
#     updated_by: Optional[str] = None
#     metadata: Optional[Dict[str, Any]] = None
#     tags: Optional[List[str]] = None
#     version: int = 1


# class BaseCreateSchema(BaseSchema):
#     """
#     Schéma de création de base.
#     """
#     pass


# class BaseUpdateSchema(BaseSchema):
#     """
#     Schéma de mise à jour de base (tous les champs optionnels).
#     """
#     pass


# class PaginatedResponseSchema(BaseSchema):
#     """
#     Schéma de réponse paginée.
#     """
#     total: int
#     page: int
#     size: int
#     pages: int
#     items: List[Any]
    
#     @classmethod
#     def from_pagination(cls, items: List[Any], total: int, page: int, size: int):
#         """
#         Crée une réponse paginée.
#         """
#         pages = (total + size - 1) // size if total > 0 else 1
#         return cls(
#             total=total,
#             page=page,
#             size=size,
#             pages=pages,
#             items=items
#         )


"""
Classe de base pour tous les schémas Pydantic.
"""
from pydantic import BaseModel, ConfigDict, field_serializer
from datetime import datetime
from typing import Optional, Any, Dict, List


class BaseSchema(BaseModel):
    """
    Classe de base pour tous les schémas Pydantic.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore"
    )


class BaseResponseSchema(BaseSchema):
    """
    Schéma de réponse de base avec les champs communs.
    """
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    version: int = 1
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime) -> str:
        """Convertit datetime en string ISO."""
        return dt.isoformat()


class PaginatedResponseSchema(BaseSchema):
    """
    Schéma de réponse paginée.
    """
    total: int
    page: int
    size: int
    pages: int
    items: List[Any]
    
    @classmethod
    def from_pagination(cls, items: List[Any], total: int, page: int, size: int):
        pages = (total + size - 1) // size if total > 0 else 1
        return cls(
            total=total,
            page=page,
            size=size,
            pages=pages,
            items=items
        )