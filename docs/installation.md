# Guide d'installation — AssIA

Ce guide détaille les étapes pour installer et lancer **AssIA** en environnement local (développement).

---

## Table des matières

- [Prérequis système](#prérequis-système)
- [Étape 1 — Cloner le dépôt](#étape-1--cloner-le-dépôt)
- [Étape 2 — Configurer les variables d'environnement](#étape-2--configurer-les-variables-denvironnement)
- [Étape 3 — Installer Ollama et les modèles](#étape-3--installer-ollama-et-les-modèles)
- [Étape 4 — Configurer Keycloak](#étape-4--configurer-keycloak)
- [Étape 5 — Lancer le backend FastAPI](#étape-5--lancer-le-backend-fastapi)
- [Étape 6 — Lancer le frontend React](#étape-6--lancer-le-frontend-react)
- [Vérification](#vérification)
- [Démarrage via Docker](#démarrage-via-docker)
- [Résolution des problèmes courants](#résolution-des-problèmes-courants)

---

## Prérequis système

| Outil | Version minimale | Vérification |
|---|---|---|
| Python | 3.11 | `python --version` |
| Node.js | 18 LTS | `node --version` |
| npm | 9 | `npm --version` |
| Ollama | Dernière version | `ollama --version` |
| Docker (optionnel) | 24 | `docker --version` |

**Ressources matérielles recommandées :**
- RAM : 8 Go minimum (16 Go recommandés pour les modèles LLM)
- Stockage : 10 Go libres pour les modèles Ollama
- CPU : 4 cœurs minimum

---

## Étape 1 — Cloner le dépôt

```bash
git clone https://github.com/votre-organisation/assistant-reunions.git
cd assistant-reunions
```

---

## Étape 2 — Configurer les variables d'environnement

Copiez le fichier exemple et adaptez les valeurs à votre environnement :

```bash
cp .env.example .env
```

Ouvrez `.env` et modifiez les variables clés :

```dotenv
# Application
APP_ENV=development
SECRET_KEY=votre-cle-secrete-aleatoire-longue-et-sure

# LLM Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:0.5b          # ou mistral, llama3.2, etc.

# Embeddings
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Keycloak
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=assistant-reunions
KEYCLOAK_CLIENT_ID=assistant-reunions-app
KEYCLOAK_CLIENT_SECRET=votre-secret-client-keycloak
```

> **Important :** Ne commitez jamais le fichier `.env` dans le dépôt. Il est déjà listé dans `.gitignore`.

---

## Étape 3 — Installer Ollama et les modèles

### Installation d'Ollama

**Linux :**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS :**
Téléchargez depuis [https://ollama.ai/download](https://ollama.ai/download)

**Windows :**
Téléchargez l'installateur depuis [https://ollama.ai/download](https://ollama.ai/download)

### Télécharger les modèles requis

```bash
# Modèle LLM (génération de texte)
ollama pull qwen2.5:0.5b    # Léger (0.5B paramètres) — recommandé pour démarrer
# ou
ollama pull mistral          # Meilleure qualité (7B paramètres)

# Modèle d'embeddings (vectorisation des documents)
ollama pull nomic-embed-text
```

### Démarrer le service Ollama

```bash
ollama serve
# Ollama écoute sur http://localhost:11434
```

Vérifiez que le service fonctionne :
```bash
curl http://localhost:11434/api/tags
```

---

## Étape 4 — Configurer Keycloak

Voir le guide dédié : [keycloak/README.md](../keycloak/README.md)

**Résumé rapide avec Docker :**
```bash
docker run -d \
  --name keycloak \
  -p 8080:8080 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  quay.io/keycloak/keycloak:latest \
  start-dev
```

Puis importez le realm depuis `keycloak/realm-export.json` via l'interface admin (http://localhost:8080/admin).

---

## Étape 5 — Lancer le backend FastAPI

### Créer l'environnement virtuel Python

```bash
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
# ou
.venv\Scripts\activate          # Windows PowerShell
```

### Installer les dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Créer les répertoires nécessaires

```bash
mkdir -p data/uploads data/chroma_db logs
```

### Lancer le serveur de développement

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

La base de données SQLite `data/app.db` est créée automatiquement au premier démarrage.

**Options utiles :**
```bash
# Changer le port
uvicorn api.main:app --reload --port 8001

# Mode production (sans rechargement automatique)
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2
```

---

## Étape 6 — Lancer le frontend React

```bash
cd frontend
npm install
npm run dev
```

Le frontend est accessible sur **http://localhost:5173**

**Commandes disponibles :**

| Commande | Description |
|---|---|
| `npm run dev` | Serveur de développement avec HMR |
| `npm run build` | Build de production optimisé |
| `npm run preview` | Prévisualisation du build de production |
| `npm run lint` | Analyse statique ESLint |

---

## Vérification

Une fois tous les services démarrés, vérifiez que tout fonctionne :

```bash
# Backend — Health check
curl http://localhost:8000/health
# Réponse attendue : {"status":"ok","llm_provider":"ollama","vector_store_provider":"chroma"}

# Backend — Endpoint racine
curl http://localhost:8000/
# Réponse attendue : {"app":"AssIA","status":"running"}

# Documentation interactive de l'API
open http://localhost:8000/docs       # Linux
# ou ouvrez l'URL dans votre navigateur
```

**URLs de l'application :**

| Service | URL |
|---|---|
| Interface utilisateur | http://localhost:5173 |
| API Backend | http://localhost:8000 |
| Documentation API (Swagger) | http://localhost:8000/docs |
| Documentation API (ReDoc) | http://localhost:8000/redoc |
| Keycloak Admin | http://localhost:8080/admin |
| Ollama API | http://localhost:11434 |

---

## Démarrage via Docker

Une alternative plus simple pour lancer tous les services simultanément :

```bash
# Copier et éditer la configuration
cp .env.example .env

# Démarrer tous les services
docker compose up -d

# Voir les logs
docker compose logs -f

# Arrêter les services
docker compose down
```

Voir [docs/deployment.md](./deployment.md) pour les options avancées de déploiement.

---

## Résolution des problèmes courants

### Erreur : `Connection refused` sur Ollama

```bash
# Vérifier que Ollama est bien lancé
ps aux | grep ollama
ollama serve &
```

### Erreur : `KEYCLOAK authentication failed`

1. Vérifiez que Keycloak est démarré sur le port 8080.
2. Vérifiez que le realm `assistant-reunions` a bien été importé.
3. Vérifiez les valeurs `KEYCLOAK_CLIENT_ID` et `KEYCLOAK_CLIENT_SECRET` dans `.env`.

### Erreur : `ChromaDB not found` ou collection vide

```bash
# Réinitialiser la base vectorielle
rm -rf data/chroma_db
mkdir -p data/chroma_db
# Redémarrer le backend — ChromaDB sera recréé automatiquement
```

### Erreur CORS au démarrage du frontend

Vérifiez que `CORS_ORIGINS` dans `.env` inclut bien l'URL du frontend :
```dotenv
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Port déjà utilisé

```bash
# Trouver le processus utilisant le port 8000
lsof -i :8000
# Puis le terminer ou changer le port dans .env (APP_PORT=8001)
```
