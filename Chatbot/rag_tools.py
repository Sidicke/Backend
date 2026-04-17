from django.utils import timezone
from datetime import timedelta
import json
from django.db.models import Q

def search_doctors_rag(specialite=None, ville=None):
    """
    Recherche des médecins dans la base de données.
    :param specialite: Nom ou partie du nom de la spécialité (ex: Cardiologie)
    :param ville: Ville de l'hôpital ou du médecin.
    :return: Chaîne JSON formatée des médecins trouvés ou un message d'absence.
    """
    from accounts.models import Medecin
    
    queryset = Medecin.objects.filter(user__is_active=True).select_related('user', 'user__hopital')
    
    if specialite:
        queryset = queryset.filter(medecin_services__service__nom__icontains=specialite)
    if ville:
        queryset = queryset.filter(Q(user__adresse__icontains=ville) | Q(user__hopital__ville__icontains=ville))
        
    medecins = queryset.distinct()[:5]  # Limiter à 5 pour ne pas surcharger le prompt
    
    if not medecins.exists():
        return json.dumps({"result": "Aucun médecin trouvé pour ces critères."})
        
    results = []
    for m in medecins:
        hopital_nom = m.user.hopital.nom if m.user.hopital else "Indépendant"
        results.append({
            "id": m.user.id,
            "nom": f"Dr. {m.user.get_full_name()}",
            "hopital": hopital_nom,
            "telephone": m.user.telephone,
            "specialites": [ms.service.nom for ms in m.medecin_services.all()]
        })
        
    return json.dumps({"result": "Medecins trouves", "data": results})

def search_hospitals_rag(ville=None):
    """
    Recherche des hôpitaux dans la base de données.
    """
    from hopitaux.models import Hopital
    
    queryset = Hopital.objects.filter(is_active=True)
    if ville:
        queryset = queryset.filter(ville__icontains=ville)
        
    hopitaux = queryset[:5]
    
    if not hopitaux.exists():
        return json.dumps({"result": "Aucun hôpital trouvé."})
        
    results = []
    for h in hopitaux:
        services = [hs.service.nom for hs in h.hopital_services.all()][:3]
        results.append({
            "id": h.id,
            "nom": h.nom,
            "ville": h.ville,
            "adresse": h.adresse,
            "services_principaux": services
        })
        
    return json.dumps({"result": "Hopitaux trouves", "data": results})

def check_availabilities_rag(medecin_id):
    """
    Vérifie les créneaux disponibles pour un médecin spécifique sur les 7 prochains jours.
    """
    from accounts.models import Medecin
    from rendezvous.utils import generer_creneaux
    
    try:
        medecin = Medecin.objects.get(user_id=medecin_id, user__is_active=True)
    except Medecin.DoesNotExist:
        return json.dumps({"result": "Médecin introuvable."})
        
    date_debut = timezone.now().date()
    date_fin = date_debut + timedelta(days=7)
    
    try:
        creneaux = generer_creneaux(medecin, date_debut, date_fin)
    except Exception as e:
        return json.dumps({"result": "Erreur lors de la récupération des créneaux."})
        
    if not creneaux:
        return json.dumps({"result": "Aucune disponibilité pour les 7 prochains jours."})
        
    # Limiter à 5 créneaux pour réduire le payload LLM
    creneaux_limites = creneaux[:5]
    return json.dumps({"result": "Creneaux disponibles trouves", "data": creneaux_limites})

# Définition des tools au format OpenAI (Groq compatible)
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_doctors",
            "description": "Cherche des médecins par spécialité ou ville.",
            "parameters": {
                "type": "object",
                "properties": {
                    "specialite": {
                        "type": "string",
                        "description": "La spécialité médicale recherchée (ex: Cardiologie, Pédiatrie)."
                    },
                    "ville": {
                        "type": "string",
                        "description": "La ville où chercher le médecin."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_hospitals",
            "description": "Cherche des hôpitaux, éventuellement par ville.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ville": {
                        "type": "string",
                        "description": "La ville où chercher l'hôpital."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_availabilities",
            "description": "Récupère les créneaux horaires disponibles d'un médecin pour prendre RDV. L'ID du médecin est obligatoire.",
            "parameters": {
                "type": "object",
                "properties": {
                    "medecin_id": {
                        "type": "integer",
                        "description": "L'ID du médecin retourné par search_doctors."
                    }
                },
                "required": ["medecin_id"]
            }
        }
    }
]

# Dispatcher
def execute_tool_call(tool_call):
    """
    Exécute l'outil demandé par le modèle Groq.
    """
    name = tool_call.get("name")
    try:
        args = json.loads(tool_call.get("arguments", "{}"))
    except Exception:
        args = {}
        
    if name == "search_doctors":
        return search_doctors_rag(specialite=args.get("specialite"), ville=args.get("ville"))
    elif name == "search_hospitals":
        return search_hospitals_rag(ville=args.get("ville"))
    elif name == "check_availabilities":
        medecin_id = args.get("medecin_id")
        if not medecin_id:
            return json.dumps({"result": "Paramètre medecin_id manquant"})
        return check_availabilities_rag(medecin_id)
        
    return json.dumps({"result": "Outil inconnu"})
