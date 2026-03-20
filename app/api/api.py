"""
Regroupement de toutes les routes API.
"""
from fastapi import APIRouter

# Importer les routeurs de chaque module
from .v1 import auth, users
from .v1 import parcelles, cultures, mesures, maladies
from .v1 import travaux_sol, recoltes, lots
#  , analyses_sol
from .v1 import transformations
# , stocks, clients, ventes, historique

api_router = APIRouter()

# Routes d'authentification
api_router.include_router(auth.router, prefix="/auth", tags=["authentification"])

# Routes principales
api_router.include_router(users.router, prefix="/users", tags=["utilisateurs"])
api_router.include_router(parcelles.router, prefix="/parcelles", tags=["parcelles"])
api_router.include_router(cultures.router, prefix="/cultures", tags=["cultures"])
api_router.include_router(mesures.router, prefix="/mesures", tags=["mesures"])
api_router.include_router(maladies.router, prefix="/maladies", tags=["maladies"])
# api_router.include_router(analyses_sol.router, prefix="/analyses-sol", tags=["analyses-sol"])
api_router.include_router(travaux_sol.router, prefix="/travaux-sol", tags=["travaux-sol"])
api_router.include_router(recoltes.router, prefix="/recoltes", tags=["recoltes"])
api_router.include_router(lots.router, prefix="/lots", tags=["lots"])
api_router.include_router(transformations.router, prefix="/transformations", tags=["transformations"])
# api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
# api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
# api_router.include_router(ventes.router, prefix="/ventes", tags=["ventes"])
# api_router.include_router(historique.router, prefix="/historique", tags=["historique"])