import os
import re
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_file, make_response
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

import config
from models import db, User, ParkingLot, ParkingSpot, Reservation, ExportJob, DailyReminderLog
from cache import cache, cached
from jobs import trigger_csv_export, run_daily_reminders, generate_user_monthly_report

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


# ==================== PREDEFINED SUPERUSER ADMIN ====================

def create_default_admin():
    """
    Ensure the superuser Admin exists whenever the database is created.
    There can be only one admin for the app.
    Requires no registration.
    """
    with app.app_context():
        admin_username = "admin"
        admin_email = "admin@example.com"
        
        existing_admin = User.query.filter(
            (User.username == admin_username) | (User.role == 'admin')
        ).first()
        
        if not existing_admin:
            admin_user = User(
                username=admin_username,
                email=admin_email,
                password_hash=generate_password_hash("admin123"),
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Default superuser Admin created successfully!")
        else:
            print("Superuser Admin already exists.")


# ==================== AUTH ROUTES ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user (Single-word username and password allowed)"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Missing request body"}), 400
        
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not username or not email or not password:
        return jsonify({"error": "Missing required fields: username, email, and password are required"}), 400
    
    if any(c.isspace() for c in username):
        return jsonify({"error": "Username must be a single word without spaces"}), 400

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({"error": "Invalid email address format"}), 400

    if any(c.isspace() for c in password):
        return jsonify({"error": "Password must be a single word without spaces"}), 400
    
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409
    
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 409
    
    # Create new standard user
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role='user'
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        "message": "User registered successfully",
        "user_id": user.id,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user or superuser admin and return JWT access token"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Missing username or password"}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Update last_visited_at
    user.last_visited_at = datetime.utcnow()
    db.session.commit()
    
    # Identity as string for pyjwt compatibility
    access_token = create_access_token(identity=str(user.id))
    
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
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }), 200


# ==================== ADMIN ROUTES ====================

@app.route('/api/admin/dashboard', methods=['GET'])
@jwt_required()
def get_admin_dashboard():
    """
    Superuser Admin Dashboard:
    - Status of all available and occupied parking spots
    - High-level platform statistics
    """
    current_user_id = int(get_jwt_identity())
    admin = User.query.get(current_user_id)
    if not admin or admin.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    
    lots = ParkingLot.query.all()
    total_spots = ParkingSpot.query.count()
    available_spots = ParkingSpot.query.filter_by(status='A').count()
    occupied_spots = ParkingSpot.query.filter_by(status='O').count()
    total_users = User.query.filter(User.role == 'user').count()
    active_reservations = Reservation.query.filter_by(status='active').count()
    
    total_revenue = db.session.query(db.func.sum(Reservation.parking_cost)).scalar() or 0.0
    
    # Real-time visual spots overview grouped by lot
    lots_detail = []
    for lot in lots:
        spots = ParkingSpot.query.filter_by(lot_id=lot.id).order_by(ParkingSpot.id.asc()).all()
        lots_detail.append({
            "id": lot.id,
            "prime_location_name": lot.prime_location_name,
            "price": lot.price,
            "address": lot.address,
            "pin_code": lot.pin_code,
            "number_of_spots": lot.number_of_spots,
            "available_count": sum(1 for s in spots if s.status == 'A'),
            "occupied_count": sum(1 for s in spots if s.status == 'O'),
            "spots": [
                {
                    "id": s.id,
                    "spot_number": s.spot_number,
                    "status": s.status  # 'A' or 'O'
                }
                for s in spots
            ]
        })
    
    return jsonify({
        "statistics": {
            "total_lots": len(lots),
            "total_spots": total_spots,
            "available_spots": available_spots,
            "occupied_spots": occupied_spots,
            "total_users": total_users,
            "active_reservations": active_reservations,
            "total_revenue": round(total_revenue, 2)
        },
        "lots": lots_detail
    }), 200


@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_all_users():
    """Get all registered users (Admin only)"""
    current_user_id = int(get_jwt_identity())
    admin_user = User.query.get(current_user_id)
    if not admin_user or admin_user.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    
    users = User.query.all()
    return jsonify({
        "total": len(users),
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "created_at": u.created_at.isoformat() if u.created_at else None
            }
            for u in users
        ]
    }), 200


