# Architecture technique — AssIA

Ce document décrit l'architecture technique détaillée d'AssIA : pipeline RAG, agents IA, couche API, base de données, authentification et frontend.

---

## Vue d'ensemble

AssIA suit une architecture **multi-couches** organisée autour d'un pipeline RAG (Retrieval-Augmented Generation) 100% local :

```
┌─────────────────────────────────────────────────────────────────┐
│                     UTILISATEUR (Navigateur)                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTPS / REST JSON
┌───────────────────────────▼─────────────────────────────────────┐
│                  FRONTEND — React 18 + Vite + Tailwind          │
│                                                                 │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌────────┐            │
│  │  Login   │ │  Chat IA  │ │Réunions  │ │Projets │ ...        │
│  │ Register │ │ + Upload  │ │          │ │        │            │
│  └──────────┘ └───────────┘ └──────────┘ └────────┘            │
│                                                                 │
│  AuthContext (JWT)  ·  React Router  ·  Axios  ·  Lucide Icons  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                    Validation JWT RS256
                    (Keycloak JWKS)
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│             BACKEND — FastAPI 0.111 (ASGI / Uvicorn)            │
│                        Port 8000                                │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ /auth    │  │  /chat   │  │/documents│  │  /reunions   │   │
│  │          │  │          │  │          │  │  /incidents  │   │
│  │ login    │  │ messages │  │ upload   │  │  /projets    │   │
│  │ /me      │  │ convs    │  │ list/del │  │  /emails     │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘   │
│       │             │              │                │           │
│  ┌────▼─────────────▼──────────────▼────────────────▼──────┐   │
│  │               COUCHE AGENTS IA                          │   │
│  │                                                         │   │
│  │  ChatAgent  MeetingAgent  IncidentAgent  ProjectAgent   │   │
│  │                     EmailAgent                          │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            │                                   │
│  ┌─────────────────────────▼───────────────────────────────┐   │
│  │                   COUCHE CORE RAG                       │   │
│  │                                                         │   │
│  │  DocumentProcessor  →  RagService  →  LLMService       │   │
│  │  (Extraction/Chunking) (Retrieval)   (Génération)       │   │
│  └───────────┬──────────────────┬──────────────────────────┘   │
│              │                  │                              │
│         SQLAlchemy          ChromaDB              Ollama       │
│         (SQLite)            (Vectoriel)          (HTTP REST)   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Pipeline RAG (Retrieval-Augmented Generation)

Le pipeline RAG est le cœur d'AssIA. Il permet de répondre à des questions en s'appuyant sur les documents indexés plutôt que sur la seule mémoire du LLM.

### 1.1 Phase d'ingestion (indexation)

```
Fichier (PDF/DOCX/TXT/MD)
         │
         ▼
DocumentProcessor.process()
         │
         ├─ Extraction du texte brut selon le format
         │   ├─ PDF    → pypdf
         │   ├─ DOCX   → python-docx
         │   └─ TXT/MD → lecture directe
         │
         ├─ Nettoyage et normalisation du texte
         │
         └─ Chunking (découpage en segments)
              │   taille : configurable (défaut ~500 tokens)
              │   chevauchement : ~50 tokens
              ▼
         VectorDocument[]
              │
              ▼
         EmbeddingProvider.embed_texts()    ← Ollama (nomic-embed-text)
              │   Vecteurs de dimension 768
              ▼
         ChromaDB.add_documents()
              │   Collection : "documents"
              ▼
         ✅ Chunks indexés dans chroma.sqlite3
```

### 1.2 Phase de retrieval (récupération de contexte)

```
Question utilisateur
         │
         ▼
EmbeddingProvider.embed_text()     ← Vecteur de la question
         │
         ▼
ChromaDB.similarity_search()       ← Recherche cosinus top-K
         │   K = 5 par défaut
         ▼
List[VectorSearchResult]
         │
         ▼
RagService.retrieve_context_as_text()
         │   Format : "[Source: doc_id] texte du chunk"
         ▼
Contexte formaté pour le prompt
```

### 1.3 Phase de génération

```
Contexte RAG + Historique + Question
         │
         ▼
system_prompt = get_chat_system_prompt(context_chunks, user_name)
         │
         ▼
LLMService.ask()
         │
         └─ POST http://localhost:11434/api/chat (Ollama API)
              │   Modèle : qwen2.5:0.5b (ou mistral)
              │   Temperature : 0.3
              │   Max tokens : 2048
              ▼
         Réponse LLM
              │
              ▼
