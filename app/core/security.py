# """
# Service de sécurité (hash, JWT, tokens).
# """
# from datetime import datetime, timedelta
# from typing import Optional, Dict, Any
# from jose import JWTError, jwt
# from passlib.context import CryptContext
# import secrets
# import string

# from ..config import settings

# # Configuration de passlib avec bcrypt
# pwd_context = CryptContext(
#     schemes=["bcrypt"],
#     deprecated="auto",
#     bcrypt__rounds=12  # Nombre de rounds pour le hash
# )


# class SecurityService:
#     """Service de sécurité (hash, JWT, tokens)"""
    
#     @staticmethod
#     def verify_password(plain_password: str, hashed_password: str) -> bool:
#         """Vérifie un mot de passe."""
#         try:
#             return pwd_context.verify(plain_password, hashed_password)
#         except Exception as e:
#             print(f"Erreur lors de la vérification du mot de passe: {e}")
#             return False
    
#     @staticmethod
#     def get_password_hash(password: str) -> str:
#         """Hash un mot de passe."""
#         # Tronquer le mot de passe à 72 caractères si nécessaire (limite bcrypt)
#         if len(password) > 72:
#             password = password[:72]
#         return pwd_context.hash(password)
    
#     @staticmethod
#     def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
#         """Crée un token d'accès JWT."""
#         to_encode = data.copy()
#         if expires_delta:
#             expire = datetime.utcnow() + expires_delta
#         else:
#             expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
#         to_encode.update({"exp": expire, "type": "access"})
#         encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
#         return encoded_jwt
    
#     @staticmethod
#     def create_refresh_token(data: Dict[str, Any]) -> str:
#         """Crée un token de rafraîchissement."""
#         to_encode = data.copy()
#         expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
#         to_encode.update({"exp": expire, "type": "refresh"})
#         encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
#         return encoded_jwt
    
#     @staticmethod
#     def decode_token(token: str) -> Optional[Dict[str, Any]]:
#         """Décode un token JWT."""
#         try:
#             payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
#             return payload
#         except JWTError:
#             return None
    
#     @staticmethod
#     def generate_reset_token() -> str:
#         """Génère un token pour réinitialisation de mot de passe."""
#         return secrets.token_urlsafe(32)
    
#     @staticmethod
#     def generate_verification_token() -> str:
#         """Génère un token pour vérification email."""
#         return secrets.token_urlsafe(32)
    
#     @staticmethod
#     def generate_temp_password(length: int = 12) -> str:
#         """Génère un mot de passe temporaire."""
#         alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
#         return ''.join(secrets.choice(alphabet) for _ in range(length))


"""
Service de sécurité (hash, JWT, tokens).
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
import string

from ..config import settings

# Configuration de passlib avec bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Nombre de rounds pour le hash
)


class SecurityService:
    """Service de sécurité (hash, JWT, tokens)"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Vérifie un mot de passe."""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            print(f"Erreur lors de la vérification du mot de passe: {e}")
            return False
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash un mot de passe."""
        # Tronquer le mot de passe à 72 caractères si nécessaire (limite bcrypt)
        if len(password) > 72:
            password = password[:72]
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Crée un token d'accès JWT."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Crée un token de rafraîchissement."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """Décode un token JWT."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def generate_reset_token() -> str:
        """Génère un token pour réinitialisation de mot de passe."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_verification_token() -> str:
        """Génère un token pour vérification email."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_temp_password(length: int = 12) -> str:
        """Génère un mot de passe temporaire."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))