# ==================== PARKING LOT ROUTES (CACHED) ====================

@app.route('/api/parking-lots', methods=['GET'])
@cached(timeout=60, key_prefix="lots_list")
def get_parking_lots():
    """
    Get all parking lots with real-time available and occupied 4-wheeler spot counts.
    Cached for high API performance.
    """
    lots = ParkingLot.query.all()
    result = []
    
    for lot in lots:
        available = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
        occupied = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
        
        result.append({
            "id": lot.id,
            "prime_location_name": lot.prime_location_name,
            "name": lot.prime_location_name,  # Compatibility
            "price": lot.price,
            "address": lot.address,
            "location": lot.address,          # Compatibility
            "pin_code": lot.pin_code,
            "number_of_spots": lot.number_of_spots,
            "total_spots": lot.number_of_spots, # Compatibility
            "available_spots": available,
            "occupied_spots": occupied
        })
    
    return jsonify({
        "total": len(result),
        "parking_lots": result
    }), 200


@app.route('/api/parking-lots/<int:lot_id>', methods=['GET'])
def get_parking_lot(lot_id):
    """Get parking lot details and its 4-wheeler parking spots"""
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return jsonify({"error": "Parking lot not found"}), 404
    
    spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
    available = sum(1 for s in spots if s.status == 'A')
    occupied = sum(1 for s in spots if s.status == 'O')
    
    return jsonify({
        "id": lot.id,
        "prime_location_name": lot.prime_location_name,
        "name": lot.prime_location_name,
        "price": lot.price,
        "address": lot.address,
        "location": lot.address,
        "pin_code": lot.pin_code,
        "number_of_spots": lot.number_of_spots,
        "available_spots": available,
        "occupied_spots": occupied,
        "spots": [
            {
                "id": s.id,
                "spot_number": s.spot_number,
                "status": s.status
            }
            for s in spots
        ]
    }), 200


@app.route('/api/parking-lots', methods=['POST'])
@jwt_required()
def create_parking_lot():
    """
    Create a new parking lot (Admin only).
    Automatically populates the specified number of 4-wheeler parking spots.
    """
    current_user_id = int(get_jwt_identity())
    admin = User.query.get(current_user_id)
    if not admin or admin.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing request body"}), 400
        
    prime_location_name = data.get('prime_location_name') or data.get('name')
    address = data.get('address') or data.get('location')
    pin_code = str(data.get('pin_code') or '')
    price = float(data.get('price', 0.0))
    number_of_spots = int(data.get('number_of_spots') or data.get('total_spots') or 0)
    
    if not prime_location_name or not address or not pin_code or number_of_spots <= 0:
        return jsonify({"error": "Prime location name, address, pin code, and a positive number of spots are required"}), 400
    
    lot = ParkingLot(
        prime_location_name=prime_location_name,
        price=price,
        address=address,
        pin_code=pin_code,
        number_of_spots=number_of_spots
    )
    db.session.add(lot)
    db.session.flush()  # Generate lot.id
    
    # Automatically create the 4-wheeler parking spots
    for i in range(1, number_of_spots + 1):
        spot = ParkingSpot(
            lot_id=lot.id,
            spot_number=f"Spot-{i}",
            status='A'  # Available
        )
        db.session.add(spot)
        
    db.session.commit()
    
    # Invalidate cache
    cache.invalidate_prefix("lots_list")
    
    return jsonify({
        "message": "Parking lot created successfully",
        "id": lot.id,
        "number_of_spots": number_of_spots
    }), 201


