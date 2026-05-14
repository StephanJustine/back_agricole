# """
# Package des schémas IA.
# """
# from .modele_ia import *
# from .dataset import *
# from .entrainement import *
# from .prediction import *
# from .inference import *
# from .recommandation import *

# __all__ = [
#     "ModeleIABase",
#     "ModeleIACreate",
#     "ModeleIAUpdate",
#     "ModeleIAResponse",
#     "DatasetBase",
#     "DatasetCreate",
#     "DatasetResponse",
#     "EntrainementBase",
#     "EntrainementCreate",
#     "EntrainementResponse",
#     "PredictionBase",
#     "PredictionCreate",
#     "PredictionResponse",
#     "InferenceBase",
#     "InferenceCreate",
#     "InferenceResponse",
#     "RecommandationBase",
#     "RecommandationCreate",
#     "RecommandationResponse",
# ]

"""
Package des schémas IA.
"""
# Imports absolus
from app.schemas.ia.modele_ia import *
from app.schemas.ia.dataset import *
from app.schemas.ia.entrainement import *
from app.schemas.ia.prediction import *
from app.schemas.ia.inference import *
from app.schemas.ia.recommandation import *

# Liste de tous les symboles exportés
__all__ = [
    # ModeleIA
    "ModeleIABase",
    "ModeleIACreate",
    "ModeleIAUpdate",
    "ModeleIAResponse",
    
    # Dataset
    "DatasetBase", 
    "DatasetCreate",
    "DatasetResponse",
    
    # Entrainement
    "EntrainementBase",
    "EntrainementCreate",
    "EntrainementResponse",
    
    # Prediction
    "PredictionBase",
    "PredictionCreate",
    "PredictionResponse",
    
    # Inference
    "InferenceBase",
    "InferenceCreate", 
    "InferenceResponse",
    
    # Recommandation
    "RecommandationBase",
    "RecommandationCreate",
    "RecommandationResponse",
]