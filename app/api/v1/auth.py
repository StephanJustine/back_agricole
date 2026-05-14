# """
# Routes d'authentification.
# """
# from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
# from fastapi.security import OAuth2PasswordRequestForm
# from fastapi.responses import JSONResponse
# from fastapi.exceptions import RequestValidationError
# from sqlalchemy.orm import Session
# from datetime import datetime, timedelta
# import logging
# import traceback

# from ...database import get_db
# from ...models.user import User
# from ...models.session import UserSession
# from ...schemas.auth import (
#     LoginRequest, LoginResponse, 
#     RefreshTokenRequest, RefreshTokenResponse,
#     ForgotPasswordRequest, ForgotPasswordResponse,
#     ResetPasswordRequest, ChangePasswordRequest,
#     VerifyEmailRequest, VerifyEmailResponse
# )
# from ...schemas.user import UserCreate, UserResponse
# from ...core.security import SecurityService
# from ...core.email import EmailService
# from ...core.dependencies import get_current_user
# from ...config import settings

# logger = logging.getLogger(__name__)
# router = APIRouter()


# # ROUTE LOGIN POUR SWAGGER UI (OAuth2 - form data)
# @router.post("/login", response_model=LoginResponse)
# async def login_oauth2(
#     form_data: OAuth2PasswordRequestForm = Depends(),
#     db: Session = Depends(get_db)
# ):
#     """
#     Connexion utilisateur (compatible OAuth2 pour Swagger UI).
#     Utilise form data: username et password.
#     """
#     try:
#         logger.info(f"=== TENTATIVE DE CONNEXION (OAuth2) ===")
#         logger.info(f"Username reçu: {form_data.username}")
#         logger.info(f"Password reçu: {'*' * len(form_data.password) if form_data.password else 'None'}")
        
#         # Vérifier que les données sont valides
#         if not form_data.username or not form_data.password:
#             logger.warning("Email ou mot de passe vide")
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Email et mot de passe requis"
#             )
        
#         # Récupérer l'utilisateur
#         user = db.query(User).filter(User.email == form_data.username).first()
        
#         if not user:
#             logger.warning(f"Utilisateur non trouvé: {form_data.username}")
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Email ou mot de passe incorrect"
#             )
        
#         logger.info(f"Utilisateur trouvé: {user.email}")
#         logger.info(f"Rôle: {user.role}")
#         logger.info(f"Actif: {user.is_active}")
#         logger.info(f"Vérifié: {user.is_verified}")
        
#         # Vérifier le mot de passe
#         try:
#             password_valid = SecurityService.verify_password(form_data.password, user.hashed_password)
#             logger.info(f"Mot de passe valide: {password_valid}")
#         except Exception as e:
#             logger.error(f"Erreur lors de la vérification du mot de passe: {e}")
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Erreur lors de la vérification du mot de passe"
#             )
        
#         if not password_valid:
#             logger.warning(f"Mot de passe incorrect pour: {form_data.username}")
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Email ou mot de passe incorrect"
#             )
        
#         if not user.is_active:
#             logger.warning(f"Compte désactivé: {form_data.username}")
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Compte désactivé"
#             )
        
#         if not user.is_verified:
#             logger.warning(f"Email non vérifié: {form_data.username}")
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Veuillez vérifier votre email avant de vous connecter"
#             )
        
#         # Mettre à jour la dernière connexion
#         user.derniere_connexion = datetime.utcnow()
        
#         # Créer les tokens
#         access_token = SecurityService.create_access_token({"sub": user.id})
#         refresh_token = SecurityService.create_refresh_token({"sub": user.id})
        
#         # Sauvegarder le refresh token
#         user.refresh_token = refresh_token
        
#         # Créer la session
#         expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES
#         session = UserSession(
#             user_id=user.id,
#             token=access_token,
#             refresh_token=refresh_token,
#             expires_at=datetime.utcnow() + timedelta(minutes=expires_in)
#         )
#         db.add(session)
#         db.commit()
        
#         logger.info(f"Connexion réussie: {user.email}")
        
#         # Retourner la réponse OAuth2 compatible
#         return {
#             "access_token": access_token,
#             "refresh_token": refresh_token,
#             "token_type": "bearer",
#             "expires_in": expires_in * 60,
#             "user": {
#                 "id": user.id,
#                 "email": user.email,
#                 "nom": user.nom,
#                 "prenom": user.prenom,
#                 "telephone": user.telephone,
#                 "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
#                 "is_active": user.is_active,
#                 "is_verified": user.is_verified,
#                 "date_inscription": user.date_inscription.isoformat() if user.date_inscription else None,
#                 "photo_url": user.photo_url
#             }
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Erreur inattendue lors de la connexion: {e}")
#         logger.error(traceback.format_exc())
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur interne: {str(e)}"
#         )


