import json
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


# ==================== PREDEFINED ACCOUNTS (ADMIN & COMPANY) ====================

def create_default_admin():
    """
    Ensure the superuser Admin and a demo Company exist whenever app initializes.
    """
    with app.app_context():
        # Superuser Admin
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
                role='admin',
                name="Platform Admin"
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Default superuser Admin created successfully!")
            
        # Demo Company Operator
        company_username = "company"
        existing_company = User.query.filter_by(username=company_username).first()
        if not existing_company:
            company_user = User(
                username=company_username,
                email="company@parkinghub.com",
                password_hash=generate_password_hash("company123"),
                role='company',
                name="Vikram Sharma",
                company_name="Apex Parking & Mobility Solutions",
                mobile_number="+91 98765 43210",
                description="Specializing in multi-tier automated commercial parking lots, EV charging bays, and handicap accessible spaces across metropolitan city centers.",
                address="Commercial Hub One, Sector 4, Outer Ring Road, Bangalore"
            )
            db.session.add(company_user)
            db.session.commit()
            print("Default Company Operator account created successfully!")
        else:
            company_user = existing_company

        # Assign existing unassigned lots to this company and initialize default layouts
        unassigned_lots = ParkingLot.query.filter_by(company_id=None).all()
        for lot in unassigned_lots:
            lot.company_id = company_user.id
            if not lot.grid_layout:
                # Default 5x6 layout: row 0 & 2 are parking, row 1 & 3 are roads, row 4 is parking & handicap
                rows, cols = 5, 6
                lot.grid_rows = rows
                lot.grid_cols = cols
                default_grid = []
                p_cnt = 0
                h_cnt = 0
                for r in range(rows):
                    row = []
                    for c in range(cols):
                        if r in [1, 3]:
                            row.append({'type': 'road'})
                        elif r == 4 and c in [0, 1]:
                            row.append({'type': 'handicap'})
                            h_cnt += 1
                        elif r == 4 and c == cols - 1:
                            row.append({'type': 'stairs'})
                        else:
                            row.append({'type': 'parking'})
                            p_cnt += 1
                    default_grid.append(row)
                lot.grid_layout = json.dumps(default_grid)
                lot.regular_spots = p_cnt
                lot.handicap_spots = h_cnt
                lot.number_of_spots = p_cnt + h_cnt
        db.session.commit()


