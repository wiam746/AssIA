# Guide Utilisateur — AssIA

Bienvenue sur **AssIA**, votre assistant IA interne pour gérer les réunions, incidents et documents d'équipe.

---

## Table des matières

- [Premiers pas](#premiers-pas)
- [Se connecter / Créer un compte](#se-connecter--créer-un-compte)
- [Chat IA — Poser des questions](#chat-ia--poser-des-questions)
- [Uploader des documents](#uploader-des-documents)
- [Gérer les réunions](#gérer-les-réunions)
- [Déclarer un incident](#déclarer-un-incident)
- [Piloter les projets](#piloter-les-projets)
- [Bibliothèque de documents](#bibliothèque-de-documents)
- [Historique du chat](#historique-du-chat)
- [Déconnexion](#déconnexion)
- [Conseils & astuces](#conseils--astuces)

---

## Premiers pas

Ouvrez votre navigateur et accédez à l'adresse fournie par votre administrateur (ex. : `https://assIA.entreprise.com` ou `http://localhost:5173` en local).

---

## Se connecter / Créer un compte

### Connexion

1. Sur la page d'accueil, saisissez votre **identifiant** (ou adresse email) et votre **mot de passe**.
2. Cliquez sur **Se connecter**.
3. En cas d'oubli du mot de passe, cliquez sur **Mot de passe oublié ?** pour recevoir un email de réinitialisation.

### Créer un compte

1. Cliquez sur l'onglet **S'inscrire**.
2. Renseignez votre **nom complet**, votre **adresse email** et choisissez un **mot de passe**.
3. Confirmez le mot de passe.
4. ✅ Cochez la case **J'accepte les Conditions Générales d'Utilisation (CGU)**.
   - Cliquez sur le lien *CGU* pour lire les conditions générales avant d'accepter.
5. Cliquez sur **Créer mon compte**.

> **Note :** La création de compte peut nécessiter une validation par votre administrateur selon la configuration de votre organisation.

---

## Chat IA — Poser des questions

Le Chat IA est le cœur d'AssIA. Il vous permet d'interroger l'ensemble de vos documents indexés en langage naturel.

### Comment l'utiliser

1. Cliquez sur **Chat IA** dans la barre latérale.
2. Tapez votre question dans le champ de saisie en bas de l'écran.
3. Appuyez sur **Entrée** ou cliquez sur le bouton d'envoi (➤).
4. L'assistant analyse vos documents et vous répond en quelques secondes.

### Exemples de questions

| Question | Ce que l'assistant peut faire |
|---|---|
| *"Quelles décisions ont été prises lors de la réunion du 15 janvier ?"* | Recherche dans vos comptes-rendus |
| *"Résume les actions à faire suite à la réunion produit"* | Extraction des plans d'action |
| *"Quel est le statut de l'incident critique du 20 janvier ?"* | Consultation de l'historique des incidents |
| *"Quelles sont les prochaines étapes du projet Migration API ?"* | Recommandations sur les projets |
| *"Explique-moi l'architecture de notre système de facturation"* | Recherche dans la documentation technique |

### Conseils pour de meilleures réponses

- **Soyez précis** : Indiquez la date, le nom du projet ou la personne concernée.
- **Posez des questions complètes** : Évitez les abréviations ou termes trop internes sans contexte.
- **Découpez les questions complexes** : Plusieurs questions simples donnent de meilleurs résultats qu'une seule question très longue.
- **Uploadez vos documents** avant de poser des questions à leur sujet (voir section suivante).

---

## Uploader des documents

Vous pouvez enrichir la base de connaissances de l'assistant en uploadant vos fichiers.

### Depuis le Chat IA

1. Cliquez sur l'icône **Trombone** (📎) à gauche du champ de saisie.
2. Sélectionnez votre fichier dans l'explorateur de fichiers.
3. Une notification verte confirme que le document a été indexé avec succès.
4. Vous pouvez immédiatement poser des questions sur ce document.

**Formats acceptés :** PDF, DOCX, TXT, Markdown (.md)  
**Taille maximale :** 25 Mo par fichier

### Depuis la Bibliothèque

Voir la section [Bibliothèque de documents](#bibliothèque-de-documents) ci-dessous.

---

## Gérer les réunions

### Créer un nouveau compte-rendu

1. Cliquez sur **Réunions** dans la barre latérale.
2. Cliquez sur le bouton **Nouveau compte-rendu**.
3. Renseignez :
   - **Titre de la réunion** (ex. : *Synchronisation hebdo équipe produit*)
   - **Notes brutes / Transcription** : collez ou tapez le compte-rendu brut
4. Cliquez sur **Générer le compte-rendu IA**.
5. L'assistant génère automatiquement :
   - Un **résumé** synthétique
   - Les **décisions** clés prises lors de la réunion
   - Le **plan d'actions** avec les responsables et échéances

### Consulter les réunions passées

La liste de toutes les réunions analysées s'affiche sur la page. Chaque réunion montre son résumé, ses décisions et son plan d'actions.

---

## Déclarer un incident

### Signaler un nouvel incident

1. Cliquez sur **Incidents** dans la barre latérale.
2. Cliquez sur **Déclarer un incident**.
3. Renseignez :
   - **Titre** : description courte et précise (ex. : *Latence élevée sur l'API de paiement*)
   - **Description détaillée** : symptômes observés, systèmes impactés, heure de début
   - **Niveau de sévérité** :
     - 🔵 **Mineur** — Impact limité, aucun arrêt de service
     - 🟡 **Majeur** — Dégradation significative des performances
     - 🔴 **Critique** — Interruption totale de service
4. Cliquez sur **Lancer l'analyse automatique**.
5. L'IA analyse l'incident et fournit un **diagnostic** avec des **recommandations concrètes**.

### Interpréter l'analyse IA

L'analyse IA s'appuie sur vos documents internes (runbooks, architectures, post-mortems précédents) pour proposer des pistes de résolution adaptées à votre contexte.

---

## Piloter les projets

### Créer un projet

1. Cliquez sur **Projets** dans la barre latérale.
2. Cliquez sur **Nouveau projet**.
3. Renseignez le **nom** et la **description** du projet.
4. Cliquez sur **Enregistrer le projet**.

### Obtenir des recommandations IA

Sur chaque carte projet, cliquez sur **Suggérer les prochaines étapes IA** pour recevoir une liste de recommandations stratégiques personnalisées, basées sur vos documents et le contexte du projet.

### Statuts de projet

| Statut | Description |
|---|---|
| **En cours** | Projet actif, travaux en cours |
| **En pause** | Projet temporairement suspendu |
| **Terminé** | Projet livré avec succès |
| **Archivé** | Projet clôturé et archivé |

---

## Bibliothèque de documents

La bibliothèque centralise tous les documents indexés dans la base de connaissances.

### Fonctionnalités

- **Rechercher** un document par nom via le champ de recherche.
- **Consulter le statut** d'indexation de chaque document :
  - ⏳ En attente — Document reçu, en file d'attente
  - 🔄 Traitement — Extraction et indexation en cours
  - ✅ Indexé — Document disponible pour le chat IA
  - ❌ Erreur — Problème lors du traitement (format non supporté, fichier corrompu)
- **Supprimer** un document (retire le fichier et ses données vectorielles).
- **Ajouter** un nouveau document via le bouton **Ajouter un document**.

> **Bon à savoir :** Un document au statut *Indexé* est immédiatement interrogeable via le Chat IA. Le traitement prend généralement quelques secondes à quelques minutes selon la taille du fichier.

---

## Historique du chat

Dans la barre latérale, sous la section **Historique du chat**, retrouvez toutes vos conversations passées.

- Cliquez sur une conversation pour **reprendre là où vous en étiez**.
- Cliquez sur **+ Nouveau** pour démarrer une **nouvelle conversation**.
- Au survol d'une conversation, cliquez sur l'icône 🗑️ pour **supprimer** une conversation.

> **Note :** Chaque nouvelle conversation démarre sans contexte de l'historique précédent. Pour continuer un sujet, reprendre la conversation existante.

---

## Déconnexion

En bas de la barre latérale, dans la section de votre profil, cliquez sur **Se déconnecter** pour terminer votre session en toute sécurité.

---

## Conseils & astuces

### 💡 Pour de meilleures synthèses de réunions

Incluez dans vos notes brutes :
- La liste des participants
- L'ordre du jour
- Les discussions par point avec les décisions prises
- Les actions avec les responsables et deadlines

### 💡 Pour enrichir la base de connaissances

Importez régulièrement :
- Comptes-rendus de réunions au format PDF ou TXT
- Documentation technique (guides, runbooks, architectures)
- Spécifications fonctionnelles et techniques
- Post-mortems et retours d'expérience

### 💡 Quand l'assistant ne trouve pas l'information

Si l'assistant répond *"Je n'ai pas d'information sur ce sujet"*, cela signifie que le document pertinent n'a pas encore été indexé. Uploadez-le depuis le chat ou la bibliothèque.

### 🔒 Confidentialité

Toutes vos données (documents, conversations, réunions) sont traitées **localement** sur l'infrastructure de votre organisation. Aucune information n'est envoyée vers des services cloud externes.
