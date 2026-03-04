from flask import Flask, render_template, session, redirect, url_for
from config import config
from database.db import init_db
from database.user_model import User
from database.waste_model import WasteUpload
from routes.auth_routes import auth_bp
from routes.waste_routes import waste_bp
from routes.dashboard_routes import dashboard_bp
import os

def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize database
    init_db(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(waste_bp, url_prefix='/waste')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    
    # Home route
    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard.index'))
        return render_template('index.html')
    
    # Health check
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500
    
    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_CONFIG', 'development'))
    app.run(host='0.0.0.0', port=5000, debug=True)