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

| **Dr. Saidou MAMA** | `mama@HOPITEL.com` | Chirurgie Générale | CHU Parakou |
| **Dr. René KODJO** | `kodjo@HOPITEL.com` | Gynécologie | HZ Calavi |
| **Dr. Pierrette SOSSA** | `sossa@HOPITEL.com` | Gynécologie | HZ Calavi |
| **Dr. Gérard ATI** | `ati@HOPITEL.com` | Gynécologie | HZ Calavi |

### 🧪 Laboratoires (BioTrack - 3 Laborantins)
| Laborantin | Email | Établissement |
|------------|-------|---------------|
| **Paul DOSSOU-LAB** | `lab.cnhu@HOPITEL.com` | CNHU-HKM Cotonou |
| **Anne MARIE-LAB** | `lab.chud@HOPITEL.com` | CHUD Porto-Novo |
| **Abdou RAMANE-LAB** | `lab.parakou@HOPITEL.com` | CHU Parakou |

### 👤 Patients (Scénarios de test variés)
| Patient | Email | Scénario de Test |
|---------|-------|------------------|
| **Sidicke TRAORE** | `sidicke@HOPITEL.com` | **Complet** : RDV terminé, Rapport médical, Analyses, Chat. |
| **Alice BENIN** | `patient2@HOPITEL.com` | **Urgence** : RDV en attente de validation. |
| **Bob CANCEL** | `patient3@HOPITEL.com` | **Historique** : Patient ayant des RDV annulés. |
| **Claire LABO** | `patient4@HOPITEL.com` | **BioTrack** : Analyse en cours (Glycémie). |
| **David INTAKE** | `patient5@HOPITEL.com` | **Pré-enregistrement** : Dossier symptômes déjà rempli. |
| **Eve NEW** | `patient6@HOPITEL.com` | **Nouveau** : Compte vide, sans historique. |

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

