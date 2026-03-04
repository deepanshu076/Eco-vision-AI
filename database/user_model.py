from database.db import db
from datetime import datetime
import bcrypt

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.LargeBinary(60), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship with waste uploads
    waste_uploads = db.relationship('WasteUpload', backref='user', lazy=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    def check_password(self, password):
        """Check password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash)
    
    def get_sustainability_score(self):
        """Calculate user's sustainability score based on uploads"""
        total_uploads = len(self.waste_uploads)
        if total_uploads == 0:
            return 0
        
        # Calculate score based on waste types and consistency
        recyclable_count = sum(1 for w in self.waste_uploads if w.category == 'recyclable')
        biodegradable_count = sum(1 for w in self.waste_uploads if w.category == 'biodegradable')
        
        # Score formula: 50% recyclable, 30% biodegradable, 20% consistency
        recyclable_score = (recyclable_count / total_uploads) * 50
        biodegradable_score = (biodegradable_count / total_uploads) * 30
        
        # Consistency bonus (uploads across different days)
        unique_days = len(set([w.upload_date.date() for w in self.waste_uploads]))
        consistency_score = min(unique_days * 2, 20)  # Max 20 points
        
        total_score = recyclable_score + biodegradable_score + consistency_score
        
        return round(total_score, 1)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'sustainability_score': self.get_sustainability_score(),
            'total_uploads': len(self.waste_uploads)
        }