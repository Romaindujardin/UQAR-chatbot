# Assistant Éducatif UQAR

## Contexte du projet

L'Assistant Éducatif UQAR est une plateforme d'apprentissage locale conçue pour aider les étudiants de l'UQAR à réviser leurs cours. Le projet vise à fournir un environnement interactif où les étudiants peuvent interagir avec un chatbot RAG (Retrieval-Augmented Generation) basé sur leurs documents de cours, générer des exercices automatiquement et recevoir des explications pédagogiques.

L'objectif principal est de créer un outil d'accompagnement autonome pour les étudiants, encourageant la réflexion critique et la prévention du plagiat passif. La plateforme est spécialement optimisée pour une utilisation locale, sur les serveurs de l'école, garantissant la confidentialité des données et un accès rapide sans dépendance à des services cloud.

Le public cible comprend :
- **Les étudiants** : Pour réviser, poser des questions sur leurs cours et s'entraîner avec des exercices.
- **Les enseignants** : Pour gérer les sections de cours, téléverser des documents, valider les exercices générés et suivre les progrès des étudiants.
- **Les super-administrateurs** : Pour gérer les comptes utilisateurs et superviser le fonctionnement global de la plateforme.

## Environnement de développement

L'Assistant Éducatif UQAR est construit avec les technologies et outils suivants :

- **Backend** : Python avec le framework FastAPI, assurant la robustesse et la rapidité des APIs.
- **Frontend** : Next.js (basé sur React) pour une interface utilisateur moderne, réactive et conviviale.
- **Base de données relationnelle** : PostgreSQL pour stocker les informations structurées (utilisateurs, cours, exercices, etc.).
- **Base de données vectorielle** : ChromaDB pour stocker les embeddings des documents de cours et permettre une recherche sémantique rapide et pertinente pour le RAG.
- **Modèle de langage (LLM)** : Ollama avec des modèles comme LLaMA 3.1 70B, optimisé pour une exécution locale. Cela permet une IA conversationnelle et de génération d'exercices performante sans nécessiter de GPU externe puissant ou de connexion internet constante.
- **Embeddings** : `sentence-transformers/all-MiniLM-L6-v2` (optimisé pour les puces M1) ou des modèles BAAI/bge pour générer les représentations vectorielles des textes.
- **Authentification** : JWT (JSON Web Tokens) avec Argon2 pour le hachage sécurisé des mots de passe.
- **Conteneurisation** : Apptainer (anciennement Singularity) pour le déploiement sur les serveurs HPC de l'UQAR, et Docker pour le développement local et sur d'autres plateformes.

L'architecture est conçue pour être modulaire, permettant des mises à jour et une maintenance facilitées.

## Guide de démarrage rapide

Ce guide s'adresse principalement à une utilisation sur un système Linux avec Apptainer, qui est l'environnement cible pour le déploiement sur les serveurs de l'UQAR. 
Pour le développement local (y compris sur macOS ou Windows), l'utilisation de Docker est une alternative recommandée ; le fichier [Guide de Développement](UQAR/DEVELOPMENT.md) contient des instructions complètes pour mettre en place un environnement de développement local ou basé sur Docker. Certains scripts spécifiques à Docker (comme `start.sh` pour macOS) peuvent se trouver dans le dossier `UQAR/`.

### Prérequis (Apptainer sur Linux)

- Apptainer installé (version 1.0.0 ou supérieure)
- Pilotes NVIDIA installés si vous utilisez un GPU (fortement recommandé)
- Git pour cloner le dépôt
- Minimum 16 Go de RAM
- Minimum 20 Go d'espace disque libre

### Installation et lancement

1.  **Cloner le dépôt et accéder au dossier du projet** :
    ```bash
    git clone <URL_DU_DEPOT>
    cd UQAR_GIT 
    ```

2.  **Configurer l'environnement** :
    Ce script vérifie les prérequis, construit les images Apptainer, crée les dossiers nécessaires, etc.
    ```bash
    chmod +x setup-uqar.sh
    ./setup-uqar.sh
    ```

3.  **Démarrer l'application** :
    Ce script lance tous les services (Ollama, PostgreSQL, ChromaDB, Backend, Frontend).
    ```bash
    ./run-uqar.sh
    ```

4.  **Accéder aux services** :
    - Frontend : http://localhost:3000
    - Backend API : http://localhost:8000
    - Documentation API : http://localhost:8000/docs
    - ChromaDB : http://localhost:8001
    - Ollama : http://localhost:11434

### Premier compte Super-Admin

