"""
Modèle Recolte - Récolte des cultures.
"""
from sqlalchemy import Column, String, Date, Float, Enum, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import BaseModel
from .enums import QualiteRecolte


class Recolte(BaseModel):
    """
    Récolte d'une culture.
    """
    __tablename__ = "recoltes"
    
    # Identifiants
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=True)
    
    # Lien avec la culture
    culture_id = Column(String, ForeignKey("cultures.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Dates
    date_debut = Column(Date, nullable=False)
    date_fin = Column(Date, nullable=True)
    
    # Quantités
    poids_frais = Column(Float, nullable=False)  # kg
    poids_sec = Column(Float, nullable=True)  # kg
    humidite = Column(Float, nullable=True)  # %
    
    # Qualité
    qualite = Column(Enum(QualiteRecolte), default=QualiteRecolte.MOYENNE)
    taux_gousses_vides = Column(Float, default=0)  # %
    taux_gousses_abimees = Column(Float, default=0)  # %
    taux_impuretes = Column(Float, default=0)  # %
    
    # Échantillonnage
    poids_100_gousses = Column(Float, nullable=True)  # g
    poids_100_graines = Column(Float, nullable=True)  # g
    nb_gousses_par_plant = Column(Integer, nullable=True)  # Moyenne
    
    # Métadonnées
    nb_sacs = Column(Integer, nullable=True)
    observations = Column(Text, nullable=True)
    photos = Column(JSON, default=[])
    
    # Rendement calculé
    rendement_kg_ha = Column(Float, nullable=True)  # kg/ha
    
    # Relations
    culture = relationship("Culture", back_populates="recolte")
    lots = relationship("Lot", back_populates="recolte_origine", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Recolte {self.code} - {self.poids_sec} kg>"
    
    @property
    def perte_poids(self) -> float:
        """Calcule la perte de poids après séchage (%)"""
        if self.poids_frais and self.poids_sec:
            return ((self.poids_frais - self.poids_sec) / self.poids_frais) * 100
        return 0
    
    @property
    def qualite_note(self) -> int:
        """Retourne une note de qualité (1-10)"""
        notes = {
            QualiteRecolte.EXCELLENTE: 9,
            QualiteRecolte.BONNE: 7,
            QualiteRecolte.MOYENNE: 5,
            QualiteRecolte.MAUVAISE: 2
        }
        return notes.get(self.qualite, 5)
    
    def calculer_rendement(self, superficie_ha: float) -> float:
        """Calcule le rendement en kg/ha"""
        if superficie_ha > 0 and self.poids_sec:
            self.rendement_kg_ha = self.poids_sec / superficie_ha
        elif superficie_ha > 0 and self.poids_frais:
            self.rendement_kg_ha = self.poids_frais / superficie_ha
        else:
            self.rendement_kg_ha = 0
        return self.rendement_kg_ha
    
    def generate_code(self):
        """Génère un code unique pour la récolte"""
        import uuid
        self.code = f"REC-{uuid.uuid4().hex[:8].upper()}"