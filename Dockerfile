FROM python:3.11-slim

# Dossier de travail
WORKDIR /app

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du projet
COPY . .

# Créer le dossier static et uploads
RUN mkdir -p /app/static/uploads/inferences \
    && mkdir -p /app/static/uploads/drones \
    && mkdir -p /app/static/uploads/profiles \
    && mkdir -p /app/static/uploads/documents

# Exposer le port
EXPOSE 8080

# Lancer l'app
CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]