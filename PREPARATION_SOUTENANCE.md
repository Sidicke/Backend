# 🎓 HOPITEL - PRÉPARATION À LA SOUTENANCE (SIMULATION DE JURY EXTRÊME)

Ce document constitue votre base d'entraînement pour le jury. Il contient les questions techniques classées par domaines d'expertise, spécifiquement adaptées à l'architecture de **HOPITEL** (Django, PostgreSQL, Flutter, Render, Baileys/WhatsApp, Brevo). 

---

## 1. JURY GÉNIE LOGICIEL & ARCHITECTURE
1. HOPITEL repose sur un backend Django REST Framework. Pourquoi un monolithe modulaire plutôt qu'une architecture 100% microservices (Node.js/Go) ?
2. Vous avez isolé l'envoi WhatsApp dans un microservice Node.js (Baileys). Pourquoi ne pas avoir intégré un client WhatsApp directement dans Python/Django ? Qu'est-ce que cela implique en termes de résilience ?
3. Expliquez le diagramme de séquence exact lorsqu'un patient s'inscrit, reçoit un OTP WhatsApp, et valide son compte. Quels sont les "goulots d'étranglement" de ce flux ?
4. Comment gérez-vous les transactions au sein de votre base de données lors d'une prise de rendez-vous ? Que se passe-t-il si le service d'email plante *après* l'insertion du RDV en base ?
5. Pourquoi avoir séparé le modèle `User` des modèles `Patient`, `Medecin` et `Laborantin` (OneToOne) plutôt que d'utiliser l'héritage de base de données (Multi-table inheritance) de Django ?
6. Comment justifiez-vous l'utilisation de Django Channels (WebSockets) ? Était-ce strictement indispensable pour les notifications ou le *Server-Sent Events (SSE)* aurait-il suffi ?
7. Si l'application atteint 10 000 utilisateurs simultanés, quelle partie de votre architecture (Base de données, Django, Serveur WhatsApp) s'écroulera en premier et pourquoi ?

## 2. JURY BACKEND (DJANGO & PYTHON)
8. Votre système de Custom User Manager gère la normalisation des emails (minuscules). Pourquoi est-ce critique en termes de sécurité ?
9. Quel est le rôle exact du Middleware dans Django ? Pouvez-vous coder mentalement un middleware personnalisé ?
10. Sur Render, comment avez-vous géré la persistance des fichiers médias (images/photos de profil) ? Sachant que Render Ephemeral Disk efface les fichiers à chaque redéploiement ?
11. Vous utilisez `get_or_create` ou `update_or_create` dans vos scripts de Seed. Expliquez comment Django gère les conditions de course (Race Conditions) sur un `get_or_create` si deux requêtes arrivent simultanément.
12. Comment optimisez-vous le "N+1 query problem" dans vos Serializers REST Framework (ex: la liste des médecins avec leurs hôpitaux) ? Utilisez-vous `select_related` ou `prefetch_related` ?
13. Pourquoi utiliser Gunicorn/Daphne en production plutôt que le serveur par défaut `runserver` de Django ? Que font-ils de différent au niveau système ?
14. Expliquez la notion d'idempotence dans vos migrations de base de données (ex: la fameuse migration `0006_patient_npi`). 

## 3. JURY FRONTEND (FLUTTER)
15. Pourquoi choisir Flutter plutôt que React Native ou une PWA (Progressive Web App) classique pour le contexte béninois ?
16. Quelle solution de State Management utilisez-vous (Provider, Bloc, GetX, Riverpod) et pourquoi est-ce la solution la plus pertinente pour HOPITEL ?
17. Comment Flutter gère-t-il le rafraîchissement des tokens JWT ? Que se passe-t-il si un utilisateur est en pleine prise de rendez-vous et que son accessToken expire ?
18. Expliquez le fonctionnement du Garbage Collector dans Dart.
19. Comment avez-vous géré la responsivité de l'interface pour s'adapter à la fois aux petits smartphones Android et aux tablettes utilisées par les médecins ?
20. En cas de coupure internet, votre application crashe-t-elle ou y a-t-il une stratégie de cache local (Hive, SQLite, SharedPreferences) ?

