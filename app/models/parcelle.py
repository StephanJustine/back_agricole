# """
# Modèle Parcelle - Champ agricole.
# """
# from sqlalchemy import Column, String, Float, Enum, ForeignKey, Boolean, JSON, Text, DateTime
# from sqlalchemy.orm import relationship
# from datetime import datetime

# from .base import BaseModel
# from .enums import TypeParcelle


# class Parcelle(BaseModel):
#     """
#     Parcelle agricole.
#     """
#     __tablename__ = "parcelles"
    
#     # Informations de base
#     nom = Column(String, nullable=False)
#     code = Column(String, unique=True, nullable=True)
#     superficie = Column(Float, nullable=False)  # hectares
#     type = Column(Enum(TypeParcelle), nullable=False)
    
#     # Localisation
#     region = Column(String, nullable=True)
#     commune = Column(String, nullable=True)
#     lieu_dit = Column(String, nullable=True)
#     coord_gps = Column(String, nullable=True)  # "lat,lon"
#     altitude = Column(Float, nullable=True)
    
#     # Caractéristiques du sol
#     type_sol = Column(String, nullable=True)  # sablonneux, argileux, limoneux
#     exposition = Column(String, nullable=True)  # nord, sud, est, ouest
#     pente = Column(String, nullable=True)  # faible, moyenne, forte
    
#     # Propriétaire
#     proprietaire_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
#     # Statut
#     is_active = Column(Boolean, default=True)
#     # is_cultivee supprimé - on utilisera culture_actuelle comme propriété
    
#     # Métadonnées
#     photo_principale = Column(String, nullable=True)
#     photos = Column(JSON, default=[])
#     notes = Column(Text, nullable=True)
#     date_abandon = Column(DateTime, nullable=True)
    
#     # Relations
#     proprietaire = relationship("User", back_populates="parcelles")
#     cultures = relationship("Culture", back_populates="parcelle", cascade="all, delete-orphan")
#     analyses_sol = relationship("AnalyseSol", back_populates="parcelle", cascade="all, delete-orphan")
#     travaux = relationship("TravailSol", back_populates="parcelle", cascade="all, delete-orphan")
#     capteurs = relationship("Capteur", back_populates="parcelle")
#     station_meteo = relationship("StationMeteo", back_populates="parcelle", uselist=False)
#     predictions = relationship("Prediction", back_populates="parcelle")
#     recommandations = relationship("Recommandation", back_populates="parcelle")
    
#     def __repr__(self):
#         return f"<Parcelle {self.nom} - {self.type}>"
    
#     @property
#     def culture_actuelle(self):
#         """Retourne la culture en cours."""
#         for culture in self.cultures:
#             if culture.date_fin_reelle is None:
#                 return culture
#         return None
    
#     @property
#     def is_cultivee(self):
#         """Retourne True si une culture est en cours."""
#         return self.culture_actuelle is not None
    
#     @property
#     def surface_utilisee(self):
#         """Surface actuellement cultivée."""
#         if self.culture_actuelle:
#             return self.superficie
#         return 0
    
#     def generate_code(self):
#         """Génère un code unique pour la parcelle."""
#         import uuid
#         self.code = f"PAR-{uuid.uuid4().hex[:8].upper()}"
    
#     def soft_delete(self):
#         """Suppression logique de la parcelle."""
#         self.is_active = False
#         self.date_abandon = datetime.utcnow()

"""
Modèle Parcelle - Champ agricole.
"""
from sqlalchemy import Column, String, Float, Enum, ForeignKey, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import BaseModel
from .enums import TypeParcelle


class Parcelle(BaseModel):
    """
    Parcelle agricole.
    """
    __tablename__ = "parcelles"
    
    # Identifiants
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=True)
    
    # Informations de base
    nom = Column(String, nullable=False)
    superficie = Column(Float, nullable=False)  # hectares
    type = Column(Enum(TypeParcelle), nullable=False)
    
    # Localisation (pour la carte)
    region = Column(String, nullable=True)
    commune = Column(String, nullable=True)
    lieu_dit = Column(String, nullable=True)
    coord_gps = Column(String, nullable=True)  # "latitude,longitude"
    altitude = Column(Float, nullable=True)
    
    # Caractéristiques du sol
    type_sol = Column(String, nullable=True)
    exposition = Column(String, nullable=True)
    pente = Column(String, nullable=True)
    
    # Propriétaire (lien avec User)
    proprietaire_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Statut
    is_active = Column(Boolean, default=True)
    
    # Métadonnées
    photo_principale = Column(String, nullable=True)
    photos = Column(JSON, default=[])
    notes = Column(Text, nullable=True)
    
    # Relations
    proprietaire = relationship("User", back_populates="parcelles")
    cultures = relationship("Culture", back_populates="parcelle", cascade="all, delete-orphan")
    analyses_sol = relationship("AnalyseSol", back_populates="parcelle", cascade="all, delete-orphan")
    travaux = relationship("TravailSol", back_populates="parcelle", cascade="all, delete-orphan")
    capteurs = relationship("Capteur", back_populates="parcelle")
    station_meteo = relationship("StationMeteo", back_populates="parcelle", uselist=False)
    predictions = relationship("Prediction", back_populates="parcelle")
    recommandations = relationship("Recommandation", back_populates="parcelle")
    
    def __repr__(self):
        return f"<Parcelle {self.nom} - {self.type.value if hasattr(self.type, 'value') else self.type}>"
    
    @property
    def latitude(self):
        """Extrait la latitude des coordonnées GPS."""
        if self.coord_gps:
            try:
                parts = self.coord_gps.replace(' ', '').split(',')
                if len(parts) >= 1:
                    return float(parts[0])
            except (ValueError, IndexError):
                pass
        return None
    
    @property
    def longitude(self):
        """Extrait la longitude des coordonnées GPS."""
        if self.coord_gps:
            try:
                parts = self.coord_gps.replace(' ', '').split(',')
                if len(parts) >= 2:
                    return float(parts[1])
            except (ValueError, IndexError):
                pass
        return None
    
    @property
    def culture_actuelle(self):
        """Retourne la culture en cours."""
        for culture in self.cultures:
            if culture.date_fin_reelle is None:
                return culture
        return None
    
    @property
    def is_cultivee(self):
        """Retourne True si une culture est en cours."""
        return self.culture_actuelle is not None
    
    @property
    def surface_utilisee(self):
        """Surface actuellement cultivée."""
        if self.culture_actuelle:
            return self.superficie
        return 0
    
    def generate_code(self):
        """Génère un code unique pour la parcelle."""
        import uuid
        self.code = f"PAR-{uuid.uuid4().hex[:8].upper()}"
    
    def soft_delete(self):
        """Suppression logique de la parcelle."""
        self.is_active = False