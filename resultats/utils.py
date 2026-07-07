"""
Utilitaires pour le stockage cloud (Backblaze B2 / S3).
Centralise la génération des URLs de téléchargement signées.
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Durée de validité des URLs signées (en secondes)
DOWNLOAD_URL_EXPIRE_SECONDS = 3600  # 1 heure

# Client boto3 lazy singleton (créé une seule fois et réutilisé)
_boto3_client = None


def _get_s3_client():
    """Retourne le client S3 (Backblaze B2) en lazy singleton."""
    global _boto3_client
    if _boto3_client is None and settings.B2_KEY_ID:
        import boto3
        from botocore.config import Config as BotoConfig

        _boto3_client = boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.B2_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=BotoConfig(signature_version='s3v4'),
        )
    return _boto3_client


def generer_url_telechargement(fichier_field):
    """
    Génère une URL signée pour télécharger un fichier depuis Backblaze B2.

    Args:
        fichier_field: Un objet FileField / FieldFile Django (ex: resultat.fichier)

    Retourne:
        str ou None: L'URL de téléchargement (signée en prod, directe en dev).
    """
    if not fichier_field:
        return None

    # Mode développement : URL directe locale
    if not settings.B2_KEY_ID:
        if settings.DEBUG and hasattr(fichier_field, 'url'):
            return settings.BACKEND_URL.rstrip('/') + fichier_field.url
        return None

    # Mode production : URL signée S3 (Backblaze B2)
    client = _get_s3_client()
    if not client:
        logger.error("Impossible de créer le client S3 (B2_KEY_ID manquant dans settings)")
        return None

    try:
        nom_fichier = fichier_field.name.split('/')[-1]
        url = client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': fichier_field.name,
                'ResponseContentDisposition': f'attachment; filename="{nom_fichier}"',
            },
            ExpiresIn=DOWNLOAD_URL_EXPIRE_SECONDS,
        )
        return url
    except Exception as e:
        logger.error(f"Erreur génération URL signée : {e}", exc_info=True)
        return None