ChatAnswer(content=..., sources=[...])
```

---

## 2. Couche Agents IA (`agents/`)

Chaque agent est une classe spécialisée qui orchestre le pipeline RAG + LLM pour un domaine métier précis.

| Agent | Fichier | Rôle |
|---|---|---|
| `ChatAgent` | `agents/chat_agent.py` | Chat conversationnel RAG général |
| `MeetingAgent` | `agents/meeting_agent.py` | Résumé, décisions, plan d'actions des réunions |
| `IncidentAgent` | `agents/incident_agent.py` | Diagnostic et recommandations sur les incidents |
| `ProjectAgent` | `agents/project_agent.py` | Suggestions stratégiques pour les projets |
| `EmailAgent` | `agents/email_agent.py` | Rédaction et analyse d'emails professionnels |

### Architecture d'un agent type

```python
class MeetingAgent:
    def __init__(self, llm_service, rag_service):
        self.llm = llm_service or LLMService()
        self.rag = rag_service or RagService()

    async def summarize(self, raw_content, title):
        context = await self.rag.retrieve_context_as_text(raw_content, top_k=3)
        prompt  = get_meeting_system_prompt(context)
        answer  = await self.llm.ask(raw_content, system_prompt=prompt)
        # Parsing structuré : résumé / décisions / actions
        return MeetingAnalysis(...)
```

---

## 3. Couche API REST (`api/`)

### Routes disponibles

| Préfixe | Méthodes | Description |
|---|---|---|
| `POST /api/auth/login` | POST | Échange identifiants contre token Keycloak |
| `GET /api/auth/me` | GET | Profil utilisateur courant |
| `POST /api/chat/messages` | POST | Envoyer un message à l'assistant |
| `GET /api/chat/conversations` | GET | Lister les conversations |
| `GET /api/chat/conversations/{id}` | GET | Détails + messages d'une conversation |
| `DELETE /api/chat/conversations/{id}` | DELETE | Supprimer une conversation |
| `POST /api/documents/upload` | POST | Uploader et indexer un document |
| `GET /api/documents` | GET | Lister les documents indexés |
| `DELETE /api/documents/{id}` | DELETE | Supprimer un document et ses chunks |
| `POST /api/reunions` | POST | Créer et analyser une réunion |
| `GET /api/reunions` | GET | Lister les réunions |
| `POST /api/incidents` | POST | Signaler et analyser un incident |
| `GET /api/incidents` | GET | Lister les incidents |
| `POST /api/projets` | POST | Créer un projet |
| `POST /api/projets/{id}/suggestions` | POST | Générer des recommandations IA |
| `POST /api/emails/rediger` | POST | Rédiger un email |
| `POST /api/emails/analyser` | POST | Analyser un email |
| `GET /health` | GET | Health check (LLM + VectorStore) |

### Authentification

Toutes les routes (sauf `/api/auth/login` et `/health`) nécessitent un en-tête `Authorization: Bearer <token>`.

Le middleware `get_current_user` (dans `api/auth.py`) :
1. Extrait le token JWT du header
2. Récupère les clés publiques JWKS de Keycloak (`/realms/{realm}/protocol/openid-connect/certs`)
3. Décode et vérifie le token (algorithme RS256, vérification de signature)
4. Synchronise l'utilisateur en base locale (`users` table)

---

## 4. Modèle de données (`models/database.py`)

### Schéma relationnel

```
┌──────────────┐       ┌──────────────────┐      ┌─────────────┐
│    users     │       │   conversations  │      │  messages   │
│──────────────│       │──────────────────│      │─────────────│
│ id (PK)      │──1:N──│ id (PK)          │──1:N─│ id (PK)     │
│ email        │       │ user_id (FK)     │      │ conv_id(FK) │
│ full_name    │       │ title            │      │ role        │
│ is_active    │       │ created_at       │      │ content     │
│ created_at   │       │ updated_at       │      │ created_at  │
└──────────────┘       └──────────────────┘      └─────────────┘
       │
       │──1:N──┌──────────────┐
       │       │  documents   │
       │       │──────────────│
       │       │ id (PK)      │
       │       │ filename     │
       │       │ file_path    │
       │       │ status       │  ← pending|processing|indexed|error
       │       │ uploaded_by  │
       │       └──────────────┘
       │
       │──1:N──┌──────────────┐
       │       │   reunions   │
       │       │──────────────│
       │       │ id (PK)      │
       │       │ title        │
       │       │ raw_content  │
       │       │ summary      │
       │       │ decisions    │
       │       │ actions      │
       │       └──────────────┘
       │
       │──1:N──┌──────────────┐
       │       │  incidents   │
       │       │──────────────│
       │       │ id (PK)      │
       │       │ severity     │  ← mineur|majeur|critique
       │       │ status       │  ← ouvert|en_cours|resolu|ferme
       │       │ analysis     │
       │       └──────────────┘
       │
       └──1:N──┌──────────────┐
               │   projets    │
               │──────────────│
               │ id (PK)      │
               │ name         │
               │ status       │  ← actif|en_pause|termine|archive
               └──────────────┘
