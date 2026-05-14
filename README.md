 Filière Arachide API
Plateforme de gestion intégrée de la filière arachide - De la graine au savon
📋 Table des matières
Présentation du projet

Architecture technique

Workflow complet

Installation

Configuration

Lancement du projet

Endpoints API

Tests

Dépannage

📖 Présentation du projet
Objectif
Créer une plateforme intégrée pour la gestion complète de la filière arachide, de la culture à la transformation en huile et savon, avec traçabilité et prédiction des rendements.

Fonctionnalités principales
Module	Fonctionnalités
👤 Authentification	Inscription, connexion, JWT tokens, mot de passe oublié
🌾 Parcelles	Gestion des parcelles améliorées/traditionnelles, géolocalisation
🌱 Cultures	Suivi des cycles de culture, stades de développement
📏 Mesures	Suivi de croissance (hauteur, feuilles, photos)
🦠 Maladies	Détection et suivi des maladies, alertes automatiques
🚜 Travaux	Gestion des travaux du sol et coûts associés
🌽 Récoltes	Enregistrement des récoltes, calcul du rendement
🏷️ Lots	Traçabilité avec codes uniques, scan QR
⚙️ Transformations	Production d'huile et de savon, calcul des rendements
📊 Statistiques	Tableaux de bord, comparaisons A vs T
🏗️ Architecture technique
Stack technologique
text
┌─────────────────────────────────────────────────────────────────┐
│                      TECHNOLOGIES                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Backend                                                         │
│  ├── FastAPI (Python) - Framework web                            │
│  ├── SQLAlchemy - ORM                                            │
│  ├── Pydantic - Validation des données                          │
│  └── JWT - Authentification                                      │
│                                                                   │
│  Base de données                                                 │
│  ├── PostgreSQL (production)                                     │
│  └── SQLite (développement)                                      │
│                                                                   │
│  Sécurité                                                        │
│  ├── bcrypt / pbkdf2_sha256 - Hash des mots de passe             │
│  ├── python-jose - JWT tokens                                    │
│  └── OAuth2PasswordBearer - Authentification                     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
Structure du projet
text
back_agricole/
├── app/
│   ├── api/                 # Routes API
│   │   └── v1/              # Version 1 de l'API
│   │       ├── auth.py      # Authentification
│   │       ├── users.py     # Utilisateurs
│   │       ├── parcelles.py # Parcelles
│   │       ├── cultures.py  # Cultures
│   │       ├── mesures.py   # Mesures
│   │       ├── maladies.py  # Maladies
│   │       ├── travaux_sol.py # Travaux
│   │       ├── recoltes.py  # Récoltes
│   │       ├── lots.py      # Lots
│   │       └── transformations.py # Transformations
│   ├── core/                # Fonctionnalités centrales
│   │   ├── security.py      # Sécurité (JWT, hash)
│   │   ├── email.py         # Envoi d'emails
│   │   ├── dependencies.py  # Dépendances
│   │   └── historique.py    # Historique des actions
│   ├── models/              # Modèles SQLAlchemy
│   │   ├── base.py          # Classe de base
│   │   ├── user.py          # Utilisateur
│   │   ├── parcelle.py      # Parcelle
│   │   ├── culture.py       # Culture
│   │   └── ...              # Autres modèles
│   ├── schemas/             # Schémas Pydantic
│   ├── services/            # Logique métier
│   └── scripts/             # Scripts utilitaires
│       └── init_admin.py    # Création admin automatique
├── .env                      # Variables d'environnement
├── requirements.txt          # Dépendances
├── run.py                    # Point d'entrée
└── README.md                 # Documentation
🔄 Workflow complet
Vue d'ensemble
text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW DE A À Z                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PHASE 1 : PRÉPARATION                                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ 1. Inscription producteur                                              │ │
│  │ 2. Création parcelle (Améliorée / Traditionnelle)                      │ │
│  │ 3. Analyse de sol                                                      │ │
│  │ 4. Enregistrement des travaux (labour, amendement)                     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    ↓                                         │
│  PHASE 2 : CULTURE                                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ 5. Démarrage culture (semis, variété, densité)                         │ │
│  │ 6. Suivi hebdomadaire (hauteur, feuilles, photos)                      │ │
│  │ 7. Gestion des maladies (signalement, traitement)                      │ │
│  │ 8. Enregistrement des travaux (sarclage, buttage, fertilisation)       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    ↓                                         │
│  PHASE 3 : RÉCOLTE                                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ 9. Enregistrement de la récolte (poids, qualité)                       │ │
│  │ 10. Calcul du rendement (kg/ha)                                        │ │
│  │ 11. Comparaison Améliorée vs Traditionnelle                            │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    ↓                                         │
│  PHASE 4 : TRANSFORMATION                                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ 12. Création de lots traçables (codes uniques)                         │ │
│  │ 13. Transformation en huile (calcul du rendement)                      │ │
│  │ 14. Transformation en savon (recettes, additifs)                       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    ↓                                         │
│  PHASE 5 : ANALYSE                                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ 15. Tableaux de bord et statistiques                                   │ │
│  │ 16. Export des données                                                 │ │
│  │ 17. Bilan économique                                                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
Diagramme de séquence des endpoints
🚀 Installation
Prérequis
Python 3.10 ou supérieur