# # ROUTE LOGIN JSON (pour les appels API normaux)
# # @router.post("/login-json", response_model=LoginResponse)
# # async def login_json(
# #     request: LoginRequest,
# #     db: Session = Depends(get_db)
# # ):
# #     """
# #     Connexion utilisateur avec JSON.
# #     """
# #     try:
# #         logger.info(f"=== TENTATIVE DE CONNEXION (JSON) ===")
# #         logger.info(f"Email reçu: {request.email}")
        
# #         # Récupérer l'utilisateur
# #         user = db.query(User).filter(User.email == request.email).first()
        
# #         if not user or not SecurityService.verify_password(request.password, user.hashed_password):
# #             raise HTTPException(
# #                 status_code=status.HTTP_401_UNAUTHORIZED,
# #                 detail="Email ou mot de passe incorrect"
# #             )
        
# #         if not user.is_active:
# #             raise HTTPException(
# #                 status_code=status.HTTP_401_UNAUTHORIZED,
# #                 detail="Compte désactivé"
# #             )
        
# #         if not user.is_verified:
# #             raise HTTPException(
# #                 status_code=status.HTTP_401_UNAUTHORIZED,
# #                 detail="Veuillez vérifier votre email avant de vous connecter"
# #             )
        
# #         # Mettre à jour la dernière connexion
# #         user.derniere_connexion = datetime.utcnow()
        
# #         # Créer les tokens
# #         access_token = SecurityService.create_access_token({"sub": user.id})
# #         refresh_token = SecurityService.create_refresh_token({"sub": user.id})
        
# #         # Sauvegarder le refresh token
# #         user.refresh_token = refresh_token
        
# #         # Créer la session
# #         expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES
# #         session = UserSession(
# #             user_id=user.id,
# #             token=access_token,
# #             refresh_token=refresh_token,
# #             expires_at=datetime.utcnow() + timedelta(minutes=expires_in)
# #         )
# #         db.add(session)
# #         db.commit()
        
# #         logger.info(f"Connexion réussie: {user.email}")
        
# #         # Construire la réponse
# #         user_dict = {
# #             "id": user.id,
# #             "email": user.email,
# #             "nom": user.nom,
# #             "prenom": user.prenom,
# #             "telephone": user.telephone,
# #             "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
# #             "is_active": user.is_active,
# #             "is_verified": user.is_verified,
# #             "date_inscription": user.date_inscription.isoformat() if user.date_inscription else None,
# #             "photo_url": user.photo_url
# #         }
        
# #         return LoginResponse(
# #             access_token=access_token,
# #             refresh_token=refresh_token,
# #             expires_in=expires_in * 60,
# #             user=user_dict
# #         )
        
# #     except HTTPException:
# #         raise
# #     except Exception as e:
# #         logger.error(f"Erreur inattendue: {e}")
# #         raise HTTPException(
# #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
# #             detail=f"Erreur interne: {str(e)}"
# #         )


# # # ROUTE D'INSCRIPTION (décommentée)
# # @router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
# # async def register(
# #     request: UserCreate,
# #     db: Session = Depends(get_db)
# # ):
# #     """
# #     Inscription d'un nouvel utilisateur.
# #     """
# #     try:
# #         # Vérifier si l'email existe déjà
# #         existing = db.query(User).filter(User.email == request.email).first()
# #         if existing:
# #             raise HTTPException(
# #                 status_code=status.HTTP_400_BAD_REQUEST,
# #                 detail="Cet email est déjà utilisé"
# #             )
        
# #         # Vérifier si le téléphone existe déjà
# #         existing_phone = db.query(User).filter(User.telephone == request.telephone).first()
# #         if existing_phone:
# #             raise HTTPException(
# #                 status_code=status.HTTP_400_BAD_REQUEST,
# #                 detail="Ce numéro de téléphone est déjà utilisé"
# #             )
        
# #         # Générer le token de vérification
# #         verification_token = SecurityService.generate_verification_token()
        