```

---

## 5. Authentification — Keycloak OIDC

```
Frontend                    Backend (FastAPI)              Keycloak
   │                               │                          │
   │── POST /api/auth/login ──────▶│                          │
   │   {username, password}        │                          │
   │                               │── POST /token ──────────▶│
   │                               │   grant_type=password    │
   │                               │◀─ {access_token, ...} ───│
   │◀─ {access_token} ─────────────│                          │
   │                               │                          │
   │── GET /api/chat/conversations ▶│                         │
   │   Authorization: Bearer TOKEN  │                         │
   │                               │── GET /certs ───────────▶│
   │                               │◀─ JWKS (clés publiques) ─│
   │                               │── Vérifier signature JWT │
   │                               │── Synchroniser user DB   │
   │◀─ [conversations...] ─────────│                          │
```

Le token JWT contient notamment :
- `sub` : identifiant unique Keycloak (utilisé comme `user.id` en base)
- `email` : email de l'utilisateur
- `name` / `preferred_username` : nom affiché

---

## 6. Frontend — Architecture React

```
src/
├── context/AuthContext.tsx      # État global d'authentification (token, user)
├── hooks/
│   ├── useAuth.ts               # Accès simplifié à AuthContext
│   ├── useApi.ts                # Instance Axios configurée (base URL + intercepteurs)
│   └── useChat.ts               # Gestion état messages + sendMessage + loadConversation
├── pages/
│   ├── Login.tsx                # Connexion / Inscription + modal CGU
│   ├── ChatPage.tsx             # Composant page chat (délègue à ChatWindow)
│   ├── Bibliotheque.tsx         # Gestion bibliothèque documentaire
│   ├── Meetings.tsx             # Création et affichage des réunions
│   ├── Incidents.tsx            # Signalement et suivi des incidents
│   └── Projects.tsx             # Gestion des projets + suggestions IA
└── components/
    ├── Layout.tsx               # Gabarit : Sidebar + <Outlet>
    ├── Sidebar.tsx              # Navigation + historique des chats
    ├── ProtectedRoute.tsx       # Garde de route (redirect /login si non-auth)
    ├── ChatWindow.tsx           # Fenêtre de chat + bouton upload fichier
    ├── MessageBubble.tsx        # Bulle de message (user/assistant)
    ├── DocumentCard.tsx         # Carte document avec statut d'indexation
    ├── DocumentUploader.tsx     # Bouton d'upload fichier
    └── ChatHistoryItem.tsx      # Item d'historique de conversation
```

### Flux d'authentification

```
Utilisateur visite /chat
         │
         ▼
ProtectedRoute vérifie AuthContext.token
         │
    Non-authentifié? → Redirect /login
         │
    Authentifié?    → Render <Layout>
                          ├── <Sidebar> (nav + historique)
                          └── <Outlet> → <ChatPage>
```

---

## 7. Configuration (`config/settings.py`)

La configuration est centralisée via **Pydantic-Settings**, qui lit automatiquement les variables depuis `.env` :

| Variable | Défaut | Description |
|---|---|---|
| `APP_ENV` | `development` | Environnement (`development`, `staging`, `production`) |
| `DATABASE_URL` | `sqlite:///./data/app.db` | URL SQLAlchemy |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL du service Ollama |
| `OLLAMA_MODEL` | `qwen2.5:0.5b` | Modèle LLM de génération |
| `OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text` | Modèle d'embeddings |
| `CHROMA_PERSIST_DIR` | `./data/chroma_db` | Répertoire de persistance ChromaDB |
| `KEYCLOAK_SERVER_URL` | `http://localhost:8080` | URL du serveur Keycloak |
| `MAX_UPLOAD_SIZE_MB` | `25` | Taille max des fichiers uploadés |

---

## 8. Logging

Les logs sont configurés via `config/logging.yaml`. Ils sont écrits :
- En console (format coloré en développement)
- Dans `logs/app.log` (rotation quotidienne, 30 jours de rétention)

Niveaux utilisés :
- `DEBUG` : Détails de l'exécution du pipeline RAG (nombre de chunks, tokens)
- `INFO` : Événements normaux (démarrage, connexions, indexations)
- `WARNING` : Situations anormales non-bloquantes (authentification échouée)
- `ERROR` : Erreurs bloquantes (Ollama indisponible, document corrompu)
