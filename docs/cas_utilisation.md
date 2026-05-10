# Diagrammes de Cas d'Utilisation — HOPITEL

> **Tutoriel Draw.io pour avoir les "Bonhommes" UML** :
> Mermaid ne permet pas de faire des bonhommes classiques. Pour avoir un vrai diagramme pro (épuré, avec le vrai bonhomme bâton), il faut utiliser le format standard UML.
> 1. Crée un fichier `global.drawio` et ouvre-le.
> 2. Dans Draw.io, clique sur le **petit "+"** > **Advanced** > **PlantUML**.
> 3. Colle un bloc de code ci-dessous et valide. Tu auras ton diagramme pro avec les bonhommes !

---

## 1. Diagramme Global et Complet du Système

```plantuml
@startuml
left to right direction
skinparam shadowing false
skinparam monochrome true
skinparam nodesep 60
skinparam ranksep 80
skinparam packageStyle rectangle

' Acteurs principaux et secondaires
actor "Patient" as P
actor "Médecin" as M
actor "Laborantin" as L
actor "Admin Hôpital" as AH
actor "Admin Général" as AG
actor "Assistant IA" as IA

rectangle "Plateforme HOPITEL - HOPITEL" {

  package "Accueil & Compte" {
    usecase "Gérer son profil\n(Inscription, Auth)" as UC_AUTH
  }

  package "Parcours de Soins" {
    usecase "Rechercher Hôpital / Médecin\n(Filtres par ville, spécialité)" as UC_SEARCH
    usecase "Gérer les rendez-vous" as UC_RDV
    usecase "Remplir le\npré-enregistrement" as UC_INTAKE
  }

  package "Intelligence Artificielle" {
    usecase "Discuter avec l'IA\n(Conseils & RAG)" as UC_IA
  }

  package "Dossier & Consultation" {
    usecase "Réaliser la consultation\n(Diagnostic, Prescription)" as UC_CONSULT
    usecase "Échanger sur la\nmessagerie sécurisée" as UC_MSG
  }

  package "Pôle Laboratoire" {
    usecase "Traiter les demandes\nd'analyses" as UC_LAB
    usecase "Publier les résultats\navec code d'accès" as UC_RESULT
  }

  package "Pôle Administration" {
    usecase "Superviser le personnel\net l'hôpital" as UC_ADMIN_H
    usecase "Superviser la plateforme\net les données globales" as UC_ADMIN_G
  }

}

' --------- RELATIONS PATIENT ---------
P -- UC_AUTH
P -- UC_SEARCH
P -- UC_RDV
P -- UC_IA
P -- UC_MSG
P -- UC_RESULT

' --------- RELATIONS MÉDECIN ---------
M -- UC_AUTH
M -- UC_RDV
M -- UC_CONSULT
M -- UC_MSG

' --------- RELATIONS LABORANTIN ---------
L -- UC_AUTH
L -- UC_LAB

' --------- RELATIONS ADMINS ---------
AH -- UC_AUTH
AH -- UC_ADMIN_H

AG -- UC_AUTH
AG -- UC_ADMIN_G

' --------- RELATIONS IA ---------
IA -- UC_IA
IA -- UC_SEARCH

' --------- DEPENDANCES ---------
UC_RDV .> UC_INTAKE : <<extend>>
UC_CONSULT .> UC_MSG : <<extend>>
UC_LAB .> UC_RESULT : <<include>>

@enduml
```

---

## 2. Patient

```plantuml
@startuml
left to right direction
skinparam shadowing false
skinparam monochrome true
skinparam packageStyle rectangle

actor "Patient" as P

rectangle "HOPITEL — Espace Patient" {
  usecase "S'inscrire par email" as UC1
  usecase "Vérification de l'email" as UC_VERIF
  usecase "Se connecter" as UC2
  usecase "Modifier / Réinitialiser profil" as UC3
  
  usecase "Rechercher un hôpital ou médecin" as UC4
  
  usecase "Prendre un rendez-vous" as UC5
  usecase "Remplir le pré-enregistrement" as UC_INTAKE
  usecase "Gérer ses rendez-vous" as UC6
  
  usecase "Consulter ses résultats d'analyses" as UC7
  usecase "Partager un résultat avec médecin" as UC_SHARE
  
  usecase "Discuter avec son médecin" as UC8
  
  usecase "Poser une question à l'IA" as UC9
  usecase "Être orienté vers un médecin via IA" as UC_ORIENT
  
  usecase "Recevoir des notifications" as UC10
}

P -- UC1
P -- UC2
P -- UC3
P -- UC4
P -- UC5
P -- UC6
P -- UC7
P -- UC8
P -- UC9
P -- UC10

UC1 .> UC_VERIF : <<include>>
UC5 .> UC10 : <<include>>
UC8 .> UC10 : <<include>>

UC5 .> UC_INTAKE : <<extend>>
UC7 .> UC_SHARE : <<extend>>
UC9 .> UC_ORIENT : <<extend>>
@enduml
```

---

## 3. Médecin

