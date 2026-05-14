"""
Modèle Lot - Lots de produits traçables.
"""
from sqlalchemy import Column, String, Date, Float, Enum, ForeignKey, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, date
import uuid

from .base import BaseModel
from .enums import TypeLot


class Lot(BaseModel):
    """
    Lot de produits traçable (arachide brute, décortiquée, huile, savon).
    """
    __tablename__ = "lots"
    
    # Code unique traçable
    code = Column(String, unique=True, nullable=False, index=True)
    
    # Type de lot
    type = Column(Enum(TypeLot), nullable=False)
    
    # Origine (si arachide brute)
    recolte_id = Column(String, ForeignKey("recoltes.id"), nullable=True)
    parcelle_source = Column(String, ForeignKey("parcelles.id"), nullable=True)
    
    # Quantités
    quantite_initiale = Column(Float, nullable=False)
    quantite_restante = Column(Float, nullable=False)
    unite = Column(String, nullable=False)  # kg, L, piece
    
    # Dates
    date_production = Column(Date, nullable=False)
    date_peremption = Column(Date, nullable=True)
    
    # Qualité
    qualite = Column(String, nullable=True)
    certificats = Column(JSON, default=[])
    
    # Traçabilité
    est_transformable = Column(Boolean, default=True)
    est_vendu = Column(Boolean, default=False)
    est_epuise = Column(Boolean, default=False)
    
    # Métadonnées
    notes = Column(Text, nullable=True)
    
    # Relations
    recolte_origine = relationship("Recolte", back_populates="lots")
    parcelle = relationship("Parcelle")
    
    transformations_entree = relationship(
        "Transformation", 
        foreign_keys="Transformation.lot_entree_id", 
        back_populates="lot_entree"
    )
    transformations_sortie = relationship(
        "Transformation", 
        foreign_keys="Transformation.lot_sortie_id", 
        back_populates="lot_sortie"
    )
    stocks = relationship("Stock", back_populates="lot", cascade="all, delete-orphan")
    ventes = relationship("Vente", back_populates="lot")
    
    def __repr__(self):
        return f"<Lot {self.code} - {self.type}>"
    
    @property
    def quantite_utilisee(self) -> float:
        """Quantité déjà utilisée (transformée ou vendue)."""
        return self.quantite_initiale - self.quantite_restante
    
    @property
    def taux_utilisation(self) -> float:
        """Taux d'utilisation en pourcentage."""
        if self.quantite_initiale > 0:
            return (self.quantite_utilisee / self.quantite_initiale) * 100
        return 0
    
    @property
    def est_disponible(self) -> bool:
        """Vérifie si le lot est disponible."""
        return not self.est_vendu and not self.est_epuise and self.quantite_restante > 0
    
    @property
    def origine_complete(self) -> dict:
        """Retourne l'origine complète du lot."""
        origine = {
            "code": self.code,
            "type": self.type,
            "date_production": self.date_production
        }
        
        if self.recolte_origine:
            origine["recolte"] = {
                "id": self.recolte_origine.id,
                "date_debut": self.recolte_origine.date_debut,
                "poids_frais": self.recolte_origine.poids_frais,
                "poids_sec": self.recolte_origine.poids_sec,
                "qualite": self.recolte_origine.qualite
            }
            
            if self.recolte_origine.culture:
                origine["culture"] = {
                    "id": self.recolte_origine.culture.id,
                    "variete": self.recolte_origine.culture.variete,
                    "date_debut": self.recolte_origine.culture.date_debut,
                    "date_fin": self.recolte_origine.culture.date_fin_reelle
                }
                
                if self.recolte_origine.culture.parcelle:
                    origine["parcelle"] = {
                        "id": self.recolte_origine.culture.parcelle.id,
                        "nom": self.recolte_origine.culture.parcelle.nom,
                        "type": self.recolte_origine.culture.parcelle.type,
                        "superficie": self.recolte_origine.culture.parcelle.superficie
                    }
                    
                    if self.recolte_origine.culture.parcelle.proprietaire:
                        origine["producteur"] = {
                            "id": self.recolte_origine.culture.parcelle.proprietaire.id,
                            "nom": self.recolte_origine.culture.parcelle.proprietaire.nom,
                            "prenom": self.recolte_origine.culture.parcelle.proprietaire.prenom,
                            "email": self.recolte_origine.culture.parcelle.proprietaire.email
                        }
        
        return origine
    
    def generer_code(self):
        """Génère un code unique pour le lot."""
        # Format: TYPE-AAAAMMJJ-XXX
        prefix = self.type.value.upper() if hasattr(self.type, 'value') else str(self.type).upper()
        date_str = self.date_production.strftime("%Y%m%d")
        # Générer un numéro séquentiel simple (à améliorer avec compteur)
        import uuid
        suffix = uuid.uuid4().hex[:3].upper()
        self.code = f"{prefix}-{date_str}-{suffix}"
    
    def reduire_stock(self, quantite: float):
        """Réduit la quantité du lot."""
        if quantite > self.quantite_restante:
            raise ValueError(f"Quantité insuffisante. Restant: {self.quantite_restante}")
        
        self.quantite_restante -= quantite
        
        if self.quantite_restante <= 0:
            self.quantite_restante = 0
            self.est_epuise = True
    
    def ajouter_stock(self, quantite: float):
        """Ajoute de la quantité au lot."""
        self.quantite_restante += quantite
        if self.est_epuise:
            self.est_epuise = False