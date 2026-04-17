import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_soutenance.settings')
django.setup()

from hopitaux.views import NearbyHospitalView
from rest_framework.test import APIRequestFactory
from accounts.models import User

factory = APIRequestFactory()
request = factory.get('/api/hopitaux/nearby/?lat=6.3&lng=2.3&radius=10')

# Need an authenticated patient
user = User.objects.filter(role='patient').first()
if user:
    from rest_framework.request import Request
    # just test the function logic
    from hopitaux.services import get_nearby_hospitals
    try:
        res = get_nearby_hospitals(user_lat=6.3, user_lng=2.3, radius_km=10)
        print("get_nearby_hospitals success:", res)

        # test serialize
        from hopitaux.serializers import NearbyHospitalSerializer
        hospitals = []
        for r in res:
            hop = r['hopital']
            hop.distance_km = r['distance_km']
            hospitals.append(hop)
        ser = NearbyHospitalSerializer(hospitals, many=True)
        print("serialize success:", ser.data)
    except Exception as e:
        import traceback
        traceback.print_exc()
else:
    print("No patient user found")
