"""
Script d'initialisation de l'administrateur par défaut.
"""
from sqlalchemy.orm import Session
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def init_admin_user(db: Session = None):
    """
    Initialise l'utilisateur administrateur par défaut.
    
    Args:
        db: Session de base de données (optionnel, créée automatiquement si None)
    """
    from app.database import SessionLocal
    from app.models.user import User
    from app.models.enums import UserRole
    from app.core.security import SecurityService
    
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    
    try:
        # Vérifier si un administrateur existe déjà
        admin = db.query(User).filter(
            User.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN])
        ).first()
        
        if admin:
            logger.info(f"✅ Administrateur déjà existant: {admin.email}")
            return
        
        # Vérifier si l'utilisateur spécifique existe
        user = db.query(User).filter(User.email == "stephanson.stp@gmail.com").first()
        
        if user:
            # Mettre à jour l'utilisateur existant en admin
            user.role = UserRole.SUPER_ADMIN
            user.is_verified = True
            db.commit()
            logger.info(f"✅ Utilisateur {user.email} promu administrateur")
            return
        
        # Mot de passe (tronqué à 72 caractères pour bcrypt)
        password = "admin123"
        if len(password) > 72:
            password = password[:72]
        
        # Créer l'administrateur par défaut
        admin = User(
            email="stephanson.stp@gmail.com",
            nom="admin",
            prenom="System",
            telephone="0340000000",
            role=UserRole.SUPER_ADMIN,
            hashed_password=SecurityService.get_password_hash(password),
            is_active=True,
            is_verified=True,
            date_inscription=datetime.utcnow()
        )
        
        db.add(admin)
        db.commit()
        
        logger.info("=" * 60)
        logger.info("✅ ADMINISTRATEUR CRÉÉ AVEC SUCCÈS !")
        logger.info(f"📧 Email: {admin.email}")
        logger.info(f"🔑 Mot de passe: admin123")
        role_value = admin.role.value if hasattr(admin.role, 'value') else admin.role
        logger.info(f"👤 Rôle: {role_value}")
        logger.info("⚠️  IMPORTANT: Changez ce mot de passe après la première connexion !")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création de l'administrateur: {e}")
        if close_db:
            db.rollback()
    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    # Configuration des logs pour l'exécution directe
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    init_admin_user()