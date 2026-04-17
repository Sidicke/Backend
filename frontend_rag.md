# Intégration Frontend : Agent Assistant Intelligent RAG

L'API de Chatbot Backend `POST /api/chatbot/message/` a été considérablement augmentée suite au passage à l'architecture RAG (Retrieval-Augmented Generation). 
L'Intelligence Artificielle est désormais capable d'interroger la base de données (hôpitaux, disponibilités médecins) en temps réel et de suggérer des actions de navigation (Deep Linking).

Ce document décrit comment l'interface Frontend (Flutter / App Web) doit s'adapter pour exploiter pleinenent ce nouveau système.

---

## 1. Comprendre la Mutation de l'Endpoint

Auparavant, la route retournait simplement le message textuel de l'IA. 
**Pour garantir une rétro-compatibilité stricte**, ce texte est toujours renvoyé intact sous la même arborescence (`message.content`). 
La nouveauté est l'apparition d'un array additionnel nommé `actions`.

### Nouveau Format de Réponse JSON
```json
{
  "message": {
    "role": "assistant",
    "content": "J'ai trouvé deux cardiologues disponibles à Cotonou. Souhaitez-vous planifier une consultation avec le Dr. Boco ou découvrir le CHU Mel ?",
    "timestamp": "2026-04-17T11:45:00Z"
  },
  "actions": [
    {
      "type": "redirect",
      "label": "Prendre RDV avec Dr. Boco",
      "url": "/medecins/45/rendezvous"
    },
    {
      "type": "redirect",
      "label": "Fiche du CHU Mel",
      "url": "/hopitaux/12"
    }
  ]
}
```

---

## 2. Adaptation de l'UI Chat (Recommandations)

L'UI du tchat devra être capable de capter cet array `actions`.

### Logique d'affichage
Si la clé `actions` est présente dans la réponse et n'est pas vide, le Frontend doit générer des boutons cliquables affichés en dessous du message textuel.

#### Conception UI Flutter (Exemple)

Lorsque l'application parcourt le payload de retour, elle peut builder un conteneur d'actions rapides (Quick Replies) :

```dart
// Réponse API simulée parsée dans un Map
final apiResponse = jsonDecode(response.body);
final String messageText = apiResponse['message']['content'];
final List<dynamic>? actions = apiResponse['actions'];

// Widget de Message
Column(
  crossAxisAlignment: CrossAxisAlignment.start,
  children: [
    // La bulle classique du chatbot
    ChatBubble(
      text: messageText,
      isSender: false,
    ),
    
    // Rendu dynamique des boutons si 'actions' existe
    if (actions != null && actions.isNotEmpty)
      Padding(
        padding: const EdgeInsets.only(top: 8.0),
        child: Wrap(
          spacing: 8.0,
          children: actions.map((action) {
            
            // Si c'est une redirection
            if (action['type'] == 'redirect') {
              return ElevatedButton.icon(
                icon: Icon(Icons.arrow_forward), // Icône indicative
                label: Text(action['label']),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Theme.of(context).primaryColor,
                  foregroundColor: Colors.white,
                ),
                onPressed: () {
                  // Navigation interne via les routes définies
                  Navigator.pushNamed(context, action['url']);
                },
              );
            }
            
            return SizedBox.shrink(); // Ignore les types inconnus
          }).toList(),
        ),
      )
  ],
)
```

---

## 3. Liste des "URL" Supportées pour la Redirection

Le système RAG tentera toujours de rediriger vers des ressources valides via les préfixes d'URL suivants. Vous devez vous assurer que le routeur ou le "DeepLink handler" frontend reconnait ces chemins :

- `/hopitaux` : Ouvre la vue Liste des Hôpitaux.
- `/hopitaux/{ID}` : Ouvre la fiche détaillée de l'Hôpital avec son ID.
- `/medecins/{ID}` : Ouvre la fiche détaillée d'un médecin.
- `/medecins/{ID}/rendezvous` : Ouvre l'écran direct de prise de rendez-vous pour ce praticien pré-sélectionné.
- `/rendezvous` : Ouvre l'onglet d'historique ou liste de rendez-vous du patient.

---

### Points de vigilance
- **Markdown** : Le champ `content` peut contenir du formattage Markdown basique (gras `**`, listes à puces `-`). Il est fortement recommandé d'utiliser une librairie comme `flutter_markdown` pour rendre le texte.
- **Fail-safe** : Le backend est programmé pour *toujours* renvoyer un champ `actions`, même vide (`[]`), lorsque l'IA juge qu'elle ne peut pas aider de façon automatisée. Gérez simplement la condition de vacuité côté UI.
