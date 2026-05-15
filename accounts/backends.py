from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrPhoneModelBackend(ModelBackend):
    """
    Backend d'authentification personnalisé permettant à un utilisateur de
    se connecter avec son adresse email OU son numéro de téléphone.
    """
    def authenticate(self, request, email=None, password=None, **kwargs):
        # Mémoriser la valeur saisie (Soit envoyée via "email", soit via "username")
        credential = email or kwargs.get('username')
        
        if not credential:
            return None
            
        try:
            # Recherche par email OU par téléphone
            user = User.objects.get(Q(email__iexact=credential) | Q(telephone=credential))
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            # Sécurité au cas où il y aurait des doublons (ex: même numéro)
            return User.objects.filter(Q(email__iexact=credential) | Q(telephone=credential)).order_by('id').first()
            
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
