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
from .v1.ia import inferences, modeles, predictions, recommandations
from .v1.iot import balises, capteurs, drones, passerelles, releves, stations_meteo

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

api_router.include_router(inferences.router, prefix="/inferences", tags=["Inferences IA"])
api_router.include_router(modeles.router, prefix="/modeles-ia", tags=["IA - Modèles"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["IA - Prédictions"])
api_router.include_router(recommandations.router, prefix="/recommandations", tags=["IA - Recommandations"])

api_router.include_router(balises.router, prefix="/balises",tags=["Balises GPS"])
api_router.include_router(capteurs.router, prefix="/capteurs", tags=["Capteurs IA"])
api_router.include_router(drones.router, prefix="/drones", tags=["Drones IA"])
api_router.include_router(passerelles.router, prefix="/passerelles", tags=["Passerelles IA"])
api_router.include_router(releves.router, prefix="/releves", tags=["Relevés IA"])
api_router.include_router(stations_meteo.router, prefix="/stations-meteo", tags=["Stations Météo IA"])
