#!/usr/bin/env bash
# build.sh — Script de build exécuté par Render avant le démarrage du serveur
# Rôle : installer les dépendances et préparer les fichiers statiques.
# NB : les migrations et le seed sont faits dans le Procfile (Start Command),
#      pas ici, pour garantir l'accès à la base PostgreSQL de Render.

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
echo "[BUILD] ✅  Build terminé avec succès !"
echo "────────────────────────────────────────────────────"
