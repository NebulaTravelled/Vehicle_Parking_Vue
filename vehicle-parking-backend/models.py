from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ==================== MODELS ====================

class User(db.Model):
    """User model (Superuser Admin & Standard Users)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'admin' or 'user'
    last_visited_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reservations = db.relationship('Reservation', backref='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class ParkingLot(db.Model):
    """
    Parking lot model
    Physical space containing a collection of 4-wheeler parking spots.
    Attributes: id, prime_location_name, price, address, pin_code, number_of_spots
    """
    __tablename__ = 'parking_lots'
    
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, default=0.0, nullable=False)  # Price per hour
    address = db.Column(db.String(255), nullable=False)
    pin_code = db.Column(db.String(20), nullable=False)
    number_of_spots = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    parking_spots = db.relationship('ParkingSpot', backref='parking_lot', cascade='all, delete-orphan', lazy=True)
    
    # Backward compatibility properties
    @property
    def name(self):
        return self.prime_location_name
        
    @property
    def location(self):
        return self.address
        
    @property
    def total_spots(self):
        return self.number_of_spots
    
    def __repr__(self):
        return f'<ParkingLot {self.prime_location_name}>'


class ParkingSpot(db.Model):
    """
    Parking spot model for 4-wheeler parking.
    Attributes: id, lot_id, spot_number, status (O-occupied / A-available)
    """
    __tablename__ = 'parking_spots'
    
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'), nullable=False)
    spot_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(5), default='A', nullable=False)  # 'A' = Available, 'O' = Occupied
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reservations = db.relationship('Reservation', backref='parking_spot', cascade='all, delete-orphan', lazy=True)
    
    # Backward compatibility property
    @property
    def parking_lot_id(self):
        return self.lot_id
    
    def __repr__(self):
        return f'<ParkingSpot {self.lot_id}-{self.spot_number} ({self.status})>'


class Reservation(db.Model):
    """
    Reserve parking spot model.
    Allocates parking spot as per user requests.
    Attributes: id, spot_id, user_id, parking_timestamp, leaving_timestamp, parking_cost, vehicle_number
    """
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parking_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)
    parking_cost = db.Column(db.Float, default=0.0, nullable=True)
    vehicle_number = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active', 'completed', 'cancelled'
    remarks = db.Column(db.String(255), default='', nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Backward compatibility properties
    @property
    def parking_spot_id(self):
        return self.spot_id
        
    @property
    def start_time(self):
        return self.parking_timestamp
        
    @property
    def end_time(self):
        return self.leaving_timestamp
    
    def __repr__(self):
        return f'<Reservation {self.id} (Spot {self.spot_id}, User {self.user_id}, Status {self.status})>'


class ExportJob(db.Model):
    """User-triggered async CSV export job model"""
    __tablename__ = 'export_jobs'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'processing', 'completed', 'failed'
    file_path = db.Column(db.String(255), nullable=True)
    filename = db.Column(db.String(120), nullable=True)
    error_message = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)


class DailyReminderLog(db.Model):
    """Daily reminders audit log"""
    __tablename__ = 'daily_reminder_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    channel = db.Column(db.String(50), default='Google Chat Webhook', nullable=False)
    message = db.Column(db.Text, nullable=False)
    recipients_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='sent', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)