PostgreSQL 12+ (ou SQLite pour développement)

pip (gestionnaire de paquets Python)

1. Cloner le repository
bash
git clone https://github.com/votre-projet/back_agricole.git
cd back_agricole
2. Créer un environnement virtuel
bash
# Windows
python -m venv env
env\Scripts\activate

# Linux/Mac
python3 -m venv env
source env/bin/activate
3. Installer les dépendances
bash
pip install -r requirements.txt
⚙️ Configuration
Créer le fichier .env
Copiez le fichier .env.example et adaptez-le :

bash
cp .env.example .env
Contenu du fichier .env
env
# ========================
# MODE
# ========================
DEBUG=True

# ========================
# BASE DE DONNÉES
# ========================
# PostgreSQL
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/arachide_db

# SQLite (alternative)
# DATABASE_URL=sqlite:///./arachide.db

# ========================
# SÉCURITÉ
# ========================
SECRET_KEY=votre_cle_secrete_tres_longue_et_aleatoire
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ========================
# EMAIL (pour réinitialisation mot de passe)
# ========================
MAIL_USERNAME=votre.email@gmail.com
MAIL_PASSWORD=votre_mot_de_passe_application
MAIL_FROM=noreply@arachide.mg
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_TLS=True

# ========================
# FRONTEND
# ========================
FRONTEND_URL=http://localhost:3000

# ========================
# ADMIN PAR DÉFAUT
# ========================
DEFAULT_ADMIN_EMAIL=stephanson.stp@gmail.com
DEFAULT_ADMIN_PASSWORD=admin123
CREATE_DEFAULT_ADMIN=True
Créer la base de données
bash
# PostgreSQL
psql -U postgres -c "CREATE DATABASE arachide_db;"

# SQLite
# Aucune action nécessaire, le fichier sera créé automatiquement
🏃 Lancement du projet
1. Démarrer l'application
bash
python run.py
2. Vérifier que l'application fonctionne
Ouvrez votre navigateur et accédez à :

API: http://localhost:8000

Documentation Swagger: http://localhost:8000/docs

Documentation ReDoc: http://localhost:8000/redoc

3. Logs de démarrage
text
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000

🔧 Création des tables de la base de données...
✅ Tables créées avec succès
🔧 Vérification de l'administrateur par défaut...
✅ ADMINISTRATEUR CRÉÉ AVEC SUCCÈS !
📧 Email: stephanson.stp@gmail.com
🔑 Mot de passe: admin123
📡 Endpoints API
Authentification
Méthode	Endpoint	Description
POST	/auth/register	Inscription
POST	/auth/login	Connexion (OAuth2)
POST	/auth/logout	Déconnexion
POST	/auth/refresh	Rafraîchir token
POST	/auth/forgot-password	Mot de passe oublié
POST	/auth/reset-password	Réinitialiser mot de passe
Utilisateurs
Méthode	Endpoint	Description
GET	/users/	Liste des utilisateurs
GET	/users/me	Mon profil
PUT	/users/me	Mettre à jour mon profil
GET	/users/{id}	Détails utilisateur
PUT	/users/{id}	Mettre à jour (admin)
DELETE	/users/{id}	Supprimer (admin)
Parcelles
Méthode	Endpoint	Description
GET	/parcelles/	Liste des parcelles
POST	/parcelles/	Créer une parcelle
GET	/parcelles/{id}	Détails parcelle
PUT	/parcelles/{id}	Mettre à jour
DELETE	/parcelles/{id}	Supprimer
Cultures
Méthode	Endpoint	Description
GET	/cultures/	Liste des cultures
POST	/cultures/	Démarrer une culture
GET	/cultures/{id}	Détails culture
PUT	/cultures/{id}	Mettre à jour
POST	/cultures/{id}/terminer	Terminer culture
Mesures
Méthode	Endpoint	Description
GET	/mesures/	Liste des mesures
POST	/mesures/	Enregistrer mesure
GET	/mesures/graphique/{culture_id}	Données graphique
Maladies
Méthode	Endpoint	Description
GET	/maladies/	Liste des maladies
POST	/maladies/	Signalement
GET	/maladies/alertes/non-traitees	Alertes (admin)
Travaux
Méthode	Endpoint	Description
GET	/travaux-sol/	Liste des travaux
POST	/travaux-sol/	Enregistrer travail
GET	/travaux-sol/cout-total-parcelles	Coûts totaux
Récoltes
Méthode	Endpoint	Description
GET	/recoltes/	Liste des récoltes
POST	/recoltes/	Enregistrer récolte
GET	/recoltes/comparaison/{culture_id}	Comparaison A vs T
Lots
Méthode	Endpoint	Description
GET	/lots/	Liste des lots
POST	/lots/	Créer un lot
GET	/lots/scan/{code}	Scanner un code
POST	/lots/from-recolte/{recolte_id}	Lot depuis récolte
Transformations
Méthode	Endpoint	Description
GET	/transformations/	Liste des transformations
POST	/transformations/huile	Transformer en huile
POST	/transformations/savon	Transformer en savon
POST	/transformations/calculer-savon	Calculer recette
🧪 Tests
Test avec curl
bash
# 1. Connexion
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=stephanson.stp@gmail.com&password=admin123"