# #         # Créer l'utilisateur
# #         user = User(
# #             email=request.email,
# #             nom=request.nom,
# #             prenom=request.prenom,
# #             telephone=request.telephone,
# #             role=request.role,
# #             hashed_password=SecurityService.get_password_hash(request.password),
# #             verification_token=verification_token,
# #             verification_expires=datetime.utcnow() + timedelta(days=7),
# #             is_verified=False,
# #             date_inscription=datetime.utcnow()
# #         )
        
# #         db.add(user)
# #         db.commit()
# #         db.refresh(user)
        
# #         # Envoyer email de vérification
# #         await EmailService.send_verification_email(
# #             email=user.email,
# #             token=verification_token,
# #             nom=user.nom,
# #             prenom=user.prenom
# #         )
        
# #         logger.info(f"Nouvel utilisateur inscrit: {user.email}")
        
# #         return user
        
# #     except HTTPException:
# #         raise
# #     except Exception as e:
# #         logger.error(f"Erreur inscription: {e}")
# #         logger.error(traceback.format_exc())
# #         raise HTTPException(
# #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
# #             detail=f"Erreur interne: {str(e)}"
# #         )


# # ROUTE DE DÉCONNEXION
# @router.post("/logout")
# async def logout(
#     request: Request,
#     db: Session = Depends(get_db)
# ):
#     """
#     Déconnexion utilisateur.
#     """
#     try:
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Token non fourni"
#             )
        
#         token = auth_header.replace("Bearer ", "")
        
#         session = db.query(UserSession).filter(
#             UserSession.token == token,
#             UserSession.is_active == True
#         ).first()
        
#         if session:
#             session.is_active = False
#             session.is_revoked = True
#             db.commit()
#             logger.info("Déconnexion réussie")
        
#         return {"message": "Déconnexion réussie"}
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Erreur lors de la déconnexion: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur interne: {str(e)}"
#         )


# # ROUTE DE RAFRAÎCHISSEMENT TOKEN
# @router.post("/refresh", response_model=RefreshTokenResponse)
# async def refresh_token(
#     request: RefreshTokenRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     Rafraîchit le token d'accès.
#     """
#     try:
#         payload = SecurityService.decode_token(request.refresh_token)
#         if not payload or payload.get("type") != "refresh":
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Token de rafraîchissement invalide"
#             )
        
#         user_id = payload.get("sub")
#         if not user_id:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Token invalide"
#             )
        
#         user = db.query(User).filter(User.id == user_id).first()
#         if not user or user.refresh_token != request.refresh_token:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Token de rafraîchissement invalide"
#             )
        
#         if not user.is_active:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Compte désactivé"
#             )
        
#         # Créer un nouveau token d'accès
#         access_token = SecurityService.create_access_token({"sub": user.id})
#         expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        
#         return RefreshTokenResponse(
#             access_token=access_token,
#             expires_in=expires_in
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Erreur lors du rafraîchissement: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur interne: {str(e)}"
#         )


# # ROUTE MOT DE PASSE OUBLIÉ
# # @router.post("/forgot-password", response_model=ForgotPasswordResponse)
# # async def forgot_password(
# #     request: ForgotPasswordRequest,
# #     db: Session = Depends(get_db)
# # ):
# #     """
# #     Demande de réinitialisation de mot de passe.
# #     """
# #     try:
# #         user = db.query(User).filter(User.email == request.email).first()
        
# #         if not user:
# #             return ForgotPasswordResponse(
# #                 message="Si l'email existe, un lien de réinitialisation a été envoyé"
# #             )
        
# #         # Générer le token
# #         reset_token = SecurityService.generate_reset_token()
# #         user.reset_password_token = reset_token
# #         user.reset_password_expires = datetime.utcnow() + timedelta(hours=24)
# #         db.commit()
        
# #         # Envoyer l'email
# #         await EmailService.send_reset_password_email(
# #             email=user.email,
# #             token=reset_token,
# #             nom=user.nom,
# #             prenom=user.prenom
# #         )
        
# #         logger.info(f"Email de réinitialisation envoyé à {user.email}")
        
# #         return ForgotPasswordResponse(
# #             message="Si l'email existe, un lien de réinitialisation a été envoyé"
# #         )
        
# #     except Exception as e:
# #         logger.error(f"Erreur forgot_password: {e}")
# #         raise HTTPException(
# #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
# #             detail=f"Erreur interne: {str(e)}"
# #         )
# @router.post("/forgot-password", response_model=ForgotPasswordResponse)
# async def forgot_password(
#     request: ForgotPasswordRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     Demande de réinitialisation de mot de passe.
#     """
#     try:
#         user = db.query(User).filter(User.email == request.email).first()
        
