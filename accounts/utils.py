from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.signing import TimestampSigner

signer = TimestampSigner()

def generate_secure_token(user_pk):
    """Génère un token cryptographiquement signé incluant un timestamp."""
    return signer.sign(str(user_pk))

def send_verification_email(user, token):
    """Envoie un email de vérification au patient inscrit."""
    verification_url = f"{settings.BACKEND_URL}/api/accounts/verify-email/{token}/"

    html_message = render_to_string('accounts/emails/verification_email.html', {
        'user': user,
        'verification_url': verification_url,
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject="Confirmez votre compte E-Santé Bénin",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_account_created_email(user, password=None, reset_token=None):
    """Envoie un email avec les identifiants ou un lien de configuration de mot de passe lors de la création d'un compte admin."""
    context = {'user': user}
    if password:
        context['password'] = password
        context['login_url'] = f"{settings.FRONTEND_URL}/login"
    elif reset_token:
        # Front-end doit avoir cette route pour définir le mot de passe initial
        context['setup_url'] = f"{settings.FRONTEND_URL}/reset-password/{reset_token}"
        
    html_message = render_to_string('accounts/emails/account_created.html', context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject="Bienvenue sur E-Santé Bénin - Votre compte a été créé",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_password_reset_email(user, token):
    """Envoie un email de réinitialisation de mot de passe."""
    # Point vers la vue HTML hébergée sur le backend
    reset_url = f"{settings.BACKEND_URL}/api/accounts/reset-password/{token}/"

    html_message = render_to_string('accounts/emails/password_reset.html', {
        'user': user,
        'reset_url': reset_url,
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject="Réinitialisation de votre mot de passe - E-Santé Bénin",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_appointment_request_email(rdv):
    """Envoie une notification au médecin lors d'une nouvelle demande de RDV."""
    context = {
        'rdv': rdv,
        'doctor_name': rdv.medecin.user.get_full_name(),
        'patient_name': rdv.patient.user.get_full_name(),
        'date': rdv.date_heure.strftime('%d/%m/%Y'),
        'heure': rdv.date_heure.strftime('%H:%M'),
    }
    html_message = render_to_string('rendezvous/emails/nouvelle_demande.html', context)
    send_mail(
        subject="Nouvelle demande de rendez-vous - E-Santé Bénin",
        message=strip_tags(html_message),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[rdv.medecin.user.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_appointment_status_email(rdv):
    """Envoie une notification au patient lorsque le statut du RDV change (confirmé/refusé)."""
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
    send_mail(
        subject=f"{subject} - E-Santé Bénin",
        message=strip_tags(html_message),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[rdv.patient.user.email],
        html_message=html_message,
        fail_silently=False,
    )