1.  Rendez-vous sur http://localhost:3000 et cliquez sur "S'inscrire".
2.  Remplissez le formulaire en choisissant le rôle "Super-Admin".
3.  Activez manuellement ce premier compte (car il n'y a pas encore d'admin pour valider) :
    ```bash
    # Commande Apptainer pour activer l'utilisateur (adaptez le nom de l'instance si besoin) :
    apptainer exec instance://postgres_instance psql -U dujr0001 -d uqar_db -c "UPDATE users SET status = 'active' WHERE id = 1;"
    # Si vous avez configuré la base de données manuellement ou via Docker pour le développement (voir UQAR/DEVELOPMENT.md), utilisez un client psql ou Docker exec :
    # docker exec -it uqar_postgres psql -U dujr0001 -d uqar_db -c "UPDATE users SET status = 'active' WHERE id = 1;"
    ```
    (L'utilisateur et le nom de la base de données par défaut sont `dujr0001` et `uqar_db`.)

### Dépannage rapide (Apptainer)

-   **Problèmes d'espace disque lors de la construction (`build`) ou de l'exécution** :
    Assurez-vous que les variables d'environnement `APPTAINER_CACHEDIR` et `APPTAINER_TMPDIR` pointent vers des répertoires avec suffisamment d'espace. Ces variables sont généralement configurées dans les scripts de démarrage (`run-uqar.sh`, `setup-uqar.sh`).
    ```bash
    export APPTAINER_CACHEDIR="${HOME}/.apptainer/cache"
    export APPTAINER_TMPDIR="${HOME}/.apptainer/tmp"
    mkdir -p "${APPTAINER_CACHEDIR}" "${APPTAINER_TMPDIR}"
    ```
-   **Erreurs `fakeroot` lors de la construction** :
    Les scripts de construction tentent d'utiliser `--ignore-fakeroot-command`. Si cela échoue, la construction en mode `sandbox` ou avec `sudo` (non recommandé sur les systèmes partagés) peut être une alternative. Consulter `UQAR/APPTAINER.md` pour plus de détails.
-   **Le modèle Ollama ne se télécharge pas** :
    Vérifiez les logs de l'instance Ollama : `apptainer instance logs ollama_instance` (le nom de l'instance peut varier).
    Vous pouvez tenter un téléchargement manuel en accédant au shell de l'instance :
    ```bash
    apptainer shell instance://ollama_instance
    ollama pull llama3.1:70b 
    exit
    ```
    Puis redémarrez les services avec `./stop-uqar.sh` et `./run-uqar.sh`.
-   **Ports déjà utilisés** :
    Utilisez `lsof -i :<port>` pour trouver le processus utilisant le port et arrêtez-le si nécessaire. Les ports par défaut sont 3000 (frontend), 8000 (backend), 8001 (ChromaDB), 11434 (Ollama), 5432 (PostgreSQL, mais mappé à 38705 par défaut dans les scripts Apptainer).

Pour **toutes les questions relatives à Apptainer** (installation, configuration avancée, GPU, dépannage approfondi), le [Guide Apptainer](UQAR/APPTAINER.md) est la ressource principale à consulter.

## Fonctionnalités et Exercices

L'Assistant Éducatif UQAR offre plusieurs fonctionnalités clés pour améliorer l'expérience d'apprentissage :

### Gestion des Cours et Documents
-   **Pour les enseignants** :
    -   Création de sections de cours (par exemple, "Mathématiques Discrètes", "Algorithmique Avancée").
    -   Téléversement de documents de cours (PDF, DOCX, etc.) dans les sections respectives.
    -   Les documents sont automatiquement traités : extraction de texte, segmentation, et vectorisation pour le RAG.
-   **Pour les étudiants** :
    -   Accès facile aux sections de cours et aux documents partagés par les enseignants.

### Chatbot RAG (Retrieval-Augmented Generation)
-   Les étudiants peuvent poser des questions en langage naturel sur le contenu de leurs cours.
-   Le système récupère les informations pertinentes des documents téléversés (via ChromaDB) et utilise le LLM (Ollama) pour générer une réponse contextuelle.
-   Le chatbot cite les sources précises des documents utilisés pour formuler sa réponse, permettant aux étudiants de vérifier et d'approfondir.
-   Un filtre anti-hors-sujet assure que les réponses restent concentrées sur le matériel pédagogique de la section.

### Génération Automatique d'Exercices
-   **Pour les enseignants** :
    -   Génération d'exercices (QCM, questions ouvertes, vrai/faux, texte à trous) basée sur le contenu des documents d'une section.
    -   Paramétrage du nombre de questions, du type et de la difficulté.
    -   Interface de validation pour réviser, modifier (si nécessaire) et approuver les exercices avant qu'ils ne soient visibles par les étudiants.
-   **Pour les étudiants** :
    -   Accès aux exercices validés par les enseignants.
    -   Interface interactive pour répondre aux questions.
    -   Feedback immédiat et automatisé, incluant le score, les réponses correctes et des explications pédagogiques générées par l'IA.