@app.route('/api/parking-lots/<int:lot_id>', methods=['PUT'])
@jwt_required()
def edit_parking_lot(lot_id):
    """
    Edit a parking lot (Admin only).
    Allows updating details and increasing or decreasing the number of parking spots.
    """
    current_user_id = int(get_jwt_identity())
    admin = User.query.get(current_user_id)
    if not admin or admin.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return jsonify({"error": "Parking lot not found"}), 404
        
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing request body"}), 400
        
    if 'prime_location_name' in data:
        lot.prime_location_name = data['prime_location_name']
    elif 'name' in data:
        lot.prime_location_name = data['name']
        
    if 'address' in data:
        lot.address = data['address']
    elif 'location' in data:
        lot.address = data['location']
        
    if 'pin_code' in data:
        lot.pin_code = str(data['pin_code'])
        
    if 'price' in data:
        lot.price = float(data['price'])
        
    # Increasing or decreasing number of parking spots
    target_spots = data.get('number_of_spots') or data.get('total_spots')
    if target_spots is not None:
        target_spots = int(target_spots)
        if target_spots <= 0:
            return jsonify({"error": "Number of spots must be at least 1"}), 400
            
        current_spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
        current_count = len(current_spots)
        
        if target_spots > current_count:
            # Increase spots
            for i in range(current_count + 1, target_spots + 1):
                new_spot = ParkingSpot(
                    lot_id=lot.id,
                    spot_number=f"Spot-{i}",
                    status='A'
                )
                db.session.add(new_spot)
        elif target_spots < current_count:
            # Decrease spots: remove available spots only
            diff = current_count - target_spots
            available_spots = [s for s in current_spots if s.status == 'A']
            if len(available_spots) < diff:
                occupied_count = current_count - len(available_spots)
                return jsonify({
                    "error": f"Cannot decrease spots to {target_spots}. There are {occupied_count} occupied spots currently in use."
                }), 400
            
            # Delete surplus available spots from the highest numbers down
            available_spots.sort(key=lambda s: s.id, reverse=True)
            for s in available_spots[:diff]:
                db.session.delete(s)
                
        lot.number_of_spots = target_spots

    db.session.commit()
    
    # Invalidate cache
    cache.invalidate_prefix("lots_list")
    
    return jsonify({
        "message": "Parking lot updated successfully",
        "id": lot.id,
        "number_of_spots": lot.number_of_spots
    }), 200


@app.route('/api/parking-lots/<int:lot_id>', methods=['DELETE'])
@jwt_required()
def delete_parking_lot(lot_id):
    """Delete a parking lot and its spots (Admin only)"""
    current_user_id = int(get_jwt_identity())
    admin = User.query.get(current_user_id)
    if not admin or admin.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return jsonify({"error": "Parking lot not found"}), 404
        
    # Check if there are active reservations
    active_res = Reservation.query.join(ParkingSpot).filter(
        ParkingSpot.lot_id == lot.id,
        Reservation.status == 'active'
    ).count()
    
    if active_res > 0:
        return jsonify({"error": f"Cannot delete parking lot with {active_res} active reservation(s). Vacate spots first."}), 400
        
    db.session.delete(lot)
    db.session.commit()
    
    # Invalidate cache
    cache.invalidate_prefix("lots_list")
    
    return jsonify({"message": "Parking lot deleted successfully", "id": lot_id}), 200


# ==================== RESERVATION ROUTES ====================

