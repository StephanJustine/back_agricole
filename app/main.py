# """
# Point d'entrée principal de l'application FastAPI.
# """
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# import logging

# from .config import settings
# from .database import engine, Base  # Import Base depuis database.py
# from .api.api import api_router
# # from .scripts.init_admin import init_admin_user
# from .init_admin import init_admin_user

# # Configuration des logs
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Création des tables (en développement uniquement)
# if settings.DEBUG:
#     Base.metadata.create_all(bind=engine)
#     logger.info("Tables créées avec succès")

# # Initialisation de l'administrateur
# logger.info("🔧 Vérification de l'administrateur par défaut...")
# init_admin_user()

# # Création de l'application FastAPI
# app = FastAPI(
#     title=settings.PROJECT_NAME,
#     version=settings.VERSION,
#     openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
#     docs_url="/docs",
#     redoc_url="/redoc",
# )

# # Configuration CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.BACKEND_CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Inclusion des routes
# app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# @app.get("/")
# async def root():
#     """
#     Route racine.
#     """
#     return {
#         "message": "Bienvenue sur l'API Filière Arachide",
#         "version": settings.VERSION,
#         "docs": "/docs",
#         "redoc": "/redoc"
#     }


# @app.get("/health")
# async def health_check():
#     """
#     Vérification de l'état de l'API.
#     """
#     return {
#         "status": "healthy",
#         "database": "connected"
#     }

"""
Point d'entrée principal de l'application FastAPI.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os

from .config import settings
from .database import engine, Base
from .api.api import api_router

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ========================
# FONCTION D'INITIALISATION DE L'ADMIN
# ========================
def init_admin_user():
    """
    Initialise l'utilisateur administrateur par défaut.
    """
    try:
        from sqlalchemy.orm import Session
        from .database import SessionLocal
        from .models.user import User
        from .models.enums import UserRole
        from .core.security import SecurityService
        from datetime import datetime
        
        db: Session = SessionLocal()
        
        try:
            # Vérifier si un administrateur existe déjà
            admin = db.query(User).filter(
                User.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN])
            ).first()
            
            if admin:
                logger.info(f"✅ Administrateur déjà existant: {admin.email}")
                return
            
            # Vérifier si l'utilisateur spécifique existe
            user = db.query(User).filter(User.email == settings.DEFAULT_ADMIN_EMAIL).first()
            
            if user:
                # Mettre à jour l'utilisateur existant en admin
                user.role = UserRole.SUPER_ADMIN
                user.is_verified = True
                db.commit()
                logger.info(f"✅ Utilisateur {user.email} promu administrateur")
                return
            
            # Créer l'administrateur par défaut
            admin = User(
                email=settings.DEFAULT_ADMIN_EMAIL,
                nom=settings.DEFAULT_ADMIN_NOM,
                prenom=settings.DEFAULT_ADMIN_PRENOM,
                telephone=settings.DEFAULT_ADMIN_TELEPHONE,
                role=UserRole.SUPER_ADMIN,
                hashed_password=SecurityService.get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
                is_active=True,
                is_verified=True,
                date_inscription=datetime.utcnow()
            )
            
            db.add(admin)
            db.commit()
            
            logger.info("=" * 60)
            logger.info("✅ ADMINISTRATEUR CRÉÉ AVEC SUCCÈS !")
            logger.info(f"📧 Email: {admin.email}")
            logger.info(f"🔑 Mot de passe: {settings.DEFAULT_ADMIN_PASSWORD}")
            logger.info(f"👤 Rôle: {admin.role}")
            logger.info("⚠️  IMPORTANT: Changez ce mot de passe après la première connexion !")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création de l'administrateur: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation de l'admin: {e}")


# ========================
# CRÉATION DES TABLES
# ========================
logger.info("🔧 Création des tables de la base de données...")

try:
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tables créées avec succès")
except Exception as e:
    logger.error(f"❌ Erreur lors de la création des tables: {e}")
    sys.exit(1)


# ========================
# INITIALISATION DE L'ADMIN
# ========================
if settings.CREATE_DEFAULT_ADMIN:
    logger.info("🔧 Vérification de l'administrateur par défaut...")
    init_admin_user()
else:
    logger.info("ℹ️ Création automatique de l'admin désactivée")


# ========================
# CRÉATION DE L'APPLICATION FASTAPI
# ========================
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# ========================
# ROUTES DE BASE
# ========================
@app.get("/")
async def root():
    """
    Route racine.
    """
    return {
        "message": "Bienvenue sur l'API Filière Arachide",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Vérification de l'état de l'API.
    """
    try:
        # Vérifier la connexion à la base de données
        from sqlalchemy import text
        from .database import SessionLocal
        
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "connected"
    except Exception as e:
        logger.error(f"Erreur base de données: {e}")
        db_status = "error"
    
    return {
        "status": "healthy",
        "database": db_status,
        "version": settings.VERSION
    }


# ========================
# ÉVÉNEMENTS DE DÉMARRAGE/ARRÊT
# ========================
@app.on_event("startup")
async def startup_event():
    """
    Événement exécuté au démarrage de l'application.
    """
    logger.info("🚀 Démarrage de l'application...")
    logger.info(f"📡 API Version: {settings.VERSION}")
    logger.info(f"🔧 Mode DEBUG: {settings.DEBUG}")
    logger.info(f"🗄️ Base de données: {settings.database_uri.split('@')[-1] if '@' in settings.database_uri else settings.database_uri}")
    logger.info(f"📧 Email configuré: {settings.is_email_configured}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Événement exécuté à l'arrêt de l'application.
    """
    logger.info("👋 Arrêt de l'application...")