import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_soutenance.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

email = "salutsidicke@gmail.com"
try:
    user = User.objects.get(email=email)
    print(f"[-] Compte trouvé : {email}")
    print(f"[-] Statut actuel : is_active={user.is_active}, is_email_verified={getattr(user, 'is_email_verified', 'N/A')}")
    
    user.is_active = True
    if hasattr(user, 'is_email_verified'):
        user.is_email_verified = True
    user.save()
    
    print(f"[+] Compte ACTIVÉ avec succès : {email}")
except User.DoesNotExist:
    print(f"[!] Erreur : Aucun utilisateur trouvé avec l'email {email}")