### Rôles Utilisateurs
La plateforme définit trois rôles distincts pour une gestion structurée :
-   **Étudiant** : Accède aux cours, interagit avec le chatbot RAG, effectue les exercices et suit ses progrès.
-   **Enseignant** : Gère ses sections de cours, téléverse les documents, génère et valide les exercices, et peut suivre l'activité de ses étudiants.
-   **Super-Admin** : Valide les inscriptions des nouveaux utilisateurs (enseignants et étudiants), gère les comptes et a une vue d'ensemble de l'activité de la plateforme.

### Optimisation Locale
-   La plateforme est conçue pour fonctionner localement, assurant la confidentialité des données.

## Liste des tâches (Status du Projet)

Ce projet est en cours de développement. Voici un aperçu des fonctionnalités implémentées et à venir.

### Backend (Python/FastAPI)
- [X] Structure modulaire (api, core, models, services)
- [X] Modèles SQLAlchemy (User, Section, Document, Exercise, ChatSession/ChatMessage)
- [X] Authentification JWT avec Argon2
- [X] Routes API de base pour la plupart des modules
- [X] Configuration sécurisée (CORS)
- [X] Système de permissions par rôle
- [X] Service Ollama pour l'IA locale
- [ ] Implémenter la génération d'exercices propre à la section et au document attaché (en cours d'amélioration)
- [ ] Améliorer le RAG, se tourner vers du KAG (Knowledge-Augmented Generation)
- [X] Filtre anti hors sujet, via HyDE (partiellement implémenté, améliorable)
- [ ] Améliorer l'aspect éducatif des interactions et feedbacks
- [ ] Se pencher plus en détail sur l'optimisation des prompts et des modèles LLM

### Frontend (Next.js)
- [X] Configuration TypeScript complète
- [X] Tailwind CSS avec thème personnalisé
- [X] Structure des composants organisée
- [X] Page de connexion et système de routing
- [X] Gestion d'état avec React Query (ou similaire)
- [X] Page enseignante avec les options (critères exercices: nombre, type, difficulté)
- [X] Page enseignante pour la validation des exercices générés
- [X] Page étudiante pour visualiser les exercices et obtenir du feedback
- [ ] Amélioration du dashboard étudiant pour englober plus de data (progrès, scores)
- [ ] Amélioration du dashboard super-admin pour englober plus de data (statistiques d'utilisation)
- [X] Fonction supprimer une section (et documents/exercices associés)

### Infrastructure et Déploiement
- [X] **Docker Compose** pour développement local (optimisé macOS Apple Silicon)
- [X] **Apptainer/Singularity** pour déploiement sur serveurs UQAR
- [X] Scripts de démarrage et de configuration (`setup-uqar.sh`, `run-uqar.sh`, etc.)
- [X] Base de données PostgreSQL et ChromaDB conteneurisées
- [X] Ollama configuré pour LLaMA 3.1 70B

### Documentation
- [X] README principal (ce fichier)
- [X] Guide de développement (`UQAR/DEVELOPMENT.md`)
- [X] Documentation Apptainer (`UQAR/APPTAINER.md`)

## Structure du dépôt

-   `README.md`: Ce fichier.
-   `UQAR/`: Code source principal du projet (backend, frontend, fichiers de définition Apptainer, scripts spécifiques Docker/macOS).
    -   `backend/`: Application FastAPI (Python).
    -   `frontend/`: Application Next.js (TypeScript).
    -   `*.def`: Fichiers de définition Apptainer pour chaque service.
    -   `DEVELOPMENT.md`: Guide pour les développeurs.
    -   `APPTAINER.md`: Informations spécifiques à l'utilisation d'Apptainer.
    -   Autres scripts et configurations spécifiques à l'environnement UQAR ou macOS (ex: `start.sh` pour Docker sur macOS).
-   `apptainer_data/`: Données persistantes pour les conteneurs Apptainer (logs, bases de données PostgreSQL et ChromaDB, modèles Ollama, fichiers téléversés).
-   `apptainer_sandbox/`: Optionnel, pour construire les conteneurs Apptainer en mode sandbox.
-   `uqar_data/`: Utilisé par certains scripts plus anciens pour les données utilisateur (sera potentiellement fusionné ou remplacé par `apptainer_data`).
-   `SCRIPT/`: Scripts individuels pour démarrer/arrêter des services spécifiques (alternative à `run-uqar.sh`).
-   `setup-uqar.sh`: Script initial pour configurer l'environnement après clonage.
-   `check-uqar.sh`: Script pour vérifier que l'environnement est correctement configuré.
-   `run-uqar.sh`: Script principal pour démarrer tous les services avec Apptainer.
-   `stop-uqar.sh`: Script pour arrêter tous les services Apptainer.
-   `start-no-ollama.sh`: Script pour démarrer les services sans Ollama (pour des tests ou environnements limités).