## 4. JURY BASE DE DONNÉES (POSTGRESQL)
21. Pourquoi PostgreSQL et pas MySQL ou MongoDB pour des données de santé ?
22. Expliquez la notion d'ACID. Comment PostgreSQL garantit-il l'intégrité de vos données lors de l'attribution d'un code court hospitalier unique ?
23. Vous avez des champs `unique=True`. Comment cela se traduit-il techniquement dans la mémoire et sur le disque du serveur PostgreSQL ? (Index B-Tree).
24. Qu'est-ce qu'une clé étrangère `on_delete=models.CASCADE` ? Quels sont les risques dévastateurs de cette commande dans HOPITEL si un Hôpital est supprimé ? Comment l'éviter ?
25. Quelles tables prendront le plus de volume dans 5 ans ? Avez-vous prévu une stratégie d'archivage des anciens rendez-vous ?

## 5. JURY CYBERSÉCURITÉ
26. Vous utilisez JWT (JSON Web Tokens). Où stockez-vous ces tokens sur l'appareil client (Flutter) ?
27. Si on vole le Token JWT d'un Médecin, l'attaquant a accès à tous les dossiers médicaux. Comment invalider un JWT sachant qu'il est "stateless" ? Avez-vous implémenté une Blacklist de tokens ?
28. Qu'est-ce qu'une attaque CSRF ? Êtes-vous vulnérable sachant que vous utilisez des API REST avec JWT ?
29. Comment protégez-vous la route de création de compte contre le "Brute Force" (spam SMS WhatsApp / Emails coûtant de l'argent et des ressources) ?
30. Avez-vous mis en place du Rate Limiting sur Django REST Framework ? 
31. Comment garantissez-vous que le Médecin A ne peut pas modifier via l'API (POST / PUT) les rendez-vous du Médecin B ? Comment les permissions DRF sont-elles architecturées ?
32. Vos variables d'environnement (`.env`) sur Render (Secret Key, Mot de passe BDD). Que se passe-t-il si un développeur pousse par erreur le fichier `.env` sur GitHub ?

## 6. JURY DÉPLOIEMENT & DEVOPS
33. Vous hébergez le backend sur Render. Quelles sont les limitations du Free Tier ou des offres basiques de Render (Spin-down, RAM limitée) ?
34. À quoi a servi la configuration dynamique du `CORS_ALLOWED_ORIGINS` dans vos settings ? Que se passe-t-il si vous mettez `*` (Wildcard) en production ?
35. Pourquoi n'avez-vous pas déployé l'application via Docker ? N'aurait-il pas été plus simple pour gérer à la fois Python et Node.js dans un seul environnement ?
36. Décrivez votre pipeline (ou flux) de déploiement manuel ou CI/CD : du `git push` jusqu'à la mise en ligne du code. 

## 7. JURY ENTREPRENEURIAT & GESTION DE PROJET
37. Quel est votre Modèle Économique (Business Model) ? Qui paie pour utiliser HOPITEL ? Les hôpitaux, les patients, ou l'État béninois ?
38. Quels sont vos principaux concurrents en Afrique de l'Ouest ? En quoi HOPITEL est-il fondamentalement meilleur ?
39. La protection des données médicales est critique (Loi sur le Numérique au Bénin, RGPD). Comment assurez-vous la confidentialité des données de résultats d'analyses (BioTrack) ?
40. Si un hôpital zonal existant (ex: Lokossa) refuse de changer ses habitudes papier. Comment conduisez-vous le changement technologique ?

---

*La banque complète de questions (plus de 300 possibilités) variera en fonction de vos réponses lors de la simulation. La simulation se déroule dans la console adjacente.*
