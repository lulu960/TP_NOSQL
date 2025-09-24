# CouchDB Analytics Project

Un projet complet de gestion et d'analyse de données avec CouchDB, incluant un ETL, des requêtes analytiques, et une interface web Streamlit.

## 📋 Table des matières

- [Aperçu du projet](#aperçu-du-projet)
- [Architecture](#architecture)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Tests](#tests)
- [Fonctionnalités](#fonctionnalités)
- [Structure du projet](#structure-du-projet)
- [Troubleshooting](#troubleshooting)

## 🎯 Aperçu du projet

Ce projet démontre l'utilisation complète de CouchDB avec Python pour :

- **Setup automatisé** de CouchDB avec utilisateurs et rôles
- **Modèle de données** dénormalisé avec schémas JSON
- **Pipeline ETL** pour le nettoyage et l'enrichissement des données
- **Opérations CRUD** complètes avec tests unitaires
- **Analytics avancés** avec requêtes Mango et vues MapReduce
- **Dashboard web** avec Streamlit, KPIs et graphiques interactifs
- **Administration** et sécurité avec export/import et backups

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │     Python      │    │    CouchDB      │
│   Dashboard     │◄───┤   Application   │◄───┤    Database     │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                        │
        │                        │                        │
   ┌────▼────┐              ┌────▼────┐              ┌────▼────┐
   │ KPIs &  │              │ CRUD    │              │ Mango   │
   │ Charts  │              │ Ops     │              │ Queries │
   └─────────┘              └─────────┘              └─────────┘
```

### Composants principaux :

- **Database Layer** : CouchDB avec index Mango et vues MapReduce
- **Application Layer** : Python avec CRUD, ETL et analytics
- **Presentation Layer** : Streamlit avec visualisations matplotlib/plotly
- **Security Layer** : Gestion des utilisateurs et rôles

## 📋 Prérequis

### Logiciels requis :

1. **CouchDB** (version 3.0+)
   - Windows : Télécharger depuis [couchdb.apache.org](https://couchdb.apache.org/)
   - Linux : `sudo apt-get install couchdb`
   - macOS : `brew install couchdb`

2. **Python** (version 3.8+)

### Installation de CouchDB :

#### Windows :
1. Télécharger l'installateur CouchDB
2. Exécuter l'installation avec les paramètres par défaut
3. CouchDB sera accessible sur `http://localhost:5984`

#### Linux (Ubuntu/Debian) :
```bash
sudo apt update
sudo apt install couchdb
sudo systemctl enable couchdb
sudo systemctl start couchdb
```

#### macOS :
```bash
brew install couchdb
brew services start couchdb
```

### Vérification de l'installation :
```bash
curl http://localhost:5984
# Devrait retourner : {"couchdb":"Welcome","version":"3.x.x"}
```

## 🚀 Installation

### 1. Cloner le projet
```bash
git clone <repository-url>
cd TP
```

### 2. Installer les dépendances Python
```bash
pip install -r requirements.txt
```

### 3. Configuration de l'environnement
```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer .env avec vos paramètres
```

## ⚙️ Configuration

### Variables d'environnement (.env)

```bash
# Configuration CouchDB
COUCHDB_URL=http://localhost:5984
COUCHDB_USER=admin
COUCHDB_PASSWORD=admin123
DATABASE_NAME=tp_database

# Utilisateurs
ADMIN_USER=admin
ADMIN_PASSWORD=admin123
ANALYST_USER=analyst
ANALYST_PASSWORD=analyst123
```

### Configuration CouchDB

Le script de setup configure automatiquement :
- Cluster CouchDB (single node)
- Base de données principale
- Utilisateurs admin et analyst
- Sécurité de la base de données
- Index Mango pour les performances

## 📖 Utilisation

### Interface unifiée (recommandée)

Le projet fournit un point d'entrée unique via `main.py` :

```bash
# Voir le statut du projet
python main.py

# Setup complet de CouchDB
python main.py setup

# Charger les données d'exemple
python main.py etl

# Lancer le dashboard web
python main.py webapp

# Voir les exemples d'analytics
python main.py analytics

# Exécuter les tests
python main.py test

# Commandes admin
python main.py admin stats
python main.py admin export data/backup.json
```

### Commandes détaillées

#### 1. Setup initial
```bash
# Setup CouchDB (base, utilisateurs, index)
python main.py setup
```

#### 2. Chargement des données
```bash
# ETL complet avec données d'exemple
python main.py etl
```

#### 3. Dashboard web
```bash
# Lancer Streamlit (http://localhost:8501)
python main.py webapp

# Ou directement :
streamlit run webapp/app.py
```

#### 4. Administration
```bash
# Statistiques de la base
python main.py admin stats

# Export JSON
python main.py admin export data/export.json --format json --type product

# Export CSV
python main.py admin export data/export.csv --format csv

# Import
python main.py admin import data/import.json --format json

# Backup complet
python main.py admin backup data/backup_$(date +%Y%m%d).json

# Restauration (attention !)
python main.py admin restore data/backup.json --confirm

# Créer utilisateur analyst
python main.py admin create-analyst analyst analyst123
```

### Commandes curl alternatives

Si vous préférez utiliser curl directement :

```bash
# Vérifier CouchDB
curl http://localhost:5984

# Créer la base
curl -X PUT http://localhost:5984/tp_database -u admin:admin123

# Créer un document
curl -X POST http://localhost:5984/tp_database \
  -H "Content-Type: application/json" \
  -u admin:admin123 \
  -d '{"type":"product","name":"Test Product","price":99.99}'

# Query Mango
curl -X POST http://localhost:5984/tp_database/_find \
  -H "Content-Type: application/json" \
  -u admin:admin123 \
  -d '{"selector":{"type":"product"},"limit":10}'
```

## 🧪 Tests

### Exécution des tests
```bash
# Tous les tests
python main.py test

# Tests spécifiques
python -m pytest tests/test_database.py -v

# Tests avec couverture
python -m pytest tests/ --cov=src --cov-report=html
```

### Tests d'intégration

Pour les tests d'intégration nécessitant CouchDB :
```bash
# Définir la variable d'environnement
export RUN_INTEGRATION_TESTS=1
python -m pytest tests/ -v -m integration
```

## 🔧 Fonctionnalités

### 1. **Setup & Configuration**
- Script Python automatisé pour CouchDB
- Création d'utilisateurs et rôles
- Configuration des index Mango
- Alternatives curl pour setup manuel

### 2. **Modèle de données**
- Schémas JSON dénormalisés
- Documents : products, customers, orders, events
- Timestamps automatiques et versioning
- Validation des données

### 3. **ETL Pipeline**
- Nettoyage et validation des données
- Enrichissement automatique (updated_at, keywords, etc.)
- Import en lots optimisé
- Gestion d'erreurs et logging

### 4. **CRUD Operations**
- Fonctions create, read, update, delete, replace
- Support des requêtes complexes
- Gestion des révisions CouchDB
- Classes spécialisées par type de document

### 5. **Analytics & Reporting**
- **Requêtes Mango** : filtres complexes, agrégations
- **Vues MapReduce** : sales_by_month, products_by_category
- Métriques KPI : revenus, commandes, clients
- Analytics en temps réel

### 6. **Dashboard Web (Streamlit)**
- **KPIs** : métriques principales avec deltas
- **Graphiques interactifs** :
  - Répartition des commandes par statut (pie chart)
  - Produits par catégorie (bar chart)
  - Évolution des ventes (line + bar chart)
  - Top produits (horizontal bar)
  - Analyse clients (scatter plot)
- **Data Explorer** : requêtes personnalisées
- **Raw Data** : inspection des documents

### 7. **Administration & Sécurité**
- Export/Import JSON et CSV volumineux
- Backup/Restore complets
- Gestion des utilisateurs et rôles
- Statistiques détaillées de la base

## 📁 Structure du projet

```
TP/
├── 📄 main.py                 # Point d'entrée unifié
├── 📄 setup_couchdb.py       # Setup CouchDB
├── 📄 requirements.txt       # Dépendances Python
├── 📄 .env.example           # Configuration exemple
├── 📄 README.md              # Documentation
│
├── 📁 src/                    # Code source
│   ├── 📄 models.py          # Schémas de données
│   ├── 📄 database.py        # CRUD operations
│   └── 📄 analytics.py       # Analytics & MapReduce
│
├── 📁 scripts/               # Scripts utilitaires
│   ├── 📄 etl.py            # Pipeline ETL
│   └── 📄 admin.py          # Administration
│
├── 📁 webapp/                # Interface web
│   └── 📄 app.py            # Application Streamlit
│
├── 📁 tests/                 # Tests unitaires
│   ├── 📄 test_database.py  # Tests CRUD
│   └── 📄 __init__.py
│
├── 📁 notebooks/             # Jupyter notebooks
│   └── 📄 etl_demo.ipynb    # Démo ETL
│
└── 📁 data/                  # Données et exports
    └── 📄 sample_data.json   # Données générées
```

## 🐛 Troubleshooting

### Problèmes courants

#### 1. CouchDB ne démarre pas
```bash
# Vérifier le statut
curl http://localhost:5984

# Linux : vérifier le service
sudo systemctl status couchdb
sudo systemctl start couchdb

# Windows : vérifier dans Services.msc
```

#### 2. Erreur de connexion
- Vérifier le fichier `.env`
- Confirmer que CouchDB écoute sur le bon port (5984)
- Tester avec curl

#### 3. Erreur d'authentification
```bash
# Réinitialiser le setup
python main.py setup

# Vérifier les credentials dans .env
```

#### 4. Base de données vide
```bash
# Charger les données d'exemple
python main.py etl

# Vérifier avec
python main.py admin stats
```

#### 5. Webapp ne se lance pas
```bash
# Vérifier Streamlit
pip install streamlit

# Lancer directement
streamlit run webapp/app.py
```

#### 6. Tests échouent
```bash
# Installer pytest
pip install pytest

# Tests sans CouchDB requis
python -m pytest tests/test_database.py -v -k "not integration"
```

### Logs et debug

Pour plus de détails :
```bash
# Logs CouchDB (Linux)
tail -f /var/log/couchdb/couchdb.log

# Debug Python
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
python -c "from database import CouchDBClient; print(CouchDBClient().get_database_info())"
```

### Réinitialisation complète

En cas de problème majeur :
```bash
# 1. Supprimer la base (attention !)
curl -X DELETE http://localhost:5984/tp_database -u admin:admin123

# 2. Setup complet
python main.py setup
python main.py etl

# 3. Vérifier
python main.py status
```

## 📊 Exemples d'utilisation

### Query Mango
```python
from src.database import CouchDBClient

client = CouchDBClient()

# Produits chers
result = client.find({
    "type": "product",
    "price": {"$gte": 100}
})

# Commandes récentes
result = client.find({
    "type": "order",
    "created_at": {"$gte": "2024-01-01T00:00:00Z"}
})
```

### Analytics personnalisés
```python
from src.analytics import AnalyticsEngine

analytics = AnalyticsEngine()

# KPIs personnalisés
sales_data = analytics.get_sales_summary()
print(f"Revenus totaux: ${sales_data['data']['total_revenue']}")

# Top produits
top_products = analytics.get_top_products(5)
```

### Administration
```python
from scripts.admin import CouchDBAdmin

admin = CouchDBAdmin()

# Export conditionnel
admin.export_data("products.json", doc_type="product")

# Backup avec métadonnées
admin.backup_database("backup_complete.json")
```

---

## 🎯 Démonstration

Pour une démonstration complète :

1. **Setup** : `python main.py setup`
2. **Données** : `python main.py etl`
3. **Dashboard** : `python main.py webapp`
4. **Analytics** : `python main.py analytics`
5. **Tests** : `python main.py test`

Le projet est maintenant prêt à l'emploi avec toutes les fonctionnalités opérationnelles !