# Interprétation des Diagrammes UML — E-Santé Bénin

---

## 1. Diagramme de Cas d'Utilisation

### 1.1 Description générale

Le diagramme de cas d'utilisation présente les interactions entre les **cinq acteurs** du système (Patient, Médecin, Laborantin, Administrateur Hôpital, Administrateur Général) ainsi qu'un acteur système (**Assistant IA / Groq**). Il recense l'ensemble des fonctionnalités offertes par la plateforme E-Santé Bénin, organisées en huit grands blocs fonctionnels :

- **Authentification & Compte** — Inscription, connexion JWT, réinitialisation de mot de passe.
- **Gestion des Rendez-vous** — Recherche, prise, confirmation, annulation, terminaison de RDV.
- **Parcours de Soins** — Pré-enregistrement (intake), rédaction et clôture de consultation.
- **Laboratoire & Résultats** — Demande d'analyse, saisie de résultat, consultation par code d'accès.
- **Messagerie** — Échanges texte/vocal/fichier entre patient et médecin.
- **Assistant IA (Chatbot)** — Questions médicales, recherche RAG, actions de redirection UI.
- **Notifications** — Alertes en temps réel pour chaque événement du parcours de soins.
- **Administration** — Gestion du personnel, des hôpitaux, des services et du tableau de bord.

### 1.2 Relations `<<include>>` et `<<extend>>`

Les relations stéréotypées permettent de modéliser les dépendances et les options entre cas d'utilisation :

#### Relations `<<include>>` (obligatoires)

| Cas d'utilisation source | Cas d'utilisation inclus | Explication |
|--------------------------|--------------------------|-------------|
| Terminer un rendez-vous | Rédiger une consultation | La terminaison d'un RDV **crée automatiquement** une consultation vide rattachée. Le médecin ne peut pas terminer un RDV sans que ce mécanisme se déclenche. |
| Confirmer / Refuser un RDV | Recevoir des notifications | Toute confirmation ou refus **déclenche obligatoirement** une notification au patient concerné. |
| Saisir et clôturer un résultat | Recevoir des notifications | La clôture d'un résultat d'analyse **génère automatiquement** une notification informant le patient que ses résultats sont disponibles. |
| Envoyer un message | Recevoir des notifications | Chaque nouveau message **déclenche systématiquement** une notification pour le destinataire (patient ou médecin). |
| Recevoir des actions de redirection | Rechercher via l'IA (RAG) | Les actions de redirection UI sont **toujours issues** d'une recherche RAG préalable dans la base de données (hôpitaux, médecins, disponibilités). |
| S'inscrire | Envoyer un email de vérification | L'inscription **inclut obligatoirement** l'envoi d'un email de vérification. En cas d'échec, la transaction est annulée (rollback atomique). |

#### Relations `<<extend>>` (optionnelles)

| Cas d'utilisation de base | Cas d'utilisation étendu | Explication |
|---------------------------|-------------------------|-------------|
| Consulter ses résultats | Partager un résultat avec un médecin | Le patient **peut optionnellement** partager un résultat d'analyse avec un médecin de son choix. Ce partage n'est pas obligatoire. |
| Prendre un rendez-vous | Remplir le pré-enregistrement (intake) | Après avoir pris un RDV, le patient **peut facultativement** remplir un formulaire de pré-enregistrement (symptômes, traitements en cours) avant la date de consultation. |
| Poser une question médicale | Rechercher un hôpital / médecin via l'IA | Lors d'une conversation avec le chatbot, l'IA **peut étendre** la réponse en lançant une recherche RAG si elle détecte une intention de recherche dans le message du patient. |

---

## 2. Diagramme de Classes

### 2.1 Description générale

Le diagramme de classes modélise la **structure statique** de la base de données de la plateforme, organisée en **sept modules** Django :

- **accounts** — Modèle utilisateur unique (`User`) avec authentification par email, et trois profils métiers spécialisés (`Patient`, `Medecin`, `Laborantin`) liés par des relations `OneToOne`.
- **hopitaux** — Gestion des établissements (`Hopital`), des spécialités médicales (`Service`), et des tables associatives (`HopitalService`, `MedecinService`) permettant d'associer des services aux hôpitaux et aux médecins. Inclut également le workflow de demande d'ajout de service (`DemandeAjoutService`).
- **rendezvous** — Cycle de vie complet d'un rendez-vous (`RendezVous` → `Consultation`), la gestion des disponibilités médecin (`Disponibilite`) et le formulaire de pré-enregistrement (`PreEnregistrement`).
- **resultats** — Circuit du laboratoire avec la demande d'analyse (`DemandeAnalyse`) et le dépôt de résultat (`Resultat`) muni d'un code d'accès unique auto-généré.
- **messagerie** — Échanges entre patient et médecin (`Message`) avec support texte, vocal et fichier, liés à une consultation.
- **chatbot** — Historique des conversations IA (`ChatSession`, `ChatMessage`) et logs anonymes (`ChatLog`).
- **notifications** — Système d'alertes en temps réel (`Notification`) avec 12 types d'événements couvrant l'intégralité du parcours de soins.