@app.route('/api/reservations', methods=['POST'])
@jwt_required()
def create_reservation():
    """
    User books a parking spot:
    - User selects a parking lot
    - Spot is automatically allotted by the app (first available spot where status == 'A')
    - Spot status is updated to 'O' (Occupied)
    - Reservation is recorded with parking_timestamp
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data or not data.get('vehicle_number'):
        return jsonify({"error": "Vehicle number is required"}), 400
        
    vehicle_number = data.get('vehicle_number', '').strip().upper()
    lot_id = data.get('lot_id') or data.get('parking_lot_id')
    remarks = data.get('remarks', '').strip()
    
    # If specific spot_id was provided (compatibility), verify it; otherwise automatically allocate
    spot = None
    if lot_id:
        lot = ParkingLot.query.get(lot_id)
        if not lot:
            return jsonify({"error": "Parking lot not found"}), 404
        # Automatically allocate the first available spot
        spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='A').first()
    elif data.get('parking_spot_id') or data.get('spot_id'):
        spot_id = data.get('parking_spot_id') or data.get('spot_id')
        spot = ParkingSpot.query.get(spot_id)
        if spot and spot.status != 'A':
            spot = None
            
    if not spot:
        return jsonify({"error": "No available 4-wheeler parking spots in this lot"}), 400
        
    # Mark spot as Occupied ('O')
    spot.status = 'O'
    
    # Create reservation
    reservation = Reservation(
        spot_id=spot.id,
        user_id=current_user_id,
        vehicle_number=vehicle_number,
        parking_timestamp=datetime.utcnow(),
        status='active',
        remarks=remarks
    )
    
    db.session.add(reservation)
    db.session.commit()
    
    # Invalidate cache
    cache.invalidate_prefix("lots_list")
    
    return jsonify({
        "message": "Parking spot automatically allotted and booked successfully",
        "reservation_id": reservation.id,
        "spot_id": spot.id,
        "spot_number": spot.spot_number,
        "lot_name": spot.parking_lot.prime_location_name,
        "parking_timestamp": reservation.parking_timestamp.isoformat(),
        "status": reservation.status
    }), 201


@app.route('/api/reservations/<int:res_id>/vacate', methods=['POST'])
@jwt_required()
def vacate_reservation(res_id):
    """
    Release or vacate a parking spot:
    - Sets leaving_timestamp
    - Computes parking_cost based on lot's hourly price and duration
    - Marks reservation status as 'completed'
    - Returns spot status to 'A' (Available)
    """
    current_user_id = int(get_jwt_identity())
    reservation = Reservation.query.get(res_id)
    
    if not reservation:
        return jsonify({"error": "Reservation not found"}), 404
        
    user = User.query.get(current_user_id)
    if reservation.user_id != current_user_id and user.role != 'admin':
        return jsonify({"error": "Unauthorized to vacate this reservation"}), 403
        
    if reservation.status != 'active':
        return jsonify({"error": f"Reservation is already {reservation.status}"}), 400
        
    now = datetime.utcnow()
    reservation.leaving_timestamp = now
    reservation.status = 'completed'
    
    # Calculate duration and parking cost
    duration_hours = max((now - reservation.parking_timestamp).total_seconds() / 3600.0, 1.0)
    lot_price = reservation.parking_spot.parking_lot.price if reservation.parking_spot else 0.0
    reservation.parking_cost = round(duration_hours * lot_price, 2)
    
    # Release spot back to Available ('A')
    if reservation.parking_spot:
        reservation.parking_spot.status = 'A'
        
    db.session.commit()
    
    # Invalidate cache
    cache.invalidate_prefix("lots_list")
    
    return jsonify({
        "message": "Parking spot vacated and released successfully",
        "reservation_id": reservation.id,
        "spot_number": reservation.parking_spot.spot_number if reservation.parking_spot else '',
        "parking_timestamp": reservation.parking_timestamp.isoformat(),
        "leaving_timestamp": reservation.leaving_timestamp.isoformat(),
        "duration_hours": round(duration_hours, 2),
        "parking_cost": reservation.parking_cost,
        "status": reservation.status
    }), 200


@app.route('/api/reservations', methods=['GET'])
@jwt_required()
def get_reservations():
    """Get reservations for current user (or all reservations if admin)"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if user.role == 'admin' and request.args.get('all') == 'true':
        reservations = Reservation.query.order_by(Reservation.parking_timestamp.desc()).all()
    else:
        reservations = Reservation.query.filter_by(user_id=current_user_id).order_by(Reservation.parking_timestamp.desc()).all()
        
    result = []
    for r in reservations:
        spot = r.parking_spot
        lot = spot.parking_lot if spot else None
        result.append({
            "id": r.id,
            "spot_id": r.spot_id,
            "parking_spot_id": r.spot_id,
            "spot_number": spot.spot_number if spot else 'N/A',
            "lot_id": lot.id if lot else None,
            "lot_name": lot.prime_location_name if lot else 'N/A',
            "lot_price": lot.price if lot else 0.0,
            "vehicle_number": r.vehicle_number,
            "parking_timestamp": r.parking_timestamp.isoformat() if r.parking_timestamp else None,
            "start_time": r.parking_timestamp.isoformat() if r.parking_timestamp else None,
            "leaving_timestamp": r.leaving_timestamp.isoformat() if r.leaving_timestamp else None,
            "end_time": r.leaving_timestamp.isoformat() if r.leaving_timestamp else None,
            "parking_cost": r.parking_cost,
            "status": r.status,
            "remarks": r.remarks
        })
        
    return jsonify({
        "total": len(result),
        "reservations": result
    }), 200


