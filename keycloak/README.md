# Keycloak — Guide de configuration

Ce guide explique comment configurer Keycloak pour l'authentification OIDC d'AssIA.

---

## Prérequis

- Keycloak ≥ 24.0 installé ou accessible via Docker
- Accès à l'interface d'administration Keycloak

---

## Démarrage rapide avec Docker

```bash
docker run -d \
  --name keycloak \
  -p 8080:8080 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  quay.io/keycloak/keycloak:latest \
  start-dev
```

L'interface admin est accessible sur : **http://localhost:8080/admin**

---

## Configuration manuelle

### 1. Créer le Realm

1. Connectez-vous à l'admin Keycloak : http://localhost:8080/admin
2. Cliquez sur le menu déroulant du realm (en haut à gauche) → **Create Realm**
3. **Realm name :** `assistant-reunions`
4. **Enabled :** On
5. Cliquez sur **Create**

### 2. Créer le Client

1. Dans le realm `assistant-reunions`, allez dans **Clients** → **Create client**
2. **Client type :** OpenID Connect
3. **Client ID :** `assistant-reunions-app`
4. Cliquez sur **Next**
5. Activez **Client authentication** (confidentiel)
6. Activez **Standard flow** et **Direct access grants** (pour le flow Resource Owner Password)
7. Cliquez sur **Next**
8. **Valid redirect URIs :** `http://localhost:5173/*`
9. **Web origins :** `http://localhost:5173`
10. Cliquez sur **Save**

### 3. Récupérer le Client Secret

1. Dans la fiche du client `assistant-reunions-app`
2. Allez dans l'onglet **Credentials**
3. Copiez la valeur de **Client secret**
4. Collez cette valeur dans votre fichier `.env` : `KEYCLOAK_CLIENT_SECRET=<valeur copiée>`

### 4. Configurer les mappers de tokens (champs utilisateur)

Pour que les champs `email` et `name` soient inclus dans le token JWT :

1. Allez dans **Clients** → `assistant-reunions-app` → **Client scopes**
2. Cliquez sur `assistant-reunions-app-dedicated`
3. Cliquez sur **Configure a new mapper** → **User Attribute**
4. Ajoutez les mappers suivants si non présents :
   - `email` → Mapper type: User Property, Token claim name: `email`
   - `full name` → Mapper type: User's full name, Token claim name: `name`

### 5. Créer un utilisateur de test

1. Allez dans **Users** → **Add user**
2. **Username :** `admin`
3. **Email :** `admin@test.com`
4. **First name / Last name :** renseignez
5. **Enabled :** On
6. Cliquez sur **Create**
7. Allez dans l'onglet **Credentials** → **Set password**
8. Entrez un mot de passe, désactivez **Temporary**
9. Cliquez sur **Save**

---

## Import du Realm depuis le fichier JSON

Pour importer automatiquement la configuration complète :

1. Dans l'admin Keycloak, cliquez sur le menu déroulant → **Create Realm**
2. Cliquez sur **Browse** et sélectionnez `keycloak/realm-export.json`
3. Cliquez sur **Create**

> **Note :** Après l'import, pensez à régénérer le client secret et à mettre à jour votre `.env`.

---

## Variables .env correspondantes

```dotenv
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=assistant-reunions
KEYCLOAK_CLIENT_ID=assistant-reunions-app
KEYCLOAK_CLIENT_SECRET=<votre-client-secret>
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=admin
JWT_ALGORITHM=RS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

## Vérifier la configuration

```bash
# Tester l'authentification directement via Keycloak
curl -X POST \
  "http://localhost:8080/realms/assistant-reunions/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=assistant-reunions-app" \
  -d "client_secret=VOTRE_CLIENT_SECRET" \
  -d "username=admin" \
  -d "password=VOTRE_MOT_DE_PASSE"

# Réponse attendue : {"access_token":"eyJ...","expires_in":3600,...}
```

---

## Résolution des problèmes

### Erreur `401 — Cle de signature inconnue`

Le backend ne peut pas accéder aux JWKS. Vérifiez :
- Que Keycloak est démarré et accessible sur `KEYCLOAK_SERVER_URL`
- Que le nom du realm est correct (`KEYCLOAK_REALM`)

```bash
# Tester l'accès aux JWKS
curl http://localhost:8080/realms/assistant-reunions/protocol/openid-connect/certs
```

### Erreur `Nom d'utilisateur ou mot de passe incorrect`

- Vérifiez que `Direct access grants` est activé dans les paramètres du client Keycloak
- Vérifiez que l'utilisateur est actif et que le mot de passe est correct
- Vérifiez que `KEYCLOAK_CLIENT_SECRET` correspond bien au secret affiché dans l'onglet Credentials du client
