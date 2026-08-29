# Guide de déploiement — AssIA

Ce guide décrit les procédures de déploiement d'AssIA en environnement **staging** ou **production** via Docker Compose.

---

## Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Déploiement avec Docker Compose](#déploiement-avec-docker-compose)
- [Variables d'environnement de production](#variables-denvironnement-de-production)
- [Configuration Keycloak en production](#configuration-keycloak-en-production)
- [Configuration HTTPS avec Nginx (reverse proxy)](#configuration-https-avec-nginx-reverse-proxy)
- [Sauvegarde et persistance des données](#sauvegarde-et-persistance-des-données)
- [Monitoring et logs](#monitoring-et-logs)
- [Mise à jour de l'application](#mise-à-jour-de-lapplication)
- [Checklist de déploiement](#checklist-de-déploiement)

---

## Vue d'ensemble

L'architecture de déploiement type comprend :

```
Internet
    │
    ▼
[ Nginx (HTTPS / 443) ]    ← Reverse proxy + TLS
    │
    ├──▶ [ Frontend (React/Nginx) ]   Port 80 interne
    │
    ├──▶ [ Backend FastAPI ]          Port 8000 interne
    │
    ├──▶ [ Keycloak ]                 Port 8080 interne
    │
    └──▶ [ Ollama ]                   Port 11434 interne (non exposé publiquement)

[ ChromaDB ]     ← Volume Docker persistant
[ SQLite ]       ← Volume Docker persistant
```

---

## Déploiement avec Docker Compose

### 1. Préparer l'environnement serveur

```bash
# Prérequis : Docker Engine 24+ et Docker Compose v2
docker --version
docker compose version

# Cloner le dépôt sur le serveur
git clone https://github.com/votre-organisation/assistant-reunions.git
cd assistant-reunions
```

### 2. Configurer les variables de production

```bash
cp .env.example .env
# Éditer .env avec les valeurs de production
nano .env
```

### 3. Démarrer tous les services

```bash
# Démarrer en arrière-plan
docker compose up -d

# Voir les logs en temps réel
docker compose logs -f

# Vérifier l'état des conteneurs
docker compose ps
```

### 4. Vérifier le déploiement

```bash
# Health check du backend
curl https://votre-domaine.com/health

# Vérifier que le frontend est accessible
curl -I https://votre-domaine.com
```

---

## Variables d'environnement de production

Pour un déploiement en production, modifiez obligatoirement ces variables :

```dotenv
# ============================================================
# PRODUCTION — Variables obligatoires à modifier
# ============================================================

APP_ENV=production
APP_DEBUG=false

# Clé secrète aléatoire longue (min 64 caractères)
SECRET_KEY=votre-cle-secrete-aleatoire-tres-longue-et-complexe

# URL de votre domaine en production
CORS_ORIGINS=https://votre-domaine.com,https://www.votre-domaine.com

# Base de données (SQLite en prod ou migrer vers PostgreSQL)
DATABASE_URL=sqlite:///./data/app.db

# LLM — pointer vers le service Ollama dans le réseau Docker
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=mistral                    # ou llama3.2, qwen2.5:7b

# Keycloak — URL interne Docker
KEYCLOAK_SERVER_URL=http://keycloak:8080
KEYCLOAK_REALM=assistant-reunions
KEYCLOAK_CLIENT_ID=assistant-reunions-app
KEYCLOAK_CLIENT_SECRET=votre-secret-client-genere-par-keycloak
KEYCLOAK_ADMIN_PASSWORD=mot-de-passe-admin-fort-et-unique

# Logs
LOG_LEVEL=INFO
```

> ⚠️ **Sécurité :** Ne commitez jamais `.env` dans Git. Utilisez un gestionnaire de secrets (HashiCorp Vault, AWS Secrets Manager, etc.) en production.

---

## Configuration Keycloak en production

### Paramètres importants à ajuster

1. **Désactiver le mode développement** : Dans l'admin Keycloak, passer Keycloak en mode production (`start` au lieu de `start-dev`)

2. **Configurer les URLs valides de redirection** :
   - Valid redirect URIs : `https://votre-domaine.com/*`
   - Web origins : `https://votre-domaine.com`

3. **Changer les mots de passe par défaut** :
   - Mot de passe admin Keycloak
   - Client secret Keycloak (régénérer depuis Clients → Credentials)

4. **Activer le chiffrement de la base Keycloak** : Utiliser PostgreSQL pour Keycloak en production plutôt que H2 embarqué

---

## Configuration HTTPS avec Nginx (reverse proxy)

Exemple de configuration Nginx pour terminer TLS et proxyfier vers les services :

```nginx
# /etc/nginx/sites-available/assIA

server {
    listen 80;
    server_name votre-domaine.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votre-domaine.com;

    ssl_certificate     /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;

    # Frontend React
    location / {
        proxy_pass         http://localhost:5173;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass         http://localhost:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        client_max_body_size 30M;     # Augmenter pour l'upload de fichiers
    }

    # FastAPI Health
    location /health {
        proxy_pass http://localhost:8000/health;
    }

    # Keycloak Auth
    location /auth/ {
        proxy_pass         http://localhost:8080;
        proxy_set_header   Host $host;
        proxy_buffer_size  128k;
        proxy_buffers      4 256k;
        proxy_busy_buffers_size 256k;
    }
}
```

**Obtenir un certificat SSL Let's Encrypt :**
```bash
certbot --nginx -d votre-domaine.com
```

---

## Sauvegarde et persistance des données

### Données à sauvegarder

| Emplacement | Contenu | Criticité |
|---|---|---|
| `data/app.db` | Base SQLite (users, conversations, documents) | ⭐⭐⭐ Critique |
| `data/chroma_db/` | Base vectorielle ChromaDB | ⭐⭐⭐ Critique |
| `data/uploads/` | Fichiers uploadés originaux | ⭐⭐ Important |
| `logs/` | Logs applicatifs | ⭐ Secondaire |

### Script de sauvegarde automatique

```bash
#!/bin/bash
# backup.sh — Sauvegarde quotidienne des données AssIA

BACKUP_DIR="/backups/assIA/$(date +%Y%m%d)"
APP_DIR="/opt/assistant-reunions"

mkdir -p "$BACKUP_DIR"

# Copier la base SQLite
cp "$APP_DIR/data/app.db" "$BACKUP_DIR/app.db"

# Copier ChromaDB
cp -r "$APP_DIR/data/chroma_db" "$BACKUP_DIR/chroma_db"

# Compresser
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

# Conserver 30 jours de sauvegardes
find /backups/assIA -name "*.tar.gz" -mtime +30 -delete

echo "Sauvegarde terminée : $BACKUP_DIR.tar.gz"
```

```bash
# Ajouter en crontab (sauvegarde à 2h du matin chaque jour)
crontab -e
# 0 2 * * * /opt/scripts/backup.sh >> /var/log/assIA-backup.log 2>&1
```

---

## Monitoring et logs

### Consulter les logs

```bash
# Logs backend FastAPI (stdout du conteneur)
docker compose logs backend -f

# Logs écrits dans le fichier applicatif
tail -f logs/app.log

# Logs avec filtrage par niveau
grep "ERROR" logs/app.log
grep "WARNING" logs/app.log
```

### Health check automatique

```bash
# Script de surveillance simple
#!/bin/bash
HEALTH=$(curl -s http://localhost:8000/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'])")
if [ "$HEALTH" != "ok" ]; then
    echo "ALERTE: AssIA en état dégradé — $HEALTH" | mail -s "AssIA Alert" admin@entreprise.com
fi
```

---

## Mise à jour de l'application

```bash
# 1. Récupérer les nouvelles versions
git pull origin main

# 2. Reconstruire les images Docker
docker compose build --no-cache

# 3. Redémarrer les services avec zéro temps d'arrêt
docker compose up -d --force-recreate

# 4. Vérifier que tout fonctionne
docker compose ps
curl http://localhost:8000/health
```

---

## Checklist de déploiement

Avant de déployer en production, vérifiez chaque point :

- [ ] `APP_ENV=production` dans `.env`
- [ ] `APP_DEBUG=false` dans `.env`
- [ ] `SECRET_KEY` changé pour une valeur aléatoire forte
- [ ] Mot de passe admin Keycloak changé
- [ ] Client secret Keycloak régénéré et renseigné dans `.env`
- [ ] `CORS_ORIGINS` configuré avec l'URL de production uniquement
- [ ] HTTPS configuré et certificat SSL valide
- [ ] Sauvegardes automatiques planifiées (crontab)
- [ ] Monitoring/alerting configuré
- [ ] `.env` exclu de Git (`.gitignore`)
- [ ] Modèles Ollama disponibles sur le serveur de production
- [ ] Répertoires `data/` et `logs/` créés avec les bons droits
