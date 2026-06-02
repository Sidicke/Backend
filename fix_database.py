#!/usr/bin/env python3
"""
Script de nettoyage et synchronisation de la base de données production.
À exécuter sur le serveur Render après déploiement.
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_soutenance.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from accounts.models import Patient, Medecin, Laborantin
from hopitaux.models import Hopital, Service
from datetime import date

User = get_user_model()

def clean_database():
    """Nettoie les données existantes et crée des données propres."""
    print("🧹 Nettoyage de la base de données...")
    
    with transaction.atomic():
        # Supprimer les données existantes dans l'ordre inverse des contraintes
        print("  - Suppression des notifications...")
        from notifications.models import Notification
        Notification.objects.all().delete()
        
        print("  - Suppression des messages...")
        from messagerie.models import Message
        Message.objects.all().delete()
        
        print("  - Suppression des conversations...")
        from messagerie.models import Conversation
        Conversation.objects.all().delete()
        
        print("  - Suppression des rendez-vous...")
        from rendezvous.models import RendezVous, Disponibilite, Consultation
        RendezVous.objects.all().delete()
        Disponibilite.objects.all().delete()
        Consultation.objects.all().delete()
        
        print("  - Suppression des résultats...")
        from resultats.models import Resultat
        Resultat.objects.all().delete()
        
        print("  - Suppression des demandes...")
        from hopitaux.models import DemandeService
        DemandeService.objects.all().delete()
        
        print("  - Suppression des profils...")
        Patient.objects.all().delete()
        Medecin.objects.all().delete()
        Laborantin.objects.all().delete()
        
        print("  - Suppression des services...")
        Service.objects.all().delete()
        
        print("  - Suppression des hôpitaux...")
        Hopital.objects.all().delete()
        
        print("  - Suppression des utilisateurs (sauf superuser)...")
        User.objects.filter(is_superuser=False).delete()

def create_initial_data():
    """Crée les données initiales pour le fonctionnement de l'app."""
    print("📥 Création des données initiales...")
    
    with transaction.atomic():
        # Créer plusieurs hôpitaux
        hopitaux_data = [
            {
                "nom": "Centre Hospitalier Universitaire (CHU)",
                "adresse": "Cotonou, Bénin",
                "telephone": "+229 21 30 00 00",
                "email": "contact@chu-benin.bj"
            },
            {
                "nom": "Centre National Hospitalier et Universitaire (CNHU)",
                "adresse": "Cotonou, Bénin",
                "telephone": "+229 21 31 00 00",
                "email": "info@cnhu-benin.bj"
            },
            {
                "nom": "Hôpital de Zone de Porto-Novo",
                "adresse": "Porto-Novo, Bénin",
                "telephone": "+229 22 20 00 00",
                "email": "hzp-portonovo@bj"
            }
        ]
        
        created_hopitaux = []
        for hopital_data in hopitaux_data:
            hopital = Hopital.objects.create(**hopital_data)
            created_hopitaux.append(hopital)
            print(f"  ✅ Hôpital créé: {hopital.nom}")
        
        # Créer des services pour chaque hôpital
        services_data = [
            {"nom": "Médecine Générale", "description": "Consultations générales"},
            {"nom": "Cardiologie", "description": "Spécialité cœur et vaisseaux"},
            {"nom": "Pédiatrie", "description": "Soins médicaux pour enfants"},
            {"nom": "Gynécologie-Obstétrique", "description": "Santé de la femme et accouchements"},
            {"nom": "Laboratoire", "description": "Analyses médicales"},
            {"nom": "Radiologie", "description": "Imagerie médicale"},
            {"nom": "Urgences", "description": "Soins d'urgence 24/7"},
            {"nom": "Chirurgie", "description": "Interventions chirurgicales"},
        ]
        
        created_services = []
        for hopital in created_hopitaux:
            for service_data in services_data:
                service = Service.objects.create(
                    hopital=hopital,
                    **service_data
                )
                created_services.append(service)
                print(f"  ✅ Service créé: {service.nom} ({hopital.nom})")
        
        # Créer plusieurs médecins
        medecins_data = [
            {
                "email": "dr.koffi@chu-benin.bj",
                "first_name": "Dr",
                "last_name": "Koffi",
                "telephone": "+229 97 00 00 01",
                "hopital": created_hopitaux[0],
                "specialite": "Médecine Générale",
                "numero_ordre": "ORD001",
                "biographie": "Médecin généraliste avec 15 ans d'expérience"
            },
            {
                "email": "dr.adjo@chu-benin.bj",
                "first_name": "Dr",
                "last_name": "Adjo",
                "telephone": "+229 97 00 00 02",
                "hopital": created_hopitaux[0],
                "specialite": "Cardiologie",
                "numero_ordre": "ORD002",
                "biographie": "Cardiologue spécialisé en maladies cardiovasculaires"
            },
            {
                "email": "dr.sossa@cnhu-benin.bj",
                "first_name": "Dr",
                "last_name": "Sossa",
                "telephone": "+229 97 00 00 03",
                "hopital": created_hopitaux[1],
                "specialite": "Pédiatrie",
                "numero_ordre": "ORD003",
                "biographie": "Pédiatre avec 12 ans d'expérience"
            },
            {
                "email": "dr.agbo@cnhu-benin.bj",
                "first_name": "Dr",
                "last_name": "Agbo",
                "telephone": "+229 97 00 00 04",
                "hopital": created_hopitaux[1],
                "specialite": "Gynécologie-Obstétrique",
                "numero_ordre": "ORD004",
                "biographie": "Gynécologue-obstétricien spécialisée"
            },
            {
                "email": "dr.tchabi@hzp-portonovo.bj",
                "first_name": "Dr",
                "last_name": "Tchabi",
                "telephone": "+229 97 00 00 05",
                "hopital": created_hopitaux[2],
                "specialite": "Chirurgie",
                "numero_ordre": "ORD005",
                "biographie": "Chirurgien général avec 20 ans d'expérience"
            }
        ]
        
        for medecin_data in medecins_data:
            hopital = medecin_data.pop("hopital")
            specialite = medecin_data.pop("specialite")
            
            medecin_user = User.objects.create_user(
                **medecin_data,
                password="Medecin123456!",
                date_naissance=date(1980, 1, 1),
                role="medecin",
                is_active=True,
                is_email_verified=True
            )
            
            medecin = Medecin.objects.create(
                user=medecin_user,
                hopital=hopital,
                specialite=specialite,
                numero_ordre=medecin_data.get("numero_ordre"),
                biographie=medecin_data.get("biographie"),
                statut="actif"
            )
            print(f"  ✅ Médecin créé: {medecin_user.email} ({specialite})")
        
        # Créer plusieurs laborantins
        laborantins_data = [
            {
                "email": "labo1@chu-benin.bj",
                "first_name": "Labo",
                "last_name": "Technicien1",
                "telephone": "+229 98 00 00 01",
                "hopital": created_hopitaux[0],
                "laboratoire": "Laboratoire CHU - Analyses générales"
            },
            {
                "email": "labo2@chu-benin.bj",
                "first_name": "Labo",
                "last_name": "Technicien2",
                "telephone": "+229 98 00 00 02",
                "hopital": created_hopitaux[0],
                "laboratoire": "Laboratoire CHU - Biochimie"
            },
            {
                "email": "labo3@cnhu-benin.bj",
                "first_name": "Labo",
                "last_name": "Technicien3",
                "telephone": "+229 98 00 00 03",
                "hopital": created_hopitaux[1],
                "laboratoire": "Laboratoire CNUH - Hématologie"
            },
            {
                "email": "labo4@hzp-portonovo.bj",
                "first_name": "Labo",
                "last_name": "Technicien4",
                "telephone": "+229 98 00 00 04",
                "hopital": created_hopitaux[2],
                "laboratoire": "Laboratoire HZP - Bactériologie"
            }
        ]
        
        for labo_data in laborantins_data:
            hopital = labo_data.pop("hopital")
            laboratoire = labo_data.pop("laboratoire")
            
            laborantin_user = User.objects.create_user(
                **labo_data,
                password="Labo123456!",
                date_naissance=date(1985, 1, 1),
                role="laborantin",
                is_active=True,
                is_email_verified=True
            )
            
            laborantin = Laborantin.objects.create(
                user=laborantin_user,
                hopital=hopital,
                laboratoire=laboratoire
            )
            print(f"  ✅ Laborantin créé: {laborantin_user.email}")
        
        # Créer des admins hôpital
        admins_hopitaux_data = [
            {
                "email": "admin.chu@chu-benin.bj",
                "first_name": "Admin",
                "last_name": "CHU",
                "telephone": "+229 96 00 00 01",
                "hopital": created_hopitaux[0]
            },
            {
                "email": "admin.cnhu@cnhu-benin.bj",
                "first_name": "Admin",
                "last_name": "CNUH",
                "telephone": "+229 96 00 00 02",
                "hopital": created_hopitaux[1]
            },
            {
                "email": "admin.hzp@hzp-portonovo.bj",
                "first_name": "Admin",
                "last_name": "HZP",
                "telephone": "+229 96 00 00 03",
                "hopital": created_hopitaux[2]
            }
        ]
        
        for admin_data in admins_hopitaux_data:
            hopital = admin_data.pop("hopital")
            
            admin_user = User.objects.create_user(
                **admin_data,
                password="Admin123456!",
                date_naissance=date(1975, 1, 1),
                role="admin_hopital",
                is_active=True,
                is_email_verified=True
            )
            
            from accounts.models import AdminHopital
            admin_hopital = AdminHopital.objects.create(
                user=admin_user,
                hopital=hopital
            )
            print(f"  ✅ Admin hôpital créé: {admin_user.email} ({hopital.nom})")
        
        # Créer des patients de test
        patients_data = [
            {
                "email": "patient.test1@esante-benin.bj",
                "first_name": "Patient",
                "last_name": "Test1",
                "telephone": "+229 97 00 00 01",
                "date_naissance": date(1990, 1, 1),
                "sexe": "M",
                "groupe_sanguin": "A+",
                "allergies": "Aucune",
                "password": "Patient123456!",
                "is_active": True,
                "is_email_verified": True
            },
            {
                "email": "patient.test2@esante-benin.bj",
                "first_name": "Patient",
                "last_name": "Test2",
                "telephone": "+229 97 00 00 02",
                "date_naissance": date(1992, 5, 15),
                "sexe": "F",
                "groupe_sanguin": "O+",
                "allergies": "Pollen",
                "password": "Patient123456!",
                "is_active": True,
                "is_email_verified": True
            },
            {
                "email": "patient.test3@esante-benin.bj",
                "first_name": "Patient",
                "last_name": "Test3",
                "telephone": "+229 97 00 00 03",
                "date_naissance": date(1988, 10, 20),
                "sexe": "M",
                "groupe_sanguin": "B+",
                "allergies": "Arachides",
                "password": "Patient123456!",
                "is_active": True,
                "is_email_verified": True
            }
        ]
        
        for patient_data in patients_data:
            patient_user = User.objects.create_user(
                email=patient_data["email"],
                first_name=patient_data["first_name"],
                last_name=patient_data["last_name"],
                telephone=patient_data["telephone"],
                date_naissance=patient_data["date_naissance"],
                sexe=patient_data["sexe"],
                password=patient_data["password"],
                role="patient",
                is_active=patient_data["is_active"],
                is_email_verified=patient_data["is_email_verified"]
            )
            
            from accounts.models import Patient
            patient = Patient.objects.create(
                user=patient_user,
                groupe_sanguin=patient_data["groupe_sanguin"],
                allergies=patient_data["allergies"]
            )
            print(f"  ✅ Patient créé: {patient_user.email}")
        
        # Créer un admin général
        
        # Créer un admin général
        admin_general_user = User.objects.create_user(
            email="admin.general@esante-benin.bj",
            password="AdminGen123456!",
            first_name="Admin",
            last_name="Général",
            telephone="+229 95 00 00 00",
            date_naissance=date(1970, 1, 1),
            role="admin_general",
            is_active=True,
            is_email_verified=True
        )
        print(f"  ✅ Admin général créé: {admin_general_user.email}")
        
        # Créer quelques disponibilités pour les médecins
        from rendezvous.models import Disponibilite
        import datetime
        from django.utils import timezone
        
        medecins = Medecin.objects.all()
        for medecin in medecins[:3]:  # Pour les 3 premiers médecins
            # Créer des disponibilités pour les 7 prochains jours
            for i in range(7):
                date_jour = timezone.now().date() + datetime.timedelta(days=i)
                for heure in [8, 10, 14, 16]:  # Créneaux de 8h, 10h, 14h, 16h
                    Disponibilite.objects.create(
                        medecin=medecin,
                        date=date_jour,
                        heure=heure,
                        disponible=True
                    )
            print(f"  ✅ Disponibilités créées pour Dr {medecin.user.last_name}")

