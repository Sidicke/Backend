import requests
import json
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.signing import TimestampSigner
import re

signer = TimestampSigner()


def validate_and_format_benin_phone(phone_number):
    """
    Valide que le numéro fait 10 chiffres et commence par '01'.
    Retourne le format +229XXXXXXXXXX ou None si invalide.
    """
    if not phone_number:
        return None

    # Nettoyer le numéro (garder uniquement les chiffres)
    clean_number = re.sub(r'\D', '', phone_number)

    # Vérifier le format : 10 chiffres commençant par 01
    if len(clean_number) == 10 and clean_number.startswith('01'):
        return f"+229{clean_number}"

    # Cas où l'utilisateur saisit déjà le format international par erreur
    if (len(clean_number) == 13 and clean_number.startswith('22901')):
        return f"+{clean_number}"

    return None

def _send_email_brevo_api(subject, html_content, recipient_email, recipient_name=""):
    """
    Envoie un email via l'API REST de Brevo (Port 443 HTTP) au lieu du SMTP.
    """
    api_key = getattr(settings, 'BREVO_API_KEY', None)
    if not api_key:
        print("BREVO_API_KEY non configurée en Local, fallback sur SMTP.")
        return send_mail(
            subject=subject,
            message=strip_tags(html_content),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_content,
            fail_silently=False,
        )

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": api_key
    }
    
    # Redirection globale en mode soutenance
    if getattr(settings, 'SOUTENANCE_MODE', False):
        recipient_email = settings.SOUTENANCE_EMAIL
        recipient_name = "Sidicke (Soutenance)"

    payload = {
        "sender": {
            "name": "HOPITEL",
            "email": settings.DEFAULT_FROM_EMAIL
        },
        "to": [
            {
                "email": recipient_email,
                "name": recipient_name
            }
        ],
        "subject": subject,
        "htmlContent": html_content
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erreur API Brevo (Local) : {e}")
        raise Exception(f"Erreur lors de l'envoi de l'email via API Brevo : {str(e)}")

def generate_secure_token(user_pk):
    """Génère un token cryptographiquement signé incluant un timestamp."""
    return signer.sign(str(user_pk))

def send_verification_email(user, otp_code):
    """Envoie un email de vérification au patient inscrit."""
    if not getattr(settings, 'ENABLE_EMAILS', True):
        return

    html_message = render_to_string('accounts/emails/verification_email.html', {
        'user': user,
        'otp_code': otp_code,
    })
    
    _send_email_brevo_api(
        subject="Confirmez votre compte HOPITEL",
        html_content=html_message,
        recipient_email=user.email,
        recipient_name=f"{user.first_name} {user.last_name}"
    )

def send_account_created_email(user, password=None, reset_token=None):
    """Envoie un email avec les identifiants ou un lien de configuration de mot de passe."""
    if not getattr(settings, 'ENABLE_EMAILS', True):
        return

    context = {'user': user}
    if password:
        context['password'] = password
        context['login_url'] = f"{settings.FRONTEND_URL}/login"
    elif reset_token:
        context['setup_url'] = f"{settings.FRONTEND_URL}/reset-password/{reset_token}"
        
    html_message = render_to_string('accounts/emails/account_created.html', context)

    _send_email_brevo_api(
        subject="Bienvenue sur HOPITEL - Votre compte a été créé",
        html_content=html_message,
        recipient_email=user.email,
        recipient_name=f"{user.first_name} {user.last_name}"
    )

def send_password_reset_email(user, token):
    """Envoie un email de réinitialisation de mot de passe."""
    if not getattr(settings, 'ENABLE_EMAILS', True):
        return

    reset_url = f"{settings.BACKEND_URL}/api/accounts/reset-password/{token}/"

    html_message = render_to_string('accounts/emails/password_reset.html', {
        'user': user,
        'reset_url': reset_url,
    })

    _send_email_brevo_api(
        subject="Réinitialisation de votre mot de passe - HOPITEL",
        html_content=html_message,
        recipient_email=user.email,
        recipient_name=f"{user.first_name} {user.last_name}"
    )

def send_account_created_whatsapp(user, password=None, reset_token=None):
    """Envoie une notification WhatsApp lors de la création d'un compte Staff."""
    if not getattr(settings, 'ENABLE_WHATSAPP', True):
        return
        
    tel = getattr(user, 'telephone', None)
    if not tel:
        return
        
    clean_phone = "".join(filter(str.isdigit, str(tel)))
    role_display = getattr(user, 'get_role_display', lambda: getattr(user, 'role', 'Utilisateur'))()
    
    msg = f"🏥 *HOPITEL - Bienvenue {user.first_name}*\n\n"
    msg += f"Votre compte *{role_display}* a été créé avec succès.\n\n"
    msg += f"📧 Email : {user.email}\n"
    
    if password:
        msg += f"🔑 Mot de passe : *{password}*\n"
        msg += f"🔗 Lien de connexion : {settings.FRONTEND_URL}/login\n\n"
        msg += "⚠️ Pour des raisons de sécurité, veuillez modifier ce mot de passe dès votre première connexion."
    elif reset_token:
        setup_url = f"{settings.FRONTEND_URL}/reset-password/{reset_token}"
        msg += f"🔗 Cliquez ici pour créer votre mot de passe : {setup_url}"
        
    try:
        from Chatbot.whatsapp_utils import send_whatsapp_message
        send_whatsapp_message(clean_phone, msg)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Impossible d'envoyer le message de création par WhatsApp: {e}")

def send_password_reset_whatsapp(user, token):
    """Envoie le lien de réinitialisation de mot de passe par WhatsApp."""
    if not getattr(settings, 'ENABLE_WHATSAPP', True):
        return
        
    tel = getattr(user, 'telephone', None)
    if not tel:
        return
        
    clean_phone = "".join(filter(str.isdigit, str(tel)))
    
    # URL vers le backend pour la page HTML de réinitialisation
    reset_url = f"{settings.BACKEND_URL}/api/accounts/reset-password/{token}/"
    
    msg = f"🔒 *HOPITEL - Réinitialisation*\n\n"
    msg += f"Bonjour {user.first_name},\n"
    msg += "Vous avez demandé à réinitialiser votre mot de passe.\n\n"
    msg += f"🔗 Cliquez ici pour le réinitialiser : {reset_url}\n\n"
    msg += "⏳ Ce lien expirera dans 15 minutes."
    
    try:
        from Chatbot.whatsapp_utils import send_whatsapp_message
        return send_whatsapp_message(clean_phone, msg)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Impossible d'envoyer le reset password par WhatsApp: {e}")
        return {"success": False}


def send_appointment_request_email(rdv):
    """Envoie une notification au médecin lors d'une nouvelle demande de RDV."""
    if not getattr(settings, 'ENABLE_EMAILS', True):
        return

    context = {
        'rdv': rdv,
        'doctor_name': rdv.medecin.user.get_full_name(),
        'patient_name': rdv.patient.user.get_full_name(),
        'date': rdv.date_heure.strftime('%d/%m/%Y'),
        'heure': rdv.date_heure.strftime('%H:%M'),
    }
    html_message = render_to_string('rendezvous/emails/nouvelle_demande.html', context)
    
    _send_email_brevo_api(
        subject="Nouvelle demande de rendez-vous - HOPITEL",
        html_content=html_message,
        recipient_email=rdv.medecin.user.email,
        recipient_name=rdv.medecin.user.get_full_name()
    )

def send_appointment_status_email(rdv):
    """Envoie une notification au patient lorsque le statut du RDV change."""
    if not getattr(settings, 'ENABLE_EMAILS', True):
        return

    context = {
        'rdv': rdv,
        'patient_name': rdv.patient.user.get_full_name(),
        'doctor_name': rdv.medecin.user.get_full_name(),
        'date': rdv.date_heure.strftime('%d/%m/%Y'),
        'heure': rdv.date_heure.strftime('%H:%M'),
        'statut': rdv.get_statut_display(),
        'motif': rdv.commentaire_annulation,
    }
    subject = "Confirmation de votre rendez-vous" if rdv.statut == 'confirme' else "Mise à jour de votre rendez-vous"
    html_message = render_to_string('rendezvous/emails/statut_rdv.html', context)
    
    _send_email_brevo_api(
        subject=f"{subject} - HOPITEL",
        html_content=html_message,
        recipient_email=rdv.patient.user.email,
        recipient_name=rdv.patient.user.get_full_name()
    )
