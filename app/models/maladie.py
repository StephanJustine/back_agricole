# """
# Modèle Maladie - Maladies des cultures.
# """
# from sqlalchemy import Column, String, Date, Integer, ForeignKey, Enum, Boolean, Text, Float
# from sqlalchemy.orm import relationship

# from .base import BaseModel
# from .enums import TypeMaladie


# class Maladie(BaseModel):
#     """
#     Maladie détectée sur une culture.
#     """
#     __tablename__ = "maladies"
    
#     culture_id = Column(String, ForeignKey("cultures.id", ondelete="CASCADE"), nullable=False)
    
#     type = Column(Enum(TypeMaladie), nullable=False)
#     date_detection = Column(Date, nullable=False)
#     gravite = Column(Integer, default=3)  # 1-5
#     surface_touchee = Column(Float, nullable=True)  # %
    
#     traitement_applique = Column(Text, nullable=True)
#     efficace = Column(Boolean, nullable=True)
    
#     photo_url = Column(String, nullable=True)
    
#     # Relations
#     culture = relationship("Culture", back_populates="maladies")
    
#     def __repr__(self):
#         return f"<Maladie {self.type} - Gravité {self.gravite}>"

"""
Modèle Maladie - Maladies des cultures.
"""
from sqlalchemy import Column, String, Date, Integer, ForeignKey, Enum, Boolean, Text, Float, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import BaseModel
from .enums import TypeMaladie


class Maladie(BaseModel):
    """
    Maladie détectée sur une culture.
    """
    __tablename__ = "maladies"
    
    # Lien avec la culture
    culture_id = Column(String, ForeignKey("cultures.id", ondelete="CASCADE"), nullable=False)
    
    # Informations sur la maladie
    type = Column(Enum(TypeMaladie), nullable=False)
    date_detection = Column(Date, nullable=False)
    gravite = Column(Integer, default=3)  # 1-5 (1=faible, 5=critique)
    surface_touchee = Column(Float, nullable=True)  # % de la parcelle touchée
    
    # Traitement
    traitement_applique = Column(Text, nullable=True)
    date_traitement = Column(Date, nullable=True)  # Date du traitement appliqué
    efficace = Column(Boolean, nullable=True)  # Traitement efficace ou non
    
    # Suivi
    date_guerison = Column(Date, nullable=True)  # Date de disparition des symptômes
    est_resolu = Column(Boolean, default=False)
    
    # Photos
    photo_url = Column(String, nullable=True)
    photos = Column(JSON, default=[])
    
    # Observations
    observations = Column(Text, nullable=True)
    recommandations = Column(Text, nullable=True)
    
    # Alertes
    alerte_envoyee = Column(Boolean, default=False)
    date_alerte = Column(DateTime, nullable=True)
    
    # Relations
    culture = relationship("Culture", back_populates="maladies")
    
    def __repr__(self):
        return f"<Maladie {self.type} - Gravité {self.gravite}>"
    
    @property
    def est_critique(self):
        """Vérifie si la maladie est critique (gravité >= 4)."""
        return self.gravite >= 4
    
    @property
    def niveau_alerte(self):
        """Retourne le niveau d'alerte."""
        if self.gravite >= 5:
            return "CRITIQUE"
        elif self.gravite >= 4:
            return "URGENT"
        elif self.gravite >= 3:
            return "IMPORTANT"
        elif self.gravite >= 2:
            return "MODÉRÉ"
        else:
            return "FAIBLE"
    
    def marquer_resolu(self):
        """Marque la maladie comme résolue."""
        self.est_resolu = True
        self.date_guerison = datetime.now().date()
    
    def marquer_alerte_envoyee(self):
        """Marque l'alerte comme envoyée."""
        self.alerte_envoyee = True
        self.date_alerte = datetime.utcnow()