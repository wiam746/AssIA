# Référence API — AssIA

L'API AssIA est une API REST JSON construite avec FastAPI. La documentation interactive complète (Swagger UI) est disponible sur **http://localhost:8000/docs** lorsque le backend est démarré.

**Base URL :** `http://localhost:8000`  
**Préfixe API :** `/api`  
**Format des données :** JSON  
**Authentification :** `Authorization: Bearer <access_token>`

---

## Authentification

### POST `/api/auth/login`

Échange un identifiant/mot de passe contre un token Keycloak.

**Corps de la requête :**
```json
{
  "username": "john.doe",
  "password": "monMotDePasse"
}
```

**Réponse 200 :**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsIn...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIsIn...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Erreurs :**
- `401` — Identifiants invalides ou service Keycloak indisponible

---

### GET `/api/auth/me`

Retourne le profil de l'utilisateur authentifié.

**Headers requis :** `Authorization: Bearer <token>`

**Réponse 200 :**
```json
{
  "id": "a3f0d8c2-...",
  "email": "john.doe@entreprise.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## Chat

### POST `/api/chat/messages`

Envoie un message à l'assistant IA et reçoit une réponse sourcée.

**Corps de la requête :**
```json
{
  "message": "Quelles sont les décisions prises lors de la réunion du 15 janvier ?",
  "conversation_id": "c7e2a1b3-..."
}
```
> Si `conversation_id` est omis, une nouvelle conversation est créée automatiquement.

**Réponse 200 :**
```json
{
  "conversation_id": "c7e2a1b3-...",
  "message": {
    "id": "m8f3b2a1-...",
    "role": "assistant",
    "content": "Lors de la réunion du 15 janvier, les décisions suivantes ont été prises : ...",
    "created_at": "2024-01-20T14:22:10Z"
  },
  "sources": [
    "[Source: doc_reunion_jan] La décision principale porte sur...",
    "[Source: doc_reunion_jan] Il a également été décidé..."
  ]
}
```

---

### GET `/api/chat/conversations`

Liste toutes les conversations de l'utilisateur courant, triées par date de mise à jour décroissante.

**Réponse 200 :**
```json
[
  {
    "id": "c7e2a1b3-...",
    "title": "Quelles décisions lors de la réunion...",
    "created_at": "2024-01-20T14:20:00Z",
    "updated_at": "2024-01-20T14:22:10Z",
    "messages": []
  }
]
```

---

### GET `/api/chat/conversations/{conversation_id}`

Récupère une conversation avec l'intégralité de ses messages.

**Paramètre URL :** `conversation_id` (UUID)

**Réponse 200 :**
```json
{
  "id": "c7e2a1b3-...",
  "title": "Quelles décisions...",
  "created_at": "2024-01-20T14:20:00Z",
  "updated_at": "2024-01-20T14:22:10Z",
  "messages": [
    {
      "id": "m1a2b3c4-...",
      "role": "user",
      "content": "Quelles sont les décisions prises lors de la réunion du 15 janvier ?",
      "created_at": "2024-01-20T14:20:05Z"
    },
    {
      "id": "m8f3b2a1-...",
      "role": "assistant",
      "content": "Lors de la réunion du 15 janvier...",
      "created_at": "2024-01-20T14:22:10Z"
    }
  ]
}
```

---

### DELETE `/api/chat/conversations/{conversation_id}`

Supprime une conversation et tous ses messages.

**Réponse :** `204 No Content`

---

## Documents

### POST `/api/documents/upload`

Upload et indexe un document dans la base vectorielle.

**Corps de la requête :** `multipart/form-data`

| Champ | Type | Description |
|---|---|---|
| `file` | File | Fichier à uploader (PDF, DOCX, TXT, MD) |

**Taille maximale :** 25 Mo (configurable via `MAX_UPLOAD_SIZE_MB`)

**Réponse 200 :**
```json
{
  "message": "Document uploaded and indexing started",
  "document": {
    "id": "d1a2b3c4-...",
    "filename": "a1b2c3d4_compte_rendu.pdf",
    "original_filename": "compte_rendu_janvier.pdf",
    "file_size": 204800,
    "content_type": "application/pdf",
    "status": "processing",
    "created_at": "2024-01-20T14:00:00Z"
  }
}
```

**Statuts du document :**
| Statut | Description |
|---|---|
| `pending` | Fichier reçu, en attente de traitement |
| `processing` | Extraction et indexation en cours |
| `indexed` | Document indexé avec succès dans ChromaDB |
| `error` | Erreur lors du traitement (voir `error_message`) |

---

### GET `/api/documents`

Liste tous les documents de l'utilisateur courant.

**Réponse 200 :**
```json
[
  {
    "id": "d1a2b3c4-...",
    "filename": "a1b2c3d4_compte_rendu.pdf",
    "original_filename": "compte_rendu_janvier.pdf",
    "file_size": 204800,
    "status": "indexed",
    "created_at": "2024-01-20T14:00:00Z",
    "indexed_at": "2024-01-20T14:01:30Z"
  }
]
```

---

### DELETE `/api/documents/{document_id}`

Supprime un document du stockage et retire ses chunks du vector store.

**Réponse :** `204 No Content`

---

## Réunions

### POST `/api/reunions`

Crée un compte-rendu de réunion et déclenche l'analyse IA automatique.

**Corps de la requête :**
```json
{
  "title": "Synchronisation produit — Semaine 3",
  "raw_content": "Participants : Alice, Bob, Carol\nPoints abordés :\n1. Avancement sprint en cours...",
  "meeting_date": "2024-01-20T10:00:00Z",
  "participants": "Alice Martin, Bob Dupont, Carol Zhang"
}
```

**Réponse 200 :**
```json
{
  "id": "r1a2b3c4-...",
  "title": "Synchronisation produit — Semaine 3",
  "meeting_date": "2024-01-20T10:00:00Z",
  "participants": "Alice Martin, Bob Dupont, Carol Zhang",
  "summary": "La réunion a porté sur l'avancement du sprint 12...",
  "decisions": "1. Priorisation du bug #347\n2. Report de la démo au 25 janvier",
  "actions": "- Alice : livrer le correctif avant jeudi\n- Bob : préparer la présentation",
  "created_at": "2024-01-20T14:05:00Z"
}
```

---

### GET `/api/reunions`

Liste toutes les réunions de l'utilisateur.

**Réponse 200 :** Tableau de réunions (même structure que ci-dessus, sans `raw_content`)

---

## Incidents

### POST `/api/incidents`

Signale un incident et déclenche l'analyse IA.

**Corps de la requête :**
```json
{
  "title": "Latence élevée sur l'API de paiement",
  "description": "Depuis 14h30, les temps de réponse de l'endpoint /api/payment dépassent 5 secondes. Impacte 30% des transactions.",
  "severity": "majeur"
}
```

**Valeurs `severity` :** `mineur` | `majeur` | `critique`

**Réponse 200 :**
```json
{
  "id": "i1a2b3c4-...",
  "title": "Latence élevée sur l'API de paiement",
  "description": "Depuis 14h30...",
  "severity": "majeur",
  "status": "ouvert",
  "analysis": "L'incident semble lié à une surcharge de la base de données...\n\nRecommandations :\n1. Vérifier les connexions actives sur PostgreSQL\n2. Analyser les requêtes lentes (slow query log)\n3. Envisager une mise en cache Redis pour les appels répétitifs",
  "created_at": "2024-01-20T14:30:00Z"
}
```

**Valeurs `status` :** `ouvert` | `en_cours` | `resolu` | `ferme`

---

### GET `/api/incidents`

Liste tous les incidents signalés.

---

## Projets

### POST `/api/projets`

Crée un nouveau projet.

**Corps de la requête :**
```json
{
  "name": "Migration API v2",
  "description": "Réécriture complète de l'API REST en architecture microservices"
}
```

**Réponse 200 :**
```json
{
  "id": "p1a2b3c4-...",
  "name": "Migration API v2",
  "description": "Réécriture complète...",
  "status": "actif",
  "created_at": "2024-01-20T09:00:00Z",
  "updated_at": "2024-01-20T09:00:00Z"
}
```

---

### POST `/api/projets/{projet_id}/suggestions`

Génère des recommandations stratégiques IA pour les prochaines étapes du projet.

**Réponse 200 :**
```json
{
  "suggestions": "Pour la migration API v2, je recommande les étapes suivantes :\n\n1. Cartographier les endpoints existants...\n2. Définir les contrats d'interface (OpenAPI 3.0)...\n3. Prioriser la migration par domaine métier..."
}
```

---

## Emails

### POST `/api/emails/rediger`

Rédige un email professionnel à partir d'une instruction.

**Corps de la requête :**
```json
{
  "instruction": "Rédige un email de suivi post-réunion pour l'équipe produit, mentionnant les décisions prises concernant le sprint 12",
  "tone": "professionnel",
  "recipients": "equipe-produit@entreprise.com"
}
```

**Réponse 200 :**
```json
{
  "subject": "Suivi réunion — Décisions Sprint 12",
  "body": "Bonjour à tous,\n\nFaisant suite à notre réunion de ce jour...",
  "tone": "professionnel",
  "created_at": "2024-01-20T15:00:00Z"
}
```

---

## Endpoint de santé

### GET `/health`

Vérifie l'état de santé de l'application et de ses dépendances.

**Réponse 200 :**
```json
{
  "status": "ok",
  "llm_provider": "ollama",
  "vector_store_provider": "chroma"
}
```

**Valeurs `status` :**
- `ok` — Tous les services fonctionnent normalement
- `degraded` — Un ou plusieurs services sont indisponibles (Ollama ou ChromaDB)

---

## Codes d'erreur HTTP

| Code | Signification | Causes fréquentes |
|---|---|---|
| `400` | Requête invalide | Corps manquant, champ requis absent |
| `401` | Non authentifié | Token absent, expiré ou invalide |
| `403` | Accès interdit | Ressource appartenant à un autre utilisateur |
| `404` | Introuvable | Conversation, document ou projet inexistant |
| `422` | Erreur de validation | Type de données incorrect (Pydantic) |
| `500` | Erreur serveur | Exception non gérée, Ollama indisponible |

**Format des erreurs :**
```json
{
  "detail": "Conversation introuvable."
}
```
