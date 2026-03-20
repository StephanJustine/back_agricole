"""
Package des schémas Pydantic.
"""
from .base import BaseSchema, BaseResponseSchema, PaginatedResponseSchema
from .user import UserCreate, UserUpdate, UserResponse, UserList
from .auth import LoginRequest, LoginResponse
from .parcelle import ParcelleCreate, ParcelleUpdate, ParcelleResponse, ParcelleList
from .culture import CultureCreate, CultureUpdate, CultureResponse, CultureList
from .mesure import MesureCreate, MesureUpdate, MesureResponse, MesureList
from .maladie import MaladieCreate, MaladieUpdate, MaladieResponse, MaladieList
from .travail_sol import (
    TravailSolBase,
    TravailSolCreate,
    TravailSolUpdate,
    TravailSolResponse,
    TravailSolList,
    CoutsParcelle
)

__all__ = [
    "BaseSchema",
    "BaseResponseSchema",
    "PaginatedResponseSchema",
    "UserCreate",
    "UserUpdate", 
    "UserResponse",
    "UserList",
    "LoginRequest",
    "LoginResponse",
    "ParcelleCreate",
    "ParcelleUpdate",
    "ParcelleResponse",
    "ParcelleList",
    "CultureCreate",
    "CultureUpdate",
    "CultureResponse",
    "CultureList",
    "MesureCreate",
    "MesureUpdate",
    "MesureResponse",
    "MesureList",
    "MaladieCreate",
    "MaladieUpdate",
    "MaladieResponse",
    "MaladieList",
    "TravailSolBase",
    "TravailSolCreate",
    "TravailSolUpdate",
    "TravailSolResponse",
    "TravailSolList",
    "CoutsParcelle"
]