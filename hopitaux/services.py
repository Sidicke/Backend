"""
Service de calcul de distance géographique.

Module isolé pour faciliter une future migration vers PostGIS.
Utilise geopy.distance.geodesic pour un calcul précis (ellipsoïde WGS-84).
"""

from geopy.distance import geodesic

from .models import Hopital


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calcule la distance en kilomètres entre deux points GPS.

    Retourne la distance arrondie à 2 décimales.
    """
    return round(geodesic((lat1, lng1), (lat2, lng2)).km, 2)


def get_nearby_hospitals(
    user_lat: float,
    user_lng: float,
    radius_km: int = 10,
    limit: int = 20,
) -> list[dict]:
    """
    Récupère les hôpitaux actifs proches de la position utilisateur.

    Étapes :
    1. Filtre les hôpitaux actifs avec coordonnées GPS valides
    2. Calcule la distance pour chaque hôpital
    3. Filtre par rayon
    4. Trie par distance ASC
    5. Limite les résultats

    Returns:
        Liste de dicts {hopital: <Hopital>, distance_km: float}
    """
    # Récupérer uniquement les hôpitaux actifs ayant des coordonnées
    hospitals = Hopital.objects.filter(
        is_active=True,
        latitude__isnull=False,
        longitude__isnull=False,
    ).only(
        'id', 'nom', 'latitude', 'longitude',
        'adresse', 'ville', 'telephone',
    )

    results = []
    for hospital in hospitals:
        # Doubler la sécurité si les coordonnées sont nulles ou corrompues
        if hospital.latitude is None or hospital.longitude is None:
            continue
            
        try:
            distance = calculate_distance(
                user_lat, user_lng,
                float(hospital.latitude), float(hospital.longitude),
            )
            if distance <= radius_km:
                results.append({
                    'hopital': hospital,
                    'distance_km': distance,
                })
        except (ValueError, TypeError, Exception) as e:
            # Ignorer cet hôpital si le calcul échoue mais continuer la boucle
            print(f"Erreur calcul distance pour hôpital {hospital.id}: {e}")
            continue

    # Tri par distance croissante + limitation
    results.sort(key=lambda r: r['distance_km'])
    return results[:limit]
