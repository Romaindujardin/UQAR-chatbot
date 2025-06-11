# 🛠️ Guide de Développement - Assistant Éducatif UQAR

Pour un aperçu général du projet et les instructions de déploiement avec Apptainer, veuillez consulter le [README.md principal](../README.md).

## 📁 Structure du Projet

```
UQAR/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── api/            # Routes API
│   │   ├── core/           # Configuration, sécurité, DB
│   │   ├── models/         # Modèles SQLAlchemy
│   │   ├── services/       # Logique métier
│   │   └── utils/          # Utilitaires
│   ├── requirements.txt    # Dépendances Python
│   ├── Dockerfile         # Image Docker backend
│   └── env.example        # Variables d'environnement
├── frontend/               # Application Next.js
│   ├── src/
│   │   ├── components/     # Composants React
│   │   ├── pages/          # Pages Next.js
│   │   ├── hooks/          # Hooks personnalisés
│   │   ├── utils/          # Utilitaires frontend
│   │   └── styles/         # Styles CSS/Tailwind
│   ├── package.json       # Dépendances Node.js
│   └── Dockerfile         # Image Docker frontend
├── docker-compose.yml     # Orchestration des services
├── start.sh              # Script de démarrage
└── README.md             # Documentation principale
```

## 🚀 Configuration de l'environnement de développement

### 1. Prérequis

- **Python 3.11+** pour le développement backend
- **Node.js 18+** pour le développement frontend
- **Docker & Docker Compose** pour l'environnement complet
- **Git** pour le versioning
- **IDE recommandé** : VS Code avec extensions Python et TypeScript

### 2. Installation locale (développement)

#### Backend (FastAPI)

```bash
cd backend

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt

# Copier et configurer l'environnement
cp env.example .env
# Modifier .env selon vos besoins

# Démarrer le serveur de développement
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend (Next.js)

```bash
cd frontend

# Installer les dépendances
npm install

# Démarrer le serveur de développement
npm run dev
```

### 3. Base de données locale

Pour le développement, vous pouvez utiliser PostgreSQL local ou Docker :

```bash
# Avec Docker (recommandé)
docker run --name uqar-postgres \
  -e POSTGRES_DB=uqar_db \
  -e POSTGRES_USER=uqar_user \
  -e POSTGRES_PASSWORD=uqar_password \
  -p 5432:5432 \
  -d postgres:15

