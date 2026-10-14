from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import config

import os

from models import db, User, ParkingLot, ParkingSpot, Reservation
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Load configuration from config.py
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['JWT_SECRET_KEY'] = config.JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = config.JWT_ACCESS_TOKEN_EXPIRES
app.config['DEBUG'] = config.DEBUG

# Initialize extensions
db.init_app(app)
CORS(app)
jwt = JWTManager(app)

# ==================== AUTH ROUTES ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Check if user already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists"}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already exists"}), 409
    
    # Create new user
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role='user'  # New users are regular users
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        "message": "User registered successfully",
        "user_id": user.id
    }), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Missing username or password"}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Create JWT tokens
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }), 200


@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at.isoformat()
    }), 200

# ==================== PARKING LOT ROUTES ====================

@app.route('/api/parking-lots', methods=['GET'])
def get_parking_lots():
    """Get all parking lots"""
    lots = ParkingLot.query.all()
    
    result = []
    for lot in lots:
        # Count available spots
        available = ParkingSpot.query.filter_by(parking_lot_id=lot.id, status='available').count()
        
        result.append({
            "id": lot.id,
            "name": lot.name,
            "location": lot.location,
            "city": lot.city,
            "total_spots": lot.total_spots,
            "available_spots": available
        })
    
    return jsonify({
        "total": len(result),
        "parking_lots": result
    }), 200


@app.route('/api/parking-lots/<int:lot_id>', methods=['GET'])
def get_parking_lot(lot_id):
    """Get parking lot details"""
    lot = ParkingLot.query.get(lot_id)
    
    if not lot:
        return jsonify({"error": "Parking lot not found"}), 404
    
    # Count available spots
    available = ParkingSpot.query.filter_by(parking_lot_id=lot.id, status='available').count()
    
    return jsonify({
        "id": lot.id,
        "name": lot.name,
        "location": lot.location,
        "city": lot.city,
        "total_spots": lot.total_spots,
        "available_spots": available
    }), 200


@app.route('/api/parking-lots', methods=['POST'])
@jwt_required()
def create_parking_lot():
    """Create a new parking lot (Admin only)"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Check if user is admin
    if not user or user.role != 'admin':
        return jsonify({"error": "Insufficient permissions"}), 403
    
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('location'):
        return jsonify({"error": "Missing required fields"}), 400
    
    lot = ParkingLot(
        name=data['name'],
        location=data['location'],
        city=data.get('city', ''),
        total_spots=data.get('total_spots', 0)
    )
    
    db.session.add(lot)
    db.session.commit()
    
    return jsonify({
        "message": "Parking lot created successfully",
        "id": lot.id
    }), 201

# ==================== PARKING SPOT ROUTES ====================

@app.route('/api/parking-lots/<int:lot_id>/spots', methods=['GET'])
def get_parking_spots(lot_id):
    """Get all parking spots in a lot"""
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return jsonify({"error": "Parking lot not found"}), 404
    
    spots = ParkingSpot.query.filter_by(parking_lot_id=lot_id).all()
    
    return jsonify({
        "total": len(spots),
        "parking_spots": [
            {
                "id": spot.id,
                "spot_number": spot.spot_number,
                "status": spot.status
            }
            for spot in spots
        ]
    }), 200

# ==================== RESERVATION ROUTES ====================

@app.route('/api/reservations', methods=['POST'])
@jwt_required()
def create_reservation():
    """Create a new parking reservation"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('parking_spot_id') or not data.get('vehicle_number'):
        return jsonify({"error": "Missing required fields"}), 400
    
    spot = ParkingSpot.query.get(data['parking_spot_id'])
    
    # Check if spot exists and is available
    if not spot or spot.status != 'available':
        return jsonify({"error": "Parking spot not available"}), 400
    
    # Parse dates
    try:
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = datetime.fromisoformat(data['end_time'])
    except:
        return jsonify({"error": "Invalid date format"}), 400
    
    if start_time >= end_time:
        return jsonify({"error": "Start time must be before end time"}), 400
    
    # Create reservation
    reservation = Reservation(
        user_id=current_user_id,
        parking_spot_id=data['parking_spot_id'],
        vehicle_number=data['vehicle_number'],
        start_time=start_time,
        end_time=end_time,
        status='active'
    )
    
    # Update spot status to reserved
    spot.status = 'reserved'
    
    db.session.add(reservation)
    db.session.commit()
    
    return jsonify({
        "message": "Reservation created successfully",
        "reservation_id": reservation.id
    }), 201