#         if not user:
#             return ForgotPasswordResponse(
#                 message="Si l'email existe, un lien de réinitialisation a été envoyé"
#             )
        
#         # Générer le token
#         reset_token = SecurityService.generate_reset_token()
#         user.reset_password_token = reset_token
#         user.reset_password_expires = datetime.utcnow() + timedelta(hours=24)
#         db.commit()
        
#         # Envoyer l'email (sans await si la fonction n'est pas asynchrone)
#         EmailService.send_reset_password_email(
#             email=user.email,
#             token=reset_token,
#             nom=user.nom,
#             prenom=user.prenom
#         )
        
#         logger.info(f"Email de réinitialisation envoyé à {user.email}")
        
#         return ForgotPasswordResponse(
#             message="Si l'email existe, un lien de réinitialisation a été envoyé"
#         )
        
#     except Exception as e:
#         logger.error(f"Erreur forgot_password: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur interne: {str(e)}"
#         )

# # ROUTE RÉINITIALISATION MOT DE PASSE
# @router.post("/reset-password")
# async def reset_password(
#     request: ResetPasswordRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     Réinitialisation du mot de passe.
#     """
#     try:
#         user = db.query(User).filter(
#             User.reset_password_token == request.token,
#             User.reset_password_expires > datetime.utcnow()
#         ).first()
        
#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Token invalide ou expiré"
#             )
        
#         # Mettre à jour le mot de passe
#         user.hashed_password = SecurityService.get_password_hash(request.new_password)
#         user.reset_password_token = None
#         user.reset_password_expires = None
#         db.commit()
        
#         logger.info(f"Mot de passe réinitialisé pour {user.email}")
        
#         return {"message": "Mot de passe réinitialisé avec succès"}
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Erreur reset_password: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur interne: {str(e)}"
#         )


# # ROUTE CHANGEMENT MOT DE PASSE
# @router.post("/change-password")
# async def change_password(
#     request: ChangePasswordRequest,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Changement de mot de passe (utilisateur connecté).
#     """
#     try:
#         if not SecurityService.verify_password(request.current_password, current_user.hashed_password):
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Mot de passe actuel incorrect"
#             )
        
#         # Mettre à jour le mot de passe
#         current_user.hashed_password = SecurityService.get_password_hash(request.new_password)
#         db.commit()
        
#         logger.info(f"Mot de passe changé pour {current_user.email}")
        
#         return {"message": "Mot de passe changé avec succès"}
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Erreur change_password: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur interne: {str(e)}"
#         )


# # ROUTE VÉRIFICATION EMAIL
# @router.post("/verify-email", response_model=VerifyEmailResponse)
# async def verify_email(
#     request: VerifyEmailRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     Vérification de l'email.
#     """
#     try:
#         user = db.query(User).filter(
#             User.verification_token == request.token,
#             User.verification_expires > datetime.utcnow()
#         ).first()
        
#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Token invalide ou expiré"
#             )
        
#         user.is_verified = True
#         user.verification_token = None
#         user.verification_expires = None
#         db.commit()
        
#         logger.info(f"Email vérifié pour {user.email}")
        
#         return VerifyEmailResponse(
#             message="Email vérifié avec succès",
#             verified=True
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Erreur verify_email: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur interne: {str(e)}"
#         )


# # ROUTE RENVOI VÉRIFICATION EMAIL
# @router.post("/resend-verification")
# async def resend_verification(
#     email: str,
#     db: Session = Depends(get_db)
# ):
#     """
#     Renvoie l'email de vérification.
#     """
#     try:
#         user = db.query(User).filter(User.email == email).first()
        
#         if not user or user.is_verified:
#             return {"message": "Si l'email existe et n'est pas vérifié, un nouveau lien a été envoyé"}
        
#         # Générer un nouveau token
#         verification_token = SecurityService.generate_verification_token()
#         user.verification_token = verification_token
#         user.verification_expires = datetime.utcnow() + timedelta(days=7)
#         db.commit()
        
#         # Envoyer l'email
#         await EmailService.send_verification_email(
#             email=user.email,
#             token=verification_token,
#             nom=user.nom,
#             prenom=user.prenom
#         )
        
#         return {"message": "Un nouveau lien de vérification a été envoyé"}
        
