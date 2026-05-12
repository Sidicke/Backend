import requests
import json
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.signing import TimestampSigner

signer = TimestampSigner()

def _send_email_brevo_api(subject, html_content, recipient_email, recipient_name=""):
    """
    Envoie un email via l'API REST de Brevo (Port 443 HTTP) au lieu du SMTP.
    """
    api_key = getattr(settings, 'BREVO_API_KEY', None)
    if not api_key:
        # Fallback sur send_mail si pas de clé API (pour le développement local)
        print("BREVO_API_KEY non configurée, fallback sur SMTP.")
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
        print(f"Erreur API Brevo : {e}")
        raise Exception(f"Erreur lors de l'envoi de l'email via API Brevo : {str(e)}")

def generate_secure_token(user_pk):
    """Génère un token cryptographiquement signé incluant un timestamp."""
    return signer.sign(str(user_pk))

def send_verification_email(user, otp_code):
    """Envoie un email avec le code de vérification au patient inscrit."""
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
