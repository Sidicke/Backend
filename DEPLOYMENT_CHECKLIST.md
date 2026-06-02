# 🚀 Checklist Déploiement Production

## ✅ Configuration Backend Complète

### 1. Variables d'environnement (.env)
- ✅ `SECRET_KEY` configuré
- ✅ `DJANGO_DEBUG=False` pour production
- ✅ `DATABASE_URL` PostgreSQL Render configuré
- ✅ Configuration Email SMTP Gmail
- ✅ `FRONTEND_URL` pointe vers frontend production
- ✅ `BACKEND_URL` pointe vers backend production
- ✅ `FRONTEND_CORS_ORIGIN` pour CORS

### 2. Settings Django
- ✅ `ALLOWED_HOSTS` inclut domaine Render
- ✅ `CORS_ALLOWED_ORIGINS` inclut frontend production
- ✅ `CORS_ALLOW_ALL_ORIGINS` basé sur DEBUG
- ✅ Base de données via `dj_database_url`
- ✅ Email SMTP configuré

### 3. Sécurité
- ✅ DEBUG=False en production
- ✅ Hosts autorisés configurés
- ✅ CORS restreint aux origines connues

## 🔧 Actions Requises

### Avant déploiement
1. **Vérifier le .env** :
   ```bash
   # Base de données
   DATABASE_URL=postgresql://user:pass@host:port/dbname
   
   # URLs production
   FRONTEND_URL=https://frontend-soutenance-1et0.onrender.com
   BACKEND_URL=https://backend-soutenance-1et0.onrender.com
   
   # Email
   EMAIL_HOST=smtp.gmail.com
   EMAIL_HOST_USER=votre-email@gmail.com
   EMAIL_HOST_PASSWORD=votre-app-password
   ```

2. **Appliquer les migrations** :
   ```bash
   python manage.py migrate
   ```

3. **Exécuter le seed** :
   ```bash
   python fix_database.py
   ```

4. **Créer superadmin** (optionnel) :
   ```bash
   python manage.py createsuperuser
   ```

### Après déploiement
1. **Tester l'API** :
   ```bash
   curl https://backend-soutenance-1et0.onrender.com/api/token/
   ```

2. **Tester l'inscription** :
   - Via frontend mobile
   - Vérifier réception email

3. **Vérifier les logs** :
   - Dashboard Render
   - Erreurs éventuelles

## 📱 Configuration Mobile

### Android
- ✅ `android:usesCleartextTraffic="true"` dans AndroidManifest.xml
- ✅ URL production dans .env mobile

### iOS
- ✅ `NSAppTransportSecurity` configuré dans Info.plist
- ✅ `NSAllowsArbitraryLoads=true`

## 🌐 Réseau

### URLs Production
- **Backend** : https://backend-soutenance-1et0.onrender.com
- **Frontend** : https://frontend-soutenance-1et0.onrender.com

### Endpoints
- **Auth** : `/api/token/`
- **Inscription** : `/api/accounts/register/`
- **Profil** : `/api/accounts/users/me/`

## 📊 Tests Post-Déploiement

### 1. Inscription
- [ ] Créer un compte patient
- [ ] Recevoir email de vérification
- [ ] Se connecter avec le compte

### 2. Connexion
- [ ] Login avec médecin existant
- [ ] Accès dashboard selon rôle
- [ ] Token JWT fonctionnel

### 3. Fonctionnalités
- [ ] Prise de rendez-vous
- [ ] Messagerie (WebSocket)
- [ ] Notifications

### 4. Email
- [ ] Email inscription reçu
- [ ] Email reset mot de passe
- [ ] Vérification spam

## 🚨 Dépannage

### Erreurs communes
1. **CORS** : Vérifier `CORS_ALLOWED_ORIGINS`
2. **Base de données** : Vérifier `DATABASE_URL`
3. **Email** : Vérifier configuration SMTP
4. **Host** : Vérifier `ALLOWED_HOSTS`

### Logs à vérifier
- Logs Render (backend)
- Console mobile (frontend)
- Network requests (Dio)

---

## ✅ Déploiement Prêt

La configuration production est maintenant complète et prête pour le déploiement sur Render !
