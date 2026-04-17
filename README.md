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

## Comptes de Démonstration (Mot de passe : `Esante2025!`)

| Rôle | Email | Description |
|------|-------|-------------|
| **Admin Général** | `admin@esante-benin.com` | Dashboard global, gestion des hôpitaux |
| **Admin Hôpital (CHU)** | `admin.cotonou@esante-benin.com` | Gestion CHU Cotonou |
| **Admin Hôpital (P-Novo)** | `admin.portonovo@esante-benin.com` | Gestion Hôpital Porto-Novo |
| **Médecin (Cardio)** | `dr.kokou@esante-benin.com` | Cardiologue (CHU Cotonou) |
| **Médecin (Pédia)** | `dr.adje@esante-benin.com` | Pédiatre (CHU Cotonou) |
| **Médecin (MG)** | `dr.houessou@esante-benin.com` | Médecine Générale (HZ Porto-Novo) |
| **Laborantin (CHU)** | `lab.dossou@esante-benin.com` | Laboratoire CHU Cotonou |
| **Laborantin (P-Novo)** | `lab.agbo@esante-benin.com` | Laboratoire HZ Porto-Novo |
| **Patient 1** | `patient1@test.com` | Jean Tossou (Historique complet) |
| **Patient 2** | `patient2@test.com` | Chantal Hounkanrin (RDV confirmé) |
| **Patient 3** | `patient3@test.com` | Abdou Ibrahim (RDV refusé) |

> [!TIP]
> Utilisez le compte `patient1@test.com` pour voir un historique complet avec rendez-vous terminés, messages de consultation et résultats d'analyses.

## Structure du projet

- `accounts/` : Gestion des utilisateurs (Admins, Médecins, Patients, Laborantins).
- `hopitaux/` : Gestion des établissements et des services.
- `rendezvous/` : Agenda, réservations et consultations.
- `messagerie/` : Système de discussion instantanée.
- `resultats/` : Gestion BioTrack des analyses médicales.
- `notifications/` : Système d'alertes en temps réel.
- `Chatbot/` : Assistant IA pour les patients.

## Configuration du Chatbot (IA) en Production

Le chatbot est compatible avec toutes les APIs de type OpenAI (Groq, OpenAI, OpenRouter, xAI). Pour le faire fonctionner sur Render (ou en local), configurez les variables suivantes :

| Variable | Valeur Recommandée (Groq/Llama-3) | Description |
|----------|-----------------------------------|-------------|
| `GROQ_API_KEY` | `votre_cle_groq` | Clé API de Groq (Gratuit, très rapide) |
| `CHATBOT_API_URL` | `https://api.groq.com/openai/v1/chat/completions` | Point d'entrée de l'API |
| `CHATBOT_MODEL` | `llama-3.3-70b-versatile` | Modèle de langage à utiliser |

> [!TIP]
> **Pour utiliser OpenAI** : Réglez `CHATBOT_API_URL` sur `https://api.openai.com/v1/chat/completions`, `CHATBOT_API_KEY` sur votre clé OpenAI, et `CHATBOT_MODEL` sur `gpt-4o`.

