import sys, os
sys.path.append(os.path.dirname(__file__))
from flask import Flask, jsonify
from config import MONGO_URI, SECRET_KEY
from flask_pymongo import PyMongo
from flask_login import LoginManager

app = Flask(__name__)
app.config['MONGO_URI'] = MONGO_URI
app.config['SECRET_KEY'] = SECRET_KEY

mongo = PyMongo(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
app.mongo = mongo

# health endpoint
@app.route('/health')
def health():
    try:
        mongo.cx.server_info()
        return jsonify({'status': 'ok', 'db': 'connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'db': str(e)})

# register blueprints
from routes.auth_routes import auth_bp
from routes.booking_routes import booking_bp
from routes.admin_routes import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(admin_bp)

# Jinja2 filter for phone number formatting
@app.template_filter('format_phone')
def format_phone(phone):
    """Format phone number for display: (XXX) XXX-XXXX or keep original if not standard format."""
    if not phone:
        return '-'
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, str(phone)))
    # Format as (XXX) XXX-XXXX if 10 digits
    if len(digits) == 10:
        return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
    # Format as +X (XXX) XXX-XXXX if 11 digits (with country code)
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
    # Return original if not standard format
    return phone

@login_manager.user_loader
def load_user(user_id):
    from models.user_model import User
    try:
        db = mongo.db
        user = User.find_by_id(db, user_id)
        if user and user.is_active():
            return user
        return None
    except Exception as e:
        print(f"[ERROR] Error loading user {user_id}: {str(e)}")
        return None

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
