from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import User, Patient
from hopitaux.models import Hopital
from hopitaux.services import calculate_distance, get_nearby_hospitals


# ──────────────────────────────────────────────
# Tests du service de distance
# ──────────────────────────────────────────────

class DistanceServiceTests(TestCase):
    """Tests pour le module hopitaux.services."""

    def test_calculate_distance_known_pair(self):
        """Vérifie la distance entre Cotonou et Porto-Novo (~32 km)."""
        distance = calculate_distance(6.3703, 2.3912, 6.4969, 2.6289)
        self.assertAlmostEqual(distance, 28.73, delta=2)

    def test_calculate_distance_same_point(self):
        """Distance entre un point et lui-même = 0."""
        distance = calculate_distance(6.3703, 2.3912, 6.3703, 2.3912)
        self.assertEqual(distance, 0.0)

    def test_calculate_distance_rounding(self):
        """Vérifie que la distance est arrondie à 2 décimales."""
        distance = calculate_distance(6.3703, 2.3912, 6.3800, 2.4000)
        self.assertEqual(len(str(distance).split('.')[-1]) <= 2, True)

    def test_get_nearby_hospitals_within_radius(self):
        """Les hôpitaux dans le rayon doivent être retournés."""
        # Hôpital proche (Cotonou centre)
        Hopital.objects.create(
            nom='Hôpital Central',
            latitude=Decimal('6.3710'),
            longitude=Decimal('2.3920'),
        )
        # Hôpital loin (Parakou, ~400 km)
        Hopital.objects.create(
            nom='Hôpital Parakou',
            latitude=Decimal('9.3370'),
            longitude=Decimal('2.6303'),
        )
        results = get_nearby_hospitals(6.3703, 2.3912, radius_km=10)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['hopital'].nom, 'Hôpital Central')

    def test_get_nearby_hospitals_sorted_by_distance(self):
        """Les résultats doivent être triés du plus proche au plus éloigné."""
        Hopital.objects.create(
            nom='Hôpital B (5km)',
            latitude=Decimal('6.4100'),
            longitude=Decimal('2.3912'),
        )
        Hopital.objects.create(
            nom='Hôpital A (1km)',
            latitude=Decimal('6.3793'),
            longitude=Decimal('2.3912'),
        )
        results = get_nearby_hospitals(6.3703, 2.3912, radius_km=50)
        self.assertTrue(results[0]['distance_km'] <= results[1]['distance_km'])

    def test_get_nearby_hospitals_excludes_inactive(self):
        """Les hôpitaux inactifs ne doivent pas apparaître."""
        Hopital.objects.create(
            nom='Hôpital Inactif',
            latitude=Decimal('6.3710'),
            longitude=Decimal('2.3920'),
            is_active=False,
        )
        results = get_nearby_hospitals(6.3703, 2.3912, radius_km=10)
        self.assertEqual(len(results), 0)

    def test_get_nearby_hospitals_excludes_no_coords(self):
        """Les hôpitaux sans coordonnées ne doivent pas apparaître."""
        Hopital.objects.create(nom='Hôpital Sans GPS')
        results = get_nearby_hospitals(6.3703, 2.3912, radius_km=10)
        self.assertEqual(len(results), 0)

    def test_get_nearby_hospitals_limit(self):
        """Le nombre de résultats est limité."""
        for i in range(25):
            Hopital.objects.create(
                nom=f'Hôpital {i}',
                latitude=Decimal('6.3710'),
                longitude=Decimal('2.3920'),
            )
        results = get_nearby_hospitals(6.3703, 2.3912, radius_km=50, limit=5)
        self.assertEqual(len(results), 5)


# ──────────────────────────────────────────────
# Tests de l'endpoint /api/hopitaux/nearby/
# ──────────────────────────────────────────────

class NearbyHospitalViewTests(TestCase):
    """Tests pour l'endpoint GET /api/hopitaux/nearby/."""

    def setUp(self):
        # Créer un patient
        self.patient_user = User.objects.create_user(
            email='patient@test.com',
            password='testpass123',
            first_name='Jean',
            last_name='Patient',
            telephone='+22990000000',
            sexe='M',
            role='patient',
        )
        Patient.objects.create(
            user=self.patient_user,
            contact_urgence_nom='Contact Urgence',
            contact_urgence_tel='+22990000001',
        )

        # Créer un médecin (non-patient)
        self.medecin_user = User.objects.create_user(
            email='medecin@test.com',
            password='testpass123',
            first_name='Dr',
            last_name='Médecin',
            telephone='+22990000002',
            sexe='M',
            role='medecin',
        )

        # Créer des hôpitaux de test
        self.hopital_proche = Hopital.objects.create(
            nom='Hôpital Proche',
            latitude=Decimal('6.3710'),
            longitude=Decimal('2.3920'),
            adresse='Cotonou Centre',
            ville='Cotonou',
            telephone='+22921000000',
        )
        self.hopital_loin = Hopital.objects.create(
            nom='Hôpital Loin',
            latitude=Decimal('9.3370'),
            longitude=Decimal('2.6303'),
            adresse='Parakou',
            ville='Parakou',
            telephone='+22923000000',
        )

        self.client = APIClient()

    def _get_token(self, email, password):
        """Helper pour obtenir un JWT."""
        response = self.client.post('/api/token/', {
            'email': email,
            'password': password,
        })
        return response.data.get('access')

    def test_unauthenticated_returns_401(self):
        """Un utilisateur non authentifié reçoit 401."""
        response = self.client.get('/api/hopitaux/nearby/?lat=6.37&lng=2.39')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_patient_returns_403(self):
        """Un médecin ne peut pas accéder à l'endpoint."""
        token = self._get_token('medecin@test.com', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/hopitaux/nearby/?lat=6.37&lng=2.39')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_params_returns_400(self):
        """L'absence de lat/lng retourne 400."""
        token = self._get_token('patient@test.com', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/hopitaux/nearby/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_coords_returns_400(self):
        """Des coordonnées invalides retournent 400."""
        token = self._get_token('patient@test.com', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/hopitaux/nearby/?lat=999&lng=2.39')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_request_returns_sorted_results(self):
        """Une requête valide retourne les résultats triés par distance."""
        token = self._get_token('patient@test.com', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/hopitaux/nearby/?lat=6.37&lng=2.39&radius=500')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)
        # L'hôpital le plus proche en premier
        self.assertEqual(data[0]['nom'], 'Hôpital Proche')
        self.assertTrue(data[0]['distance_km'] < data[1]['distance_km'])

    def test_radius_filtering(self):
        """Seuls les hôpitaux dans le rayon sont retournés."""
        token = self._get_token('patient@test.com', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/hopitaux/nearby/?lat=6.37&lng=2.39&radius=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['nom'], 'Hôpital Proche')

    def test_response_format(self):
        """Vérifie le format JSON de la réponse."""
        token = self._get_token('patient@test.com', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/hopitaux/nearby/?lat=6.37&lng=2.39&radius=5')
        data = response.json()
        self.assertGreater(len(data), 0)
        item = data[0]
        expected_keys = {'id', 'nom', 'latitude', 'longitude', 'distance_km', 'adresse', 'ville', 'telephone'}
        self.assertEqual(set(item.keys()), expected_keys)

    def test_no_results_returns_empty_list(self):
        """Aucun hôpital dans le rayon → liste vide."""
        token = self._get_token('patient@test.com', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        # Coordonnées très éloignées (Arctique)
        response = self.client.get('/api/hopitaux/nearby/?lat=80.0&lng=0.0&radius=10')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])
