# Intégration Frontend : Patient Intake (Pré-consultation)

Notre plateforme vient d'être enrichie par un système de préenregistrement ("Patient Intake"). 
Ce document décrit comment l'interface Frontend doit interagir avec les endpoints pour permettre aux patients de soumettre leurs maux avant le jour du rendez-vous, tout en permettant au médecin de lire le dossier.

---

## 1. Vue d'Ensemble des API

Une nouvelle route imbriquée sur les rendez-vous a été déployée côté Backend :
👉 `GET /api/rendezvous/{id_rendezvous}/preenregistrement/`
👉 `POST /api/rendezvous/{id_rendezvous}/preenregistrement/`
👉 `PUT /api/rendezvous/{id_rendezvous}/preenregistrement/`

### Format du Payload (POST / PUT / GET)
```json
{
  "symptomes_principaux": "Maux de ventre et toux grasse",
  "debut_symptomes": "2026-04-25",
  "traitements_en_cours": "Sirop Hélicidine",
  "observations": "Je ressens aussi des vertiges.",
  "soumis_le": "2026-04-28T19:30:00Z",          // Uniquement en Lecture
  "mis_a_jour_le": "2026-04-28T19:30:00Z"      // Uniquement en Lecture
}
```

---

## 2. Parcours du Patient (Espace Patient)

Le Patient peut remplir ce formulaire **uniquement s'il est titulaire du RDV** et que ce dernier n'est ni terminé, ni refusé ni annulé.

### 📝 Algorithme suggéré (UI UI/UX) :

1. **Quand solliciter le patient ?**
   - Sur l'écran de détail du `RendezVous` (ex: `rendezvous_booking_screen.dart` ou historique), vérifiez la présence de l'objet ou permettez un CTA (Call To Action).
   - *Optionnel* : À la confirmation d'un RDV, afficher une pop-up *"Aidez votre médecin à préparer la consultation : Remplissez vos antécédents."* avec un bouton ignorer.

2. **Étape 1 : Vérifier l'existence**
   - Faire un `GET /api/rendezvous/{id}/preenregistrement/`.
   - Si l'API retourne HTTP `200 OK`, pré-remplissez le formulaire (mode Modification).
   - Si HTTP `404 Not Found`, affichez un formulaire vide (mode Création).

3. **Étape 2 : Envoyer les données**
   - Si Création, effectuez une requête `POST`.
   - Si Modification, effectuez une requête `PUT`.
   - ⚠️ Le backend renverra une erreur `400 Bad Request` si vous tentez un POST alors qu'une fiche existe déjà, ou un PUT si la fiche est inexistante. Gérer ces retours API correctement avec Dio/HTTP.
   - En cas de succès `201` ou `200`, afficher un message "Dossier transmis au médecin".

---

## 3. Accès du Médecin (Espace Praticien)

Le parcours médecin a été optimisé massivement. 
L'objet `pre_enregistrement` est **directement injecté en lecture seule** dans la liste globale des RDV du médecin. 
Aucune requête supplémentaire n'est nécessaire !

### Format dans la liste des RDV du médecin
`GET /api/rendezvous/`

```json
[
  {
    "id": 142,
    "patient_nom": "Talon Patrice",
    "medecin_nom": "Dr. Dossou",
    "date_heure": "2026-05-10T14:00:00Z",
    "statut": "confirme",
    "has_consultation": false,
    "pre_enregistrement": {
         "symptomes_principaux": "Maux de ventre et toux grasse",
         "debut_symptomes": "2026-04-25",
         "traitements_en_cours": "Sirop",
         "observations": "Vertiges au réveil."
    }
  }
]
```

### 🩺 Algorithme côté Médecin :

1. Sur l'écran `medecin_agenda_screen.dart` ou sur le détail (`rendezvous_detail`), vous avez directement accès à la clé `pre_enregistrement` dans l'objet RDV. 
2. Si `pre_enregistrement` n'est pas `null`, affichez une carte "Motif de Consultation / Symptômes" en haut du dossier patient (avant de commencer à écrire l'ordonnance).
3. **Important** : Le médecin ne peut faire **aucun PUT ou POST** sur cette route. Le diagnostic final va dans l'objet `Consultation`. 

---

## Conclusion
Le formulaire est 100% facultatif par nature. Ne rendez pas les écrans bloquants côté UX. L'effort doit être mis sur l'incitation douce (Gamification/Rappel).
