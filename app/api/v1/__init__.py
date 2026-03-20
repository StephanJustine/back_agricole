# app/api/v1/__init__.py
from .auth import router as auth_router
from .users import router as users_router
from .parcelles import router as parcelles_router
from .cultures import router as cultures_router
from .mesures import router as mesures_router
from .maladies import router as maladies_router
from .travaux_sol import router as travaux_sol_router
from .recoltes import router as recoltes_router
from .lots import router as lots_router
from .transformations import router as transformations_router

# Commenter les imports des modules non créés
# from .analyses_sol import router as analyses_sol_router
# from .recoltes import router as recoltes_router
# from .lots import router as lots_router
# from .transformations import router as transformations_router
# from .stocks import router as stocks_router
# from .clients import router as clients_router
# from .ventes import router as ventes_router
# from .historique import router as historique_router

__all__ = [
    "auth_router",
    "users_router",
    "parcelles_router",
    "cultures_router",
    "mesures_router",
    "maladies_router",
    "travaux_sol_router",
    "recoltes_router",
    "lots_router",
    "transformations_router"

]