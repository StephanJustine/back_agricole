# """
# Modèle Culture - Cycle de culture.
# """
# from sqlalchemy import Column, String, Date, Enum, Integer, ForeignKey, JSON, Text
# from sqlalchemy.orm import relationship
# from datetime import date, datetime

# from .base import BaseModel
# from .enums import StadeCulture


# class Culture(BaseModel):
#     """
#     Cycle de culture sur une parcelle.
#     """
#     __tablename__ = "cultures"
    
#     parcelle_id = Column(String, ForeignKey("parcelles.id", ondelete="CASCADE"), nullable=False)
    
#     # Dates
#     date_debut = Column(Date, nullable=False)
#     date_fin_prevue = Column(Date, nullable=True)
#     date_fin_reelle = Column(Date, nullable=True)
    
#     # Informations culturales
#     variete = Column(String, nullable=False)
#     type_semence = Column(String, nullable=True)
#     origine_semence = Column(String, nullable=True)
    
#     # Paramètres
#     densite_semis = Column(Integer, nullable=True)
#     ecartement_lignes = Column(Integer, nullable=True)
#     ecartement_poquets = Column(Integer, nullable=True)
    
#     # Suivi
#     stade = Column(Enum(StadeCulture), default=StadeCulture.PREPARATION)
#     sante = Column(Integer, default=10)
#     vigueur = Column(Integer, default=10)
    
#     # Métadonnées
#     observations = Column(Text, nullable=True)
#     photos = Column(JSON, default=[])
    
#     # Relations
#     parcelle = relationship("Parcelle", back_populates="cultures")
#     mesures = relationship("Mesure", back_populates="culture", cascade="all, delete-orphan")
#     maladies = relationship("Maladie", back_populates="culture", cascade="all, delete-orphan")
#     recolte = relationship("Recolte", back_populates="culture", uselist=False)
    
#     def __repr__(self):
#         return f"<Culture {self.variete} - {self.stade}>"
    
#     @property
#     def duree_ecoulee(self) -> int:
#         """Jours depuis le début."""
#         if self.date_debut:
#             delta = datetime.now().date() - self.date_debut
#             return delta.days
#         return 0
    
#     @property
#     def progression(self) -> int:
#         """Pourcentage de progression estimé."""
#         duree_totale = 120  # jours
#         return min(100, int((self.duree_ecoulee / duree_totale) * 100))

"""
Modèle Culture - Cycle de culture.
"""
from sqlalchemy import Column, String, Date, Enum, Integer, ForeignKey, JSON, Text, Float
from sqlalchemy.orm import relationship
from datetime import date, datetime
import uuid

from .base import BaseModel
from .enums import StadeCulture


class Culture(BaseModel):
    """
    Cycle de culture sur une parcelle.
    """
    __tablename__ = "cultures"
    
    # Identifiants
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=True)
    
    # Lien avec la parcelle
    parcelle_id = Column(String, ForeignKey("parcelles.id", ondelete="CASCADE"), nullable=False)
    
    # Dates
    date_debut = Column(Date, nullable=False)
    date_fin_prevue = Column(Date, nullable=True)
    date_fin_reelle = Column(Date, nullable=True)
    
    # Informations culturales
    variete = Column(String, nullable=False)
    type_semence = Column(String, nullable=True)  # certifiee, fermiere, selectionnee
    origine_semence = Column(String, nullable=True)
    
    # Paramètres de culture
    densite_semis = Column(Integer, nullable=True)  # plants/ha
    ecartement_lignes = Column(Integer, nullable=True)  # cm
    ecartement_poquets = Column(Integer, nullable=True)  # cm
    
    # Suivi
    stade = Column(Enum(StadeCulture), default=StadeCulture.PREPARATION)
    sante = Column(Integer, default=10)  # 1-10
    vigueur = Column(Integer, default=10)  # 1-10
    
    # Métadonnées
    observations = Column(Text, nullable=True)
    photos = Column(JSON, default=[])
    
    # Relations
    parcelle = relationship("Parcelle", back_populates="cultures")
    mesures = relationship("Mesure", back_populates="culture", cascade="all, delete-orphan")
    maladies = relationship("Maladie", back_populates="culture", cascade="all, delete-orphan")
    recolte = relationship("Recolte", back_populates="culture", uselist=False)
    
    def __repr__(self):
        return f"<Culture {self.variete} - {self.stade.value if hasattr(self.stade, 'value') else self.stade}>"
    
    @property
    def duree_ecoulee(self) -> int:
        """Jours depuis le début."""
        if self.date_debut:
            delta = datetime.now().date() - self.date_debut
            return delta.days
        return 0
    
    @property
    def progression(self) -> int:
        """Pourcentage de progression estimé (120 jours cycle total)."""
        duree_totale = 120  # jours
        return min(100, int((self.duree_ecoulee / duree_totale) * 100))
    
    @property
    def jours_restants(self) -> int:
        """Jours restants estimés."""
        duree_totale = 120
        return max(0, duree_totale - self.duree_ecoulee)
    
    @property
    def stade_description(self) -> str:
        """Description du stade actuel."""
        descriptions = {
            "preparation": "Préparation du sol",
            "semis": "Semis en cours",
            "levee": "Levée des plants",
            "croissance": "Croissance végétative",
            "floraison": "Floraison",
            "formation_gousses": "Formation des gousses",
            "maturite": "Maturité",
            "recolte": "Récolte",
            "termine": "Cycle terminé"
        }
        key = self.stade.value if hasattr(self.stade, 'value') else self.stade
        return descriptions.get(key, str(self.stade))
    
    def generate_code(self):
        """Génère un code unique pour la culture."""
        import uuid
        self.code = f"CUL-{uuid.uuid4().hex[:8].upper()}"
    
    def terminer(self):
        """Termine la culture."""
        self.date_fin_reelle = datetime.now().date()
        self.stade = StadeCulture.TERMINE
    
    def update_stade(self):
        """Met à jour le stade en fonction de la date de début."""
        if self.date_fin_reelle:
            self.stade = StadeCulture.TERMINE
            return
        
        jours = self.duree_ecoulee
        
        if jours < 0:
            self.stade = StadeCulture.PREPARATION
        elif jours < 7:
            self.stade = StadeCulture.SEMIS
        elif jours < 21:
            self.stade = StadeCulture.LEVEE
        elif jours < 51:
            self.stade = StadeCulture.CROISSANCE
        elif jours < 71:
            self.stade = StadeCulture.FLORAISON
        elif jours < 96:
            self.stade = StadeCulture.FORMATION_GOUSSES
        elif jours < 111:
            self.stade = StadeCulture.MATURITE
        else:
            self.stade = StadeCulture.RECOLTE