# ==================== AUTH ROUTES ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user or company operator"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Missing request body"}), 400
        
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    requested_role = data.get('role', 'user').strip().lower()
    role = 'company' if requested_role == 'company' else 'user'
    
    name = data.get('name', '').strip() or username
    company_name = data.get('company_name', '').strip()
    mobile_number = data.get('mobile_number', '').strip()
    description = data.get('description', '').strip()
    address = data.get('address', '').strip()
    
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
    
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
        name=name,
        company_name=company_name or (name if role == 'company' else ''),
        mobile_number=mobile_number,
        description=description,
        address=address
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        "message": f"{'Company operator' if role == 'company' else 'User'} registered successfully",
        "user_id": user.id,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "name": user.name,
            "company_name": user.company_name,
            "mobile_number": user.mobile_number,
            "description": user.description,
            "address": user.address
        }
    }), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user, company operator, or admin and return JWT access token"""
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
    
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "name": user.name or user.username,
            "company_name": user.company_name or '',
            "mobile_number": user.mobile_number or '',
            "description": user.description or '',
            "address": user.address or ''
        }
    }), 200


@app.route('/api/auth/profile', methods=['GET', 'PUT'])
@app.route('/api/company/profile', methods=['GET', 'PUT'])
@jwt_required()
def handle_profile():
    """Get or update current profile (Company, User or Admin)"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    if request.method == 'PUT':
        data = request.get_json() or {}
        if 'name' in data:
            user.name = data['name'].strip()
        if 'company_name' in data:
            user.company_name = data['company_name'].strip()
        if 'mobile_number' in data:
            user.mobile_number = data['mobile_number'].strip()
        if 'description' in data:
            user.description = data['description'].strip()
        if 'address' in data:
            user.address = data['address'].strip()
        if 'email' in data and data['email'].strip():
            new_email = data['email'].strip().lower()
            # Verify uniqueness if email changed
            existing = User.query.filter(User.email == new_email, User.id != user.id).first()
            if existing:
                return jsonify({"error": "Email is already taken by another account"}), 409
            user.email = new_email
            
        db.session.commit()
    
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "name": user.name or user.username,
        "company_name": user.company_name or user.username,
        "mobile_number": user.mobile_number or '',
        "description": user.description or '',
        "address": user.address or '',
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
    
    # Real-time visual spots overview grouped by lot with layout grid
    lots_detail = []
    for lot in lots:
        spots = ParkingSpot.query.filter_by(lot_id=lot.id).order_by(ParkingSpot.id.asc()).all()
        
        # Build coordinate lookup if set
        spot_by_coord = {}
        for s in spots:
            if s.row_idx is not None and s.col_idx is not None:
                spot_by_coord[(s.row_idx, s.col_idx)] = s

        grid_data = None
        if lot.grid_layout:
            try:
                grid_data = json.loads(lot.grid_layout)
            except Exception:
                grid_data = None
                
        rows = lot.grid_rows or 5
        cols = lot.grid_cols or 6
        
        # If no grid_layout exists, generate a standard layout
        if not grid_data or not isinstance(grid_data, list):
            grid_data = []
            p_alloc = 0
            for r in range(rows):
                row = []
                for c in range(cols):
                    if r == 1:
                        row.append({'type': 'road'})
                    elif r == rows - 1 and c == 0:
                        row.append({'type': 'handicap'})
                    elif r == rows - 1 and c == cols - 1:
                        row.append({'type': 'stairs'})
                    elif p_alloc < len(spots):
                        row.append({'type': 'parking'})
                        p_alloc += 1
                    else:
                        row.append({'type': 'empty'})
                grid_data.append(row)
            lot.grid_layout = json.dumps(grid_data)
            lot.grid_rows = rows
            lot.grid_cols = cols
            db.session.commit()

        # Build enriched grid with real-time slot occupancy overlay
        roads_count = 0
        stairs_count = 0
        empty_count = 0
        enriched_grid = []
        reg_iter = iter([s for s in spots if s.spot_type != 'handicap'])
        handi_iter = iter([s for s in spots if s.spot_type == 'handicap'])
        all_iter = iter(spots)
        
        for r_idx, row in enumerate(grid_data):
            enriched_row = []
            for c_idx, cell in enumerate(row):
                ctype = cell.get('type') if isinstance(cell, dict) else str(cell)
                spot_obj = None
                
                if (r_idx, c_idx) in spot_by_coord:
                    sp = spot_by_coord[(r_idx, c_idx)]
                    spot_obj = {
                        "id": sp.id,
                        "spot_number": sp.spot_number,
                        "status": sp.status,
                        "spot_type": sp.spot_type
                    }
                elif ctype == 'parking':
                    sp = next(reg_iter, None) or next(all_iter, None)
                    if sp:
                        spot_obj = {
                            "id": sp.id,
                            "spot_number": sp.spot_number,
                            "status": sp.status,
                            "spot_type": sp.spot_type or 'regular'
                        }
                elif ctype == 'handicap':
                    sp = next(handi_iter, None) or next(all_iter, None)
                    if sp:
                        spot_obj = {
                            "id": sp.id,
                            "spot_number": sp.spot_number,
                            "status": sp.status,
                            "spot_type": 'handicap'
                        }
                elif ctype == 'road':
                    roads_count += 1
                elif ctype == 'stairs':
                    stairs_count += 1
                elif ctype == 'empty':
                    empty_count += 1
                    
                enriched_row.append({
                    "type": ctype,
                    "row": r_idx,
                    "col": c_idx,
                    "spot": spot_obj
                })
            enriched_grid.append(enriched_row)
            
        lots_detail.append({
            "id": lot.id,
            "prime_location_name": lot.prime_location_name,
            "price": lot.price,
            "address": lot.address,
            "pin_code": lot.pin_code,
            "number_of_spots": lot.number_of_spots,
            "available_count": sum(1 for s in spots if s.status == 'A'),
            "occupied_count": sum(1 for s in spots if s.status == 'O'),
            "regular_spots": sum(1 for s in spots if s.spot_type != 'handicap'),
            "handicap_spots": sum(1 for s in spots if s.spot_type == 'handicap'),
            "regular_available": sum(1 for s in spots if s.status == 'A' and s.spot_type != 'handicap'),
            "handicap_available": sum(1 for s in spots if s.status == 'A' and s.spot_type == 'handicap'),
            "roads_count": roads_count,
            "stairs_count": stairs_count,
            "empty_count": empty_count,
            "grid_rows": rows,
            "grid_cols": cols,
            "grid_layout": enriched_grid,
            "spots": [
                {
                    "id": s.id,
                    "spot_number": s.spot_number,
                    "status": s.status,
                    "spot_type": s.spot_type or 'regular',
                    "row_idx": s.row_idx,
                    "col_idx": s.col_idx
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


# ==================== COMPANY & PARKING LOT ROUTES ====================

@app.route('/api/company/dashboard', methods=['GET'])
@jwt_required()
def get_company_dashboard():
    """
    Company Operator Dashboard:
    - Statistics of company's lots, spots, occupancy, and active reservations
    - Detailed lot information including grid layouts and slot configurations
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user or user.role not in ['company', 'admin']:
        return jsonify({"error": "Company operator or admin access required"}), 403
        
    if user.role == 'admin':
        lots = ParkingLot.query.all()
    else:
        lots = ParkingLot.query.filter_by(company_id=user.id).all()
        # If no lots are assigned specifically, associate existing unassigned lots
        if not lots:
            unassigned = ParkingLot.query.filter_by(company_id=None).all()
            for l in unassigned:
                l.company_id = user.id
            if unassigned:
                db.session.commit()
                lots = ParkingLot.query.filter_by(company_id=user.id).all()
                
    lot_ids = [l.id for l in lots]
    all_spots = ParkingSpot.query.filter(ParkingSpot.lot_id.in_(lot_ids)).all() if lot_ids else []
    
    total_spots = len(all_spots)
    available_spots = sum(1 for s in all_spots if s.status == 'A')
    occupied_spots = sum(1 for s in all_spots if s.status == 'O')
    regular_spots = sum(1 for s in all_spots if s.spot_type != 'handicap')
    handicap_spots = sum(1 for s in all_spots if s.spot_type == 'handicap')
    
    active_reservations = Reservation.query.join(ParkingSpot).filter(
        ParkingSpot.lot_id.in_(lot_ids),
        Reservation.status == 'active'
    ).count() if lot_ids else 0
    
    total_revenue = db.session.query(db.func.sum(Reservation.parking_cost)).join(ParkingSpot).filter(
        ParkingSpot.lot_id.in_(lot_ids)
    ).scalar() or 0.0 if lot_ids else 0.0
    
    lots_detail = []
    for lot in lots:
        l_spots = [s for s in all_spots if s.lot_id == lot.id]
        grid_data = None
        if lot.grid_layout:
            try:
                grid_data = json.loads(lot.grid_layout)
            except Exception:
                grid_data = None
                
        lots_detail.append({
            "id": lot.id,
            "prime_location_name": lot.prime_location_name,
            "name": lot.prime_location_name,
            "price": lot.price,
            "address": lot.address,
            "location": lot.address,
            "pin_code": lot.pin_code,
            "number_of_spots": lot.number_of_spots,
            "total_spots": lot.number_of_spots,
            "regular_spots": sum(1 for s in l_spots if s.spot_type != 'handicap'),
            "handicap_spots": sum(1 for s in l_spots if s.spot_type == 'handicap'),
            "available_spots": sum(1 for s in l_spots if s.status == 'A'),
            "occupied_spots": sum(1 for s in l_spots if s.status == 'O'),
            "regular_available": sum(1 for s in l_spots if s.status == 'A' and s.spot_type != 'handicap'),
            "handicap_available": sum(1 for s in l_spots if s.status == 'A' and s.spot_type == 'handicap'),
            "grid_rows": lot.grid_rows or 5,
            "grid_cols": lot.grid_cols or 6,
            "grid_layout": grid_data,
            "spots": [
                {
                    "id": s.id,
                    "spot_number": s.spot_number,
                    "status": s.status,
                    "spot_type": s.spot_type or 'regular',
                    "row_idx": s.row_idx,
                    "col_idx": s.col_idx
                }
                for s in sorted(l_spots, key=lambda x: x.id)
            ]
        })
        
    return jsonify({
        "statistics": {
            "total_lots": len(lots),
            "total_spots": total_spots,
            "available_spots": available_spots,
            "occupied_spots": occupied_spots,
            "regular_spots": regular_spots,
            "handicap_spots": handicap_spots,
            "active_reservations": active_reservations,
            "total_revenue": round(total_revenue, 2)
        },
        "lots": lots_detail
    }), 200


@app.route('/api/company/lots', methods=['GET'])
@jwt_required()
def get_company_lots():
    """Get lots owned by current company"""
    return get_company_dashboard()


@app.route('/api/parking-lots', methods=['GET'])
@cached(timeout=60, key_prefix="lots_list")
def get_parking_lots():
    """
    Get all parking lots with real-time available and occupied spot counts,
    including regular and handicap counts.
    """
    lots = ParkingLot.query.all()
    result = []
    
    for lot in lots:
        spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
        available = sum(1 for s in spots if s.status == 'A')
        occupied = sum(1 for s in spots if s.status == 'O')
        regular_avail = sum(1 for s in spots if s.status == 'A' and s.spot_type != 'handicap')
        handicap_avail = sum(1 for s in spots if s.status == 'A' and s.spot_type == 'handicap')
        regular_total = sum(1 for s in spots if s.spot_type != 'handicap')
        handicap_total = sum(1 for s in spots if s.spot_type == 'handicap')
        
        result.append({
            "id": lot.id,
            "prime_location_name": lot.prime_location_name,
            "name": lot.prime_location_name,
            "price": lot.price,
            "address": lot.address,
            "location": lot.address,
            "pin_code": lot.pin_code,
            "number_of_spots": lot.number_of_spots,
            "total_spots": lot.number_of_spots,
            "available_spots": available,
            "occupied_spots": occupied,
            "regular_spots": regular_total,
            "handicap_spots": handicap_total,
            "regular_available_spots": regular_avail,
            "handicap_available_spots": handicap_avail,
            "grid_rows": lot.grid_rows or 5,
            "grid_cols": lot.grid_cols or 6
        })
    
    return jsonify({
        "total": len(result),
        "parking_lots": result
    }), 200


@app.route('/api/parking-lots/<int:lot_id>', methods=['GET'])
def get_parking_lot(lot_id):
    """Get parking lot details, grid structure and its parking spots"""
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return jsonify({"error": "Parking lot not found"}), 404
    
    spots = ParkingSpot.query.filter_by(lot_id=lot.id).order_by(ParkingSpot.id.asc()).all()
    available = sum(1 for s in spots if s.status == 'A')
    occupied = sum(1 for s in spots if s.status == 'O')
    regular_avail = sum(1 for s in spots if s.status == 'A' and s.spot_type != 'handicap')
    handicap_avail = sum(1 for s in spots if s.status == 'A' and s.spot_type == 'handicap')
    
    grid_data = None
    if lot.grid_layout:
        try:
            grid_data = json.loads(lot.grid_layout)
        except Exception:
            grid_data = None
            
    return jsonify({
        "id": lot.id,
        "prime_location_name": lot.prime_location_name,
        "name": lot.prime_location_name,
        "price": lot.price,
        "address": lot.address,
        "location": lot.address,
        "pin_code": lot.pin_code,
        "number_of_spots": lot.number_of_spots,
        "total_spots": lot.number_of_spots,
        "regular_spots": sum(1 for s in spots if s.spot_type != 'handicap'),
        "handicap_spots": sum(1 for s in spots if s.spot_type == 'handicap'),
        "available_spots": available,
        "occupied_spots": occupied,
        "regular_available": regular_avail,
        "handicap_available": handicap_avail,
        "grid_rows": lot.grid_rows or 5,
        "grid_cols": lot.grid_cols or 6,
        "grid_layout": grid_data,
        "spots": [
            {
                "id": s.id,
                "spot_number": s.spot_number,
                "status": s.status,
                "spot_type": s.spot_type or 'regular',
                "row_idx": s.row_idx,
                "col_idx": s.col_idx
            }
            for s in spots
        ]
    }), 200


@app.route('/api/parking-lots', methods=['POST'])
@app.route('/api/company/lots', methods=['POST'])
@jwt_required()
def create_parking_lot():
    """
    Create a new parking space (Admin or Company).
    Accepts name, cost/price, address, pin code, grid dimensions, and grid layout.
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user or user.role not in ['admin', 'company']:
        return jsonify({"error": "Admin or Company access required"}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing request body"}), 400
        
    prime_location_name = data.get('prime_location_name') or data.get('name')
    address = data.get('address') or data.get('location') or "Main Facility"
    pin_code = str(data.get('pin_code') or '560001')
    price = float(data.get('price', 0.0))
    grid_rows = int(data.get('grid_rows', 5))
    grid_cols = int(data.get('grid_cols', 6))
    grid_layout = data.get('grid_layout')
    
    if not prime_location_name:
        return jsonify({"error": "Parking space name is required"}), 400
        
    # Analyze clickable grid if provided
    parking_cells = []
    handicap_cells = []
    parsed_layout = None
    
    if grid_layout:
        if isinstance(grid_layout, str):
            try:
                parsed_layout = json.loads(grid_layout)
            except Exception:
                parsed_layout = None
        elif isinstance(grid_layout, list):
            parsed_layout = grid_layout
            
        if parsed_layout:
            for r_idx, row in enumerate(parsed_layout):
                for c_idx, cell in enumerate(row):
                    ctype = cell.get('type') if isinstance(cell, dict) else str(cell)
                    if ctype == 'parking':
                        parking_cells.append((r_idx, c_idx))
                    elif ctype == 'handicap':
                        handicap_cells.append((r_idx, c_idx))
                        
    total_slots = len(parking_cells) + len(handicap_cells)
    
    # If no grid layout provided, generate standard layout from number_of_spots
    if total_slots == 0:
        total_slots = int(data.get('number_of_spots') or data.get('total_spots') or 10)
        grid_rows = max(3, (total_slots + 3) // 4 + 1)
        grid_cols = 5
        parsed_layout = []
        p_count = 0
        h_target = max(1, total_slots // 5)
        for r in range(grid_rows):
            row = []
            for c in range(grid_cols):
                if r == 1:
                    row.append({'type': 'road'})
                elif len(handicap_cells) < h_target and p_count >= (total_slots - h_target):
                    row.append({'type': 'handicap'})
                    handicap_cells.append((r, c))
                elif p_count < (total_slots - h_target):
                    row.append({'type': 'parking'})
                    parking_cells.append((r, c))
                    p_count += 1
                else:
                    row.append({'type': 'empty'})
            parsed_layout.append(row)
        total_slots = len(parking_cells) + len(handicap_cells)
        
    lot = ParkingLot(
        company_id=user.id if user.role == 'company' else None,
        prime_location_name=prime_location_name,
        price=price,
        address=address,
        pin_code=pin_code,
        number_of_spots=total_slots,
        regular_spots=len(parking_cells),
        handicap_spots=len(handicap_cells),
        grid_rows=grid_rows,
        grid_cols=grid_cols,
        grid_layout=json.dumps(parsed_layout) if parsed_layout else None
    )
    db.session.add(lot)
    db.session.flush()
    
    # Create spots
    for i, (r, c) in enumerate(parking_cells, start=1):
        spot = ParkingSpot(
            lot_id=lot.id,
            spot_number=f"P-{i}",
            spot_type='regular',
            row_idx=r,
            col_idx=c,
            status='A'
        )
        db.session.add(spot)
        
    for j, (r, c) in enumerate(handicap_cells, start=1):
        spot = ParkingSpot(
            lot_id=lot.id,
            spot_number=f"H-{j}",
            spot_type='handicap',
            row_idx=r,
            col_idx=c,
            status='A'
        )
        db.session.add(spot)
        
    db.session.commit()
    cache.invalidate_prefix("lots_list")
    
    return jsonify({
        "message": "Parking space created successfully",
        "id": lot.id,
        "number_of_spots": total_slots,
        "regular_spots": len(parking_cells),
        "handicap_spots": len(handicap_cells)
    }), 201


@app.route('/api/parking-lots/<int:lot_id>', methods=['PUT'])
@app.route('/api/company/lots/<int:lot_id>', methods=['PUT'])
@jwt_required()
def edit_parking_lot(lot_id):
    """
    Edit a parking lot (Admin or Company Operator).
    Supports editing:
    1) Name of slot/space
    2) Cost of parking
    3) Grid size (row and column info)
    4) Grid space (clickable grid: parking, road, stairs, handicap)
    The number of parking space + handicap space is added and saved as number_of_spots.
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user or user.role not in ['admin', 'company']:
        return jsonify({"error": "Admin or Company access required"}), 403
    
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return jsonify({"error": "Parking lot not found"}), 404
        
    # Check ownership if company
    if user.role == 'company' and lot.company_id and lot.company_id != user.id:
        return jsonify({"error": "Unauthorized to edit this parking lot"}), 403
        
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing request body"}), 400
        
    # 1) Edit name of slot / space
    if 'prime_location_name' in data and data['prime_location_name']:
        lot.prime_location_name = data['prime_location_name'].strip()
    elif 'name' in data and data['name']:
        lot.prime_location_name = data['name'].strip()
        
    # 2) Edit cost of parking
    if 'price' in data and data['price'] is not None:
        lot.price = float(data['price'])
        
    if 'address' in data and data['address']:
        lot.address = data['address'].strip()
    elif 'location' in data and data['location']:
        lot.address = data['location'].strip()
        
    if 'pin_code' in data and data['pin_code']:
        lot.pin_code = str(data['pin_code']).strip()
        
    # 3) Edit grid size & 4) Edit grid space
    grid_layout_raw = data.get('grid_layout')
    grid_rows = data.get('grid_rows')
    grid_cols = data.get('grid_cols')
    
    if grid_rows is not None:
        lot.grid_rows = int(grid_rows)
    if grid_cols is not None:
        lot.grid_cols = int(grid_cols)
        
    if grid_layout_raw is not None:
        parsed_layout = None
        if isinstance(grid_layout_raw, str):
            try:
                parsed_layout = json.loads(grid_layout_raw)
            except Exception:
                parsed_layout = []
        elif isinstance(grid_layout_raw, list):
            parsed_layout = grid_layout_raw
            
        parking_cells = []
        handicap_cells = []
        
        if parsed_layout:
            for r_idx, row in enumerate(parsed_layout):
                for c_idx, cell in enumerate(row):
                    ctype = cell.get('type') if isinstance(cell, dict) else str(cell)
                    if ctype == 'parking':
                        parking_cells.append((r_idx, c_idx))
                    elif ctype == 'handicap':
                        handicap_cells.append((r_idx, c_idx))
                        
        total_slots = len(parking_cells) + len(handicap_cells)
        if total_slots <= 0:
            return jsonify({"error": "Grid must include at least 1 Parking space or Handicap space."}), 400
            
        # Check occupied spots
        current_spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
        occupied_spots = [s for s in current_spots if s.status == 'O']
        if len(occupied_spots) > total_slots:
            return jsonify({
                "error": f"Cannot resize to {total_slots} slots. There are currently {len(occupied_spots)} occupied spots in use."
            }), 400
            
        lot.grid_layout = json.dumps(parsed_layout)
        lot.number_of_spots = total_slots
        lot.regular_spots = len(parking_cells)
        lot.handicap_spots = len(handicap_cells)
        
        # Build desired spot configurations
        desired = []
        for idx, (r, c) in enumerate(parking_cells, start=1):
            desired.append({
                "spot_number": f"P-{idx}",
                "spot_type": "regular",
                "row_idx": r,
                "col_idx": c
            })
        for idx, (r, c) in enumerate(handicap_cells, start=1):
            desired.append({
                "spot_number": f"H-{idx}",
                "spot_type": "handicap",
                "row_idx": r,
                "col_idx": c
            })
            
        # Update existing spots safely to preserve foreign keys
        for idx, des in enumerate(desired):
            if idx < len(current_spots):
                sp = current_spots[idx]
                sp.spot_number = des["spot_number"]
                sp.spot_type = des["spot_type"]
                sp.row_idx = des["row_idx"]
                sp.col_idx = des["col_idx"]
            else:
                new_sp = ParkingSpot(
                    lot_id=lot.id,
                    spot_number=des["spot_number"],
                    spot_type=des["spot_type"],
                    row_idx=des["row_idx"],
                    col_idx=des["col_idx"],
                    status='A'
                )
                db.session.add(new_sp)
                
        # If surplus available spots exist, remove them
        if len(current_spots) > len(desired):
            surplus = current_spots[len(desired):]
            for sp in surplus:
                if sp.status == 'A':
                    db.session.delete(sp)
                    
    elif data.get('number_of_spots') or data.get('total_spots'):
        # Fallback manual number_of_spots change
        target = int(data.get('number_of_spots') or data.get('total_spots'))
        if target <= 0:
            return jsonify({"error": "Number of spots must be at least 1"}), 400
        current_spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
        current_count = len(current_spots)
        if target > current_count:
            for i in range(current_count + 1, target + 1):
                db.session.add(ParkingSpot(lot_id=lot.id, spot_number=f"Spot-{i}", status='A', spot_type='regular'))
        elif target < current_count:
            diff = current_count - target
            avail = [s for s in current_spots if s.status == 'A']
            if len(avail) < diff:
                return jsonify({"error": f"Cannot decrease spots: {current_count - len(avail)} spots are currently occupied."}), 400
            avail.sort(key=lambda s: s.id, reverse=True)
            for s in avail[:diff]:
                db.session.delete(s)
        lot.number_of_spots = target

    db.session.commit()
    cache.invalidate_prefix("lots_list")
    
    return jsonify({
        "message": "Parking lot and slot configuration updated successfully",
        "id": lot.id,
        "name": lot.prime_location_name,
        "price": lot.price,
        "number_of_spots": lot.number_of_spots,
        "regular_spots": lot.regular_spots,
        "handicap_spots": lot.handicap_spots
    }), 200


@app.route('/api/parking-lots/<int:lot_id>', methods=['DELETE'])
@app.route('/api/company/lots/<int:lot_id>', methods=['DELETE'])
@jwt_required()
def delete_parking_lot(lot_id):
    """Delete a parking lot and its spots (Admin or Company owner)"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user or user.role not in ['admin', 'company']:
        return jsonify({"error": "Admin or Company access required"}), 403
    
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return jsonify({"error": "Parking lot not found"}), 404
        
    if user.role == 'company' and lot.company_id and lot.company_id != user.id:
        return jsonify({"error": "Unauthorized to delete this parking lot"}), 403
        
    # Check if there are active reservations
    active_res = Reservation.query.join(ParkingSpot).filter(
        ParkingSpot.lot_id == lot.id,
        Reservation.status == 'active'
    ).count()
    
    if active_res > 0:
        return jsonify({"error": f"Cannot delete parking lot with {active_res} active reservation(s). Vacate spots first."}), 400
        
    db.session.delete(lot)
    db.session.commit()
    cache.invalidate_prefix("lots_list")
    
    return jsonify({"message": "Parking lot deleted successfully", "id": lot_id}), 200


# ==================== RESERVATION ROUTES ====================

@app.route('/api/reservations', methods=['POST'])
@jwt_required()
def create_reservation():
    """
    User books a parking spot:
    - User selects a parking lot
    - Users can book regular or handicap parking
    - Spot is automatically allotted based on spot_type (regular / handicap)
    - Spot status updated to 'O' (Occupied)
    - Reservation recorded with parking_timestamp and spot_type
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data or not data.get('vehicle_number'):
        return jsonify({"error": "Vehicle number is required"}), 400
        
    vehicle_number = data.get('vehicle_number', '').strip().upper()
    lot_id = data.get('lot_id') or data.get('parking_lot_id')
    remarks = data.get('remarks', '').strip()
    requested_type = data.get('spot_type', 'regular').strip().lower()
    if requested_type not in ['regular', 'handicap']:
        requested_type = 'regular'
    
    spot = None
    if lot_id:
        lot = ParkingLot.query.get(lot_id)
        if not lot:
            return jsonify({"error": "Parking lot not found"}), 404
            
        # Find first available spot matching the requested spot type
        spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='A', spot_type=requested_type).first()
        if not spot:
            type_label = "Handicap (Accessible)" if requested_type == 'handicap' else "Regular"
            return jsonify({"error": f"No available {type_label} parking spots in this lot."}), 400
            
    elif data.get('parking_spot_id') or data.get('spot_id'):
        spot_id = data.get('parking_spot_id') or data.get('spot_id')
        spot = ParkingSpot.query.get(spot_id)
        if spot and spot.status != 'A':
            spot = None
        if not spot:
            return jsonify({"error": "Selected spot is not available"}), 400
        requested_type = spot.spot_type or 'regular'
            
    if not spot:
        return jsonify({"error": "No available parking spots in this lot"}), 400
        
    # Mark spot as Occupied ('O')
    spot.status = 'O'
    
    # Create reservation
    reservation = Reservation(
        spot_id=spot.id,
        user_id=current_user_id,
        vehicle_number=vehicle_number,
        spot_type=requested_type,
        parking_timestamp=datetime.utcnow(),
        status='active',
        remarks=remarks
    )
    
    db.session.add(reservation)
    db.session.commit()
    
    cache.invalidate_prefix("lots_list")
    
    return jsonify({
        "message": f"{'Handicap' if requested_type == 'handicap' else 'Regular'} parking spot automatically allotted and booked successfully",
        "reservation_id": reservation.id,
        "spot_id": spot.id,
        "spot_number": spot.spot_number,
        "spot_type": spot.spot_type,
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
            "spot_type": r.spot_type or (spot.spot_type if spot else 'regular'),
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