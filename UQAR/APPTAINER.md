# Guide de Migration Docker → Apptainer pour UQAR

## 📋 Introduction

Ce document explique comment migrer l'Assistant Éducatif UQAR de Docker vers Apptainer (anciennement Singularity). Apptainer est un système de conteneurs optimisé pour les environnements HPC et scientifiques, offrant une meilleure sécurité et isolation.

Pour un aperçu général du projet et d'autres sujets, veuillez consulter le [README.md principal](../README.md).

## 🔧 Prérequis

- Apptainer (version 1.0.0 ou supérieure)
- Linux 64-bit (CentOS/RHEL, Ubuntu, Debian, etc.)
- Accès sudo (nécessaire uniquement pour l'installation d'Apptainer)
- 8 GB RAM minimum, 15 GB espace disque
- GPU NVIDIA (pour l'accélération des modèles Ollama)

## 🚀 Installation d'Apptainer

### Ubuntu/Debian

```bash
# Installer les dépendances
sudo apt-get update && sudo apt-get install -y \
    build-essential \
    libseccomp-dev \
    pkg-config \
    squashfs-tools \
    cryptsetup \
    wget git

# Télécharger et installer Apptainer
git clone https://github.com/apptainer/apptainer.git
cd apptainer
./mconfig
cd ./builddir
make
sudo make install
```

### CentOS/RHEL

```bash
# Installer les dépendances
sudo yum groupinstall -y 'Development Tools'
sudo yum install -y \
    libseccomp-devel \
    squashfs-tools \
    cryptsetup \
    wget git

# Télécharger et installer Apptainer
git clone https://github.com/apptainer/apptainer.git
cd apptainer
./mconfig
cd ./builddir
make
sudo make install
```

## 🖥️ Configuration spécifique au serveur UQAR GPU

Sur le serveur GPU de l'UQAR, il est recommandé d'utiliser les variables d'environnement suivantes pour éviter les problèmes d'espace disque :

```bash
export APPTAINER_CACHEDIR="${HOME}/.apptainer/cache"
export APPTAINER_TMPDIR="${HOME}/.apptainer/tmp"
mkdir -p "${APPTAINER_CACHEDIR}" "${APPTAINER_TMPDIR}"
```

Ces variables sont déjà intégrées dans tous les scripts de démarrage fournis.

## 🐋 Migration depuis Docker

Le projet UQAR a été initialement configuré pour utiliser Docker et Docker Compose. Les principales différences avec Apptainer sont :

1. **Conteneurs indépendants** : Apptainer gère les conteneurs individuellement plutôt qu'avec un fichier de composition.
2. **Fichiers de définition** : Remplace les Dockerfiles, définissant comment construire les conteneurs.
3. **Instances persistantes** : Concept similaire aux conteneurs Docker mais avec une gestion différente.
4. **Montage de volumes** : Utilise le flag `--bind` au lieu des volumes Docker.
5. **Privilèges limités** : Moins de permissions par défaut pour plus de sécurité.
6. **Support GPU** : Utilise le flag `--nv` pour activer le support GPU NVIDIA.

### Structure du projet avec Apptainer

```
UQAR/
├── backend/                # Backend FastAPI
│   └── backend.def         # Définition Apptainer pour le backend
├── frontend/               # Frontend Next.js
│   └── frontend.def        # Définition Apptainer pour le frontend
├── postgres.def            # Définition Apptainer pour PostgreSQL
├── chromadb.def            # Définition Apptainer pour ChromaDB
├── ollama.def              # Définition Apptainer pour Ollama
├── start-apptainer.sh      # Script de démarrage Apptainer
└── stop-apptainer.sh       # Script d'arrêt Apptainer
```

## 🚀 Utilisation

### Démarrage des services

Plusieurs options sont disponibles pour démarrer les services :

#### 1. Méthode standard avec SIF files

```bash
chmod +x start-apptainer.sh
./start-apptainer.sh
```

#### 2. Méthode Sandbox (pour les problèmes de fakeroot)

```bash
chmod +x start-apptainer-sandbox.sh
./start-apptainer-sandbox.sh
```

#### 3. Méthode Directe (solution plus compatible)

```bash
chmod +x start-apptainer-direct.sh
./start-apptainer-direct.sh
```

Cette méthode utilise directement les images Docker originales sans construire de fichiers SIF ou de répertoires sandbox, ce qui contourne complètement les problèmes de fakeroot. C'est la méthode la plus compatible avec les différentes versions d'Apptainer et distributions Linux.

#### 4. Méthode Minimale (sans conteneurs)

```bash
chmod +x start-minimal.sh
./start-minimal.sh
```

Cette méthode n'utilise pas du tout de conteneurs et exécute les services directement sur le système hôte. C'est la méthode la plus simple et la plus légère, mais elle nécessite que PostgreSQL soit installé sur le système. Idéale quand Apptainer n'est pas disponible ou en cas de problèmes persistants avec les conteneurs.

### Arrêt des services

Le script `stop-apptainer.sh` arrête proprement tous les services :

```bash
chmod +x stop-apptainer.sh
./stop-apptainer.sh
```

### Commandes Apptainer utiles

```bash
# Lister les instances en cours d'exécution
apptainer instance list

# Voir les logs d'une instance
apptainer instance logs backend_instance

# Exécuter une commande dans une instance
apptainer exec instance://backend_instance python -c "print('Hello')"

# Ouvrir un shell dans une instance
apptainer shell instance://backend_instance

# Arrêter une instance spécifique
apptainer instance stop backend_instance

# Vérifier l'état du GPU
nvidia-smi
```

## 🔄 Différences de configuration

### Mise en réseau

Les instances Apptainer utilisent le réseau de l'hôte par défaut, donc les services communiquent via `localhost` aux ports exposés.

### Stockage persistant

Les données persistantes sont stockées dans `UQAR_GIT/apptainer_data/` avec des sous-dossiers pour chaque service :
- `postgres_data` : Données PostgreSQL
- `chromadb_data` : Données ChromaDB 
- `ollama_data` : Modèles et données Ollama
- `uploads` : Fichiers uploadés
- `logs` : Logs de l'application

### Variables d'environnement

Les variables d'environnement sont passées aux instances via les flags `--env` lors du démarrage. Les connexions entre services utilisent `localhost` au lieu des noms de service comme dans Docker Compose.

### Support GPU

Pour activer le support GPU, plusieurs éléments sont nécessaires :

1. Le flag `--nv` lors du démarrage des instances qui utilisent le GPU (Ollama)
2. Les variables d'environnement NVIDIA :
   ```
   NVIDIA_VISIBLE_DEVICES=all
   NVIDIA_DRIVER_CAPABILITIES=compute,utility
   ```
3. S'assurer que le GPU est disponible avec la commande `nvidia-smi`

## 🐛 Résolution de problèmes

### Erreurs fakeroot

Si vous rencontrez des erreurs liées à fakeroot lors de la construction des conteneurs, comme:

```
/.singularity.d/libs/faked: /lib/x86_64-linux-gnu/libc.so.6: version `GLIBC_2.33' not found
```

Vous avez plusieurs options:

1. **Utiliser le mode sandbox**:
   ```bash
   chmod +x start-apptainer-sandbox.sh
   ./start-apptainer-sandbox.sh
   ```
   Ce script utilise le mode sandbox d'Apptainer qui crée des répertoires au lieu de fichiers SIF, ce qui peut contourner certains problèmes de fakeroot.

2. **Utiliser l'option `--ignore-fakeroot-command`** (déjà activée dans le script de démarrage):
   ```bash
   apptainer build --ignore-fakeroot-command image.sif definition.def
   ```

3. **Construire les images en mode root** (nécessite des privilèges sudo):
   ```bash
   sudo apptainer build image.sif definition.def
   ```

### Mode Sandbox vs SIF

Apptainer prend en charge deux formats de conteneurs:

- **SIF (Singularity Image Format)**: Format de fichier unique immuable (.sif)
- **Sandbox**: Répertoire pouvant être modifié après création

Le mode sandbox est utile pour:
- Développement et débogage
- Environnements avec problèmes de fakeroot
- Modification des conteneurs après construction

### Erreurs GPU

Si vous rencontrez des erreurs liées au GPU :

1. **Vérifier que le GPU est visible** :
   ```bash
   nvidia-smi
   ```
   Cette commande devrait afficher les GPUs disponibles et leur utilisation.

2. **Vérifier que CUDA est correctement installé** :
   ```bash
   nvcc --version
   ```

3. **Processus GPU bloqués** :
   Si un processus GPU est bloqué, vous pouvez le tuer :
   ```bash
   # Trouver le PID du processus bloqué dans la colonne PID de nvidia-smi
   kill -9 <PID>
   ```

### Permissions

Si vous rencontrez des erreurs de permission :

```bash
# Assurez-vous que votre utilisateur a accès aux dossiers de données
chmod -R 755 UQAR_GIT/apptainer_data
```

### Ports déjà utilisés

Si un port est déjà utilisé, vous verrez un message d'erreur. Pour libérer un port :

```bash
# Trouver le processus utilisant le port
lsof -i :<port>

# Terminer le processus
kill <PID>
```

### Problèmes d'espace disque

Si vous rencontrez des erreurs d'espace disque insuffisant, vous pouvez :

```bash
# Définir des répertoires temporaires et de cache alternatifs
export APPTAINER_CACHEDIR="${HOME}/.apptainer/cache"
export APPTAINER_TMPDIR="${HOME}/.apptainer/tmp"
mkdir -p "${APPTAINER_CACHEDIR}" "${APPTAINER_TMPDIR}"
```

### Modèle Ollama non téléchargé

Si le modèle Ollama n'est pas téléchargé automatiquement :

```bash
# Accéder à l'instance Ollama
apptainer shell instance://ollama_instance

# Télécharger manuellement le modèle
ollama pull tinyllama
```

## 📊 Performance

Apptainer peut offrir de meilleures performances que Docker pour certaines charges de travail, notamment celles utilisant le GPU ou des opérations intensives en calcul.

### Optimisation GPU

Pour optimiser l'utilisation du GPU :

1. Utilisez des modèles adaptés à la taille de votre GPU (mémoire)
2. Vérifiez l'utilisation avec `nvidia-smi`
3. Ajustez les paramètres du modèle Ollama si nécessaire