```plantuml
@startuml
left to right direction
skinparam shadowing false
skinparam monochrome true
skinparam packageStyle rectangle

actor "Médecin" as M

rectangle "HOPITEL — Espace Médecin" {
  usecase "Gérer ses disponibilités" as UC1
  usecase "Déclarer une indisponibilité" as UC_INDISPO
  usecase "Consulter son agenda" as UC2
  
  usecase "Confirmer un rendez-vous" as UC3
  usecase "Refuser un rendez-vous" as UC4
  usecase "Terminer un rendez-vous" as UC5
  
  usecase "Consulter le pré-enregistrement" as UC6
  usecase "Rédiger diagnostic et prescription" as UC_DIAG
  usecase "Clôturer la consultation" as UC7
  usecase "Fermer la messagerie" as UC_CLOSE
  
  usecase "Discuter avec le patient" as UC8
  usecase "Consulter historique patient" as UC9
  usecase "Recevoir des notifications" as UC10
}

M -- UC1
M -- UC2
M -- UC3
M -- UC4
M -- UC5
M -- UC6
M -- UC7
M -- UC8
M -- UC9
M -- UC10

UC5 .> UC_DIAG : <<include>>
UC3 .> UC10 : <<include>>
UC4 .> UC10 : <<include>>
UC7 .> UC_CLOSE : <<include>>

UC1 .> UC_INDISPO : <<extend>>
@enduml
```

---

## 4. Laborantin

```plantuml
@startuml
left to right direction
skinparam shadowing false
skinparam monochrome true
skinparam packageStyle rectangle

actor "Laborantin" as L

rectangle "HOPITEL — Espace Laboratoire" {
  usecase "Consulter les patients envoyés" as UC1
  usecase "Rechercher un patient" as UC2
  
  usecase "Inscrire une demande d'analyse" as UC3
  usecase "Renseigner infos du patient" as UC_INFO
  
  usecase "Saisir résultats et uploader PDF" as UC4
  usecase "Clôturer l'analyse" as UC5
  
  usecase "Générer code d'accès" as UC_CODE
  usecase "Notifier le patient" as UC_NOTIF
}

L -- UC1
L -- UC2
L -- UC3
L -- UC4
L -- UC5

UC3 .> UC_INFO : <<include>>
UC5 .> UC_CODE : <<include>>
UC5 .> UC_NOTIF : <<include>>

UC1 .> UC2 : <<extend>>
@enduml
```

---

## 5. Admin Hôpital

```plantuml
@startuml
left to right direction
skinparam shadowing false
skinparam monochrome true
skinparam packageStyle rectangle

actor "Admin Hôpital" as AH

rectangle "HOPITEL — Administration Hospitalière" {
  usecase "Créer compte médecin" as UC1
  usecase "Créer compte laborantin" as UC2
  usecase "Importer médecins par CSV" as UC3
  usecase "Activer/Désactiver un membre" as UC4
  usecase "Envoyer email avec mot de passe" as UC_EMAIL
  
  usecase "Gérer les services de l'hôpital" as UC5
  usecase "Demander l'ajout d'un service" as UC6
  
  usecase "Consulter les statistiques" as UC7
  usecase "Superviser l'activité du personnel" as UC8
  usecase "Recevoir des notifications" as UC9
}

AH -- UC1
AH -- UC2
AH -- UC3
AH -- UC4
AH -- UC5
AH -- UC6
AH -- UC7
AH -- UC8
AH -- UC9

UC1 .> UC_EMAIL : <<include>>
UC2 .> UC_EMAIL : <<include>>
UC6 .> UC9 : <<include>>

UC5 .> UC6 : <<extend>>
UC1 .> UC3 : <<extend>>
@enduml
```

---

## 6. Admin Général

```plantuml
@startuml
left to right direction
skinparam shadowing false
skinparam monochrome true
skinparam packageStyle rectangle

actor "Admin Général" as AG

rectangle "HOPITEL — Super Administration" {
  usecase "Créer un hôpital" as UC1
  usecase "Modifier/Désactiver un hôpital" as UC2
  
  usecase "Nommer un admin hôpital" as UC3
  usecase "Envoyer email création compte" as UC_EMAIL
  
  usecase "Gérer tous les professionnels" as UC4
  usecase "Gérer tous les patients" as UC5
  
  usecase "Créer service médical global" as UC6
  usecase "Valider/Refuser demande de service" as UC7
  
  usecase "Consulter tableau de bord global" as UC8
  usecase "Recevoir des notifications" as UC9
}

AG -- UC1
AG -- UC2
AG -- UC3
AG -- UC4
AG -- UC5
AG -- UC6
AG -- UC7
AG -- UC8
AG -- UC9

UC3 .> UC_EMAIL : <<include>>
UC7 .> UC9 : <<include>>

UC1 .> UC2 : <<extend>>
@enduml
```

---

## 7. Assistant IA

```plantuml
@startuml
left to right direction
skinparam shadowing false
skinparam monochrome true
skinparam packageStyle rectangle

actor "Patient" as P
actor "Assistant IA" as IA

rectangle "HOPITEL — Assistant Intelligent" {
  usecase "Poser une question de santé" as UC1
  
  usecase "Recevoir un conseil médical" as UC2
  usecase "Rappel légal : consultez un médecin" as UC3
  
  usecase "Rechercher hôpitaux (Base de données)" as UC4
  usecase "Rechercher médecins (Base de données)" as UC5
  usecase "Vérifier les disponibilités" as UC6
  
  usecase "Proposer redirection vers médecin ou RDV" as UC7
}

P -- UC1

UC1 -- IA
UC4 -- IA
UC5 -- IA
UC6 -- IA

UC1 .> UC2 : <<include>>
UC2 .> UC3 : <<include>>
UC4 .> UC7 : <<include>>
UC5 .> UC7 : <<include>>

UC1 .> UC4 : <<extend>>
UC1 .> UC5 : <<extend>>
UC1 .> UC6 : <<extend>>
@enduml
```
