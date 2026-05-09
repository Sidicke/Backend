# E-Santé Bénin — Backend

## Administration Initiale

Une fois la base de données initialisée, vous pouvez vous connecter avec le compte administrateur général par défaut.

**Identifiants par défaut :**

| Champ | Valeur |
|-------|--------|
| **Email** | `admin@esante-benin.com` |
| **Mot de passe** | `Esante2025!` |

> [!IMPORTANT]
> Il est fortement recommandé de changer ce mot de passe dès la première connexion via l'interface d'administration ou le profil.

## Initialisation des données (Seed)

Le script de seed permet d'initialiser rapidement l'environnement.

```bash
# 1. Pour une installation PROPRE (Super Admin + Services de base)
python manage.py seed --clean

# 2. Pour une DÉMONSTRATION COMPLÈTE (Hôpitaux, Médecins, Patients, RDV, Analyses, Messages)
python manage.py seed_demo --clean
```

## Comptes de Démonstration (Soutenance)

Tous les comptes ci-dessous utilisent le mot de passe unique : **`Esante2025!`**

### 🏢 Administration & Gestion
| Rôle | Email | Zone / Hôpital |
|------|-------|----------------|
| **Admin Général** | `admin@esante-benin.com` | Tous les sites (Super Admin) |
| **Admin CNHU** | `admin.cnhu@esante.com` | CNHU-HKM (Cotonou) |
| **Admin CHUD** | `admin.chud@esante.com` | CHUD Porto-Novo |
| **Admin Parakou** | `admin.parakou@esante.com` | CHU Parakou |
| **Admin Calavi** | `admin.calavi@esante.com` | Hôpital de Zone (Calavi) |

### 👨‍⚕️ Corps Médical (Liste Intégrale des 12 médecins)
| Médecin | Email | Spécialité | Hôpital |
|---------|-------|------------|---------|
| **Dr. Jean DOSSOU** | `dossou@esante.com` | Cardiologie | CNHU-HKM |
| **Dr. Marie TOSSOU** | `tossou@esante.com` | Pédiatrie | CNHU-HKM |
| **Dr. Alain GNONLONFOUN** | `gnonlonfoun@esante.com` | Gynécologie | CNHU-HKM |
| **Dr. Marc HOUESSOU** | `houessou@esante.com` | Pédiatrie | CHUD Porto-Novo |
| **Dr. Sophie AGOSSOU** | `agossou@esante.com` | Neurologie | CHUD Porto-Novo |
| **Dr. Basile ZANNOU** | `zannou@esante.com` | Pédiatrie | CHUD Porto-Novo |
| **Dr. Yacoubou BIO** | `bio@esante.com` | Chirurgie Générale | CHU Parakou |
| **Dr. Félicien SIKA** | `sika@esante.com` | Ophtalmologie | CHU Parakou |
| **Dr. Saidou MAMA** | `mama@esante.com` | Chirurgie Générale | CHU Parakou |
| **Dr. René KODJO** | `kodjo@esante.com` | Gynécologie | HZ Calavi |
| **Dr. Pierrette SOSSA** | `sossa@esante.com` | Gynécologie | HZ Calavi |
| **Dr. Gérard ATI** | `ati@esante.com` | Gynécologie | HZ Calavi |

### 🧪 Laboratoires (BioTrack - 3 Laborantins)
| Laborantin | Email | Établissement |
|------------|-------|---------------|
| **Paul DOSSOU-LAB** | `lab.cnhu@esante.com` | CNHU-HKM Cotonou |
| **Anne MARIE-LAB** | `lab.chud@esante.com` | CHUD Porto-Novo |
| **Abdou RAMANE-LAB** | `lab.parakou@esante.com` | CHU Parakou |

### 👤 Patients (Scénarios de test variés)
| Patient | Email | Scénario de Test |
|---------|-------|------------------|
| **Sidicke TRAORE** | `sidicke@esante.com` | **Complet** : RDV terminé, Rapport médical, Analyses, Chat. |
| **Alice BENIN** | `patient2@esante.com` | **Urgence** : RDV en attente de validation. |
| **Bob CANCEL** | `patient3@esante.com` | **Historique** : Patient ayant des RDV annulés. |
| **Claire LABO** | `patient4@esante.com` | **BioTrack** : Analyse en cours (Glycémie). |
| **David INTAKE** | `patient5@esante.com` | **Pré-enregistrement** : Dossier symptômes déjà rempli. |
| **Eve NEW** | `patient6@esante.com` | **Nouveau** : Compte vide, sans historique. |

> [!TIP]
> Pour une démonstration fluide : connectez-vous d'abord en tant que **Sidicke** pour montrer l'historique riche, puis avec le **Dr. Dossou** pour voir le dashboard médecin.

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

