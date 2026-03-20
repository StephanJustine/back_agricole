"""
Package des schémas IoT.
"""
from .passerelle import *
from .capteur import *
from .releve import *
from .station_meteo import *
from .drone import *
from .balise_gps import *

__all__ = [
    "PasserelleBase",
    "PasserelleCreate",
    "PasserelleUpdate",
    "PasserelleResponse",
    "CapteurBase",
    "CapteurCreate",
    "CapteurUpdate",
    "CapteurResponse",
    "ReleveCapteurBase",
    "ReleveCapteurCreate",
    "ReleveCapteurResponse",
    "StationMeteoBase",
    "StationMeteoCreate",
    "StationMeteoUpdate",
    "StationMeteoResponse",
    "DroneBase",
    "DroneCreate",
    "DroneResponse",
    "BaliseGPSBase",
    "BaliseGPSCreate",
    "BaliseGPSUpdate",
    "BaliseGPSResponse",
]