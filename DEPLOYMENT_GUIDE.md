# 🚀 GUIDE DE DÉPLOIEMENT PRODUCTION

## ✅ **ALIGNEMENT TERMINÉ**

Le backend production est maintenant **strictement identique** au backend_local.

---

## 📋 **PROCÉDURE DE DÉPLOIEMENT**

### 1. **Pré-déploiement**
```bash
# 1. Commiter les modifications
git add .
git commit -m "Align backend production with backend_local - complete"
git push origin main

# 2. Render déploie automatiquement
```

### 2. **Post-déploiement sur Render**
```bash
# 1. Appliquer les migrations
python manage.py migrate

# 2. Nettoyer et créer les données
python fix_database.py

# 3. Vérifier l'API
curl https://backend-soutenance-1et0.onrender.com/api/token/
```

---

## 🔧 **CONFIGURATION VÉRIFIÉE**

### ✅ **Backend**
- **Endpoints** : Identiques au local
- **Logique** : Alignée avec backend_local
- **Authentification** : JWT configuré
- **Email** : SMTP Gmail actif
- **Base de données** : PostgreSQL Render

### ✅ **Frontend**
- **URLs** : Production configurées
- **Réseau** : Android/iOS autorisés
- **Endpoints** : Cohérents avec backend

---

## 🧪 **TESTS POST-DÉPLOIEMENT**

### 1. **Inscription Patient**
```bash
# Test API
curl -X POST https://backend-soutenance-1et0.onrender.com/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test.patient@example.com",
    "password": "Test123456!",
    "password_confirm": "Test123456!",
    "first_name": "Test",
    "last_name": "Patient",
    "telephone": "+229 99 00 00 00"
  }'
```

### 2. **Connexion**
```bash
curl -X POST https://backend-soutenance-1et0.onrender.com/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dr.koffi@chu-benin.bj",
    "password": "Medecin123456!"
  }'
```

### 3. **Reset Password**
```bash
curl -X POST https://backend-soutenance-1et0.onrender.com/api/accounts/request-password-reset/ \
  -H "Content-Type: application/json" \
  -d '{"email": "dr.koffi@chu-benin.bj"}'
```

---

## 👥 **COMPTES DE TEST DISPONIBLES**

### 🔴 **Médecins**
- `dr.koffi@chu-benin.bj` / `Medecin123456!`
- `dr.adjo@chu-benin.bj` / `Medecin123456!`
- `dr.sossa@cnhu-benin.bj` / `Medecin123456!`

### 🧪 **Laborantins**
- `labo1@chu-benin.bj` / `Labo123456!`
- `labo2@chu-benin.bj` / `Labo123456!`

### 👨‍💼 **Administrateurs**
- `admin.chu@chu-benin.bj` / `Admin123456!`
- `admin.general@esante-benin.bj` / `AdminGen123456!`

---

## 📱 **TESTS MOBILE**

### 1. **Build APK**
```bash
cd ../Frontend
flutter clean
flutter pub get
flutter build apk --release
```

### 2. **Installation et Tests**
- Installer l'APK
- Test inscription → Email reçu
- Test connexion → Accès dashboard
- Test rendez-vous → Fonctionnel

---

## 🔍 **DÉPANNAGE**

### **Erreurs communes**
1. **CORS** : Vérifier `CORS_ALLOWED_ORIGINS`
2. **Email** : Vérifier configuration SMTP
3. **Base de données** : Exécuter `fix_database.py`

### **Logs à vérifier**
- Dashboard Render (backend)
- Console mobile (frontend)

---

## 🎯 **RÉSULTAT FINAL**

✅ **Backend production** = **Backend_local**  
✅ **Fonctionnalités** identiques  
✅ **Email** opérationnel  
✅ **Base de données** propre  
✅ **Frontend** compatible  

---

**L'application est prête pour la production !** 🎉
