#!/usr/bin/env bash
# build.sh — Script de configuration pour le déploiement sur Railway
# Rôle : installer les dépendances et préparer les fichiers statiques.
# NB : ce script s'intègre parfaitement avec Railway (Nixpacks / build command).

set -o errexit  # Arrêter immédiatement en cas d'erreur

echo "────────────────────────────────────────────────────"
echo "[BUILD] Installation des dépendances Python..."
echo "────────────────────────────────────────────────────"
pip install -r requirements.txt

echo ""
echo "────────────────────────────────────────────────────"
echo "[BUILD] Collecte des fichiers statiques..."
echo "────────────────────────────────────────────────────"
python manage.py collectstatic --noinput

echo ""
echo "────────────────────────────────────────────────────"
echo "[BUILD] Exécution des Migrations et Seeding de Test..."
echo "────────────────────────────────────────────────────"
python manage.py migrate --noinput
echo "────────────────────────────────────────────────────"
echo "[BUILD] Nettoyage des comptes inactifs (non validés)..."
echo "────────────────────────────────────────────────────"
python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_soutenance.settings'); django.setup(); from django.contrib.auth import get_user_model; get_user_model().objects.filter(is_active=False, is_email_verified=False).delete()"
python manage.py seed_demo --clean

echo ""
echo "────────────────────────────────────────────────────"
echo "[BUILD] ✅  Build terminé avec succès !"
echo "────────────────────────────────────────────────────"
