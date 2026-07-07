"""
Utilitaires pour le téléchargement des fichiers.
Stockage Cloudinary utilisé (CDN).
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Durée de validité des URLs de téléchargement (en secondes)
DOWNLOAD_URL_EXPIRE_SECONDS = 3600  # 1 heure


def generer_url_telechargement(fichier_field):
    """
    Génère l'URL de téléchargement d'un fichier stocké sur Cloudinary.
    Retourne une URL Cloudinary (CDN) directe.

    Args:
        fichier_field: Un objet FileField / FieldFile Django (ex: resultat.fichier)

    Retourne:
        str ou None: L'URL de téléchargement directe (Cloudinary CDN).
    """
    if not fichier_field:
        return None

    # Cloudinary génère directement une URL CDN complète via fichier.url
    if hasattr(fichier_field, 'url') and fichier_field.url:
        url = fichier_field.url
        # L'URL Cloudinary est déjà complète (https://res.cloudinary.com/...)
        # On la retourne telle quelle
        return url

    return None
