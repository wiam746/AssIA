# AssIA — Assistant Interne IA 

<div align="center">

![AssIA Banner](https://img.shields.io/badge/AssIA-1.0.0-059669?style=for-the-badge&logo=robot&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-18.3-61DAFB?style=flat-square&logo=react)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-000000?style=flat-square&logo=ollama)

**Plateforme IA interne propulsée par un pipeline RAG 100% local (Ollama + ChromaDB) pour synthétiser les réunions, diagnostiquer les incidents et piloter les projets d'équipe.**

[Documentation](#documentation) · [Installation rapide](#-démarrage-rapide) · [Évaluation RAG](#-évaluation-du-pipeline-rag)

</div>

---

## Table des matières

- [À propos du projet](#-à-propos-du-projet)
- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Technologies utilisées](#-technologies-utilisées)
- [Prérequis](#-prérequis)
- [Démarrage rapide](#-démarrage-rapide)
- [Évaluation du Pipeline RAG](#-évaluation-du-pipeline-rag)
- [Structure du projet](#-structure-du-projet)
- [Documentation](#-documentation)
- [Licence](#-licence)

---

## 📋 À propos du projet

**AssIA** est un assistant IA entreprise souverain et 100% local. Il est conçu pour permettre aux équipes métier d'analyser leurs comptes-rendus, spécifications et guides sans **jamais transférer de données sensibles vers des services cloud tiers**.

Le pipeline **RAG (Retrieval-Augmented Generation)** s'appuie exclusivement sur des modèles open-source locaux exécutés via [Ollama](https://ollama.ai/) (`Qwen 2.5` ou `Mistral`) pour la génération et les embeddings (`nomic-embed-text`), combinés à la base vectorielle [ChromaDB](https://www.trychroma.com/).

### Pourquoi AssIA ?

| Besoin Métier | Solution AssIA Local |
|---|---|
| Résumer automatiquement les réunions | Agent `MeetingAgent` + LLM local (Qwen 2.5 / Mistral) |
| Diagnostiquer et tracer les incidents | Agent `IncidentAgent` avec analyse contextuelle |
| Retrouver une information dans des documents | Pipeline RAG + Vector Store ChromaDB |
| Piloter les projets avec recommandations IA | Agent `ProjectAgent` |
| Souveraineté & Confidentialité totale | **100% local**, aucun appel cloud ni clé API externe |
| Authentification sécurisée entreprise | Keycloak OIDC avec validation JWT (RS256) |

---

## ✨ Fonctionnalités

- 💬 **Chat IA RAG Scopé** — Posez des questions ciblées sur vos documents, projets ou incidents
- 📁 **Upload & Indexation instantanée** — Découpage et vectorisation automatique des PDF, DOCX, TXT, MD
- 📝 **Synthèse de réunions** — Génération de compte-rendu, décisions clés et plan d'actions
- 🚨 **Gestion d'incidents** — Signalement, classification de sévérité et recommandations de résolution
- 📊 **Suivi de projets** — Recommandations stratégiques et jalons pour les équipes
- 📚 **Bibliothèque de documents** — Gestion des droits et des collections vectorielles
- 🔐 **Sécurité Keycloak** — Gestion des rôles et contrôle d'accès basé sur les jetons JWT
- ⚡ **Évaluation automatisée** — Suite de tests quantitatifs pour mesurer la précision du RAG

---

## 🏛️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   FRONTEND (React + Vite)                    │
│  Login/Register · Chat · Bibliothèque · Réunions · Incidents │
└───────────────────────────┬──────────────────────────────────┘
                            │ REST API (JSON + Bearer JWT)
┌───────────────────────────▼──────────────────────────────────┐
│               BACKEND (FastAPI, port 8000)                   │
│                                                              │
│  /api/auth  /api/chat  /api/documents  /api/reunions         │
│  /api/incidents  /api/projets  /api/emails                   │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────────┐   │
│  │ ChatAgent  │  │MeetingAgent│  │ IncidentAgent        │   │
│  │   RAG +    │  │ Résumé +   │  │ Diagnostic + Analyse │   │
│  │ LLM Local  │  │ Décisions  │  │                      │   │
│  └─────┬──────┘  └─────┬──────┘  └──────────┬───────────┘   │
│        │               │                     │               │
│  ┌─────▼───────────────▼─────────────────────▼───────────┐  │
│  │                   RagService                           │  │
│  │    DocumentProcessor → VectorStore → LLM Service      │  │
│  └─────────────────────────────────────────────────────┬─┘  │
└────────────────────────────────────────────────────────┼────┘
                                                         │
┌────────────────────────────────────────────────────────▼────┐
│              SERVICES LOCAUX & ON-PREMISE                    │
│  Ollama (Qwen 2.5 / Mistral)  ChromaDB  SQLite  Keycloak  │
└─────────────────────────────────────────────────────────────┘
```

**Pipeline RAG 100% Local :**

1. **Ingestion** : `DocumentProcessor` extrait le texte et applique un chunking de 500 caractères (overlap 80 chars)
2. **Embedding** : Vectorisation locale via `nomic-embed-text` d'Ollama
3. **Indexation** : Persistance dans ChromaDB en recherche par similarité cosinus
4. **Retrieval** : Extraction du Top-5 des chunks pertinents avec filtre de périmètre
5. **Génération** : Prompting strict de `qwen2.5:0.5b` ou `qwen2.5:3b` / `mistral` sans hallucination

---

## 🛠️ Technologies utilisées

### Backend & IA
| Composant | Technologie | Description |
|---|---|---|
| Framework API | FastAPI (0.111) | Serveur ASGI Uvicorn haute performance |
| ORM & BDD | SQLAlchemy 2.0 + SQLite | Persistance des réunions, incidents et projets |
| Engine LLM Local | Ollama | Modèles `qwen2.5:0.5b`, `qwen2.5:3b` ou `mistral` |
| Embeddings | Ollama (`nomic-embed-text`) | Modèle d'embedding vectoriel (768 dim) |
| Base Vectorielle | ChromaDB | Vector Store local persistant |
| Authentification | Keycloak OIDC | Validation JWT RS256 |

### Frontend
| Composant | Technologie | Description |
|---|---|---|
| UI Framework | React 18.3 + TypeScript | Single Page Application (SPA) |
| Build Tool | Vite 5.3 | Compilation et serveur de dév ultra-rapide |
| Design & Style | Vanilla CSS / CSS Modules | Design moderne et réactif |
| Icônes | Lucide React | Icônes d'interface |

---

## 📦 Prérequis

Avant de lancer le projet, vérifiez que votre système dispose de :

- **Python** ≥ 3.11
- **Node.js** ≥ 18 et **npm** ≥ 9
- **Ollama** — [Télécharger Ollama](https://ollama.ai/download)
- **Docker & Docker Compose** (Optionnel pour Keycloak)

---

## 🚀 Démarrage rapide

### 1. Cloner le projet
```bash
git clone https://github.com/votre-organisation/assistant-reunions.git
cd assistant-reunions
```

### 2. Démarrer et configurer Ollama (LLM Local)
Assurez-vous que le service Ollama est lancé, puis téléchargez les modèles requis :
```bash
# Téléchargement du LLM de génération (Qwen 2.5 ou Mistral)
ollama pull qwen2.5:0.5b

# Téléchargement du modèle d'embeddings
ollama pull nomic-embed-text
```

### 3. Configuration des variables d'environnement
Copiez le fichier de modèle d'environnement :
```bash
cp .env.example .env
```
*(Le fichier `.env` est déjà préconfiguré pour fonctionner en mode Ollama local).*

### 4. Lancer le Backend (Python FastAPI)
```bash
python -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Lancer le Frontend (React + Vite)
Dans une seconde fenêtre de terminal :
```bash
cd frontend
npm install
npm run dev
```

L'application Web est accessible sur **http://localhost:5173**  
L'API REST et la documentation OpenAPI sur **http://localhost:8000/docs**

---

## 📊 Évaluation du Pipeline RAG

AssIA intègre une suite d'évaluation automatisée pour mesurer objectivement les performances du système (Retrieval, Triade RAG, Latence) :

```bash
PYTHONPATH=. .venv/bin/python scripts/evaluate_rag.py
```

Le script calcule les métriques suivantes et génère des graphiques dans `docs/evaluation/charts/` :
* **Precision@K & Recall@K** : Mesure de la qualité du Vector Store (Recall@5 = 100%).
* **Triade RAG** : Évaluation de la *Faithfulness* (100% sans hallucination) et de la pertinence des réponses.
* **Décomposition de Latence** : Temps de parsing, vectorisation, et temps du premier token (TTFT).

Consultez le [Rapport d'évaluation complet](./docs/evaluation_report.md) pour l'analyse détaillée.

---

## 📁 Structure du projet

```
assistant-reunions/
├── 📄 README.md
├── 📄 .env.example              # Modèle de configuration local
├── 📄 requirements.txt          # Dépendances Python backend
├── 📄 docker-compose.yml        # Service Keycloak et stack complète
│
├── 📂 api/                      # API REST FastAPI
│   ├── main.py                  # Application FastAPI
│   ├── auth.py                  # Décodeur JWT Keycloak
│   └── routes/                  # Endpoints (Chat, Documents, Réunions, Incidents, Projets)
│
├── 📂 agents/                   # Agents IA métier
│   ├── chat_agent.py            # Agent RAG conversationnel
│   ├── meeting_agent.py         # Agent de synthèse de réunions
│   ├── incident_agent.py        # Agent de diagnostic d'incidents
│   └── project_agent.py         # Agent de suivi de projets
│
├── 📂 core/                     # Cœur RAG & LLM
│   ├── document_processor.py    # Chunking et extraction textuelle
│   ├── llm/                     # Provider Ollama local
│   ├── embedding/               # Provider Embedding nomic-embed-text
│   └── vector_store/            # Gestionnaire ChromaDB local
│
├── 📂 services/                 # Logique métier et orchestration
│   ├── rag_service.py           # Service central RAG
│   └── ...
│
├── 📂 frontend/                 # Application Web React/TypeScript
│   ├── src/
│   │   ├── components/          # ChatWindow, Sidebar, etc.
│   │   └── pages/               # Vues applicatives
│   └── package.json
│
├── 📂 docs/                     # Documentation et rapports d'évaluation
│   ├── evaluation_report.md     # Rapport technique RAG
│   ├── evaluation/charts/       # Graphiques de benchmark
│   └── ...
│
└── 📂 scripts/                  # Scripts utilitaires
    ├── evaluate_rag.py          # Benchmark automatisé RAG
    ├── reset_password.py        # Re-initialisation d'accès
    └── setup_environment.sh     # Script d'installation shell
```

---

## 📚 Documentation

| Fichier | Description |
|---|---|
| [Evaluation Report](./docs/evaluation_report.md) | Rapport de performance et benchmarks RAG |
| [Architecture](./docs/architecture.md) | Diagrammes et détails d'architecture technique |
| [Installation](./docs/installation.md) | Guide pas-à-pas de déploiement |
| [Keycloak](./keycloak/README.md) | Guide de configuration Keycloak OIDC |

