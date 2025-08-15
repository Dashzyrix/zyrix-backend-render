import os
import secrets
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
from supabase import create_client, Client

app = Flask(__name__)
CORS(app)

# Konfiguration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# E-Mail Konfiguration - Checkdomain SMTP
SMTP_SERVER = "host285.checkdomain.de"
SMTP_PORT = 465
EMAIL_USER = os.environ.get('EMAIL_USER', 'noreply@zyrix.de')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

# Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_email(to_email, subject, html_content):
    """E-Mail versenden über Checkdomain SMTP"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # SSL-Verbindung für Port 465
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"E-Mail Fehler: {e}")
        return False
def create_verification_email(user_name, verification_link):
    """Bestätigungs-E-Mail Template erstellen"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Poppins', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
            .logo {{ font-size: 2.5rem; font-weight: 800; color: #FF9900; margin-bottom: 10px; }}
            .content {{ padding: 30px; }}
            .button {{ display: inline-block; background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
            .footer {{ background: #f8f9fa; padding: 20px; font-size: 12px; color: #666; border-top: 1px solid #eee; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">Zyrix</div>
                <h2>E-Mail-Adresse bestätigen</h2>
            </div>
            <div class="content">
                <h3>Hallo {user_name}!</h3>
                <p>Vielen Dank für Ihre Registrierung bei Zyrix.de!</p>
                <p>Um Ihr Konto zu aktivieren und Ihre <strong>1200 kostenlosen Test-Tokens</strong> zu erhalten, bestätigen Sie bitte Ihre E-Mail-Adresse:</p>
                <div style="text-align: center;">
                    <a href="{verification_link}" class="button">✅ E-Mail-Adresse bestätigen</a>
                </div>
                <p><strong>Wichtig:</strong> Ohne Bestätigung können Sie sich nicht anmelden und haben keinen Zugriff auf die Zyrix-Tools.</p>
                <p>Falls Sie sich nicht bei Zyrix registriert haben, ignorieren Sie diese E-Mail einfach.</p>
                <p>Bei Fragen erreichen Sie uns unter: <a href="mailto:support@zyrix.de">support@zyrix.de</a></p>
            </div>
            <div class="footer">
                <strong>Zyrix.de</strong>  

                Inhaber: Marc Netzer  

                Mürmeln 77, 41363 Jüchen, Deutschland  

                E-Mail: support@zyrix.de | Website: www.zyrix.de  

                USt-IdNr.: DE327892859
            </div>
        </div>
    </body>
    </html>
    """

def create_password_reset_email(user_name, reset_link):
    """Passwort-Reset-E-Mail Template erstellen"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Poppins', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
            .logo {{ font-size: 2.5rem; font-weight: 800; color: #FF9900; margin-bottom: 10px; }}
            .content {{ padding: 30px; }}
            .button {{ display: inline-block; background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
            .footer {{ background: #f8f9fa; padding: 20px; font-size: 12px; color: #666; border-top: 1px solid #eee; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">Zyrix</div>
                <h2>Passwort zurücksetzen</h2>
            </div>
            <div class="content">
                <h3>Hallo {user_name}!</h3>
                <p>Sie haben eine Anfrage zum Zurücksetzen Ihres Passworts gestellt.</p>
                <p>Klicken Sie auf den folgenden Link, um ein neues Passwort zu erstellen:</p>
                <div style="text-align: center;">
                    <a href="{reset_link}" class="button">🔑 Neues Passwort erstellen</a>
                </div>
                <p><strong>Wichtig:</strong> Dieser Link ist nur 24 Stunden gültig.</p>
                <p>Falls Sie diese Anfrage nicht gestellt haben, ignorieren Sie diese E-Mail einfach.</p>
                <p>Bei Fragen erreichen Sie uns unter: <a href="mailto:support@zyrix.de">support@zyrix.de</a></p>
            </div>
            <div class="footer">
                <strong>Zyrix.de</strong>  

                Inhaber: Marc Netzer  

                Mürmeln 77, 41363 Jüchen, Deutschland  

                E-Mail: support@zyrix.de | Website: www.zyrix.de  

                USt-IdNr.: DE327892859
            </div>
        </div>
    </body>
    </html>
    """
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validierung
        required_fields = ['full_name', 'email', 'password', 'strasse', 'plz', 'stadt', 'land']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} ist erforderlich'}), 400
        
        # E-Mail bereits registriert?
        existing_user = supabase.table('users').select('*').eq('email', data['email']).execute()
        if existing_user.data:
            return jsonify({'error': 'E-Mail-Adresse bereits registriert'}), 400
        
        # Passwort hashen
        password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
        
        # Verification Token generieren
        verification_token = secrets.token_urlsafe(32)
        
        # Benutzer in Datenbank speichern (status: pending)
        user_data = {
            'full_name': data['full_name'],
            'email': data['email'],
            'password_hash': password_hash,
            'strasse': data['strasse'],
            'plz': data['plz'],
            'stadt': data['stadt'],
            'land': data['land'],
            'firmenname': data.get('firmenname'),
            'ust_idnr': data.get('ust_idnr'),
            'tokens': 1200,
            'status': 'pending',
            'verification_token': verification_token,
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('users').insert(user_data).execute()
        
        if result.data:
            # Bestätigungs-E-Mail senden
            verification_link = f"https://zyrix-backend-render.onrender.com/verify-email?token={verification_token}"
            email_html = create_verification_email(data['full_name'], verification_link )
            
            email_sent = send_email(
                data['email'],
                "Zyrix.de - E-Mail-Adresse bestätigen",
                email_html
            )
            
            if email_sent:
                return jsonify({
                    'message': 'Registrierung erfolgreich! Bitte bestätigen Sie die Anmeldung in Ihrem E-Mail-Account.',
                    'status': 'pending_verification'
                }), 201
            else:
                return jsonify({
                    'message': 'Registrierung erfolgreich, aber E-Mail konnte nicht gesendet werden. Kontaktieren Sie den Support.',
                    'status': 'pending_verification'
                }), 201
        else:
            return jsonify({'error': 'Registrierung fehlgeschlagen'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server-Fehler: {str(e)}'}), 500

@app.route('/verify-email', methods=['GET'])
def verify_email():
    """E-Mail-Adresse bestätigen"""
    try:
        token = request.args.get('token')
        if not token:
            return "Ungültiger Bestätigungslink", 400
        
        # Benutzer mit Token finden
        user = supabase.table('users').select('*').eq('verification_token', token).eq('status', 'pending').execute()
        
        if not user.data:
            return "Bestätigungslink ungültig oder bereits verwendet", 400
        
        user_data = user.data[0]
        
        # Benutzer aktivieren
        supabase.table('users').update({
            'status': 'verified',
            'verification_token': None,
            'verified_at': datetime.utcnow().isoformat()
        }).eq('id', user_data['id']).execute()
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>E-Mail bestätigt - Zyrix</title>
            <style>
                body {{ font-family: 'Poppins', Arial, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
                .container {{ background: white; border-radius: 20px; padding: 40px; text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.1); max-width: 500px; }}
                .logo {{ font-size: 3rem; font-weight: 800; color: #FF9900; margin-bottom: 20px; }}
                .success {{ color: #28a745; font-size: 1.2rem; margin-bottom: 20px; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">Zyrix</div>
                <div class="success">✅ E-Mail-Adresse erfolgreich bestätigt!</div>
                <p>Ihr Konto ist jetzt aktiviert und Sie haben <strong>1200 Test-Tokens</strong> erhalten.</p>
                <p>Sie können sich jetzt anmelden und alle Zyrix-Tools nutzen.</p>
                <a href="https://www.zyrix.de/myzyrix" class="button">🚀 Zum Zyrix Dashboard</a>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        return f"Fehler bei der Bestätigung: {str(e )}", 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'E-Mail und Passwort erforderlich'}), 400
        
        # Benutzer finden
        user = supabase.table('users').select('*').eq('email', email).execute()
        
        if not user.data:
            return jsonify({'error': 'Ungültige Anmeldedaten'}), 401
        
        user_data = user.data[0]
        
        # E-Mail-Bestätigung prüfen
        if user_data.get('status') != 'verified':
            return jsonify({
                'error': 'Bitte bestätigen Sie zuerst Ihre E-Mail-Adresse. Prüfen Sie Ihr E-Mail-Postfach.',
                'status': 'email_not_verified'
            }), 401
        
        # Passwort prüfen
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user_data['password_hash'] != password_hash:
            return jsonify({'error': 'Ungültige Anmeldedaten'}), 401
        
        # JWT Token erstellen
        token_payload = {
            'user_id': user_data['id'],
            'email': user_data['email'],
            'exp': datetime.utcnow() + timedelta(days=30)
        }
        token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'message': 'Anmeldung erfolgreich',
            'token': token,
            'redirect_url': 'https://www.zyrix.de/myzyrix',
            'user': {
                'id': user_data['id'],
                'email': user_data['email'],
                'full_name': user_data['full_name'],
                'tokens': user_data['tokens']
            }
        } ), 200
        
    except Exception as e:
        return jsonify({'error': f'Server-Fehler: {str(e)}'}), 500
@app.route('/request-password-reset', methods=['POST'])
def request_password_reset():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'E-Mail-Adresse erforderlich'}), 400
        
        # Benutzer finden
        user = supabase.table('users').select('*').eq('email', email).execute()
        
        if not user.data:
            # Aus Sicherheitsgründen immer Erfolg melden
            return jsonify({'message': 'Falls die E-Mail-Adresse registriert ist, wurde ein Reset-Link gesendet'}), 200
        
        user_data = user.data[0]
        
        # Reset Token generieren
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Reset Token in Datenbank speichern
        supabase.table('password_resets').insert({
            'user_id': user_data['id'],
            'token': reset_token,
            'expires_at': expires_at.isoformat(),
            'used': False,
            'created_at': datetime.utcnow().isoformat()
        }).execute()
        
        # Reset-E-Mail senden
        reset_link = f"https://zyrix-backend-render.onrender.com/reset-password-page?token={reset_token}"
        email_html = create_password_reset_email(user_data['full_name'], reset_link )
        
        email_sent = send_email(
            email,
            "Zyrix.de - Passwort zurücksetzen",
            email_html
        )
        
        if email_sent:
            return jsonify({'message': 'Reset-Link wurde an Ihre E-Mail-Adresse gesendet'}), 200
        else:
            return jsonify({'message': 'E-Mail konnte nicht gesendet werden. Versuchen Sie es später erneut.'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server-Fehler: {str(e)}'}), 500

@app.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('password')
        
        if not token or not new_password:
            return jsonify({'error': 'Token und neues Passwort erforderlich'}), 400
        
        # Reset Token prüfen
        reset_data = supabase.table('password_resets').select('*').eq('token', token).eq('used', False).execute()
        
        if not reset_data.data:
            return jsonify({'error': 'Ungültiger oder bereits verwendeter Reset-Link'}), 400
        
        reset_info = reset_data.data[0]
        
        # Token-Ablauf prüfen
        expires_at = datetime.fromisoformat(reset_info['expires_at'].replace('Z', '+00:00'))
        if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
            return jsonify({'error': 'Reset-Link ist abgelaufen'}), 400
        
        # Neues Passwort hashen
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        
        # Passwort aktualisieren
        supabase.table('users').update({
            'password_hash': password_hash
        }).eq('id', reset_info['user_id']).execute()
        
        # Reset Token als verwendet markieren
        supabase.table('password_resets').update({
            'used': True
        }).eq('id', reset_info['id']).execute()
        
        return jsonify({'message': 'Passwort erfolgreich zurückgesetzt'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Server-Fehler: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200

# HTML-Templates sind sehr lang - verwenden Sie die bestehenden aus der alten app.py
# Oder ich kann sie separat schicken

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
        'message': 'Zyrix Backend API mit Checkdomain E-Mail-System',
        'version': '5.0',
        'status': 'online',
        'platform': 'Render.com',
        'email_provider': 'Checkdomain',
        'features': ['registration', 'login', 'email_verification', 'password_reset', 'dashboard_redirect'],
        'endpoints': ['/register', '/login', '/verify-email', '/request-password-reset', '/reset-password']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
# HTML-Templates
REGISTER_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registrierung - Zyrix</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100% ); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
        .container { background: white; border-radius: 20px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1); overflow: hidden; width: 100%; max-width: 400px; padding: 40px; }
        .logo { text-align: center; margin-bottom: 30px; }
        .logo h1 { font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 500; color: #333; }
        input[type="text"], input[type="email"], input[type="password"] { width: 100%; padding: 15px; border: 2px solid #e1e5e9; border-radius: 10px; font-size: 16px; transition: border-color 0.3s; }
        input[type="text"]:focus, input[type="email"]:focus, input[type="password"]:focus { outline: none; border-color: #FF9900; }
        .checkbox-group { display: flex; align-items: center; margin-bottom: 20px; }
        .checkbox-group input[type="checkbox"] { margin-right: 10px; }
        .btn { width: 100%; padding: 15px; background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%); color: white; border: none; border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s; }
        .btn:hover { transform: translateY(-2px); }
        .login-link { text-align: center; margin-top: 20px; }
        .login-link a { color: #FF9900; text-decoration: none; font-weight: 500; }
        .message { padding: 15px; margin-bottom: 20px; border-radius: 8px; text-align: center; }
        .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>Zyrix</h1>
            <p>Registrierung</p>
        </div>
        
        <div id="message"></div>
        
        <form id="registerForm">
            <div class="form-group">
                <label for="full_name">Vollständiger Name *</label>
                <input type="text" id="full_name" name="full_name" required>
            </div>
            
            <div class="form-group">
                <label for="email">E-Mail-Adresse *</label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="password">Passwort *</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <div class="form-group">
                <label for="strasse">Straße *</label>
                <input type="text" id="strasse" name="strasse" required>
            </div>
            
            <div class="form-group">
                <label for="plz">PLZ *</label>
                <input type="text" id="plz" name="plz" required>
            </div>
            
            <div class="form-group">
                <label for="stadt">Stadt *</label>
                <input type="text" id="stadt" name="stadt" required>
            </div>
            
            <div class="form-group">
                <label for="land">Land *</label>
                <input type="text" id="land" name="land" value="Deutschland" required>
            </div>
            
            <div class="checkbox-group">
                <input type="checkbox" id="is_company" name="is_company">
                <label for="is_company">Ich registriere mich als Unternehmen</label>
            </div>
            
            <div class="form-group" id="company_fields" style="display: none;">
                <label for="firmenname">Firmenname</label>
                <input type="text" id="firmenname" name="firmenname">
                
                <label for="ust_idnr" style="margin-top: 15px;">USt-IdNr.</label>
                <input type="text" id="ust_idnr" name="ust_idnr">
            </div>
            
            <button type="submit" class="btn">Registrieren</button>
        </form>
        
        <div class="login-link">
            Bereits registriert? <a href="https://zyrix-backend-render.onrender.com/login-page">Jetzt anmelden</a>
        </div>
    </div>

    <script>
        document.getElementById('is_company' ).addEventListener('change', function() {
            const companyFields = document.getElementById('company_fields');
            companyFields.style.display = this.checked ? 'block' : 'none';
        });

        document.getElementById('registerForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData.entries());
            
            try {
                const response = await fetch('/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                const messageDiv = document.getElementById('message');
                
                if (response.ok) {
                    messageDiv.innerHTML = '<div class="success">' + result.message + '</div>';
                    this.reset();
                } else {
                    messageDiv.innerHTML = '<div class="error">' + result.error + '</div>';
                }
            } catch (error) {
                document.getElementById('message').innerHTML = '<div class="error">Netzwerkfehler. Bitte versuchen Sie es erneut.</div>';
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
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100% ); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
        .container { background: white; border-radius: 20px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1); overflow: hidden; width: 100%; max-width: 400px; padding: 40px; }
        .logo { text-align: center; margin-bottom: 30px; }
        .logo h1 { font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 500; color: #333; }
        input[type="email"], input[type="password"] { width: 100%; padding: 15px; border: 2px solid #e1e5e9; border-radius: 10px; font-size: 16px; transition: border-color 0.3s; }
        input[type="email"]:focus, input[type="password"]:focus { outline: none; border-color: #FF9900; }
        .btn { width: 100%; padding: 15px; background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%); color: white; border: none; border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s; }
        .btn:hover { transform: translateY(-2px); }
        .links { text-align: center; margin-top: 20px; }
        .links a { color: #FF9900; text-decoration: none; font-weight: 500; margin: 0 10px; }
        .message { padding: 15px; margin-bottom: 20px; border-radius: 8px; text-align: center; }
        .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>Zyrix</h1>
            <p>Anmeldung</p>
        </div>
        
        <div id="message"></div>
        
        <form id="loginForm">
            <div class="form-group">
                <label for="email">E-Mail-Adresse</label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="password">Passwort</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="btn">Anmelden</button>
        </form>
        
        <div class="links">
            <a href="https://zyrix-backend-render.onrender.com/forgot-password-page">Passwort vergessen?</a>  
  

            Noch kein Account? <a href="https://zyrix-backend-render.onrender.com/register-page">Jetzt registrieren</a>
        </div>
    </div>

    <script>
        document.getElementById('loginForm' ).addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData.entries());
            
            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                const messageDiv = document.getElementById('message');
                
                if (response.ok) {
                    messageDiv.innerHTML = '<div class="success">Anmeldung erfolgreich! Sie werden zum Dashboard weitergeleitet...</div>';
                    localStorage.setItem('zyrix_token', result.token);
                    localStorage.setItem('zyrix_user', JSON.stringify(result.user));
                    setTimeout(() => {
                        window.location.href = result.redirect_url || 'https://www.zyrix.de/myzyrix';
                    }, 2000 );
                } else {
                    messageDiv.innerHTML = '<div class="error">' + result.error + '</div>';
                }
            } catch (error) {
                document.getElementById('message').innerHTML = '<div class="error">Netzwerkfehler. Bitte versuchen Sie es erneut.</div>';
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
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100% ); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
        .container { background: white; border-radius: 20px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1); overflow: hidden; width: 100%; max-width: 400px; padding: 40px; }
        .logo { text-align: center; margin-bottom: 30px; }
        .logo h1 { font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .description { text-align: center; color: #666; margin-bottom: 30px; line-height: 1.6; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 500; color: #333; }
        input[type="password"] { width: 100%; padding: 15px; border: 2px solid #e1e5e9; border-radius: 10px; font-size: 16px; transition: border-color 0.3s; }
        input[type="password"]:focus { outline: none; border-color: #FF9900; }
        .btn { width: 100%; padding: 15px; background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%); color: white; border: none; border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s; }
        .btn:hover { transform: translateY(-2px); }
        .login-link { text-align: center; margin-top: 20px; }
        .login-link a { color: #FF9900; text-decoration: none; font-weight: 500; }
        .message { padding: 15px; margin-bottom: 20px; border-radius: 8px; text-align: center; }
        .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>Zyrix</h1>
            <p>Passwort zurücksetzen</p>
        </div>
        
        <div class="description">
            Geben Sie Ihr neues Passwort ein.
        </div>
        
        <div id="message"></div>
        
        <form id="resetForm">
            <div class="form-group">
                <label for="password">Neues Passwort</label>
                <input type="password" id="password" name="password" required minlength="6">
            </div>
            
            <div class="form-group">
                <label for="confirm_password">Passwort bestätigen</label>
                <input type="password" id="confirm_password" name="confirm_password" required minlength="6">
            </div>
            
            <button type="submit" class="btn">Passwort zurücksetzen</button>
        </form>
        
        <div class="login-link">
            <a href="https://zyrix-backend-render.onrender.com/login-page">Zurück zur Anmeldung</a>
        </div>
    </div>

    <script>
        const urlParams = new URLSearchParams(window.location.search );
        const token = urlParams.get('token');
        
        if (!token) {
            document.getElementById('message').innerHTML = '<div class="error">Ungültiger Reset-Link</div>';
        }

        document.getElementById('resetForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            
            if (password !== confirmPassword) {
                document.getElementById('message').innerHTML = '<div class="error">Passwörter stimmen nicht überein</div>';
                return;
            }
            
            try {
                const response = await fetch('/reset-password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: token, password: password })
                });
                
                const result = await response.json();
                const messageDiv = document.getElementById('message');
                
                if (response.ok) {
                    messageDiv.innerHTML = '<div class="success">' + result.message + ' Sie werden zur Anmeldung weitergeleitet...</div>';
                    setTimeout(() => {
                        window.location.href = 'https://zyrix-backend-render.onrender.com/login-page';
                    }, 3000 );
                } else {
                    messageDiv.innerHTML = '<div class="error">' + result.error + '</div>';
                }
            } catch (error) {
                document.getElementById('message').innerHTML = '<div class="error">Netzwerkfehler. Bitte versuchen Sie es erneut.</div>';
            }
        });
    </script>
</body>
</html>
"""
