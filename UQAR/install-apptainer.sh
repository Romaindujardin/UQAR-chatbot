#!/bin/bash

# Script d'installation d'Apptainer pour l'Assistant Éducatif UQAR
# Ce script détecte automatiquement la distribution Linux et installe Apptainer

set -e

echo "🚀 Installation d'Apptainer pour UQAR"
echo "==================================="

# Fonction pour détecter la distribution Linux
detect_distro() {
  if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
    VERSION=$VERSION_ID
    echo "Distribution détectée : $DISTRO $VERSION"
  else
    echo "❌ Impossible de détecter la distribution Linux."
    exit 1
  fi
}

# Vérifier si Apptainer est déjà installé
if command -v apptainer &> /dev/null; then
    APPTAINER_VERSION=$(apptainer --version | awk '{print $3}')
    echo "✅ Apptainer est déjà installé (version $APPTAINER_VERSION)"
    exit 0
fi

# Vérifier les privilèges sudo
if ! sudo -n true 2>/dev/null; then
    echo "❌ Privilèges sudo requis pour l'installation."
    echo "Veuillez exécuter avec un utilisateur ayant des privilèges sudo."
    exit 1
fi

detect_distro

# Installation selon la distribution
case $DISTRO in
  ubuntu|debian)
    echo "🔄 Installation des dépendances pour $DISTRO..."
    sudo apt-get update
    sudo apt-get install -y \
        build-essential \
        libseccomp-dev \
        pkg-config \
        squashfs-tools \
        cryptsetup \
        wget \
        git \
        golang

    # Méthode d'installation rapide avec Go
    export VERSION=1.2.0
    wget https://github.com/apptainer/apptainer/releases/download/v${VERSION}/apptainer-${VERSION}.tar.gz
    tar -xzf apptainer-${VERSION}.tar.gz
    cd apptainer-${VERSION}
    
    # Compilation et installation
    ./mconfig
    make -C builddir
    sudo make -C builddir install
    ;;
    
  centos|rhel|rocky|almalinux)
    echo "🔄 Installation des dépendances pour $DISTRO..."
    sudo yum groupinstall -y 'Development Tools'
    sudo yum install -y \
        libseccomp-devel \
        squashfs-tools \
        cryptsetup \
        wget \
        git \
        golang

    # Méthode d'installation rapide avec Go
    export VERSION=1.2.0
    wget https://github.com/apptainer/apptainer/releases/download/v${VERSION}/apptainer-${VERSION}.tar.gz
    tar -xzf apptainer-${VERSION}.tar.gz
    cd apptainer-${VERSION}
    
    # Compilation et installation
    ./mconfig
    make -C builddir
    sudo make -C builddir install
    ;;
    
  *)
    echo "❌ Distribution non supportée : $DISTRO"
    echo "Veuillez consulter la documentation officielle d'Apptainer :"
    echo "https://apptainer.org/docs/admin/main/installation.html"
    exit 1
    ;;
esac

# Nettoyage
cd ..
rm -rf apptainer-${VERSION} apptainer-${VERSION}.tar.gz

# Vérification de l'installation
if command -v apptainer &> /dev/null; then
    APPTAINER_VERSION=$(apptainer --version | awk '{print $3}')
    echo "✅ Apptainer a été installé avec succès (version $APPTAINER_VERSION)"
    echo ""
    echo "Vous pouvez maintenant exécuter :"
    echo "  ./start-apptainer.sh"
    echo "pour démarrer les services UQAR."
else
    echo "❌ Erreur lors de l'installation d'Apptainer."
    echo "Veuillez consulter la documentation officielle :"
    echo "https://apptainer.org/docs/admin/main/installation.html"
    exit 1
fi 