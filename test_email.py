import os
import django
from decouple import config

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_soutenance.settings')
django.setup()

from django.core.mail import send_mail

try:
    send_mail(
        'Test Subject',
        'Test Message',
        config('DEFAULT_FROM_EMAIL'),
        [config('EMAIL_HOST_USER')], # send to self
        fail_silently=False,
    )
    print("EMAIL SENT SUCCESSFULLY!")
except Exception as e:
    print(f"EMAIL ERROR: {e}")
