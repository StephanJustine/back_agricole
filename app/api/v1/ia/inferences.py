import shutil
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from ....database import get_db
from ....models.ia.inference import Inference
from ....schemas.ia.inference import InferenceResponse

router = APIRouter()

# Dossier de stockage des images
UPLOAD_DIR = Path("static/uploads/inferences")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload", response_model=InferenceResponse, status_code=status.HTTP_201_CREATED)
async def create_inference_with_image(
    # On utilise Form pour les données textuelles car on envoie un fichier (Multipart)
    resultat: str = Form(...),
    confidence: float = Form(...),
    modele_id: str = Form(...),
    culture_id: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload une image, la sauvegarde localement et crée l'entrée d'inférence.
    """
    # 1. Validation de l'extension
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image.")

    # 2. Création d'un nom de fichier unique
    file_path = UPLOAD_DIR / f"{os.urandom(8).hex()}_{file.filename}"

    # 3. Sauvegarde physique du fichier
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()

    # 4. Enregistrement en base de données
    new_inference = Inference(
        modele_id=modele_id,
        culture_id=culture_id,
        resultat=resultat,
        confidence=confidence,
        image_url=str(file_path), # Stockage du chemin local
        image_originale=file.filename
    )

    db.add(new_inference)
    db.commit()
    db.refresh(new_inference)
    
    return new_inference