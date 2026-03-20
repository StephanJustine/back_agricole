"""
Package des modèles IA.
"""
from .modele_ia import ModeleIA
from .dataset import Dataset
from .entrainement import Entrainement
from .prediction import Prediction
from .inference import Inference
from .recommandation import Recommandation

__all__ = [
    "ModeleIA",
    "Dataset", 
    "Entrainement",
    "Prediction",
    "Inference",
    "Recommandation"
]