@app.route('/api/reservations', methods=['GET'])
@jwt_required()
def get_user_reservations():
    """Get current user's reservations"""
    current_user_id = get_jwt_identity()
    reservations = Reservation.query.filter_by(user_id=current_user_id).all()
    
    return jsonify({
        "total": len(reservations),
        "reservations": [
            {
                "id": res.id,
                "parking_spot_id": res.parking_spot_id,
                "vehicle_number": res.vehicle_number,
                "start_time": res.start_time.isoformat(),
                "end_time": res.end_time.isoformat(),
                "status": res.status,
                "created_at": res.created_at.isoformat()
            }
            for res in reservations
        ]
    }), 200


@app.route('/api/reservations/<int:res_id>', methods=['PUT'])
@jwt_required()
def update_reservation(res_id):
    """Update reservation status"""
    current_user_id = get_jwt_identity()
    reservation = Reservation.query.get(res_id)
    
    if not reservation:
        return jsonify({"error": "Reservation not found"}), 404
    
    if reservation.user_id != current_user_id:
        return jsonify({"error": "You can only update your own reservations"}), 403
    
    data = request.get_json()
    
    if not data or not data.get('status'):
        return jsonify({"error": "Missing status field"}), 400
    
    if data['status'] not in ['active', 'completed', 'cancelled']:
        return jsonify({"error": "Invalid status"}), 400
    
    # If cancelling, free up the parking spot
    if data['status'] == 'cancelled' and reservation.status == 'active':
        spot = ParkingSpot.query.get(reservation.parking_spot_id)
        if spot:
            spot.status = 'available'
    
    reservation.status = data['status']
    db.session.commit()
    
    return jsonify({
        "message": "Reservation updated successfully",
        "reservation_id": reservation.id,
        "status": reservation.status
    }), 200


@app.route('/api/reservations/<int:res_id>', methods=['DELETE'])
@jwt_required()
def delete_reservation(res_id):
    """Delete a reservation"""
    current_user_id = get_jwt_identity()
    reservation = Reservation.query.get(res_id)
    
    if not reservation:
        return jsonify({"error": "Reservation not found"}), 404
    
    if reservation.user_id != current_user_id:
        return jsonify({"error": "You can only delete your own reservations"}), 403
    
    # Free up the parking spot
    spot = ParkingSpot.query.get(reservation.parking_spot_id)
    if spot:
        spot.status = 'available'
    
    db.session.delete(reservation)
    db.session.commit()
    
    return jsonify({
        "message": "Reservation deleted successfully",
        "reservation_id": res_id
    }), 200

# ==================== Predefined Admin =============
def create_default_admin():
    with app.app_context():
            admin_username = "admin"
            admin_email = "admin@example.com"
            
            # Check if an admin user already exists by username or role
            existing_admin = User.query.filter(
                (User.username == admin_username) | (User.role == 'admin')
            ).first()
            
            if not existing_admin:
                admin_user = User(
                    username=admin_username,
                    email=admin_email,
                    password_hash=generate_password_hash("admin123"),
                    role='admin'  # Make sure role is set to admin
                )
                
                db.session.add(admin_user)
                db.session.commit()
                print("Default admin user created successfully!")
            else:
                print("Admin user already exists. Skipping creation.")


# ==================== MAIN ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_admin()
    app.run(debug=True, port=5000)