from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ==================== MODELS ====================

class User(db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'admin' or 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'


class ParkingLot(db.Model):
    """Parking lot model"""
    __tablename__ = 'parking_lots'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(80))
    total_spots = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    parking_spots = db.relationship('ParkingSpot', backref='parking_lot', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ParkingLot {self.name}>'


class ParkingSpot(db.Model):
    """Parking spot model"""
    __tablename__ = 'parking_spots'
    
    id = db.Column(db.Integer, primary_key=True)
    parking_lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'), nullable=False)
    spot_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='available', nullable=False)  # available, occupied, reserved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reservations = db.relationship('Reservation', backref='parking_spot', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ParkingSpot {self.parking_lot_id}-{self.spot_number}>'


class Reservation(db.Model):
    """Reservation model"""
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parking_spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active', nullable=False)  # active, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='reservations')
    
    def __repr__(self):
        return f'<Reservation {self.id}>'