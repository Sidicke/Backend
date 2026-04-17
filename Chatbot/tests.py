from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User, Patient
from Chatbot.models import ChatSession

class ChatbotPermissionsTest(TestCase):
    def setUp(self):
        # Patient
        self.patient_user = User.objects.create_user(
            email='patientbot@test.com', password='testpass123',
            first_name='Jean', last_name='Patient', role='patient'
        )
        self.patient = Patient.objects.create(user=self.patient_user)
        
        # Medecin
        self.medecin_user = User.objects.create_user(
            email='medicbot@test.com', password='testpass123',
            first_name='Doc', last_name='Medic', role='medecin'
        )
        self.client = APIClient()

    def get_token(self, email, password):
        resp = self.client.post('/api/token/', {'email': email, 'password': password})
        return resp.data['access']

    def test_unauthenticated_forbidden(self):
        resp = self.client.get('/api/chatbot/history/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_medecin_forbidden(self):
        token = self.get_token('medicbot@test.com', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.post('/api/chatbot/message/', {'message': 'Hello'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_patient_allowed_history(self):
        token = self.get_token('patientbot@test.com', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.get('/api/chatbot/history/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json(), []) # empty list
        
        # Test implicit session creation
        self.assertEqual(ChatSession.objects.filter(patient=self.patient).count(), 1)