@app.route('/api/reservations/<int:res_id>', methods=['DELETE'])
@jwt_required()
def cancel_reservation(res_id):
    """Cancel / Delete a reservation"""
    current_user_id = int(get_jwt_identity())
    reservation = Reservation.query.get(res_id)
    
    if not reservation:
        return jsonify({"error": "Reservation not found"}), 404
        
    user = User.query.get(current_user_id)
    if reservation.user_id != current_user_id and user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
        
    if reservation.status == 'active' and reservation.parking_spot:
        reservation.parking_spot.status = 'A'
        
    db.session.delete(reservation)
    db.session.commit()
    
    cache.invalidate_prefix("lots_list")
    return jsonify({"message": "Reservation deleted successfully", "reservation_id": res_id}), 200


# ==================== BACKEND JOBS & REPORTS ====================

@app.route('/api/export/csv', methods=['POST'])
@jwt_required()
def export_csv_job():
    """
    User-Triggered Async Job: Export as CSV
    Triggers a background batch job to generate a CSV export of user's parking history till date.
    """
    current_user_id = int(get_jwt_identity())
    job = trigger_csv_export(app, current_user_id)
    
    return jsonify({
        "message": "CSV Export job initiated in background",
        "job_id": job.id,
        "status": job.status
    }), 202


@app.route('/api/export/<job_id>/status', methods=['GET'])
@jwt_required()
def get_export_status(job_id):
    """Check status of a user-triggered CSV export job"""
    current_user_id = int(get_jwt_identity())
    job = ExportJob.query.get(job_id)
    
    if not job or job.user_id != current_user_id:
        return jsonify({"error": "Export job not found"}), 404
        
    return jsonify({
        "job_id": job.id,
        "status": job.status,
        "filename": job.filename,
        "download_url": f"/api/export/{job.id}/download" if job.status == 'completed' else None,
        "error": job.error_message
    }), 200


@app.route('/api/export/<job_id>/download', methods=['GET'])
@jwt_required()
def download_export_csv(job_id):
    """Download generated CSV file"""
    current_user_id = int(get_jwt_identity())
    job = ExportJob.query.get(job_id)
    
    if not job or job.user_id != current_user_id or job.status != 'completed' or not job.file_path:
        return jsonify({"error": "File not ready or job not found"}), 404
        
    if not os.path.exists(job.file_path):
        return jsonify({"error": "Export file not found on server"}), 404
        
    return send_file(
        job.file_path,
        mimetype='text/csv',
        as_attachment=True,
        download_name=job.filename or "parking_history.csv"
    )


@app.route('/api/reports/monthly', methods=['GET'])
@jwt_required()
def get_monthly_report():
    """
    Scheduled Job B: Monthly Activity Report
    Returns HTML report and activity parameters: spots booked, most used lot, total spent.
    """
    current_user_id = int(get_jwt_identity())
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    as_html = request.args.get('format') == 'html'
    
    report = generate_user_monthly_report(current_user_id, year, month)
    if not report:
        return jsonify({"error": "Report could not be generated"}), 500
        
    if as_html:
        response = make_response(report['html_content'])
        response.headers['Content-Type'] = 'text/html'
        return response
        
    return jsonify(report), 200


@app.route('/api/jobs/daily-reminders', methods=['POST'])
@jwt_required()
def trigger_daily_reminders():
    """
    Scheduled Job A: Daily Reminders
    Checks if users haven't visited or new parking lots created.
    Sends alerts to Google Chat Webhook or saves digest logs.
    """
    current_user_id = int(get_jwt_identity())
    admin = User.query.get(current_user_id)
    if not admin or admin.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403
        
    webhook_url = request.get_json().get('webhook_url') if request.is_json else None
    result = run_daily_reminders(app, webhook_url=webhook_url)
    return jsonify(result), 200


@app.route('/api/cache/stats', methods=['GET'])
@jwt_required()
def get_cache_stats():
    """API performance cache statistics"""
    current_user_id = int(get_jwt_identity())
    admin = User.query.get(current_user_id)
    if not admin or admin.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403
        
    return jsonify({
        "cache_hits": cache.stats['hits'],
        "cache_misses": cache.stats['misses'],
        "cached_entries_count": len(cache._cache)
    }), 200


# ==================== MAIN ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_admin()
    app.run(debug=True, port=5000)