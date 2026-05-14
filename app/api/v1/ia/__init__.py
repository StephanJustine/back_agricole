"""
Package des routes IA.
"""
from .modeles import router as modeles_router
from .predictions import router as predictions_router
from .inferences import router as inferences_router
from .recommandations import router as recommandations_router

__all__ = [
    "modeles_router",
    "predictions_router", 
    "inferences_router",
    "recommandations_router"
]