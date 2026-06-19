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
echo "[BUILD] Vérification de l'état de la base de données..."
echo "────────────────────────────────────────────────────"
# Prévient les erreurs de colonne npi déjà existante (état résiduel de déploiement précédent)
python << 'PYEOF' 2>&1 || true
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_soutenance.settings')
import django
django.setup()
from django.db import connection
from django.utils import timezone
try:
    with connection.cursor() as cursor:
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_name='accounts_patient' AND table_schema='public'
        )
        """)
        table_exists = cursor.fetchone()[0]
        if table_exists:                cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='accounts_patient' AND table_schema='public' AND column_name='npi'
                )
                """)
            has_npi = cursor.fetchone()[0]
            if has_npi:
                cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM django_migrations
                    WHERE app='accounts' AND name='0004_patient_npi'
                )
                """)
                if not cursor.fetchone()[0]:
                    cursor.execute(
                        "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, %s)",
                        ['accounts', '0004_patient_npi', timezone.now()]
                    )
                    print('[BUILD] Migration 0004_patient_npi marquee comme appliquee (colonne npi deja existante)')
                else:
                    print('[BUILD] Base de donnees OK')
            else:
                print('[BUILD] Base fraiche - colonne npi absente')
        else:
            print('[BUILD] Base fraiche - table accounts_patient absente')
except Exception as e:
    print(f'[BUILD] Avertissement: impossible de verifier la base: {e}')
    print('[BUILD] Continuation avec la migration normale...')
PYEOF

echo ""
echo "────────────────────────────────────────────────────"
echo "[BUILD] Exécution des Migrations et Seeding de Test..."
echo "────────────────────────────────────────────────────"
python manage.py migrate --noinput
echo "────────────────────────────────────────────────────"
echo "[BUILD] Nettoyage des comptes inactifs (non validés)..."
echo "────────────────────────────────────────────────────"
python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_soutenance.settings'); django.setup(); from django.contrib.auth import get_user_model; get_user_model().objects.filter(is_active=False, is_email_verified=False).delete()"
python seed_memoire_final.py

echo ""
echo "────────────────────────────────────────────────────"
echo "[BUILD] ✅  Build terminé avec succès !"
echo "────────────────────────────────────────────────────"
