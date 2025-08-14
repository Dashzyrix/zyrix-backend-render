Zyrix Backend für Render

🚀 Deployment auf Render

Schritt 1: Repository erstellen

1.
Gehen Sie zu GitHub und erstellen Sie ein neues Repository: zyrix-backend-render

2.
Laden Sie alle Dateien aus diesem Ordner hoch

Schritt 2: Render verbinden

1.
Gehen Sie zu render.com

2.
Klicken Sie auf "New Web Service"

3.
Verbinden Sie Ihr GitHub-Repository zyrix-backend-render

4.
Konfiguration:

•
Name: zyrix-backend

•
Environment: Python 3

•
Build Command: pip install -r requirements.txt

•
Start Command: gunicorn app:app

•
Plan: Free (für Tests) oder Starter ($7/Monat für Production)



Schritt 3: Deploy

1.
Klicken Sie auf "Create Web Service"

2.
Warten Sie 5-10 Minuten auf das Deployment

3.
Ihre Backend-URL wird angezeigt (z.B. https://zyrix-backend.onrender.com)

🔧 API-Endpunkte

•
POST /register - Benutzerregistrierung

•
POST /login - Benutzeranmeldung

•
POST /request-password-reset - Passwort-Reset anfordern

•
POST /reset-password - Neues Passwort setzen

🔗 Frontend verbinden

Nach dem Deployment müssen Sie die Backend-URL in Ihren Frontend-Dateien anpassen:

JavaScript


// In register.html, login.html, etc.
const API_BASE_URL = 'https://zyrix-backend.onrender.com';


✅ Features

•
✅ Vollständige Supabase-Integration

•
✅ 1200 Test-Tokens für neue Benutzer

•
✅ Sichere Passwort-Hashing

•
✅ JWT-Token-Authentifizierung

•
✅ Passwort-Reset-Funktionalität

•
✅ CORS-Unterstützung

•
✅ Produktions-ready für 30.000+ Benutzer

