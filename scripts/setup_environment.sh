#!/usr/bin/env bash
# ==============================================================================
# Script de configuration de l'environnement AssIA (FastAPI + React)
# ==============================================================================

set -euo pipefail

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Initialisation de l'environnement AssIA ===${NC}"

# 1. Vérification des prérequis
echo -e "\n${BLUE}1. Vérification des outils requis...${NC}"
for cmd in python3 node npm; do
    if ! command -v "$cmd" &> /dev/null; then
        echo -e "${RED}Erreur : $cmd n'est pas installé. Veuillez l'installer et réessayer.${NC}"
        exit 1
    fi
    echo -e "  - $cmd: ${GREEN}OK${NC} ($( $cmd --version | head -n 1 ))"
done

# 2. Création de l'environnement virtuel Python
echo -e "\n${BLUE}2. Configuration de l'environnement virtuel Python...${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "  - Environnement virtuel .venv : ${GREEN}Créé${NC}"
else
    echo -e "  - Environnement virtuel .venv : ${GREEN}Déjà existant${NC}"
fi

# Activation de l'environnement virtuel
source .venv/bin/activate

# Installation/Mise à jour des dépendances Python
echo -e "  - Installation des dépendances Python (requirements.txt)..."
pip install --upgrade pip
pip install -r requirements.txt
echo -e "  - Dépendances Python : ${GREEN}OK${NC}"

# 3. Création des répertoires de persistance
echo -e "\n${BLUE}3. Création des répertoires de données locaux...${NC}"
mkdir -p data/uploads data/chroma_db logs
echo -e "  - data/uploads : ${GREEN}Créé/OK${NC}"
echo -e "  - data/chroma_db : ${GREEN}Créé/OK${NC}"
echo -e "  - logs : ${GREEN}Créé/OK${NC}"

# 4. Copie du fichier .env d'exemple si inexistant
echo -e "\n${BLUE}4. Configuration du fichier .env...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "  - Fichier .env : ${GREEN}Créé à partir de .env.example${NC}"
    echo -e "  - ${YELLOW}RAPPEL : N'oubliez pas de mettre à jour les secrets dans votre .env !${NC}"
else
    echo -e "  - Fichier .env : ${GREEN}Déjà existant${NC}"
fi

# 5. Configuration du Frontend
echo -e "\n${BLUE}5. Installation des dépendances du Frontend...${NC}"
if [ -d "frontend" ]; then
    cd frontend
    npm install
    cd ..
    echo -e "  - Dépendances Frontend : ${GREEN}OK${NC}"
else
    echo -e "${RED}Avertissement : Le dossier 'frontend' n'a pas été trouvé.${NC}"
fi

echo -e "\n${GREEN}=== Configuration terminée avec succès ! ===${NC}"
echo -e "Pour démarrer le serveur Backend :"
echo -e "  ${BLUE}source .venv/bin/activate${NC}"
echo -e "  ${BLUE}uvicorn api.main:app --reload${NC}"
echo -e "Pour démarrer le serveur Frontend :"
echo -e "  ${BLUE}cd frontend && npm run dev${NC}"