#     except Exception as e:
#         logger.error(f"Erreur resend_verification: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur interne: {str(e)}"
#         )




"""
Routes d'authentification.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import traceback

from ...database import get_db
from ...models.user import User
from ...models.session import UserSession
from ...schemas.auth import (
    LoginRequest, LoginResponse, 
    RefreshTokenRequest, RefreshTokenResponse,
    ForgotPasswordRequest, ForgotPasswordResponse,
    ResetPasswordRequest, ChangePasswordRequest,
    VerifyEmailRequest, VerifyEmailResponse
)
from ...schemas.user import UserCreate, UserResponse
from ...core.security import SecurityService
from ...core.email import EmailService
from ...core.dependencies import get_current_user
from ...config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


# ROUTE LOGIN POUR SWAGGER UI (OAuth2 - form data)
@router.post("/login", response_model=LoginResponse)
async def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Connexion utilisateur (compatible OAuth2 pour Swagger UI).
    Utilise form data: username et password.
    """
    try:
        logger.info(f"=== TENTATIVE DE CONNEXION (OAuth2) ===")
        logger.info(f"Username reçu: {form_data.username}")
        
        # Vérifier que les données sont valides
        if not form_data.username or not form_data.password:
            logger.warning("Email ou mot de passe vide")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email et mot de passe requis"
            )
        
        # Récupérer l'utilisateur
        user = db.query(User).filter(User.email == form_data.username).first()
        
        if not user:
            logger.warning(f"Utilisateur non trouvé: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou mot de passe incorrect"
            )
        
        logger.info(f"Utilisateur trouvé: {user.email}")
        logger.info(f"Rôle: {user.role}")
        logger.info(f"Actif: {user.is_active}")
        logger.info(f"Vérifié: {user.is_verified}")
        
        # Vérifier le mot de passe
        try:
            password_valid = SecurityService.verify_password(form_data.password, user.hashed_password)
            logger.info(f"Mot de passe valide: {password_valid}")
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du mot de passe: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de la vérification du mot de passe"
            )
        
        if not password_valid:
            logger.warning(f"Mot de passe incorrect pour: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou mot de passe incorrect"
            )
        
        if not user.is_active:
            logger.warning(f"Compte désactivé: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Compte désactivé"
            )
        
        # Vérification email (optionnelle - commenter pour le développement)
        # if not user.is_verified:
        #     logger.warning(f"Email non vérifié: {form_data.username}")
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail="Veuillez vérifier votre email avant de vous connecter"
        #     )
        
        # Mettre à jour la dernière connexion
        user.derniere_connexion = datetime.utcnow()
        
        # Créer les tokens
        access_token = SecurityService.create_access_token({"sub": user.id, "email": user.email})
        refresh_token = SecurityService.create_refresh_token({"sub": user.id})
        
        # Sauvegarder le refresh token
        user.refresh_token = refresh_token
        
        # Créer la session
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        session = UserSession(
            user_id=user.id,
            token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(minutes=expires_in),
            created_at=datetime.utcnow(),
            is_active=True
        )
        db.add(session)
        db.commit()
        
        logger.info(f"Connexion réussie: {user.email}")
        
        # Retourner la réponse OAuth2 compatible
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "nom": user.nom,
                "prenom": user.prenom,
                "telephone": user.telephone,
                "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "date_inscription": user.date_inscription.isoformat() if user.date_inscription else None,
                "photo_url": getattr(user, 'photo_url', None)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la connexion: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


