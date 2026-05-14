"""
Enums pour tous les modèles.
"""
from enum import Enum


class UserRole(str, Enum):
    """Rôles des utilisateurs."""
    PRODUCTEUR = "producteur"
    COLLECTEUR = "collecteur"
    TRANSFORMATEUR = "transformateur"
    COMMERCIAL = "commercial"
    TECHNICIEN = "technicien"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class TypeParcelle(str, Enum):
    """Type de parcelle."""
    AMELIOREE = "amelioree"
    TRADITIONNELLE = "traditionnelle"
    EXPERIMENTALE = "experimentale"
    TEMOIN = "temoin"


class StadeCulture(str, Enum):
    """Stade de culture."""
    PREPARATION = "preparation"
    SEMIS = "semis"
    LEVEE = "levee"
    CROISSANCE = "croissance"
    FLORAISON = "floraison"
    FORMATION_GOUSSES = "formation_gousses"
    MATURITE = "maturite"
    RECOLTE = "recolte"
    TERMINE = "termine"


class TypeTravail(str, Enum):
    """Type de travail du sol."""
    LABOUR = "labour"
    SARCLAGE = "sarclage"
    BUTTAGE = "buttage"
    AMENDEMENT = "amendement"
    TRAITEMENT = "traitement"
    FERTILISATION = "fertilisation"
    IRRIGATION = "irrigation"
    AUTRE = "autre"

class TypeMaladie(str, Enum):
    """Type de maladie."""
    ROSETTE = "rosette"
    CERCOSPORIOSE = "cercosporiose"
    FLAETRISSEMENT = "fletrissement"
    POURRITURE = "pourriture"
    CARENCE = "carence"  # Ajout
    AUTRE = "autre"


class QualiteRecolte(str, Enum):
    """Qualité de la récolte."""
    EXCELLENTE = "excellente"
    BONNE = "bonne"
    MOYENNE = "moyenne"
    MAUVAISE = "mauvaise"


class TypeLot(str, Enum):
    """Type de lot."""
    ARACHIDE_BRUTE = "arachide_brute"
    ARACHIDE_DECORTIQUEE = "arachide_decortiquee"
    HUILE = "huile"
    SAVON = "savon"


class TypeTransformation(str, Enum):
    """Type de transformation."""
    HUILE = "huile"
    SAVON = "savon"


class TypeClient(str, Enum):
    """Type de client."""
    GROSSISTE = "grossiste"
    DETAIL = "detail"
    PARTICULIER = "particulier"


class TypeModeleIA(str, Enum):
    """Type de modèle IA."""
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    VISION = "vision"


class SourceDataset(str, Enum):
    """Source du dataset."""
    TERRAIN = "terrain"
    HISTORIQUE = "historique"
    EXTERNE = "externe"


class StatusEntrainement(str, Enum):
    """Statut de l'entraînement."""
    EN_COURS = "en_cours"
    TERMINE = "termine"
    ECHEC = "echec"


class TypeRecommandation(str, Enum):
    """Type de recommandation."""
    FERTILISATION = "fertilisation"
    TRAITEMENT = "traitement"
    CALENDRIER = "calendrier"
    ARROSAGE = "arrosage"


class TypeCapteur(str, Enum):
    """Type de capteur."""
    HUMIDITE_SOL = "humidite_sol"
    TEMPERATURE_SOL = "temperature_sol"
    TEMPERATURE_AIR = "temperature_air"
    PH = "ph"
    LUMINOSITE = "luminosite"
    PLUIE = "pluie"
    VENT = "vent"


class StatusPasserelle(str, Enum):
    """Statut de la passerelle."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    