### 2.2 Relations clés

| Relation | Type | Description |
|----------|------|-------------|
| User ↔ Patient / Medecin / Laborantin | OneToOne | Chaque utilisateur possède **au plus un** profil métier, déterminé par son rôle |
| User → Hopital | ForeignKey (N:1) | Un utilisateur (médecin, laborantin, admin) est rattaché à **un** hôpital |
| Hopital ↔ Service | ManyToMany via HopitalService | Un hôpital propose **plusieurs** services et un service existe dans **plusieurs** hôpitaux |
| Medecin ↔ Service | ManyToMany via MedecinService | Un médecin exerce **plusieurs** spécialités |
| Patient → RendezVous ← Medecin | ForeignKey (N:1) | Un RDV lie **un** patient à **un** médecin |
| RendezVous → Consultation | OneToOne | Chaque RDV terminé génère **exactement une** consultation |
| RendezVous → PreEnregistrement | OneToOne | Un patient peut soumettre **un** formulaire d'intake par RDV |
| DemandeAnalyse → Resultat | OneToOne | Chaque demande d'analyse produit **au plus un** résultat à la clôture |
| Resultat ↔ Medecin | ManyToMany (partages) | Un résultat peut être partagé avec **plusieurs** médecins |

---

## 3. Diagrammes de Séquence

### 3.1 Description générale

Les six diagrammes de séquence illustrent les **flux dynamiques** principaux de la plateforme, montrant l'enchaînement chronologique des interactions entre les acteurs, l'API REST, la base de données et les services externes.

### 3.2 Interprétation de chaque diagramme

#### Séquence 1 : Inscription d'un Patient
Ce diagramme illustre le mécanisme de **transaction atomique** mis en place pour sécuriser l'inscription. L'utilisateur remplit le formulaire sur l'application mobile. Le backend valide les données, crée le compte (inactif) et tente d'envoyer un email de vérification. Si l'email échoue (coupure réseau), un **rollback** annule la création du compte, évitant ainsi les "comptes fantômes" qui bloqueraient les futures tentatives d'inscription.

#### Séquence 2 : Prise de Rendez-vous
Ce diagramme montre le flux de réservation : le patient sélectionne un médecin et un créneau, l'API vérifie la disponibilité du médecin, crée le rendez-vous avec un statut "en attente", et déclenche une notification au médecin. Si le créneau est indisponible, le système renvoie une erreur explicite.

#### Séquence 3 : Flux de Consultation Complet
Ce diagramme couvre le cycle complet côté médecin, depuis la **confirmation** du rendez-vous, sa **terminaison** (qui crée automatiquement une consultation vide), la **rédaction** du diagnostic et de la prescription, jusqu'à la **clôture** de la consultation (qui ferme la messagerie associée). Chaque étape génère une notification pour le patient.

#### Séquence 4 : Flux Laboratoire
Ce diagramme détaille le circuit de l'analyse médicale : le laborantin inscrit une demande d'analyse, puis la clôture en saisissant les résultats et un fichier PDF. Le système génère automatiquement un **code d'accès unique** (exemple : `CNHU-202605-A3F9K1`) et notifie le patient que ses résultats sont disponibles. Le patient peut ensuite consulter ses résultats via ce code.

#### Séquence 5 : Interaction avec l'Assistant IA
Ce diagramme illustre le fonctionnement du **RAG (Retrieval-Augmented Generation)**. Le patient pose une question au chatbot, qui est transmise à l'API Groq avec un schéma de **Function Calling**. L'IA détecte l'intention (ex: recherche de médecin), appelle la fonction appropriée qui interroge la base de données via l'ORM Django, puis formule une réponse contextualisée accompagnée d'**actions de redirection UI** (ex: "Voir le profil du Dr. DOSSOU").

#### Séquence 6 : Messagerie Patient ↔ Médecin
Ce diagramme montre l'échange de messages dans le cadre d'une consultation. Le système vérifie que la consultation n'est pas clôturée avant d'autoriser l'envoi. Chaque message déclenche une notification pour le destinataire. Une fois la consultation clôturée par le médecin, la messagerie est **automatiquement fermée** pour ce rendez-vous.

---

> **Note** : Pour générer les images des diagrammes, copiez le code PlantUML des fichiers `cas_utilisation.md`, `classe.md` ou `sequence.md` dans [PlantText.com](https://www.planttext.com/) ou un plugin VS Code comme "PlantUML".