# ROUTE DE DÉCONNEXION
@router.post("/logout")
async def logout(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Déconnexion utilisateur.
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token non fourni"
            )
        
        token = auth_header.replace("Bearer ", "")
        
        session = db.query(UserSession).filter(
            UserSession.token == token,
            UserSession.is_active == True
        ).first()
        
        if session:
            session.is_active = False
            session.is_revoked = True
            session.revoked_at = datetime.utcnow()
            db.commit()
            logger.info("Déconnexion réussie")
        
        return {"message": "Déconnexion réussie"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la déconnexion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


# ROUTE MOT DE PASSE OUBLIÉ (CORRIGÉE)
@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Demande de réinitialisation de mot de passe.
    """
    try:
        user = db.query(User).filter(User.email == request.email).first()
        
        if not user:
            return ForgotPasswordResponse(
                message="Si l'email existe, un lien de réinitialisation a été envoyé"
            )
        # Générer le token
        reset_token = SecurityService.generate_reset_token()
        user.reset_password_token = reset_token
        user.reset_password_expires = datetime.utcnow() + timedelta(hours=24)
        db.commit()
        
        # Afficher le lien dans les logs (développement)
        reset_link = f"http://localhost:8000/api/v1/auth/reset-password-page?token={reset_token}"
        
        print("\n" + "="*80)
        print("🔐 RÉINITIALISATION DE MOT DE PASSE")
        print("="*80)
        print(f"📧 Email    : {user.email}")
        print(f"👤 Utilisateur: {user.prenom} {user.nom}")
        print(f"🎫 Token    : {reset_token}")
        print(f"🔗 Lien API : POST http://localhost:8000/api/v1/auth/reset-password")
        print(f"📦 Body     : {{ \"token\": \"{reset_token}\", \"new_password\": \"...\", \"confirm_password\": \"...\" }}")
        print("="*80 + "\n")
        
        logger.info(f"Token de réinitialisation généré pour {user.email}: {reset_token}")
        logger.info(f"Lien de réinitialisation: {reset_link}")
        
        # Tentative d'envoi d'email (sans await)
        try:
            EmailService.send_reset_password_email(
                email=user.email,
                token=reset_token,
                nom=user.nom,
                prenom=user.prenom
            )
            logger.info(f"Email de réinitialisation envoyé à {user.email}")
        except Exception as email_error:
            logger.warning(f"Email non envoyé (mode développement): {email_error}")
        
        return ForgotPasswordResponse(
            message="Si l'email existe, un lien de réinitialisation a été envoyé"
        )
        
    except Exception as e:
        logger.error(f"Erreur forgot_password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


# ROUTE RÉINITIALISATION MOT DE PASSE
@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Réinitialisation du mot de passe avec token.
    """
    try:
        # Chercher l'utilisateur avec le token valide
        user = db.query(User).filter(
            User.reset_password_token == request.token,
            User.reset_password_expires > datetime.utcnow()
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token invalide ou expiré"
            )
        
        # Vérifier que les mots de passe correspondent
        if request.new_password != request.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Les mots de passe ne correspondent pas"
            )
        
        # Mettre à jour le mot de passe
        user.hashed_password = SecurityService.get_password_hash(request.new_password)
        user.reset_password_token = None
        user.reset_password_expires = None
        db.commit()
        
        logger.info(f"Mot de passe réinitialisé pour {user.email}")
        
        return {"message": "Mot de passe réinitialisé avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur reset_password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


# ROUTE CHANGEMENT MOT DE PASSE
@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Changement de mot de passe (utilisateur connecté).
    """
    try:
        # Vérifier l'ancien mot de passe
        if not SecurityService.verify_password(request.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mot de passe actuel incorrect"
            )
        
        # Vérifier que les nouveaux mots de passe correspondent
        if request.new_password != request.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Les nouveaux mots de passe ne correspondent pas"
            )
        
        # Mettre à jour le mot de passe
        current_user.hashed_password = SecurityService.get_password_hash(request.new_password)
        db.commit()
        
        logger.info(f"Mot de passe changé pour {current_user.email}")
        
        return {"message": "Mot de passe changé avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur change_password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


# ROUTE VÉRIFICATION EMAIL
@router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Vérification de l'email.
    """
    try:
        user = db.query(User).filter(
            User.verification_token == request.token,
            User.verification_expires > datetime.utcnow()
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token invalide ou expiré"
            )
        
        user.is_verified = True
        user.verification_token = None
        user.verification_expires = None
        db.commit()
        
        logger.info(f"Email vérifié pour {user.email}")
        
        return VerifyEmailResponse(
            message="Email vérifié avec succès",
            verified=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur verify_email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


# ROUTE RAFRAÎCHISSEMENT TOKEN (Version simplifiée)
@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Rafraîchit le token d'accès.
    """
    try:
        logger.info(f"Tentative de rafraîchissement de token")
        
        # Décoder le refresh token
        payload = SecurityService.decode_token(request.refresh_token)
        
        if not payload:
            logger.warning("Refresh token invalide ou expiré")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token invalide ou expiré"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisateur invalide ou inactif"
            )
        
        # Créer un nouveau token d'accès
        access_token = SecurityService.create_access_token({
            "sub": user.id, 
            "email": user.email
        })
        
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        
        logger.info(f"Token rafraîchi avec succès pour {user.email}")
        
        return RefreshTokenResponse(
            access_token=access_token,
            expires_in=expires_in,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du rafraîchissement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )