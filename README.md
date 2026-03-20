mon_projet_arachide/
│
├── .env                           # Variables d'environnement
├── .gitignore                     # Fichiers à ignorer par git
├── requirements.txt               # Dépendances du projet
├── README.md                      # Documentation du projet
├── run.py                         # Point d'entrée pour lancer l'app
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # Application FastAPI principale
│   ├── config.py                   # Configuration (settings)
│   ├── database.py                  # Connexion à la base de données
│   │
│   ├── models/                     # Modèles SQLAlchemy
│   │   ├── __init__.py
│   │   ├── base.py                  # Classe de base pour tous les modèles
│   │   ├── enums.py                  # Tous les enums du projet
│   │   │
│   │   ├── user.py                   # Modèle User
│   │   ├── session.py                 # Modèle UserSession
│   │   ├── historique.py              # Modèle Historique
│   │   ├── parcelle.py                # Modèle Parcelle
│   │   ├── culture.py                 # Modèle Culture
│   │   ├── mesure.py                  # Modèle Mesure
│   │   ├── maladie.py                 # Modèle Maladie
│   │   ├── analyse_sol.py             # Modèle AnalyseSol
│   │   ├── travail_sol.py             # Modèle TravailSol
│   │   ├── recolte.py                 # Modèle Recolte
│   │   ├── lot.py                     # Modèle Lot
│   │   ├── transformation.py          # Modèle Transformation
│   │   ├── stock.py                   # Modèle Stock
│   │   ├── client.py                  # Modèle Client
│   │   ├── vente.py                   # Modèle Vente
│   │   │
│   │   ├── ia/                        # Modèles IA
│   │   │   ├── __init__.py
│   │   │   ├── modele_ia.py
│   │   │   ├── dataset.py
│   │   │   ├── entrainement.py
│   │   │   ├── prediction.py
│   │   │   ├── inference.py
│   │   │   └── recommandation.py
│   │   │
│   │   └── iot/                       # Modèles IoT
│   │       ├── __init__.py
│   │       ├── passerelle.py
│   │       ├── capteur.py
│   │       ├── releve.py
│   │       ├── station_meteo.py
│   │       ├── drone.py
│   │       └── balise_gps.py
│   │
│   ├── schemas/                    # Schémas Pydantic (validation)
│   │   ├── __init__.py
│   │   ├── base.py                   # Schémas de base
│   │   │
│   │   ├── user.py                    # Schémas User
│   │   ├── auth.py                    # Schémas Authentification
│   │   ├── parcelle.py                # Schémas Parcelle
│   │   ├── culture.py                 # Schémas Culture
│   │   ├── mesure.py                  # Schémas Mesure
│   │   ├── maladie.py                 # Schémas Maladie
│   │   ├── analyse_sol.py             # Schémas AnalyseSol
│   │   ├── travail_sol.py             # Schémas TravailSol
│   │   ├── recolte.py                 # Schémas Recolte
│   │   ├── lot.py                     # Schémas Lot
│   │   ├── transformation.py          # Schémas Transformation
│   │   ├── stock.py                   # Schémas Stock
│   │   ├── client.py                  # Schémas Client
│   │   ├── vente.py                   # Schémas Vente
│   │   ├── historique.py               # Schémas Historique
│   │   │
│   │   ├── ia/                        # Schémas IA
│   │   │   ├── __init__.py
│   │   │   ├── modele_ia.py
│   │   │   ├── dataset.py
│   │   │   ├── entrainement.py
│   │   │   ├── prediction.py
│   │   │   ├── inference.py
│   │   │   └── recommandation.py
│   │   │
│   │   └── iot/                       # Schémas IoT
│   │       ├── __init__.py
│   │       ├── passerelle.py
│   │       ├── capteur.py
│   │       ├── releve.py
│   │       ├── station_meteo.py
│   │       ├── drone.py
│   │       └── balise_gps.py
│   │
│   ├── api/                         # Routes API
│   │   ├── __init__.py
│   │   ├── api.py                     # Regroupe toutes les routes
│   │   ├── dependencies.py             # Dépendances communes
│   │   │
│   │   ├── v1/                         # Version 1 de l'API
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                  # Routes d'authentification
│   │   │   ├── users.py                 # Routes utilisateurs
│   │   │   ├── parcelles.py             # Routes parcelles
│   │   │   ├── cultures.py              # Routes cultures
│   │   │   ├── mesures.py               # Routes mesures
│   │   │   ├── maladies.py              # Routes maladies
│   │   │   ├── analyses_sol.py          # Routes analyses sol
│   │   │   ├── travaux_sol.py           # Routes travaux sol
│   │   │   ├── recoltes.py              # Routes récoltes
│   │   │   ├── lots.py                  # Routes lots
│   │   │   ├── transformations.py       # Routes transformations
│   │   │   ├── stocks.py                # Routes stocks
│   │   │   ├── clients.py               # Routes clients
│   │   │   ├── ventes.py                # Routes ventes
│   │   │   ├── historique.py            # Routes historique
│   │   │   │
│   │   │   ├── ia/                      # Routes IA
│   │   │   │   ├── __init__.py
│   │   │   │   ├── modeles.py
│   │   │   │   ├── predictions.py
│   │   │   │   ├── inferences.py
│   │   │   │   └── recommandations.py
│   │   │   │
│   │   │   └── iot/                     # Routes IoT
│   │   │       ├── __init__.py
│   │   │       ├── passerelles.py
│   │   │       ├── capteurs.py
│   │   │       ├── releves.py
│   │   │       ├── stations_meteo.py
│   │   │       ├── drones.py
│   │   │       └── balises.py
│   │
│   ├── core/                         # Fonctionnalités centrales
│   │   ├── __init__.py
│   │   ├── security.py                 # Sécurité (JWT, hash)
│   │   ├── email.py                    # Envoi d'emails
│   │   ├── exceptions.py               # Gestion des erreurs
│   │   ├── pagination.py               # Pagination
│   │   ├── permissions.py              # Gestion des permissions
│   │   └── historique.py               # Enregistrement automatique de l'historique
│   │
│   ├── utils/                         # Utilitaires
│   │   ├── __init__.py
│   │   ├── validators.py                # Validateurs personnalisés
│   │   ├── helpers.py                   # Fonctions d'aide
│   │   ├── telemetry.py                 # Métriques
│   │   └── seed.py                      # Données de test
│   │
│   └── services/                      # Logique métier (optionnel)
│       ├── __init__.py
│       ├── auth_service.py              # Service d'authentification
│       ├── user_service.py              # Service utilisateur
│       ├── parcelle_service.py          # Service parcelle
│       ├── prediction_service.py        # Service IA
│       └── notification_service.py      # Service notifications
│
├── tests/                           # Tests unitaires
│   ├── __init__.py
│   ├── conftest.py                    # Configuration des tests
│   ├── test_main.py
│   │
│   ├── test_api/
│   │   ├── test_auth.py
│   │   ├── test_users.py
│   │   └── ...
│   │
│   └── test_services/
│       └── ...
│
├── alembic/                         # Migrations de base de données
│   ├── versions/
│   ├── env.py
│   ├── README
│   └── script.py.mako
│
├── logs/                             # Fichiers de logs
│   └── app.log
│
└── scripts/                          # Scripts utilitaires
    ├── create_db.py
    ├── seed_data.py
    └── backup_db.py