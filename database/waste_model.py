from database.db import db
from datetime import datetime

class WasteUpload(db.Model):
    __tablename__ = 'waste_uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    image_hash = db.Column(db.String(64), unique=True, nullable=False)  # Perceptual hash
    category = db.Column(db.String(50), nullable=False)  # biodegradable, recyclable, hazardous
    confidence = db.Column(db.Float, nullable=False)
    carbon_saved = db.Column(db.Float, nullable=False)  # kg CO2 saved
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_carbon_saved(self):
        """Calculate carbon saved based on waste category"""
        carbon_values = {
            'biodegradable': 0.5,  # kg CO2 saved per item
            'recyclable': 1.2,
            'hazardous': 2.5
        }
        return carbon_values.get(self.category, 0)
    
    def to_dict(self):
        """Convert waste upload to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'image_path': self.image_path,
            'category': self.category,
            'confidence': self.confidence,
            'carbon_saved': self.carbon_saved,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'username': self.user.username if self.user else None
        }