# 2. Créer une parcelle
curl -X POST "http://localhost:8000/api/v1/parcelles/" \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Antanambao",
    "superficie": 1.5,
    "type": "amelioree"
  }'

# 3. Démarrer une culture
curl -X POST "http://localhost:8000/api/v1/cultures/" \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "parcelle_id": "ID_PARCELLE",
    "date_debut": "2024-03-20",
    "variete": "ICGV 86024"
  }'

# 4. Enregistrer une mesure
curl -X POST "http://localhost:8000/api/v1/mesures/" \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "culture_id": "ID_CULTURE",
    "date_mesure": "2024-04-22",
    "hauteur_moyenne": 18.5,
    "nb_feuilles_moyen": 6
  }'
Test avec Python
python
import requests

# Connexion
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    data={"username": "stephanson.stp@gmail.com", "password": "admin123"}
)
token = response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Créer une parcelle
parcelle = requests.post(
    "http://localhost:8000/api/v1/parcelles/",
    headers=headers,
    json={"nom": "Test", "superficie": 1.5, "type": "amelioree"}
)
print(parcelle.json())
🔧 Dépannage
Erreurs courantes
Erreur	Solution
ModuleNotFoundError	pip install -r requirements.txt
Connection refused	Vérifier que PostgreSQL est démarré
Secret key not set	Configurer SECRET_KEY dans .env
Email not configured	Configurer MAIL_USERNAME et MAIL_PASSWORD
Réinitialiser la base de données
bash
# Supprimer et recréer les tables
python -c "
from app.database import engine
from app.models import Base
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
"

# Recréer l'admin
python -c "from app.scripts.init_admin import init_admin_user; init_admin_user()"
Réinitialiser le mot de passe admin
bash
python -c "
from app.database import SessionLocal
from app.models.user import User
from app.core.security import SecurityService

db = SessionLocal()
admin = db.query(User).filter(User.email == 'stephanson.stp@gmail.com').first()
if admin:
    admin.hashed_password = SecurityService.get_password_hash('admin123')
    db.commit()
    print('Mot de passe réinitialisé')
db.close()
"
📊 Modèles de données
Relations principales
text
User 1──* Parcelle 1──* Culture 1──* Mesure
                     │
                     └──1 Recolte 1──* Lot 1──* Transformation
                                              │
                                              └──* Vente
Codes traçables
Type	Format	Exemple
Arachide brute	ARACHIDE_BRUTE-AAAAMMJJ-XXX	ARACHIDE_BRUTE-20240618-A3F
Huile	HUILE-AAAAMMJJ-XXX	HUILE-20240710-B7E
Savon	SAVON-AAAAMMJJ-XXX	SAVON-20240801-C9D
👥 Équipe
Product Owner: [Nom]

Scrum Master: [Nom]

Développeurs: [Noms]

📝 Licence
Ce projet est sous licence MIT.

🙏 Remerciements
FastAPI pour le framework

SQLAlchemy pour l'ORM

La communauté open source

Bon développement ! 🚀

