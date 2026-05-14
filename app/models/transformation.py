"""
Modèle Transformation - Transformation des produits (huile, savon).
"""
from sqlalchemy import Column, String, Date, Float, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import json

from .base import BaseModel
from .enums import TypeTransformation


class Transformation(BaseModel):
    """
    Transformation d'arachide en huile ou savon.
    """
    __tablename__ = "transformations"
    
    # Type de transformation
    type = Column(Enum(TypeTransformation), nullable=False)
    
    # Lots
    lot_entree_id = Column(String, ForeignKey("lots.id"), nullable=False)
    lot_sortie_id = Column(String, ForeignKey("lots.id"), nullable=True)
    
    # Dates
    date_transformation = Column(Date, nullable=False)
    responsable_id = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Quantités
    quantite_entree = Column(Float, nullable=False)
    quantite_sortie = Column(Float, nullable=True)
    rendement = Column(Float, nullable=True)  # %
    
    # Recette (pour savon) - stockée comme JSON
    recette = Column(JSON, default=dict)  # <-- Utiliser dict au lieu de {}
    
    # Métadonnées
    observations = Column(Text, nullable=True)
    
    # Relations
    lot_entree = relationship("Lot", foreign_keys=[lot_entree_id], back_populates="transformations_entree")
    lot_sortie = relationship("Lot", foreign_keys=[lot_sortie_id], back_populates="transformations_sortie")
    responsable = relationship("User", back_populates="transformations")
    
    def __repr__(self):
        return f"<Transformation {self.type} - Rendement {self.rendement}%>"
    
    def calculer_rendement(self):
        """Calcule le rendement en pourcentage."""
        if self.quantite_entree and self.quantite_sortie and self.quantite_entree > 0:
            self.rendement = (self.quantite_sortie / self.quantite_entree) * 100
        else:
            self.rendement = 0
        return self.rendement
    
    def calculer_quantite_savon(self, huile_l: float, surgraissage: float = 5) -> dict:
        """
        Calcule les quantités nécessaires pour la fabrication de savon.
        
        Args:
            huile_l: Quantité d'huile en litres
            surgraissage: Pourcentage de surgraissage (défaut 5%)
        
        Returns:
            dict: Quantités de soude, eau, et nombre de savons
        """
        # Densité de l'huile d'arachide ~0.92 kg/L
        huile_kg = huile_l * 0.92
        
        # Indice de saponification de l'huile d'arachide ~0.136
        soude_necessaire = huile_kg * 0.136 * (1 - surgraissage / 100)
        
        # Eau: 25-30% du poids de l'huile
        eau_necessaire = huile_kg * 0.28
        
        # Nombre de savons (poids moyen 100g)
        poids_total = huile_kg + soude_necessaire + eau_necessaire
        nb_savons = int(poids_total / 0.1)  # 100g par savon
        
        return {
            "huile_kg": round(huile_kg, 2),
            "soude_kg": round(soude_necessaire, 2),
            "eau_kg": round(eau_necessaire, 2),
            "poids_total": round(poids_total, 2),
            "nb_savons": nb_savons,
            "surgraissage": surgraissage
        }
    
    def set_recette(self, recette_data: dict):
        """
        Définit la recette en s'assurant qu'elle est correctement sérialisée.
        """
        self.recette = recette_data
    
    def get_recette(self) -> dict:
        """
        Récupère la recette comme dictionnaire.
        """
        if isinstance(self.recette, str):
            try:
                return json.loads(self.recette)
            except:
                return {}
        return self.recette or {}