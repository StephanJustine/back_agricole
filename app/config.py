# from pydantic_settings import BaseSettings
# from typing import Optional, List

# class Settings(BaseSettings):
#     # ========================
#     # MODE
#     # ========================
#     DEBUG: bool = False

#     # ========================
#     # BASE DE DONNÉES
#     # ========================
#     DATABASE_URL: str  # obligatoire depuis .env

#     # (optionnel si tu veux fallback)
#     POSTGRES_SERVER: Optional[str] = None
#     POSTGRES_USER: Optional[str] = None
#     POSTGRES_PASSWORD: Optional[str] = None
#     POSTGRES_DB: Optional[str] = None
#     POSTGRES_PORT: Optional[int] = 5432

#     # ========================
#     # SÉCURITÉ
#     # ========================
#     SECRET_KEY: str
#     ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
#     REFRESH_TOKEN_EXPIRE_DAYS: int = 7

#     # ========================
#     # CORS
#     # ========================
#     BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

#     # ========================
#     # EMAIL
#     # ========================
#     MAIL_USERNAME: Optional[str] = None
#     MAIL_PASSWORD: Optional[str] = None
#     MAIL_FROM: str
#     MAIL_PORT: int = 587
#     MAIL_SERVER: str = "smtp.gmail.com"
#     MAIL_TLS: bool = True

#     # ========================
#     # FRONTEND
#     # ========================
#     FRONTEND_URL: str = "http://localhost:3000"

#     # ========================
#     # API
#     # ========================
#     API_V1_PREFIX: str = "/api/v1"
#     PROJECT_NAME: str = "Filiere Arachide API"
#     VERSION: str = "1.0.0"

#     class Config:
#         env_file = ".env"
#         case_sensitive = True

#     # ========================
#     # DATABASE URI (fallback auto)
#     # ========================
#     @property
#     def database_uri(self) -> str:
#         if self.DATABASE_URL:
#             return self.DATABASE_URL

#         return (
#             f"postgresql+psycopg2://{self.POSTGRES_USER}:"
#             f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:"
#             f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
#         )


# settings = Settings()


from pydantic_settings import BaseSettings
from typing import Optional, List
import secrets


class Settings(BaseSettings):
    # ========================
    # MODE
    # ========================
    DEBUG: bool = False

    # ========================
    # BASE DE DONNÉES
    # ========================
    DATABASE_URL: Optional[str] = None  # optionnel car on peut construire depuis postgres_*

    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_PORT: Optional[int] = 5432

    # ========================
    # SÉCURITÉ
    # ========================
    SECRET_KEY: str = secrets.token_urlsafe(32)  # généré automatiquement si absent
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ========================
    # CORS
    # ========================
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]

    # ========================
    # EMAIL CONFIGURATION
    # ========================
    # Serveur SMTP Gmail
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_USERNAME: str = "stephanson.stp@gmail.com"  # Votre email Gmail
    MAIL_PASSWORD: str = "bins eqpm ndmy uazz"  # Mot de passe d'application Gmail (à configurer)
    MAIL_FROM: str = "stephanson.stp@gmail.com"
    MAIL_FROM_NAME: str = "Application Agricole"
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    MAIL_USE_CREDENTIALS: bool = True
    MAIL_TIMEOUT: int = 30

    # URLs pour les liens dans les emails
    FRONTEND_URL: str = "http://localhost:3000"  # URL de votre frontend
    BACKEND_URL: str = "http://localhost:8000"   # URL de votre backend

    # ========================
    # API
    # ========================
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Filiere Arachide API"
    VERSION: str = "1.0.0"

    # ========================
    # ADMIN PAR DÉFAUT
    # ========================
    DEFAULT_ADMIN_EMAIL: str = "stephanson.stp@gmail.com"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"
    DEFAULT_ADMIN_NOM: str = "admin"
    DEFAULT_ADMIN_PRENOM: str = "System"
    DEFAULT_ADMIN_TELEPHONE: str = "0340000000"
    CREATE_DEFAULT_ADMIN: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # ignore les champs supplémentaires dans .env

    # ========================
    # DATABASE URI (fallback auto)
    # ========================
    @property
    def database_uri(self) -> str:
        """Retourne l'URI de connexion à la base de données."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        # Construction depuis les paramètres PostgreSQL
        if all([self.POSTGRES_USER, self.POSTGRES_PASSWORD, self.POSTGRES_SERVER, self.POSTGRES_DB]):
            return (
                f"postgresql://{self.POSTGRES_USER}:"
                f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:"
                f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        
        # Fallback vers SQLite en développement
        if self.DEBUG:
            return "sqlite:///./arachide.db"
        
        raise ValueError("Aucune configuration de base de données valide")

    # ========================
    # PROPRIÉTÉS UTILES
    # ========================
    @property
    def is_email_configured(self) -> bool:
        """Vérifie si l'email est correctement configuré."""
        return bool(self.MAIL_USERNAME and self.MAIL_PASSWORD and self.MAIL_FROM)
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Retourne la liste des origines CORS."""
        return self.BACKEND_CORS_ORIGINS


# Instance globale des settings
settings = Settings()


# Fonction pour valider la configuration au démarrage
def validate_settings():
    """Valide la configuration et affiche des avertissements."""
    import logging
    logger = logging.getLogger(__name__)
    
    if not settings.is_email_configured:
        logger.warning("⚠️ EMAIL NON CONFIGURÉ: Les emails de réinitialisation ne fonctionneront pas")
        logger.warning("   Configurez MAIL_USERNAME et MAIL_PASSWORD dans .env")
    
    if settings.DEBUG:
        logger.info("🔧 Mode DEBUG activé")
        logger.info(f"📧 Email configuré: {settings.is_email_configured}")
        logger.info(f"🗄️ Base de données: {settings.database_uri}")
    
    return settings