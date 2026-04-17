# Détails Frontend — Changements Backend E-Santé Bénin

## Date : 13 Avril 2026

Ce document répertorie les modifications backend et leur impact sur le frontend Flutter.

---

## ✅ Fonctionnalités Rétro-Compatibles (Aucune Modification Frontend Requise)

### 1. Correction de l'affichage des messages
- **Endpoint** : `GET /api/messages/?consultation={id}`
- **Changement** : Le serializer retourne désormais les champs complets (`expediteur_nom`, `destinataire_nom`, etc.) au lieu des champs de création uniquement.
- **Impact frontend** : **Aucun**. Le `MessageModel.fromJson()` existant parse déjà ces champs. Les messages s'afficheront correctement sans modification.

### 2. Correction de la liste des conversations
- **Endpoint** : `GET /api/conversations/`
- **Changement** : La logique interne a été réécrite pour compatibilité SQLite/PostgreSQL.
- **Impact frontend** : **Aucun**. La structure de réponse JSON est identique.
- **Nouveau champ** : `est_cloture` (boolean) ajouté à chaque conversation. Rétro-compatible.

### 3. Blocage du chat après clôture
- **Endpoint** : `POST /api/messages/`
- **Changement** : Le backend refuse désormais l'envoi de messages si `consultation.est_cloture == True` (erreur 400).
- **Impact frontend** : **Aucun requis** (le backend gère seul). **Recommandé** : utiliser le champ `est_cloture` de la conversation pour désactiver le champ de saisie côté UI.

### 4. Vérification temporelle pour terminer un RDV
- **Endpoint** : `POST /api/rendezvous/{id}/terminer/`
- **Changement** : Retourne une erreur 400 si `date_heure > now()`.
- **Impact frontend** : **Aucun**. Le message d'erreur sera affiché normalement.

### 5. Enrichissement du ConsultationSerializer
- **Endpoint** : `GET /api/consultations/`, `GET /api/consultations/{id}/`
- **Nouveaux champs** : `patient_nom`, `medecin_nom`, `date_rdv`, `motif`
- **Impact frontend** : **Aucun** (champs additionnels ignorés si non mappés).

### 6. Notification laborantin corrigée
- **Impact frontend** : **Aucun**. Correction purement backend.

---

## ⚠️ Fonctionnalités Nécessitant une Adaptation Frontend

### 1. Messages Vocaux (Nouvelle Feature)

#### Nouveaux Champs dans `MessageModel`
```json
{
  "id": 1,
  "consultation": 5,
  "expediteur": 12,
  "expediteur_nom": "Jean Dupont",
  "destinataire": 45,
  "destinataire_nom": "Dr. Kofi",
  "contenu": "",
  "type_message": "vocal",    // NOUVEAU : "texte" | "vocal" | "fichier"
  "audio": "/media/messages/audio/2026/04/voice_abc123.webm",  // NOUVEAU
  "piece_jointe": null,
  "date_envoi": "2026-04-13T12:00:00Z",
  "lu": false
}
```

#### Adaptations Requises

##### a) `MessageModel` (Dart)
Ajouter les champs `typeMessage` et `audio` :
```dart
class MessageModel {
  // ... champs existants
  final String typeMessage;  // "texte", "vocal", "fichier"
  final String? audio;       // URL du fichier audio

  factory MessageModel.fromJson(Map<String, dynamic> json) {
    return MessageModel(
      // ... champs existants
      typeMessage: json['type_message'] as String? ?? 'texte',
      audio: json['audio'] as String?,
    );
  }
}
```

##### b) `MessagerieRemoteDatasource`
Ajouter une méthode d'envoi de message vocal :
```dart
Future<MessageModel> sendVoiceMessage({
  int? consultationId,
  int? destinataireId,
  required File audioFile,
}) async {
  final formData = FormData.fromMap({
    if (consultationId != null) 'consultation': consultationId,
    if (destinataireId != null) 'destinataire': destinataireId,
    'type_message': 'vocal',
    'contenu': '🎙 Message vocal',
    'audio': await MultipartFile.fromFile(audioFile.path),
  });
  final response = await _client.upload(ApiConstants.messages, formData: formData);
  return MessageModel.fromJson(response.data);
}
```

##### c) `ChatScreen` (UI)
- Ajouter un bouton microphone à côté du bouton envoi
- Afficher un lecteur audio pour les messages de type `vocal`
- Utiliser un package comme `record` ou `flutter_sound` pour l'enregistrement

---

## 📋 Résumé des Endpoints

| Endpoint | Méthode | Changement | Frontend |
|---|---|---|---|
| `/api/conversations/` | GET | Réécrit + `est_cloture` | Aucun |
| `/api/messages/` | GET | Fix serializer | Aucun |
| `/api/messages/` | POST | Blocage clôture + vocal | Vocal = adaptation |
| `/api/rendezvous/{id}/terminer/` | POST | Vérif temporelle | Aucun |
| `/api/consultations/` | GET | +4 champs | Aucun |
| `/api/analyses/{id}/cloturer/` | POST | Fix notification | Aucun |
