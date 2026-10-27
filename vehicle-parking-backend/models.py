from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

def utc_now():
    """Returns current UTC timestamp, replacing deprecated datetime.utcnow()"""
    return datetime.now(timezone.utc)

# ==================== MODELS ====================

class User(db.Model):
    """User model (Superuser Admin, Company Operators & Standard Users)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'admin', 'company', or 'user'
    name = db.Column(db.String(100), nullable=True)
    company_name = db.Column(db.String(150), nullable=True)
    mobile_number = db.Column(db.String(30), nullable=True)
    description = db.Column(db.Text, nullable=True)
    address = db.Column(db.String(255), nullable=True)
    last_visited_at = db.Column(db.DateTime, default=utc_now)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relationships
    reservations = db.relationship('Reservation', backref='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class ParkingLot(db.Model):
    """
    Parking lot model
    Physical space containing a collection of 4-wheeler parking spots.
    Attributes: id, prime_location_name, price, address, pin_code, number_of_spots, company_id, grid dimensions
    """
    __tablename__ = 'parking_lots'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    prime_location_name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, default=0.0, nullable=False)  # Price per hour
    address = db.Column(db.String(255), nullable=False)
    pin_code = db.Column(db.String(20), nullable=False)
    number_of_spots = db.Column(db.Integer, default=0, nullable=False)
    handicap_spots = db.Column(db.Integer, default=0, nullable=True)
    regular_spots = db.Column(db.Integer, default=0, nullable=True)
    grid_rows = db.Column(db.Integer, default=5, nullable=True)
    grid_cols = db.Column(db.Integer, default=6, nullable=True)
    grid_layout = db.Column(db.Text, nullable=True)  # JSON representation of grid
    
    # Pricing Tiers & Operations
    daily_rate = db.Column(db.Float, default=0.0, nullable=True)          # Daily / 24-hr maximum cap
    overnight_rate = db.Column(db.Float, default=0.0, nullable=True)      # Flat overnight rate (10 PM - 7 AM)
    peak_multiplier = db.Column(db.Float, default=1.0, nullable=True)     # Rush hour multiplier (e.g. 1.5x)
    grace_period_minutes = db.Column(db.Integer, default=15, nullable=True) # Free exit / cancel window
    overstay_penalty_rate = db.Column(db.Float, default=50.0, nullable=True) # Surcharge per hour past scheduled exit
    
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relationships
    company = db.relationship('User', backref=db.backref('company_lots', lazy=True), foreign_keys=[company_id])
    parking_spots = db.relationship('ParkingSpot', backref='parking_lot', cascade='all, delete-orphan', lazy=True)
    floors = db.relationship('ParkingFloor', backref='parking_lot', cascade='all, delete-orphan', order_by='ParkingFloor.floor_number', lazy=True)
    
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


class ParkingFloor(db.Model):
    """
    Parking Floor / Level model for multi-deck and multi-storey facilities.
    Attributes: id, lot_id, floor_number, floor_name, grid_rows, grid_cols, grid_layout, regular_spots, handicap_spots
    """
    __tablename__ = 'parking_floors'
    
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id', ondelete='CASCADE'), nullable=False)
    floor_number = db.Column(db.Integer, default=0, nullable=False)  # -2: B2, -1: B1, 0: Ground, 1: Level 1, etc.
    floor_name = db.Column(db.String(80), nullable=False)            # e.g., "Ground Floor", "Basement 1"
    grid_rows = db.Column(db.Integer, default=5, nullable=True)
    grid_cols = db.Column(db.Integer, default=6, nullable=True)
    grid_layout = db.Column(db.Text, nullable=True)                  # JSON representation of 2D matrix
    regular_spots = db.Column(db.Integer, default=0, nullable=True)
    handicap_spots = db.Column(db.Integer, default=0, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relationships
    spots = db.relationship('ParkingSpot', backref='floor', cascade='all, delete-orphan', lazy=True)
    
    def __repr__(self):
        return f'<ParkingFloor {self.floor_name} (Number: {self.floor_number}, Lot: {self.lot_id})>'


class ParkingSpot(db.Model):
    """
    Parking spot model for 4-wheeler parking.
    Attributes: id, lot_id, floor_id, floor_number, floor_name, spot_number, status (O-occupied / A-available), spot_type ('regular'/'handicap')
    """
    __tablename__ = 'parking_spots'
    __table_args__ = (
        db.Index('idx_spots_quickbook', 'lot_id', 'status', 'floor_id', 'spot_type'),
        db.Index('idx_spots_heuristic', 'lot_id', 'status', 'floor_number', 'row_idx', 'col_idx'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'), nullable=False)
    floor_id = db.Column(db.Integer, db.ForeignKey('parking_floors.id', ondelete='CASCADE'), nullable=True)
    floor_number = db.Column(db.Integer, default=0, nullable=True)
    floor_name = db.Column(db.String(80), default='Ground Floor', nullable=True)
    spot_number = db.Column(db.String(20), nullable=False)
    spot_type = db.Column(db.String(20), default='regular', nullable=False)  # 'regular' or 'handicap'
    row_idx = db.Column(db.Integer, nullable=True)
    col_idx = db.Column(db.Integer, nullable=True)
    slot_order = db.Column(db.Integer, default=0, nullable=True)
    status = db.Column(db.String(5), default='A', nullable=False)  # 'A' = Available, 'O' = Occupied
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relationships
    reservations = db.relationship('Reservation', backref='parking_spot', cascade='all, delete-orphan', lazy=True)
    
    # Backward compatibility property
    @property
    def parking_lot_id(self):
        return self.lot_id
    
    def __repr__(self):
        return f'<ParkingSpot {self.lot_id}-{self.spot_number} ({self.floor_name}, {self.spot_type}, {self.status})>'


class Vehicle(db.Model):
    """
    Vehicle model for Customer Garage (multi-car management).
    Attributes: id, user_id, license_plate, nickname, vehicle_type ('Car', 'SUV', 'Motorcycle', 'EV'), is_default, created_at
    """
    __tablename__ = 'vehicles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    license_plate = db.Column(db.String(30), nullable=False)
    nickname = db.Column(db.String(80), nullable=True)  # e.g., "Dad's SUV", "Daily Commuter"
    vehicle_type = db.Column(db.String(30), default='Car', nullable=False)  # 'Car', 'SUV', 'Motorcycle', 'EV'
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('vehicles', cascade='all, delete-orphan', lazy=True))
    
    def __repr__(self):
        return f'<Vehicle {self.license_plate} ({self.vehicle_type}, User: {self.user_id})>'


class Reservation(db.Model):
    """
    Reserve parking spot model.
    Allocates parking spot as per user requests.
    Stores comprehensive location hierarchy (Venue -> Floor -> Slot) and duration metrics.
    """
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Location Hierarchy & Metadata
    venue_name = db.Column(db.String(150), nullable=True)
    company_name = db.Column(db.String(150), nullable=True)
    floor_id = db.Column(db.Integer, nullable=True)
    floor_number = db.Column(db.Integer, default=0, nullable=True)
    floor_name = db.Column(db.String(80), default='Ground Floor', nullable=True)
    spot_number = db.Column(db.String(30), nullable=True)
    spot_type = db.Column(db.String(20), default='regular', nullable=True)  # 'regular' or 'handicap'
    location_hierarchy = db.Column(db.String(255), nullable=True)
    
    # Vehicle Association
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=True)
    vehicle_number = db.Column(db.String(30), nullable=False)
    vehicle_type = db.Column(db.String(30), default='Car', nullable=True)  # 'Car', 'SUV', 'Motorcycle', 'EV'
    
    # Audit Timestamps & Calculated Metrics
    booking_type = db.Column(db.String(20), default='immediate', nullable=False)  # 'immediate' or 'scheduled'
    scheduled_start_time = db.Column(db.DateTime, nullable=True)
    scheduled_end_time = db.Column(db.DateTime, nullable=True)
    parking_timestamp = db.Column(db.DateTime, default=utc_now, nullable=False)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, default=0, nullable=True)
    duration_formatted = db.Column(db.String(50), nullable=True)
    parking_cost = db.Column(db.Float, default=0.0, nullable=True)
    grace_period_applied = db.Column(db.Boolean, default=False, nullable=True)
    overstay_penalty_cost = db.Column(db.Float, default=0.0, nullable=True)
    
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active', 'completed', 'cancelled'
    remarks = db.Column(db.String(255), default='', nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relationships
    vehicle = db.relationship('Vehicle', backref=db.backref('reservations', lazy=True), foreign_keys=[vehicle_id])
    
    # Location path helper
    @property
    def location_path(self):
        return self.location_hierarchy or f"{self.venue_name or 'Venue'} → {self.floor_name or 'Ground Floor'} → {self.spot_number or 'Spot'}"
    
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
    created_at = db.Column(db.DateTime, default=utc_now)
    completed_at = db.Column(db.DateTime, nullable=True)


class DailyReminderLog(db.Model):
    """Daily reminders audit log"""
    __tablename__ = 'daily_reminder_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    channel = db.Column(db.String(50), default='Google Chat Webhook', nullable=False)
    message = db.Column(db.Text, nullable=False)
    recipients_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='sent', nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)