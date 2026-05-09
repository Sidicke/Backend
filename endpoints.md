# API Endpoints - Soutenance Backend

Cette liste répertorie tous les points de terminaison (endpoints) disponibles pour tester l'API de votre Backend (notamment après votre déploiement sur **Railway**).  
Si l'application est hébergée sur `https://web-production-c678d.up.railway.app`, chaque endpoint de type `/api/...` doit y être préfixé. *(ex: `https://web-production-c678d.up.railway.app/api/token/`)*.

---

## 🔐 Authentification & Utilisateurs (`/api/accounts/` & JWT)

*   `POST /api/token/` — Obtenir un token d'accès JWT (Login)
*   `POST /api/token/refresh/` — Rafraîchir le token d'accès JWT
*   `POST /api/accounts/register/` — Créer un nouveau compte patient
*   `GET  /api/accounts/verify-email/<str:token>/` — Vérifier l'adresse e-mail
*   `POST /api/accounts/request-password-reset/` — Demander la réinitialisation du mot de passe
*   `POST /api/accounts/reset-password-confirm/` — Confirmer la réinitialisation du mot de passe (via API)
*   `GET  /api/accounts/users/me/` — Obtenir les infos de l'utilisateur connecté

### Gestion des Profils (sous `/api/accounts/`)
*   `GET, POST /api/accounts/medecins/` — Lister et créer des médecins
*   `GET, PUT, DELETE /api/accounts/medecins/<int:pk>/` — Gérer un médecin spécifique
*   `POST /api/accounts/medecins/<int:pk>/desactiver/` — Désactiver un compte médecin
*   `POST /api/accounts/medecins/import/` — Importer des médecins par fichier CSV
*   `GET  /api/accounts/medecins/import-template/` — Télécharger le template d'import CSV
*   `GET, POST /api/accounts/laborantins/` — Lister et créer des laborantins
*   `GET, PUT, DELETE /api/accounts/laborantins/<int:pk>/` — Gérer un laborantin spécifique
*   `GET, POST /api/accounts/patients/` — Lister et créer des patients
*   `GET, PUT, DELETE /api/accounts/patients/<int:pk>/` — Gérer un patient spécifique
*   `GET, POST /api/accounts/admin-hopitaux/` — Lister et créer des admins d'hôpital
*   `GET, PUT, DELETE /api/accounts/admin-hopitaux/<int:pk>/` — Gérer un admin d'hôpital

---

## 🏥 Hôpitaux, Services & Médecins (`/api/`)

*   `GET, POST /api/hopitaux/` — Lister et créer des hôpitaux
*   `GET, PUT, DELETE /api/hopitaux/<int:pk>/` — Gérer un hôpital spécifique
*   `GET  /api/hopitaux/nearby/` — Trouver les hôpitaux à proximité (géolocalisation)
*   `GET  /api/hopitaux/statistiques/` — Statistiques de l'hôpital
*   `GET  /api/hopitaux/patients/` — Liste des patients d'un hôpital
*   `GET  /api/hopitaux/mes-services/` — Lister les services de son hôpital (`GET`, `POST`)
*   `PUT, DELETE /api/hopitaux/mes-services/<int:pk>/` — Modifier un service de son hôpital
*   `GET  /api/hopitaux/<int:hopital_pk>/services/` — Lister les services d'un hôpital précis
*   `GET, POST /api/services/` — Lister tous les services médicaux globaux
*   `GET, PUT, DELETE /api/services/<int:pk>/` — Gérer un service médical
*   `GET, POST /api/medecins/<int:medecin_pk>/services/` — Ajouter ou lister les services rattachés à un médecin
*   `DELETE /api/medecins/<int:medecin_pk>/services/<int:service_pk>/` — Retirer un médecin d'un service
*   `GET  /api/demandes/` — Liste des demandes (recrutement, etc.)
*   `POST /api/hopitaux/<int:hopital_pk>/demandes/` — Créer une demande auprès d'un hôpital
*   `POST /api/demandes/<int:pk>/valider/` — Valider une demande
*   `POST /api/demandes/<int:pk>/refuser/` — Refuser une demande

---

## 🔬 Examens & Résultats de Laboratoire (`/api/`)

*   `GET, POST /api/analyses/` — Créer ou lister des demandes d'analyses médicales
*   `POST /api/analyses/<int:pk>/cloturer/` — Clôturer une analyse
*   `GET  /api/laborantins/patients/` — Lister les patients assignés au laborantin
*   `GET, POST /api/resultats/` — Envoyer ou consulter un résultat d'examen
*   `GET, PUT, DELETE /api/resultats/<int:pk>/` — Consulter ou modifier un résultat précis
*   `GET  /api/resultats/<int:pk>/telecharger/` — Télécharger un résultat (PDF, doc...)
*   `POST /api/resultats/<int:pk>/partager/` — Partager un résultat (à un médecin)
*   `POST /api/resultats/<int:pk>/partager/<int:medecin_pk>/` — Retirer le partage d'un résultat
*   `GET  /api/resultats/acces/<str:code_acces>/` — Accéder à un résultat par code (public)

---

## 💬 Messagerie Interne (`/api/`)

*   `GET, POST /api/conversations/` — Accéder à ses conversations privées
*   `GET, POST /api/messages/` — Envoyer un message ou lister les historiques de messages interne
*   `POST /api/messages/<int:pk>/mark-read/` — Marquer un message comme lu

---

## 🤖 Chatbot IA (`/api/chatbot/`)

*   `GET  /api/chatbot/history/` — Récupérer l'historique complet de discussion avec l'IA
*   `POST /api/chatbot/message/` — Envoyer une requête textuelle à l'IA

---

## 🔔 Notifications (`/api/notifications/`)

*   `GET  /api/notifications/` — Obtenir la liste de ses notifications
*   `POST /api/notifications/<int:pk>/mark-read/` — Marquer une notification spécifique comme lue
*   `POST /api/notifications/mark-all-read/` — Marquer toutes les notifications comme lues
