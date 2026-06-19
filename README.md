# E-Santé Bénin — Backend (HOPITEL)

## Administration Initiale

Une fois la base de données initialisée, vous pouvez vous connecter avec le compte administrateur général.

**Identifiants par défaut :**

| Champ | Valeur |
|-------|--------|
| **Email** | `admin@hopitel.com` |
| **Mot de passe** | `HopitelAdmin2025*` |

> [!IMPORTANT]
> En mode Soutenance, toutes les notifications sont redirigées vers l'auteur.

## Initialisation des données (Seed Final)

Pour une démonstration complète et réaliste (Mémoire), utilisez le script suivant :

```bash
python seed_memoire_final.py
```

## Comptes de Démonstration (Soutenance)

### 🏥 1. Hôpital de Zone de Lokossa (Comptes Principaux)
| Rôle | Nom | Email | Mot de passe | Spécialité / Info |
|------|-----|-------|--------------|-------------------|
| **Admin Hôpital** | Gill-Marilin BADJI | `gillmarilin4@gmail.com` | `AdminLokossa2025!` | Gestion HZ Lokossa |
| **Médecin** | Marion BADJI | `marionbdj9@gmail.com` | `MedecinCardio2025!` | Cardiologue |
| **Médecin** | Akoue-Maho GILL-CHRIST | `akouemahogillchristmarilinbadj@gmail.com` | `MedecinPedia2025!` | Pédiatre |
| **Médecin** | Gill BADJI | `gillbadji@gmail.com` | `MedecinNeuro2025!` | Neurologue |
| **Laborantin** | Marilin BADJI | `marilinbadji@gmail.com` | `LaboLokossa2025!` | Laboratoire HZ Lokossa |

### 🏥 2. Autres Établissements
| Dr. Jean DOSSOU | `dr.dossou@hopitel.com` | `MedecinDossou123!` | Cardiologie | CNHU-HKM Cotonou |
| Dr. Marie TOSSOU | `dr.tossou@hopitel.com` | `TossouPedia!99` | Pédiatrie | Clinique Mahouna |
| Dr. Paul AMOUSSOU | `dr.amoussou@hopitel.com` | `AmoussouGyn!25` | Gynécologie | CHUD Porto-Novo |
| Laboratoire CNHU | `labo.agbo@hopitel.com` | `AgboLabo229#` | Laborantin | CNHU-HKM Cotonou |

### 👤 Patients (Scénarios de test variés)
| Patient | Email | Mot de passe | Scénario de Test |
|---------|-------|--------------|------------------|
| **Sidicke TRAORÉ** | `sidicke@hopitel.com` | `PatientSidicke01` | **Complet** : RDV terminé, Rapport médical, Analyses. |
| **Koffi MENSAH** | `koffi@hopitel.com` | `PatientKoffi02` | **En attente** : RDV à venir et RDV terminé. |
| **Amina SALIU** | `amina@hopitel.com` | `PatientAmina03` | **Historique** : RDV récent et annulé. |

> [!TIP]
> Pour une démonstration fluide : connectez-vous avec `marionbdj9@gmail.com` (Médecin) pour voir le dashboard médecin, puis avec `marilinbadji@gmail.com` (Laborantin) pour gérer les analyses de BioTrack.

## Structure du projet

- `accounts/` : Gestion des utilisateurs (Admins, Médecins, Patients, Laborantins).
- `hopitaux/` : Gestion des établissements et des services.
- `rendezvous/` : Agenda, réservations et consultations.
- `messagerie/` : Système de discussion instantanée professionnelle.
- `resultats/` : Module **BioTrack** pour les analyses médicales.
- `Chatbot/` : Assistant IA (RAG) pour l'orientation patient.

## Configuration de l'IA (Groq) en Production

Pour faire fonctionner le Chatbot sur Render, configurez ces variables d'environnement :

| Variable | Valeur Recommandée | Description |
|----------|-------------------|-------------|
| `GROQ_API_KEY` | `gsk_...` | Votre clé API Groq |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Modèle de langage |
| `CHATBOT_API_URL` | `https://api.groq.com/openai/v1/chat/completions` | Endpoint API |

> [!TIP]
> **Pour utiliser OpenAI** : Réglez `CHATBOT_API_URL` sur `https://api.openai.com/v1/chat/completions`, `CHATBOT_API_KEY` sur votre clé OpenAI, et `CHATBOT_MODEL` sur `gpt-4o`.

