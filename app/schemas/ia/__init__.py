"""
Package des schémas IA.
"""
from .modele_ia import *
from .dataset import *
from .entrainement import *
from .prediction import *
from .inference import *
from .recommandation import *

__all__ = [
    "ModeleIABase",
    "ModeleIACreate",
    "ModeleIAUpdate",
    "ModeleIAResponse",
    "DatasetBase",
    "DatasetCreate",
    "DatasetResponse",
    "EntrainementBase",
    "EntrainementCreate",
    "EntrainementResponse",
    "PredictionBase",
    "PredictionCreate",
    "PredictionResponse",
    "InferenceBase",
    "InferenceCreate",
    "InferenceResponse",
    "RecommandationBase",
    "RecommandationCreate",
    "RecommandationResponse",
]