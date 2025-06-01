-- Script d'initialisation de la base de données UQAR
-- Ce script est exécuté automatiquement lors du premier démarrage de PostgreSQL

-- Créer la base de données si elle n'existe pas
-- (PostgreSQL crée automatiquement la base spécifiée dans POSTGRES_DB)

-- Extensions utiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Index pour la recherche textuelle
-- Ces index seront créés automatiquement par SQLAlchemy, mais on peut les optimiser ici

-- Fonction pour générer des slugs
CREATE OR REPLACE FUNCTION generate_slug(input_text TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN lower(regexp_replace(
        regexp_replace(input_text, '[^a-zA-Z0-9\s]', '', 'g'),
        '\s+', '-', 'g'
    ));
END;
$$ LANGUAGE plpgsql;

-- Fonction pour nettoyer le texte
CREATE OR REPLACE FUNCTION clean_text(input_text TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN regexp_replace(
        regexp_replace(input_text, '\s+', ' ', 'g'),
        '^\s+|\s+$', '', 'g'
    );
END;
$$ LANGUAGE plpgsql; 