def main():
    """Fonction principale."""
    print("🚀 DÉMARRAGE DE LA SYNCHRONISATION BASE DE DONNÉES")
    print("=" * 50)
    
    try:
        clean_database()
        print()
        create_initial_data()
        print()
        print("✅ SYNCHRONISATION TERMINÉE AVEC SUCCÈS")
        print()
        print("📋 COMPTES DE TEST CRÉÉS:")
        print()
        print("🏥 HÔPITAUX:")
        print("  - Centre Hospitalier Universitaire (CHU)")
        print("  - Centre National Hospitalier et Universitaire (CNHU)")
        print("  - Hôpital de Zone de Porto-Novo")
        print()
        print("👨‍⚕️ MÉDECINS:")
        print("  🔴 Dr Koffi (Médecine Générale) - dr.koffi@chu-benin.bj / Medecin123456!")
        print("  🔴 Dr Adjo (Cardiologie) - dr.adjo@chu-benin.bj / Medecin123456!")
        print("  🔴 Dr Sossa (Pédiatrie) - dr.sossa@cnhu-benin.bj / Medecin123456!")
        print("  🔴 Dr Agbo (Gynécologie) - dr.agbo@cnhu-benin.bj / Medecin123456!")
        print("  🔴 Dr Tchabi (Chirurgie) - dr.tchabi@hzp-portonovo.bj / Medecin123456!")
        print()
        print("🧪 LABORANTINS:")
        print("  🟡 Labo Technicien1 - labo1@chu-benin.bj / Labo123456!")
        print("  🟡 Labo Technicien2 - labo2@chu-benin.bj / Labo123456!")
        print("  🟡 Labo Technicien3 - labo3@cnhu-benin.bj / Labo123456!")
        print("  🟡 Labo Technicien4 - labo4@hzp-portonovo.bj / Labo123456!")
        print()
        print("👨‍💼 ADMINISTRATEURS:")
        print("  ⚫ Admin CHU - admin.chu@chu-benin.bj / Admin123456!")
        print("  ⚫ Admin CNUH - admin.cnhu@cnhu-benin.bj / Admin123456!")
        print("  ⚫ Admin HZP - admin.hzp@hzp-portonovo.bj / Admin123456!")
        print("  ⚫ Admin Général - admin.general@esante-benin.bj / AdminGen123456!")
        print()
        print("� PATIENTS:")
        print("  🟢 Patient Test1 - patient.test1@esante-benin.bj / Patient123456!")
        print("  🟢 Patient Test2 - patient.test2@esante-benin.bj / Patient123456!")
        print("  🟢 Patient Test3 - patient.test3@esante-benin.bj / Patient123456!")
        print()
        print("�� DISPONIBILITÉS:")
        print("  ✅ Créneaux disponibles pour les 7 prochains jours")
        print("  ✅ 4 créneaux par jour (8h, 10h, 14h, 16h)")
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
