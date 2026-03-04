from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import current_app
import os

db = SQLAlchemy()

def init_db(app):
    """Initialize database with app"""
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        print("Database initialized!")

def get_db():
    """Get database instance"""
    return db