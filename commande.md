# Commandes Git Utilisées pour Résoudre les Conflits et Sécuriser le Dépôt

Voici la liste des commandes utilisées lors des dernières étapes, ainsi que leur rôle, leur description et le moment opportun pour les utiliser.

## 1. `git pull origin main --rebase`
- **Rôle** : Synchroniser le travail local avec le serveur distant (GitHub) proprement.
- **Description** : Cette commande télécharge les modifications de la branche `main` distante et rejoue tes validations locales par-dessus. Cela évite de créer des "commits de fusion" (merge commits) inutiles, gardant ainsi l'historique linéaire et propre.
- **Quand l'utiliser** : Avant de pousser ton code, si quelqu'un d'autre (ou toi via l'interface GitHub) a apporté des modifications en ligne (ex: création d'un README).

## 2. `git rebase --abort`
- **Rôle** : Annuler une opération de rebase en cours.
- **Description** : Permet de stopper immédiatement le rebase et de revenir à l'état exact où se trouvait le dépôt avant le lancement du rebase. 
- **Quand l'utiliser** : Quand tu effectues un `git pull --rebase` et que tu fais face à un trop grand nombre de conflits complexes. Cela te permet d'annuler sans rien casser et de réfléchir à une autre approche (comme utiliser `--theirs` ou créer un nouveau commit par-dessus le distant).

## 3. `git rm --cached <nom_du_fichier>` (ex: `git rm --cached .env`)
- **Rôle** : Arrêter de suivre un fichier sans le supprimer du disque.
- **Description** : Retire le fichier de l'index de Git (le cache). Le fichier reste physiquement présent dans ton dossier de travail local, mais Git arrêtera de surveiller ses modifications ou de l'envoyer sur le serveur.
- **Quand l'utiliser** : Lorsque tu as accidentellement ajouté ou validé (commité) un fichier sensible contenant des mots de passe, comme un fichier `.env`, et que tu souhaites qu'il reste sur ta machine tout en disparaissant du dépôt Git. *(Toujours s'assurer d'avoir ajouté le fichier au `.gitignore` au préalable).*

## 4. `git commit --amend --no-edit`
- **Rôle** : Modifier le dernier commit sans changer son message obligatoire.
- **Description** : Modifie le commit le plus récent (la pointe de la branche) pour y intégrer de nouveaux changements, comme des suppressions de fichiers sensibles issues du `git rm --cached`. `--no-edit` empêche Git d'ouvrir l'éditeur de texte pour modifier le message de validation.
- **Quand l'utiliser** : Quand tu viens tout juste de faire un commit et que tu te rends compte que tu as oublié un fichier, ou, comme dans notre cas, que tu as laissé fuiter une clé d'API. Tu corriges le fichier, l'ajoutes avec `git add`, puis tu lances cette commande pour écraser l'ancien commit défectueux.

## 5. `git push origin HEAD:main --force`
- **Rôle** : Forcer l'envoi de l'historique local vers GitHub.
- **Description** : Oblige GitHub à accepter ton historique de commits local et à écraser l'historique présent sur le serveur (branche `main`). Le mot clé `--force` contourne les protections standards de refus de poussée si les historiques local et distant divergent.
- **Quand l'utiliser** : **UNIQUEMENT** après avoir modifié l'historique (comme avec un `git rebase` ou `git commit --amend`). Puisque nous avions supprimé des secrets du dernier commit (ce qui a recréé l'ID du commit), la version de GitHub et la tienne n'étaient plus "alignées". Il a fallu forcer GitHub à accepter cette nouvelle version "nettoyée". À utiliser avec d'extrêmes précautions si tu travailles en équipe.

## 6. `git add .`
- **Rôle** : Préparer tous les fichiers modifiés.
- **Description** : Ajoute au "Staging Area" (index) tous les fichiers nouveaux, modifiés, ou supprimés (sauf ceux inscrits dans `.gitignore`), les préparant ainsi pour le prochain `git commit`. 
- **Quand l'utiliser** : Lorsque tu as terminé de modifier plusieurs fichiers pour une fonctionnalité ou pour la résolution d'un conflit et que tu souhaites valider le tout (ex: après avoir ajusté `settings.py` et `.gitignore`).
