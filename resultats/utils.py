"""
Utilitaires pour le téléchargement des fichiers.
Stockage local utilisé (disque Render).
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Durée de validité des URLs de téléchargement (en secondes)
DOWNLOAD_URL_EXPIRE_SECONDS = 3600  # 1 heure


def generer_url_telechargement(fichier_field):
    """
    Génère l'URL de téléchargement d'un fichier stocké localement.
    Retourne une URL directe vers le backend Django qui servira le fichier
    via le endpoint /api/resultats/<pk>/telecharger/ ou l'URL statique.

    Args:
        fichier_field: Un objet FileField / FieldFile Django (ex: resultat.fichier)

    Retourne:
        str ou None: L'URL de téléchargement directe.
    """
    if not fichier_field:
        return None

    # URL directe vers le fichier servi par Django
    if hasattr(fichier_field, 'url') and fichier_field.url:
        return settings.BACKEND_URL.rstrip('/') + fichier_field.url

    return None
