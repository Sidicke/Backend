# Diagrammes de Séquence — E-Santé Bénin

> Copiez chaque bloc PlantUML ci-dessous dans [PlantText](https://www.planttext.com/) ou tout éditeur PlantUML pour générer les diagrammes.

---

## 1. Inscription d'un Patient (avec Transaction Atomique)

```plantuml
@startuml Sequence_Inscription_Patient

skinparam shadowing false
skinparam backgroundColor #FEFEFE
skinparam defaultFontName Inter
skinparam sequenceArrowThickness 2
skinparam sequenceParticipantBorderColor #343A40

actor "Patient" as P #228B22
participant "App Mobile\n(Flutter)" as APP #87CEEB
participant "API REST\n(Django)" as API #FFD700
database "PostgreSQL" as DB #FF6347
participant "Serveur SMTP\n(Gmail)" as SMTP #DC143C

P -> APP : Remplit le formulaire\nd'inscription
APP -> API : POST /api/accounts/register/\n{email, password, nom, tel...}
activate API

API -> API : Validation du serializer\n(email unique, mdp conforme,\ntéléphone béninois)

alt Email déjà utilisé (compte non vérifié)
  API -> DB : Suppression du compte\n"fantôme" existant
end

API -> DB : BEGIN TRANSACTION
activate DB
API -> DB : Créer User (is_active=False)
API -> DB : Créer Patient (profil)
DB --> API : OK
deactivate DB

API -> API : Générer un token\nde vérification (24h)

API -> SMTP : Envoyer email de vérification
activate SMTP

alt Succès envoi email
  SMTP --> API : Email envoyé
  deactivate SMTP
  API -> DB : COMMIT TRANSACTION
  API --> APP : 201 Created\n"Vérifiez votre boîte email"
  APP --> P : Message de confirmation
else Échec envoi (coupure réseau)
  SMTP --> API : Timeout / Erreur
  API -> DB : ROLLBACK TRANSACTION
  note right of DB : Aucun compte\ncréé en base !
  API --> APP : 400 Bad Request\n"Erreur réseau, réessayez"
  APP --> P : Message d'erreur
end

deactivate API

@enduml
```

---

## 2. Prise de Rendez-vous

```plantuml
@startuml Sequence_Prise_RDV

skinparam shadowing false
skinparam backgroundColor #FEFEFE
skinparam defaultFontName Inter
skinparam sequenceArrowThickness 2

actor "Patient" as P #228B22
participant "App Mobile\n(Flutter)" as APP #87CEEB
participant "API REST\n(Django)" as API #FFD700
database "PostgreSQL" as DB #FF6347
participant "Notifications" as NOTIF #9932CC

P -> APP : Sélectionne un médecin\net un créneau
APP -> API : POST /api/rendezvous/\n{medecin_id, date_heure, motif}
activate API

API -> API : Vérifier le token JWT\n(authentification)

API -> DB : Vérifier les disponibilités\ndu médecin
activate DB
DB --> API : Créneaux disponibles
deactivate DB

alt Créneau disponible
  API -> DB : Créer RendezVous\n(statut = "en_attente", durée = 30 min)
  activate DB
  DB --> API : RDV créé (id=X)
  deactivate DB

  API -> NOTIF : Créer notification\npour le médecin\n(type: "nouveau_rdv")
  NOTIF --> API : OK

  API --> APP : 201 Created\n{id, date_heure, statut}
  APP --> P : "RDV enregistré !\nEn attente de confirmation"
else Créneau indisponible
  API --> APP : 400 Bad Request\n"Créneau non disponible"
  APP --> P : Message d'erreur
end

deactivate API

@enduml
```

---

## 3. Flux de Consultation Complet (Médecin)

```plantuml
@startuml Sequence_Consultation

skinparam shadowing false
skinparam backgroundColor #FEFEFE
skinparam defaultFontName Inter
skinparam sequenceArrowThickness 2

actor "Médecin" as M #1E90FF
participant "Dashboard\nAdmin (Web)" as WEB #87CEEB
participant "API REST\n(Django)" as API #FFD700
database "PostgreSQL" as DB #FF6347
participant "Notifications" as NOTIF #9932CC
actor "Patient" as P #228B22

== Confirmation du RDV ==
M -> WEB : Confirme le rendez-vous
WEB -> API : PATCH /api/rendezvous/{id}/\n{statut: "confirme"}
API -> DB : Mettre à jour statut
API -> NOTIF : Notification patient\n(type: "rdv_confirme")
NOTIF --> P : "Votre RDV est confirmé"
API --> WEB : 200 OK

== Jour J : Terminer le RDV ==
M -> WEB : Termine le rendez-vous
WEB -> API : POST /api/rendezvous/{id}/terminer/
API -> API : Vérifier que la date\ndu RDV est passée
API -> DB : Statut = "termine"
API -> DB : Créer Consultation\n(vide, liée au RDV)
API --> WEB : 200 OK

== Rédaction de la Consultation ==
M -> WEB : Rédige le diagnostic\net la prescription
WEB -> API : PATCH /api/consultations/{id}/\n{diagnostic, prescription,\ncompte_rendu}
API -> DB : Mettre à jour Consultation
API -> NOTIF : Notification patient\n(type: "consultation_ajoutee")
API --> WEB : 200 OK

== Clôture de la Consultation ==
M -> WEB : Clôture la consultation
WEB -> API : POST /api/consultations/{id}/cloturer/
API -> DB : est_cloture = True\ndate_cloture = now()
note right of DB : La messagerie est\ndésormais fermée\npour ce RDV
API --> WEB : 200 OK

@enduml
```

---

## 4. Flux Laboratoire (Analyse → Résultat)

```plantuml
@startuml Sequence_Laboratoire

skinparam shadowing false
skinparam backgroundColor #FEFEFE
skinparam defaultFontName Inter
skinparam sequenceArrowThickness 2

actor "Laborantin" as L #FF8C00
participant "Dashboard\nLaborantin" as DASH #87CEEB
participant "API REST\n(Django)" as API #FFD700
database "PostgreSQL" as DB #FF6347
participant "Notifications" as NOTIF #9932CC
actor "Patient" as P #228B22

== Inscription d'une demande d'analyse ==
L -> DASH : Inscrit une nouvelle\ndemande d'analyse
DASH -> API : POST /api/demandes-analyse/\n{patient, type_analyse,\nhopital}
activate API
API -> DB : Créer DemandeAnalyse\n(statut = "en_cours")
DB --> API : OK
API --> DASH : 201 Created
deactivate API

== Clôture avec résultat ==
L -> DASH : Saisit les résultats\net le fichier PDF
DASH -> API : POST /api/demandes-analyse/{id}/cloturer/\n{titre, fichier, date_analyse}
activate API

API -> DB : Créer Resultat\n(code_acces auto-généré:\n"CNHU-202605-A3F9K1")
activate DB
DB --> API : Resultat créé
deactivate DB

API -> DB : Mettre à jour DemandeAnalyse\n(statut = "cloture",\nresultat = Resultat.id)

API -> NOTIF : Notification patient\n(type: "nouveau_resultat")
activate NOTIF
NOTIF --> P : "Vos résultats sont\ndisponibles (code: CNHU-...)"
deactivate NOTIF

API --> DASH : 200 OK\n{resultat, code_acces}
deactivate API

== Consultation du résultat par le patient ==
P -> API : GET /api/resultats/code/{code_acces}/
API -> DB : Rechercher par code_acces
DB --> API : Résultat trouvé
API --> P : 200 OK\n{titre, fichier_pdf, date}

@enduml
```

---

## 5. Interaction avec l'Assistant IA (Chatbot RAG)

```plantuml
@startuml Sequence_Chatbot_IA

skinparam shadowing false
skinparam backgroundColor #FEFEFE
skinparam defaultFontName Inter
skinparam sequenceArrowThickness 2

actor "Patient" as P #228B22
participant "App Mobile\n(Flutter)" as APP #87CEEB
participant "API REST\n(Django)" as API #FFD700
database "PostgreSQL" as DB #FF6347
participant "API Groq\n(LLM)" as GROQ #708090

P -> APP : "Je cherche un\ncardiologue au CNHU"
APP -> API : POST /api/chatbot/message/\n{message: "..."}
activate API

API -> DB : Sauvegarder message\nutilisateur (ChatMessage)
API -> DB : Charger historique\n(20 derniers messages)

API -> GROQ : Appel chat/completions\n+ TOOLS_SCHEMA\n(Function Calling)
activate GROQ

GROQ -> GROQ : Détection d'intention :\n"search_doctors"
GROQ --> API : tool_call:\nsearch_doctors_rag\n(specialite="cardio",\nhopital="CNHU")
deactivate GROQ

API -> DB : ORM Django :\nMedecin.filter(\nservices__nom__icontains=\n"cardio",\nuser__hopital__nom__icontains=\n"CNHU")
activate DB
DB --> API : [Dr. DOSSOU, Dr. TOSSOU]
deactivate DB

API -> GROQ : Réponse outil :\n{médecins trouvés}
activate GROQ
GROQ --> API : Réponse finale :\n"Au CNHU, vous pouvez\nconsulter le Dr. DOSSOU\n(Cardiologue)..."\n+ bloc JSON actions
deactivate GROQ

API -> API : extract_actions_and_clean_message()\n→ séparer texte + actions UI

API -> DB : Sauvegarder réponse IA\n(ChatMessage, role="assistant")

API --> APP : 200 OK\n{\n  "message": {contenu nettoyé},\n  "actions": [\n    {type: "navigate",\n     screen: "doctor_detail",\n     params: {id: 51}}\n  ]\n}
deactivate API

APP --> P : Affiche la réponse IA\n+ bouton "Voir le profil\ndu Dr. DOSSOU"

@enduml
```

---

## 6. Messagerie Patient ↔ Médecin

```plantuml
@startuml Sequence_Messagerie

skinparam shadowing false
skinparam backgroundColor #FEFEFE
skinparam defaultFontName Inter
skinparam sequenceArrowThickness 2

actor "Patient" as P #228B22
participant "App Mobile\n(Flutter)" as APP #87CEEB
participant "API REST\n(Django)" as API #FFD700
database "PostgreSQL" as DB #FF6347
participant "Notifications" as NOTIF #9932CC
actor "Médecin" as M #1E90FF

P -> APP : Rédige un message
APP -> API : POST /api/messages/\n{destinataire, contenu,\nconsultation_id}
activate API

API -> DB : Vérifier que la\nconsultation n'est\npas clôturée

alt Consultation ouverte
  API -> DB : Créer Message\n(type: texte, lu: false)
  API -> NOTIF : Notification médecin\n(type: "nouveau_message")
  NOTIF --> M : "Nouveau message\nde votre patient"
  API --> APP : 201 Created
  APP --> P : Message envoyé ✓
else Consultation clôturée
  API --> APP : 403 Forbidden\n"La consultation\nest clôturée"
  APP --> P : Erreur affichée
end

deactivate API

== Réponse du médecin ==
M -> API : POST /api/messages/\n{destinataire: patient,\ncontenu, consultation_id}
API -> DB : Créer Message
API -> NOTIF : Notification patient
API --> M : 201 Created

@enduml
```
