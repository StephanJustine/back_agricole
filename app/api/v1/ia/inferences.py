# import shutil
# import os
# from pathlib import Path
# from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
# from sqlalchemy.orm import Session

# from ....database import get_db
# from ....models.ia.inference import Inference
# from ....schemas.ia.inference import InferenceResponse

# router = APIRouter()

# # Dossier de stockage des images
# UPLOAD_DIR = Path("static/uploads/inferences")
# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# @router.post("/upload", response_model=InferenceResponse, status_code=status.HTTP_201_CREATED)
# async def create_inference_with_image(
#     # On utilise Form pour les données textuelles car on envoie un fichier (Multipart)
#     resultat: str = Form(...),
#     confidence: float = Form(...),
#     modele_id: str = Form(...),
#     culture_id: str = Form(None),
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db)
# ):
#     """
#     Upload une image, la sauvegarde localement et crée l'entrée d'inférence.
#     """
#     # 1. Validation de l'extension
#     if not file.content_type.startswith("image/"):
#         raise HTTPException(status_code=400, detail="Le fichier doit être une image.")

#     # 2. Création d'un nom de fichier unique
#     file_path = UPLOAD_DIR / f"{os.urandom(8).hex()}_{file.filename}"

#     # 3. Sauvegarde physique du fichier
#     try:
#         with file_path.open("wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)
#     finally:
#         file.file.close()

#     # 4. Enregistrement en base de données
#     new_inference = Inference(
#         modele_id=modele_id,
#         culture_id=culture_id,
#         resultat=resultat,
#         confidence=confidence,
#         image_url=str(file_path), # Stockage du chemin local
#         image_originale=file.filename
#     )

#     db.add(new_inference)
#     db.commit()
#     db.refresh(new_inference)
    
#     return new_inference


import shutil
import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from datetime import datetime
from PIL import Image
import io

from app.database import get_db
from app.models.ia.inference import Inference
from app.schemas.ia.inference import InferenceResponse
from app.core.dependencies import get_current_active_user
from app.core.permissions import require_roles
from app.models.enums import UserRole

router = APIRouter()

# Dossier de stockage des images
UPLOAD_DIR = Path("static/uploads/inferences")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Extensions autorisées
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def is_valid_image(file_content: bytes) -> bool:
    """Vérifie si le fichier est une image valide en utilisant Pillow."""
    try:
        image = Image.open(io.BytesIO(file_content))
        image.verify()  # Vérifie que c'est une image valide
        return True
    except Exception:
        return False


def get_image_format(file_content: bytes) -> Optional[str]:
    """Retourne le format de l'image."""
    try:
        image = Image.open(io.BytesIO(file_content))
        return image.format.lower()
    except Exception:
        return None


def secure_filename(filename: str) -> str:
    """Nettoie et sécurise le nom du fichier."""
    # Enlever les caractères dangereux
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ")
    safe_name = safe_name.replace(" ", "_")
    # Limiter la longueur
    if len(safe_name) > 100:
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:96] + ext
    return safe_name


@router.post("/upload", response_model=InferenceResponse, status_code=status.HTTP_201_CREATED)
async def create_inference_with_image(
    resultat: str = Form(...),
    confidence: float = Form(...),
    modele_id: str = Form(...),
    culture_id: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Upload une image, la sauvegarde localement et crée l'entrée d'inférence.
    Seuls les utilisateurs authentifiés peuvent effectuer des inférences.
    """
    try:
        # 1. Validation du fichier
        if not file or not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucun fichier fourni"
            )
        
        # 2. Vérification de la taille
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Fichier trop volumineux. Maximum {MAX_FILE_SIZE // (1024*1024)} MB"
            )
        
        # 3. Validation du type de fichier avec Pillow
        if not is_valid_image(file_content):
            # Afficher les premiers bytes pour debug
            hex_header = file_content[:20].hex()
            print(f"Headers reçus: {hex_header}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le fichier doit être une image valide (jpg, png, gif, webp, etc.)"
            )
        
        # 4. Récupérer le format réel de l'image
        image_format = get_image_format(file_content)
        print(f"Format détecté: {image_format}")
        
        # 5. Vérification de l'extension (optionnelle)
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            # Ne pas bloquer, juste logger
            print(f"Extension non standard: {file_extension}")
        
        # 6. Validation de la confiance
        if not 0 <= confidence <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La confiance doit être comprise entre 0 et 1"
            )
        
        # 7. Validation du résultat
        if not resultat or len(resultat) > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le résultat est requis et ne doit pas dépasser 500 caractères"
            )
        
        # 8. Création d'un nom de fichier sécurisé
        # Préserver l'extension originale ou celle détectée
        if image_format:
            ext = f".{image_format}"
        else:
            ext = file_extension
        
        safe_filename = secure_filename(file.filename)
        # Enlever l'extension existante
        safe_filename = os.path.splitext(safe_filename)[0]
        
        unique_id = uuid.uuid4().hex[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{timestamp}_{unique_id}_{safe_filename}{ext}"
        
        # Créer le chemin complet (avec sous-dossiers par date)
        date_folder = datetime.now().strftime("%Y/%m/%d")
        full_upload_dir = UPLOAD_DIR / date_folder
        full_upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = full_upload_dir / new_filename
        relative_path = f"uploads/inferences/{date_folder}/{new_filename}"
        
        # 9. Sauvegarde physique du fichier
        try:
            with file_path.open("wb") as buffer:
                buffer.write(file_content)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la sauvegarde du fichier: {str(e)}"
            )
        
        # 10. Enregistrement en base de données
        new_inference = Inference(
            modele_id=modele_id,
            culture_id=culture_id,
            resultat=resultat,
            confidence=confidence,
            image_url=relative_path,
            image_originale=file.filename,
            notes=notes,
            date_inference=datetime.utcnow(),
            temps_inference=None
        )
        
        # Ajouter user_id si le champ existe
        if hasattr(Inference, 'user_id'):
            new_inference.user_id = current_user.id
        
        db.add(new_inference)
        db.commit()
        db.refresh(new_inference)
        
        return new_inference
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Erreur détaillée: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'inférence: {str(e)}"
        )
    finally:
        await file.close()