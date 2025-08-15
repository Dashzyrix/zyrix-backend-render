import os
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client

# Flask App initialisieren
app = Flask(__name__)
CORS(app)

# Supabase Konfiguration
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
JWT_SECRET = os.environ.get('JWT_SECRET', 'zyrix-jwt-secret-key-2024')

# Supabase Client initialisieren
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Supabase-Verbindung fehlgeschlagen: {e}")

# Hilfsfunktionen
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_jwt_token(user_id, email):
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

# API Routes
@app.route('/register', methods=['POST'])
def register():
    try:
        if not supabase:
            return jsonify({'error': 'Datenbankverbindung nicht verfügbar'}), 500
            
        data = request.get_json()
        
        # Validierung
        required_fields = ['full_name', 'email', 'password', 'strasse', 'plz', 'stadt', 'land']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} ist erforderlich'}), 400
        
        # E-Mail bereits registriert?
        existing_user = supabase.table('users').select('email').eq('email', data['email']).execute()
        if existing_user.data:
            return jsonify({'error': 'E-Mail-Adresse bereits registriert'}), 400
        
        # Passwort validieren
        if len(data['password']) < 8:
            return jsonify({'error': 'Passwort muss mindestens 8 Zeichen lang sein'}), 400
        
        # Benutzer erstellen
        user_data = {
            'full_name': data['full_name'],
            'email': data['email'],
            'password_hash': hash_password(data['password']),
            'strasse': data['strasse'],
            'plz': data['plz'],
            'stadt': data['stadt'],
            'land': data['land'],
            'firmenname': data.get('firmenname'),
            'ust_idnr': data.get('ust_idnr'),
            'tokens': 1200,
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('users').insert(user_data).execute()
        
        if result.data:
            user = result.data[0]
            token = generate_jwt_token(user['id'], user['email'])
            
            return jsonify({
                'message': 'Registrierung erfolgreich',
                'token': token,
                'user': {
                    'id': user['id'],
                    'full_name': user['full_name'],
                    'email': user['email'],
                    'tokens': user['tokens']
                }
            }), 201
        else:
            return jsonify({'error': 'Registrierung fehlgeschlagen'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server-Fehler: {str(e)}'}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        if not supabase:
            return jsonify({'error': 'Datenbankverbindung nicht verfügbar'}), 500
            
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'E-Mail und Passwort sind erforderlich'}), 400
        
        # Benutzer suchen
        user_result = supabase.table('users').select('*').eq('email', data['email']).execute()
        
        if not user_result.data:
            return jsonify({'error': 'Ungültige Anmeldedaten'}), 401
        
        user = user_result.data[0]
        
        # Passwort prüfen
        if hash_password(data['password']) != user['password_hash']:
            return jsonify({'error': 'Ungültige Anmeldedaten'}), 401
        
        # JWT-Token generieren
        token = generate_jwt_token(user['id'], user['email'])
        
        return jsonify({
            'message': 'Anmeldung erfolgreich',
            'token': token,
            'user': {
                'id': user['id'],
                'full_name': user['full_name'],
                'email': user['email'],
                'tokens': user['tokens']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server-Fehler: {str(e)}'}), 500

@app.route('/request-password-reset', methods=['POST'])
def request_password_reset():
    try:
        if not supabase:
            return jsonify({'error': 'Datenbankverbindung nicht verfügbar'}), 500
            
        data = request.get_json()
        
        if not data.get('email'):
            return jsonify({'error': 'E-Mail-Adresse ist erforderlich'}), 400
        
        # Benutzer suchen
        user_result = supabase.table('users').select('*').eq('email', data['email']).execute()
        
        if not user_result.data:
            return jsonify({'error': 'E-Mail-Adresse nicht gefunden'}), 404
        
        user = user_result.data[0]
        
        # Reset-Token generieren
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        # Reset-Token in Datenbank speichern
        supabase.table('password_resets').insert({
            'user_id': user['id'],
            'token': reset_token,
            'expires_at': expires_at.isoformat(),
            'used': False
        }).execute()
        
        reset_link = f"https://zyrix-backend-render.onrender.com/reset-password-page?token={reset_token}"
        
        return jsonify({
            'message': 'Reset-Link wurde gesendet',
            'reset_link': reset_link
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server-Fehler: {str(e)}'}), 500

@app.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        if not supabase:
            return jsonify({'error': 'Datenbankverbindung nicht verfügbar'}), 500
            
        data = request.get_json()
        
        if not data.get('token') or not data.get('new_password'):
            return jsonify({'error': 'Token und neues Passwort sind erforderlich'}), 400
        
        # Reset-Token prüfen
        reset_result = supabase.table('password_resets').select('*').eq('token', data['token']).eq('used', False).execute()
        
        if not reset_result.data:
            return jsonify({'error': 'Ungültiger oder abgelaufener Reset-Token'}), 400
        
        reset_record = reset_result.data[0]
        
        # Token-Ablauf prüfen
        expires_at = datetime.fromisoformat(reset_record['expires_at'].replace('Z', '+00:00'))
        if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
            return jsonify({'error': 'Reset-Token ist abgelaufen'}), 400
        
        # Neues Passwort validieren
        if len(data['new_password']) < 8:
            return jsonify({'error': 'Passwort muss mindestens 8 Zeichen lang sein'}), 400
        
        # Passwort aktualisieren
        new_password_hash = hash_password(data['new_password'])
        supabase.table('users').update({
            'password_hash': new_password_hash
        }).eq('id', reset_record['user_id']).execute()
        
        # Reset-Token als verwendet markieren
        supabase.table('password_resets').update({
            'used': True
        }).eq('id', reset_record['id']).execute()
        
        return jsonify({'message': 'Passwort erfolgreich geändert'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Server-Fehler: {str(e)}'}), 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.utcnow().isoformat(),
        'supabase_connected': supabase is not None
    })

# HTML-Templates als Strings
REGISTER_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registrierung - Zyrix</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            width: 100%;
            max-width: 500px;
            padding: 40px;
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo h1 {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-row {
            display: flex;
            gap: 15px;
        }
        .form-row .form-group {
            flex: 1;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #333;
        }
        input[type="text"], input[type="email"], input[type="password"], input[type="tel"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        input[type="text"]:focus, input[type="email"]:focus, input[type="password"]:focus, input[type="tel"]:focus {
            outline: none;
            border-color: #FF9900;
        }
        .checkbox-group {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        .checkbox-group input[type="checkbox"] {
            margin-right: 10px;
            transform: scale(1.2);
        }
        .submit-btn {
            width: 100%;
            background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%);
            color: white;
            padding: 15px;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        .submit-btn:hover {
            transform: translateY(-2px);
        }
        .submit-btn:disabled {
            opacity: 0.7;
            cursor: not-allowed;
            transform: none;
        }
        .company-fields {
            display: none;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .company-fields.show {
            display: block;
        }
        .error-message {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
        .success-message {
            background: #efe;
            color: #3c3;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
        .login-link {
            text-align: center;
            margin-top: 20px;
        }
        .login-link a {
            color: #FF9900;
            text-decoration: none;
            font-weight: 600;
        }
        .login-link a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>Zyrix</h1>
            <p>Registrierung</p>
        </div>

        <div id="error-message" class="error-message"></div>
        <div id="success-message" class="success-message"></div>

        <form id="registerForm">
            <div class="form-group">
                <label for="fullName">Vollständiger Name *</label>
                <input type="text" id="fullName" name="fullName" required>
            </div>

            <div class="form-group">
                <label for="email">E-Mail-Adresse *</label>
                <input type="email" id="email" name="email" required>
            </div>

            <div class="form-group">
                <label for="password">Passwort *</label>
                <input type="password" id="password" name="password" required minlength="8">
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="strasse">Straße *</label>
                    <input type="text" id="strasse" name="strasse" required>
                </div>
                <div class="form-group">
                    <label for="plz">PLZ *</label>
                    <input type="text" id="plz" name="plz" required>
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="stadt">Stadt *</label>
                    <input type="text" id="stadt" name="stadt" required>
                </div>
                <div class="form-group">
                    <label for="land">Land *</label>
                    <input type="text" id="land" name="land" value="Deutschland" required>
                </div>
            </div>

            <div class="checkbox-group">
                <input type="checkbox" id="isCompany" name="isCompany">
                <label for="isCompany">Ich registriere mich als Unternehmen</label>
            </div>

            <div id="companyFields" class="company-fields">
                <div class="form-group">
                    <label for="companyName">Firmenname</label>
                    <input type="text" id="companyName" name="companyName">
                </div>
                <div class="form-group">
                    <label for="vatId">USt-IdNr.</label>
                    <input type="text" id="vatId" name="vatId">
                </div>
            </div>

            <button type="submit" class="submit-btn" id="submitBtn">Registrieren</button>
        </form>

        <div class="login-link">
            <p>Bereits registriert? <a href="/login-page">Jetzt anmelden</a></p>
        </div>
    </div>

    <script>
        // Firmenfelder ein-/ausblenden
        document.getElementById('isCompany').addEventListener('change', function() {
            const companyFields = document.getElementById('companyFields');
            if (this.checked) {
                companyFields.classList.add('show');
            } else {
                companyFields.classList.remove('show');
            }
        });

        // Formular-Submission
        document.getElementById('registerForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const errorDiv = document.getElementById('error-message');
            const successDiv = document.getElementById('success-message');
            const submitBtn = document.getElementById('submitBtn');
            
            errorDiv.style.display = 'none';
            successDiv.style.display = 'none';
            submitBtn.disabled = true;
            submitBtn.textContent = 'Wird registriert...';

            const formData = new FormData(this);
            const data = {
                full_name: formData.get('fullName'),
                email: formData.get('email'),
                password: formData.get('password'),
                strasse: formData.get('strasse'),
                plz: formData.get('plz'),
                stadt: formData.get('stadt'),
                land: formData.get('land'),
                firmenname: formData.get('isCompany') ? formData.get('companyName') : null,
                ust_idnr: formData.get('isCompany') ? formData.get('vatId') : null
            };

            try {
                const response = await fetch('/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (response.ok) {
                    successDiv.textContent = 'Registrierung erfolgreich! Sie erhalten 1200 Test-Tokens.';
                    successDiv.style.display = 'block';
                    this.reset();
                    
                    setTimeout(() => {
                        window.location.href = '/login-page';
                    }, 2000);
                } else {
                    errorDiv.textContent = result.error || 'Registrierung fehlgeschlagen.';
                    errorDiv.style.display = 'block';
                }
            } catch (error) {
                errorDiv.textContent = 'Verbindungsfehler. Bitte versuchen Sie es erneut.';
                errorDiv.style.display = 'block';
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Registrieren';
            }
        });
    </script>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anmeldung - Zyrix</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            width: 100%;
            max-width: 400px;
            padding: 40px;
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo h1 {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #333;
        }
        input[type="email"], input[type="password"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        input[type="email"]:focus, input[type="password"]:focus {
            outline: none;
            border-color: #FF9900;
        }
        .submit-btn {
            width: 100%;
            background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%);
            color: white;
            padding: 15px;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        .submit-btn:hover {
            transform: translateY(-2px);
        }
        .submit-btn:disabled {
            opacity: 0.7;
            cursor: not-allowed;
            transform: none;
        }
        .forgot-password {
            text-align: center;
            margin-top: 15px;
        }
        .forgot-password a {
            color: #666;
            text-decoration: none;
            font-size: 14px;
        }
        .forgot-password a:hover {
            color: #FF9900;
            text-decoration: underline;
        }
        .register-link {
            text-align: center;
            margin-top: 20px;
        }
        .register-link a {
            color: #FF9900;
            text-decoration: none;
            font-weight: 600;
        }
        .register-link a:hover {
            text-decoration: underline;
        }
        .error-message {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
        .success-message {
            background: #efe;
            color: #3c3;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>Zyrix</h1>
            <p>Anmeldung</p>
        </div>

        <div id="error-message" class="error-message"></div>
        <div id="success-message" class="success-message"></div>

        <form id="loginForm">
            <div class="form-group">
                <label for="email">E-Mail-Adresse</label>
                <input type="email" id="email" name="email" required>
            </div>

            <div class="form-group">
                <label for="password">Passwort</label>
                <input type="password" id="password" name="password" required>
            </div>

            <button type="submit" class="submit-btn" id="submitBtn">Anmelden</button>
        </form>

        <div class="forgot-password">
            <a href="/forgot-password-page">Passwort vergessen?</a>
        </div>

        <div class="register-link">
            <p>Noch kein Account? <a href="/register-page">Jetzt registrieren</a></p>
        </div>
    </div>

    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const errorDiv = document.getElementById('error-message');
            const successDiv = document.getElementById('success-message');
            const submitBtn = document.getElementById('submitBtn');
            
            errorDiv.style.display = 'none';
            successDiv.style.display = 'none';
            submitBtn.disabled = true;
            submitBtn.textContent = 'Wird angemeldet...';

            const formData = new FormData(this);
            const data = {
                email: formData.get('email'),
                password: formData.get('password')
            };

            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (response.ok) {
                    localStorage.setItem('authToken', result.token);
                    localStorage.setItem('userLoggedIn', 'true');
                    localStorage.setItem('userData', JSON.stringify(result.user));
                    
                    successDiv.textContent = 'Anmeldung erfolgreich! Du wirst weitergeleitet...';
                    successDiv.style.display = 'block';
                    
                    setTimeout(() => {
                        window.location.href = 'https://www.zyrix.de/myzyrix';
                    }, 1500);
                } else {
                    errorDiv.textContent = result.error || 'Anmeldung fehlgeschlagen.';
                    errorDiv.style.display = 'block';
                }
            } catch (error) {
                errorDiv.textContent = 'Verbindungsfehler. Bitte versuchen Sie es erneut.';
                errorDiv.style.display = 'block';
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Anmelden';
            }
        });
    </script>
</body>
</html>
"""

FORGOT_PASSWORD_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Passwort vergessen - Zyrix</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            width: 100%;
            max-width: 400px;
            padding: 40px;
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo h1 {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .description {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            line-height: 1.6;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #333;
        }
        input[type="email"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        input[type="email"]:focus {
            outline: none;
            border-color: #FF9900;
        }
        .submit-btn {
            width: 100%;
            background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%);
            color: white;
            padding: 15px;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        .submit-btn:hover {
            transform: translateY(-2px);
        }
        .submit-btn:disabled {
            opacity: 0.7;
            cursor: not-allowed;
            transform: none;
        }
        .back-link {
            text-align: center;
            margin-top: 20px;
        }
        .back-link a {
            color: #FF9900;
            text-decoration: none;
            font-weight: 600;
        }
        .back-link a:hover {
            text-decoration: underline;
        }
        .error-message {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
        .success-message {
            background: #efe;
            color: #3c3;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>Zyrix</h1>
            <p>Passwort vergessen</p>
        </div>

        <div class="description">
            Geben Sie Ihre E-Mail-Adresse ein und wir senden Ihnen einen Link zum Zurücksetzen Ihres Passworts.
        </div>

        <div id="error-message" class="error-message"></div>
        <div id="success-message" class="success-message"></div>

        <form id="forgotPasswordForm">
            <div class="form-group">
                <label for="email">E-Mail-Adresse</label>
                <input type="email" id="email" name="email" required>
            </div>

            <button type="submit" class="submit-btn" id="submitBtn">Reset-Link senden</button>
        </form>

        <div class="back-link">
            <p><a href="/login-page">Zurück zur Anmeldung</a></p>
        </div>
    </div>

    <script>
        document.getElementById('forgotPasswordForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const errorDiv = document.getElementById('error-message');
            const successDiv = document.getElementById('success-message');
            const submitBtn = document.getElementById('submitBtn');
            
            errorDiv.style.display = 'none';
            successDiv.style.display = 'none';
            submitBtn.disabled = true;
            submitBtn.textContent = 'Wird gesendet...';

            const formData = new FormData(this);
            const email = formData.get('email');

            try {
                const response = await fetch('/request-password-reset', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email })
                });

                const result = await response.json();

                if (response.ok) {
                    successDiv.innerHTML = 'Reset-Link wurde gesendet! <br><a href="' + result.reset_link + '" target="_blank">Direkt öffnen</a>';
                    successDiv.style.display = 'block';
                    this.reset();
                } else {
                    errorDiv.textContent = result.error || 'Fehler beim Senden des Reset-Links.';
                    errorDiv.style.display = 'block';
                }
            } catch (error) {
                errorDiv.textContent = 'Verbindungsfehler. Bitte versuchen Sie es erneut.';
                errorDiv.style.display = 'block';
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Reset-Link senden';
            }
        });
    </script>
</body>
</html>
"""

RESET_PASSWORD_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Passwort zurücksetzen - Zyrix</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            width: 100%;
            max-width: 400px;
            padding: 40px;
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo h1 {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .description {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            line-height: 1.6;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #333;
        }
        input[type="password"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        input[type="password"]:focus {
            outline: none;
            border-color: #FF9900;
        }
        .submit-btn {
            width: 100%;
            background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%);
            color: white;
            padding: 15px;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        .submit-btn:hover {
            transform: translateY(-2px);
        }
        .submit-btn:disabled {
            opacity: 0.7;
            cursor: not-allowed;
            transform: none;
        }
        .back-link {
            text-align: center;
            margin-top: 20px;
        }
        .back-link a {
            color: #FF9900;
            text-decoration: none;
            font-weight: 600;
        }
        .back-link a:hover {
            text-decoration: underline;
        }
        .error-message {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
        .success-message {
            background: #efe;
            color: #3c3;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
        .password-requirements {
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>Zyrix</h1>
            <p>Neues Passwort setzen</p>
        </div>

        <div class="description">
            Geben Sie Ihr neues Passwort ein. Es muss mindestens 8 Zeichen lang sein.
        </div>

        <div id="error-message" class="error-message"></div>
        <div id="success-message" class="success-message"></div>

        <form id="resetPasswordForm">
            <div class="form-group">
                <label for="newPassword">Neues Passwort</label>
                <input type="password" id="newPassword" name="newPassword" required minlength="8">
                <div class="password-requirements">Mindestens 8 Zeichen</div>
            </div>

            <div class="form-group">
                <label for="confirmPassword">Passwort bestätigen</label>
                <input type="password" id="confirmPassword" name="confirmPassword" required minlength="8">
            </div>

            <button type="submit" class="submit-btn" id="submitBtn">Passwort ändern</button>
        </form>

        <div class="back-link">
            <p><a href="/login-page">Zurück zur Anmeldung</a></p>
        </div>
    </div>

    <script>
        // Token aus URL extrahieren
        const urlParams = new URLSearchParams(window.location.search);
        const resetToken = urlParams.get('token');

        if (!resetToken) {
            document.getElementById('error-message').textContent = 'Ungültiger Reset-Link. Bitte fordern Sie einen neuen an.';
            document.getElementById('error-message').style.display = 'block';
            document.getElementById('resetPasswordForm').style.display = 'none';
        }

        document.getElementById('resetPasswordForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const errorDiv = document.getElementById('error-message');
            const successDiv = document.getElementById('success-message');
            const submitBtn = document.getElementById('submitBtn');
            
            errorDiv.style.display = 'none';
            successDiv.style.display = 'none';

            const formData = new FormData(this);
            const newPassword = formData.get('newPassword');
            const confirmPassword = formData.get('confirmPassword');

            // Passwort-Bestätigung prüfen
            if (newPassword !== confirmPassword) {
                errorDiv.textContent = 'Die Passwörter stimmen nicht überein.';
                errorDiv.style.display = 'block';
                return;
            }

            submitBtn.disabled = true;
            submitBtn.textContent = 'Wird geändert...';

            try {
                const response = await fetch('/reset-password', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        token: resetToken,
                        new_password: newPassword 
                    })
                });

                const result = await response.json();

                if (response.ok) {
                    successDiv.textContent = 'Passwort erfolgreich geändert! Sie werden zur Anmeldung weitergeleitet.';
                    successDiv.style.display = 'block';
                    this.reset();
                    
                    setTimeout(() => {
                        window.location.href = '/login-page';
                    }, 2000);
                } else {
                    errorDiv.textContent = result.error || 'Fehler beim Ändern des Passworts.';
                    errorDiv.style.display = 'block';
                }
            } catch (error) {
                errorDiv.textContent = 'Verbindungsfehler. Bitte versuchen Sie es erneut.';
                errorDiv.style.display = 'block';
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Passwort ändern';
            }
        });
    </script>
</body>
</html>
"""

# HTML-Seiten Routes
@app.route('/register-page')
def register_page():
    return REGISTER_TEMPLATE

@app.route('/login-page')
def login_page():
    return LOGIN_TEMPLATE

@app.route('/forgot-password-page')
def forgot_password_page():
    return FORGOT_PASSWORD_TEMPLATE

@app.route('/reset-password-page')
def reset_password_page():
    return RESET_PASSWORD_TEMPLATE

# Hauptseite Route
@app.route('/')
def home():
    return jsonify({
        'message': 'Zyrix Backend API',
        'version': '3.0',
        'status': 'online',
        'platform': 'Render.com',
        'endpoints': ['/register', '/login', '/request-password-reset', '/reset-password']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
