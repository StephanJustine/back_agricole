"""
Package des modèles SQLAlchemy.
"""
from .base import BaseModel
from .enums import *

# Import de tous les modèles pour que SQLAlchemy les connaisse
from .user import User
from .session import UserSession  # <-- IMPORTANT: Importer UserSession
from .historique import Historique
from .parcelle import Parcelle
from .culture import Culture
from .mesure import Mesure
from .maladie import Maladie
from .analyse_sol import AnalyseSol
from .travail_sol import TravailSol
from .recolte import Recolte
from .lot import Lot
from .transformation import Transformation
from .stock import Stock
from .client import Client
from .vente import Vente

# Modèles IA
from .ia.modele_ia import ModeleIA
from .ia.dataset import Dataset
from .ia.entrainement import Entrainement
from .ia.prediction import Prediction
from .ia.inference import Inference
from .ia.recommandation import Recommandation

# Modèles IoT
from .iot.passerelle import Passerelle
from .iot.capteur import Capteur
from .iot.releve import ReleveCapteur
from .iot.station_meteo import StationMeteo
from .iot.drone import Drone
from .iot.balise_gps import BaliseGPS

__all__ = [
    "BaseModel",
    # Enums
    "UserRole",
    "TypeParcelle",
    "StadeCulture",
    "TypeTravail",
    "TypeMaladie",
    "QualiteRecolte",
    "TypeLot",
    "TypeTransformation",
    "TypeClient",
    "TypeModeleIA",
    "SourceDataset",
    "StatusEntrainement",
    "TypeRecommandation",
    "TypeCapteur",
    "StatusPasserelle",
    # Modèles
    "User",
    "UserSession",
    "Historique",
    "Parcelle",
    "Culture",
    "Mesure",
    "Maladie",
    "AnalyseSol",
    "TravailSol",
    "Recolte",
    "Lot",
    "Transformation",
    "Stock",
    "Client",
    "Vente",
    "ModeleIA",
    "Dataset",
    "Entrainement",
    "Prediction",
    "Inference",
    "Recommandation",
    "Passerelle",
    "Capteur",
    "ReleveCapteur",
    "StationMeteo",
    "Drone",
    "BaliseGPS",
]