# Créer les tables
cd backend
python -c "from app.core.database import create_tables; create_tables()"
```

## 🏗️ Architecture Technique

### Backend (FastAPI)

#### Modèles de données

- **User** : Gestion des utilisateurs (Super-Admin, Enseignant, Étudiant)
- **Section** : Sections de cours créées par les enseignants
- **Document** : Fichiers uploadés et vectorisés
- **Exercise** : Exercices générés automatiquement
- **ChatSession/ChatMessage** : Historique des conversations RAG

#### Services principaux

- **UserService** : Gestion des utilisateurs et authentification
- **DocumentService** : Traitement et vectorisation des documents
- **ExerciseService** : Génération d'exercices avec IA
- **ChatService** : Système RAG avec ChromaDB et vLLM
- **EmbeddingService** : Génération d'embeddings avec BAAI/bge

#### Sécurité

- **JWT** avec refresh tokens
- **Argon2** pour le hashing des mots de passe
- **CORS** configuré pour le frontend
- **Rate limiting** sur les endpoints sensibles

### Frontend (Next.js)

#### Structure des composants

```
components/
├── auth/           # Composants d'authentification
├── chat/           # Interface de chat RAG
├── dashboard/      # Tableaux de bord par rôle
├── documents/      # Gestion des documents
├── exercises/      # Interface des exercices
├── layout/         # Layout et navigation
└── ui/             # Composants UI réutilisables
```

#### État global

- **React Query** pour la gestion des données serveur
- **Context API** pour l'authentification
- **Local Storage** pour la persistance des tokens

#### Styling

- **Tailwind CSS** pour le styling
- **Headless UI** pour les composants accessibles
- **Heroicons** pour les icônes
- **Framer Motion** pour les animations

### Base de données vectorielle (ChromaDB)

- **Collections par section** : Isolation des données par cours
- **Embeddings BAAI/bge** : Modèle performant pour le français
- **Métadonnées** : Informations sur les documents sources
- **Recherche sémantique** : Récupération de contexte pertinent

### IA (LLaMA)

- **LLaMA 3.1 70B** : Modèle de base (évolutif vers la version Instruct)
- **Prompts structurés** : Templates pour différents types de tâches
- **Streaming** : Réponses en temps réel

## 🔧 Développement des fonctionnalités

### Ajouter une nouvelle route API

1. **Créer le schéma Pydantic** dans `backend/app/api/`
2. **Implémenter la logique** dans `backend/app/services/`
3. **Ajouter la route** dans le router approprié
4. **Tester** avec FastAPI docs (`/docs`)

Exemple :

```python
# backend/app/api/sections.py
@router.post("/", response_model=SectionResponse)
async def create_section(
    section_data: SectionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Logique de création
    pass
```

### Ajouter un nouveau composant React

1. **Créer le composant** dans `frontend/src/components/`
2. **Définir les types TypeScript**
3. **Implémenter les styles Tailwind**
4. **Ajouter les tests** (si applicable)

Exemple :

```tsx
// frontend/src/components/ui/Button.tsx
interface ButtonProps {
  variant: "primary" | "secondary";
  children: React.ReactNode;
  onClick?: () => void;
}

export const Button: React.FC<ButtonProps> = ({
  variant,
  children,
  onClick,
}) => {
  return (
    <button
      className={`btn ${
        variant === "primary" ? "btn-primary" : "btn-secondary"
      }`}
      onClick={onClick}
    >
      {children}
    </button>
  );
};
```

### Intégrer une nouvelle fonctionnalité IA

1. **Définir le prompt** dans `backend/app/services/`
2. **Implémenter l'appel ollama**
3. **Ajouter la validation** des réponses
4. **Créer l'interface frontend**

## 🧪 Tests

### Backend

```bash
cd backend

# Tests unitaires
pytest tests/

# Tests avec coverage
pytest --cov=app tests/

# Tests d'intégration
pytest tests/integration/
```

### Frontend

```bash
cd frontend

# Tests unitaires
npm test

# Tests E2E (si configurés)
npm run test:e2e
```

## 📊 Monitoring et Debugging

### Logs

```bash
# Logs backend
tail -f backend/logs/app.log

# Logs Docker
docker-compose logs -f backend
docker-compose logs -f vllm
```

### Métriques

- **FastAPI** : Métriques Prometheus sur `/metrics`
- **PostgreSQL** : Monitoring des requêtes lentes
- **ChromaDB** : Temps de recherche vectorielle

### Debugging

```python
# Backend - Activer le mode debug
# Dans backend/.env
DEBUG=true

# Logs SQL détaillés
# Dans backend/app/core/database.py
engine = create_engine(DATABASE_URL, echo=True)
```

## 🚀 Déploiement

### Environnement de staging

```bash
# Construire les images
docker-compose -f docker-compose.staging.yml build

# Déployer
docker-compose -f docker-compose.staging.yml up -d
```

### Production

1. **Sécuriser les variables d'environnement**
2. **Configurer HTTPS** avec reverse proxy
3. **Optimiser les performances** GPU
4. **Mettre en place la sauvegarde** des données
5. **Configurer le monitoring** avancé

## 📚 Ressources utiles

### Documentation

- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [ChromaDB](https://docs.trychroma.com/)

### Outils de développement

- **Postman/Insomnia** : Test des APIs
- **pgAdmin** : Administration PostgreSQL
- **React DevTools** : Debug React
- **Docker Desktop** : Gestion des conteneurs
