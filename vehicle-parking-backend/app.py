import json
import os
import re
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify, request, send_file, make_response
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

import config
from models import db, User, ParkingLot, ParkingSpot, Reservation, ExportJob, DailyReminderLog, ParkingFloor, Vehicle
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


# ==================== PREDEFINED ACCOUNTS & MULTI-FLOOR SCHEMA SYNC ====================

def format_iso(dt):
    """Serialize a datetime object to standard ISO 8601 string with UTC timezone offset (+00:00)"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def format_duration(seconds):
    """Format duration in seconds into human-readable string (e.g., '2d 5h 30m', '1h 15m', or '45s')"""
    if seconds is None or seconds <= 0:
        return "0s"
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if not parts or (days == 0 and hours == 0 and minutes < 3):
        parts.append(f"{secs}s")
    return " ".join(parts)

def serialize_floor(floor):
    """Serialize a ParkingFloor with its spots, layout, and availability counts"""
    spots = [s for s in floor.spots]
    grid_data = None
    if floor.grid_layout:
        try:
            grid_data = json.loads(floor.grid_layout)
        except Exception:
            grid_data = None
            
    available = sum(1 for s in spots if s.status == 'A')
    occupied = sum(1 for s in spots if s.status == 'O')
    regular_avail = sum(1 for s in spots if s.status == 'A' and s.spot_type != 'handicap')
    handicap_avail = sum(1 for s in spots if s.status == 'A' and s.spot_type == 'handicap')
    
    return {
        "id": floor.id,
        "lot_id": floor.lot_id,
        "floor_number": floor.floor_number,
        "floor_name": floor.floor_name,
        "grid_rows": floor.grid_rows or 5,
        "grid_cols": floor.grid_cols or 6,
        "grid_layout": grid_data,
        "regular_spots": floor.regular_spots or 0,
        "handicap_spots": floor.handicap_spots or 0,
        "total_spots": (floor.regular_spots or 0) + (floor.handicap_spots or 0),
        "available_spots": available,
        "occupied_spots": occupied,
        "regular_available": regular_avail,
        "handicap_available": handicap_avail,
        "spots": [
            {
                "id": s.id,
                "spot_number": s.spot_number,
                "status": s.status,
                "spot_type": s.spot_type or 'regular',
                "row_idx": s.row_idx,
                "col_idx": s.col_idx,
                "floor_id": s.floor_id,
                "floor_number": s.floor_number,
                "floor_name": s.floor_name
            }
            for s in sorted(spots, key=lambda x: (x.row_idx if x.row_idx is not None else 0, x.col_idx if x.col_idx is not None else 0, x.id))
        ]
    }


def create_default_admin():
    """
    Ensure the superuser Admin, demo Company, and multi-floor structures exist whenever app initializes.
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

        # Synchronize default floors for any lots lacking ParkingFloor records
        all_lots = ParkingLot.query.all()
        for lot in all_lots:
            existing_floors = ParkingFloor.query.filter_by(lot_id=lot.id).all()
            if not existing_floors:
                g_floor = ParkingFloor(
                    lot_id=lot.id,
                    floor_number=0,
                    floor_name="Ground Floor",
                    grid_rows=lot.grid_rows or 5,
                    grid_cols=lot.grid_cols or 6,
                    grid_layout=lot.grid_layout,
                    regular_spots=lot.regular_spots or 0,
                    handicap_spots=lot.handicap_spots or 0
                )
                db.session.add(g_floor)
                db.session.flush()
                # Link existing spots to this floor
                lot_spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
                for s in lot_spots:
                    s.floor_id = g_floor.id
                    s.floor_number = 0
                    s.floor_name = "Ground Floor"
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
    user.last_visited_at = datetime.now(timezone.utc)
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
    user = db.session.get(User, current_user_id)
    
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
        "created_at": format_iso(user.created_at)
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
    admin = db.session.get(User, current_user_id)
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
            
        # Build enriched floors for multi-floor visualization
        enriched_floors = []
        for fl in sorted(lot.floors, key=lambda x: x.floor_number):
            fl_spots = [s for s in fl.spots]
            fl_spot_by_coord = {}
            for s in fl_spots:
                if s.row_idx is not None and s.col_idx is not None:
                    fl_spot_by_coord[(s.row_idx, s.col_idx)] = s
                    
            fl_grid_data = None
            if fl.grid_layout:
                try:
                    fl_grid_data = json.loads(fl.grid_layout)
                except Exception:
                    fl_grid_data = None
            if not fl_grid_data or not isinstance(fl_grid_data, list):
                fl_grid_data = []
                
            fl_roads = 0
            fl_stairs = 0
            fl_ramps_up = 0
            fl_ramps_down = 0
            fl_elevators = 0
            fl_empty = 0
            fl_enriched_grid = []
            
            fl_reg_iter = iter([s for s in fl_spots if s.spot_type != 'handicap'])
            fl_handi_iter = iter([s for s in fl_spots if s.spot_type == 'handicap'])
            fl_all_iter = iter(fl_spots)
            
            for r_idx, row in enumerate(fl_grid_data):
                enriched_row = []
                for c_idx, cell in enumerate(row):
                    ctype = cell.get('type') if isinstance(cell, dict) else str(cell)
                    spot_obj = None
                    if (r_idx, c_idx) in fl_spot_by_coord:
                        sp = fl_spot_by_coord[(r_idx, c_idx)]
                        spot_obj = {
                            "id": sp.id,
                            "spot_number": sp.spot_number,
                            "status": sp.status,
                            "spot_type": sp.spot_type
                        }
                    elif ctype == 'parking':
                        sp = next(fl_reg_iter, None) or next(fl_all_iter, None)
                        if sp:
                            spot_obj = {
                                "id": sp.id,
                                "spot_number": sp.spot_number,
                                "status": sp.status,
                                "spot_type": sp.spot_type or 'regular'
                            }
                    elif ctype == 'handicap':
                        sp = next(fl_handi_iter, None) or next(fl_all_iter, None)
                        if sp:
                            spot_obj = {
                                "id": sp.id,
                                "spot_number": sp.spot_number,
                                "status": sp.status,
                                "spot_type": 'handicap'
                            }
                    elif ctype == 'road':
                        fl_roads += 1
                    elif ctype == 'stairs':
                        fl_stairs += 1
                    elif ctype == 'ramp_up':
                        fl_ramps_up += 1
                    elif ctype == 'ramp_down':
                        fl_ramps_down += 1
                    elif ctype == 'elevator':
                        fl_elevators += 1
                    elif ctype == 'empty':
                        fl_empty += 1
                        
                    enriched_row.append({
                        "type": ctype,
                        "row": r_idx,
                        "col": c_idx,
                        "spot": spot_obj
                    })
                fl_enriched_grid.append(enriched_row)
                
            enriched_floors.append({
                "id": fl.id,
                "floor_number": fl.floor_number,
                "floor_name": fl.floor_name,
                "grid_rows": fl.grid_rows or 5,
                "grid_cols": fl.grid_cols or 6,
                "grid_layout": fl_enriched_grid,
                "regular_spots": sum(1 for s in fl_spots if s.spot_type != 'handicap'),
                "handicap_spots": sum(1 for s in fl_spots if s.spot_type == 'handicap'),
                "available_count": sum(1 for s in fl_spots if s.status == 'A'),
                "occupied_count": sum(1 for s in fl_spots if s.status == 'O'),
                "roads_count": fl_roads,
                "stairs_count": fl_stairs,
                "ramp_up_count": fl_ramps_up,
                "ramp_down_count": fl_ramps_down,
                "elevator_count": fl_elevators,
                "empty_count": fl_empty,
                "spots": [
                    {
                        "id": s.id,
                        "spot_number": s.spot_number,
                        "status": s.status,
                        "spot_type": s.spot_type or 'regular',
                        "row_idx": s.row_idx,
                        "col_idx": s.col_idx
                    }
                    for s in fl_spots
                ]
            })

        lots_detail.append({
            "id": lot.id,
            "prime_location_name": lot.prime_location_name,
            "price": lot.price,
            "daily_rate": lot.daily_rate or 0.0,
            "overnight_rate": lot.overnight_rate or 0.0,
            "peak_multiplier": lot.peak_multiplier or 1.0,
            "grace_period_minutes": lot.grace_period_minutes if lot.grace_period_minutes is not None else 15,
            "overstay_penalty_rate": lot.overstay_penalty_rate if lot.overstay_penalty_rate is not None else 50.0,
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
            "floors": enriched_floors,
            "floor_count": len(enriched_floors),
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
    admin_user = db.session.get(User, current_user_id)
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
                "created_at": format_iso(u.created_at)
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
    user = db.session.get(User, current_user_id)
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
            "daily_rate": lot.daily_rate or 0.0,
            "overnight_rate": lot.overnight_rate or 0.0,
            "peak_multiplier": lot.peak_multiplier or 1.0,
            "grace_period_minutes": lot.grace_period_minutes if lot.grace_period_minutes is not None else 15,
            "overstay_penalty_rate": lot.overstay_penalty_rate if lot.overstay_penalty_rate is not None else 50.0,
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
            "floors": [serialize_floor(f) for f in sorted(lot.floors, key=lambda f: f.floor_number)],
            "floor_count": len(lot.floors),
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
            "daily_rate": lot.daily_rate or 0.0,
            "overnight_rate": lot.overnight_rate or 0.0,
            "peak_multiplier": lot.peak_multiplier or 1.0,
            "grace_period_minutes": lot.grace_period_minutes if lot.grace_period_minutes is not None else 15,
            "overstay_penalty_rate": lot.overstay_penalty_rate if lot.overstay_penalty_rate is not None else 50.0,
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
            "grid_cols": lot.grid_cols or 6,
            "floors": [serialize_floor(f) for f in sorted(lot.floors, key=lambda f: f.floor_number)],
            "floor_count": len(lot.floors)
        })
    
    return jsonify({
        "total": len(result),
        "parking_lots": result
    }), 200


@app.route('/api/parking-lots/<int:lot_id>', methods=['GET'])
def get_parking_lot(lot_id):
    """Get parking lot details, grid structure and its parking spots"""
    lot = db.session.get(ParkingLot, lot_id)
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
        "daily_rate": lot.daily_rate or 0.0,
        "overnight_rate": lot.overnight_rate or 0.0,
        "peak_multiplier": lot.peak_multiplier or 1.0,
        "grace_period_minutes": lot.grace_period_minutes if lot.grace_period_minutes is not None else 15,
        "overstay_penalty_rate": lot.overstay_penalty_rate if lot.overstay_penalty_rate is not None else 50.0,
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
        "floors": [serialize_floor(f) for f in sorted(lot.floors, key=lambda f: f.floor_number)],
        "floor_count": len(lot.floors),
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
    user = db.session.get(User, current_user_id)
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
        daily_rate=float(data.get('daily_rate', 0.0) or 0.0),
        overnight_rate=float(data.get('overnight_rate', 0.0) or 0.0),
        peak_multiplier=float(data.get('peak_multiplier', 1.0) or 1.0),
        grace_period_minutes=int(data.get('grace_period_minutes', 15) or 15),
        overstay_penalty_rate=float(data.get('overstay_penalty_rate', 50.0) or 50.0),
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

    # Create default Ground Floor for multi-floor facility support
    g_floor = ParkingFloor(
        lot_id=lot.id,
        floor_number=0,
        floor_name="Ground Floor",
        grid_rows=grid_rows,
        grid_cols=grid_cols,
        grid_layout=json.dumps(parsed_layout) if parsed_layout else None,
        regular_spots=len(parking_cells),
        handicap_spots=len(handicap_cells)
    )
    db.session.add(g_floor)
    db.session.flush()
    
    # Create spots linked to Ground Floor
    for i, (r, c) in enumerate(parking_cells, start=1):
        spot = ParkingSpot(
            lot_id=lot.id,
            floor_id=g_floor.id,
            floor_number=0,
            floor_name="Ground Floor",
            spot_number=f"G-P{i}",
            spot_type='regular',
            row_idx=r,
            col_idx=c,
            status='A'
        )
        db.session.add(spot)
        
    for j, (r, c) in enumerate(handicap_cells, start=1):
        spot = ParkingSpot(
            lot_id=lot.id,
            floor_id=g_floor.id,
            floor_number=0,
            floor_name="Ground Floor",
            spot_number=f"G-H{j}",
            spot_type='handicap',
            row_idx=r,
            col_idx=c,
            status='A'
        )
        db.session.add(spot)
        
    db.session.commit()
    cache.invalidate_prefix("lots_list")
    
    return jsonify({
        "message": "Parking space created successfully with Ground Floor",
        "id": lot.id,
        "number_of_spots": total_slots,
        "regular_spots": len(parking_cells),
        "handicap_spots": len(handicap_cells),
        "floors": [serialize_floor(g_floor)]
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
    user = db.session.get(User, current_user_id)
    if not user or user.role not in ['admin', 'company']:
        return jsonify({"error": "Admin or Company access required"}), 403
    
    lot = db.session.get(ParkingLot, lot_id)
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
        
    # 2) Edit cost of parking & dynamic pricing rules
    if 'price' in data and data['price'] is not None:
        lot.price = float(data['price'])
    if 'daily_rate' in data and data['daily_rate'] is not None:
        lot.daily_rate = float(data['daily_rate'])
    if 'overnight_rate' in data and data['overnight_rate'] is not None:
        lot.overnight_rate = float(data['overnight_rate'])
    if 'peak_multiplier' in data and data['peak_multiplier'] is not None:
        lot.peak_multiplier = float(data['peak_multiplier'])
    if 'grace_period_minutes' in data and data['grace_period_minutes'] is not None:
        lot.grace_period_minutes = int(data['grace_period_minutes'])
    if 'overstay_penalty_rate' in data and data['overstay_penalty_rate'] is not None:
        lot.overstay_penalty_rate = float(data['overstay_penalty_rate'])
        
    if 'address' in data and data['address']:
        lot.address = data['address'].strip()
    elif 'location' in data and data['location']:
        lot.address = data['location'].strip()
        
    if 'pin_code' in data and data['pin_code']:
        lot.pin_code = str(data['pin_code']).strip()
        
    # 3) Multi-Floor or Single-Floor Grid Updates
    floors_input = data.get('floors')
    grid_layout_raw = data.get('grid_layout')
    
    if floors_input is not None and isinstance(floors_input, list):
        if len(floors_input) == 0:
            return jsonify({"error": "A parking facility must contain at least one floor."}), 400
            
        existing_floors = {f.id: f for f in lot.floors}
        seen_floor_ids = set()
        
        all_floor_parsed = []
        for fl_data in floors_input:
            f_num = int(fl_data.get('floor_number', 0))
            f_name = str(fl_data.get('floor_name') or ("Ground Floor" if f_num == 0 else f"Floor {f_num}")).strip()
            f_rows = int(fl_data.get('grid_rows', 5))
            f_cols = int(fl_data.get('grid_cols', 6))
            raw_layout = fl_data.get('grid_layout')
            
            p_layout = None
            if isinstance(raw_layout, str):
                try:
                    p_layout = json.loads(raw_layout)
                except Exception:
                    p_layout = []
            elif isinstance(raw_layout, list):
                p_layout = raw_layout
            else:
                p_layout = []
                
            p_cells = []
            h_cells = []
            for r_idx, row in enumerate(p_layout):
                for c_idx, cell in enumerate(row):
                    ctype = cell.get('type') if isinstance(cell, dict) else str(cell)
                    if ctype == 'parking':
                        p_cells.append((r_idx, c_idx))
                    elif ctype == 'handicap':
                        h_cells.append((r_idx, c_idx))
                        
            all_floor_parsed.append({
                "id": fl_data.get('id'),
                "floor_number": f_num,
                "floor_name": f_name,
                "grid_rows": f_rows,
                "grid_cols": f_cols,
                "grid_layout": p_layout,
                "parking_cells": p_cells,
                "handicap_cells": h_cells
            })
            
        grand_total = sum(len(f["parking_cells"]) + len(f["handicap_cells"]) for f in all_floor_parsed)
        if grand_total <= 0:
            return jsonify({"error": "Facility must include at least 1 bookable Parking or Handicap space across its floors."}), 400
            
        # Process each floor
        for fl in all_floor_parsed:
            floor_obj = None
            if fl["id"] and int(fl["id"]) in existing_floors:
                floor_obj = existing_floors[int(fl["id"])]
            else:
                for ef in lot.floors:
                    if ef.floor_number == fl["floor_number"]:
                        floor_obj = ef
                        break
                if not floor_obj:
                    floor_obj = ParkingFloor(
                        lot_id=lot.id,
                        floor_number=fl["floor_number"],
                        floor_name=fl["floor_name"],
                        grid_rows=fl["grid_rows"],
                        grid_cols=fl["grid_cols"]
                    )
                    db.session.add(floor_obj)
                    db.session.flush()
                    
            floor_obj.floor_number = fl["floor_number"]
            floor_obj.floor_name = fl["floor_name"]
            floor_obj.grid_rows = fl["grid_rows"]
            floor_obj.grid_cols = fl["grid_cols"]
            floor_obj.grid_layout = json.dumps(fl["grid_layout"])
            floor_obj.regular_spots = len(fl["parking_cells"])
            floor_obj.handicap_spots = len(fl["handicap_cells"])
            seen_floor_ids.add(floor_obj.id)
            
            # Floor prefix for spots: e.g. G-P1, L1-P1, B1-P1
            if floor_obj.floor_number == 0:
                p_pfx, h_pfx = "G-P", "G-H"
            elif floor_obj.floor_number < 0:
                p_pfx, h_pfx = f"B{abs(floor_obj.floor_number)}-P", f"B{abs(floor_obj.floor_number)}-H"
            else:
                p_pfx, h_pfx = f"L{floor_obj.floor_number}-P", f"L{floor_obj.floor_number}-H"
                
            desired_spots = []
            for idx, (r, c) in enumerate(fl["parking_cells"], start=1):
                desired_spots.append({
                    "spot_number": f"{p_pfx}{idx}",
                    "spot_type": "regular",
                    "row_idx": r,
                    "col_idx": c
                })
            for idx, (r, c) in enumerate(fl["handicap_cells"], start=1):
                desired_spots.append({
                    "spot_number": f"{h_pfx}{idx}",
                    "spot_type": "handicap",
                    "row_idx": r,
                    "col_idx": c
                })
                
            curr_floor_spots = ParkingSpot.query.filter_by(lot_id=lot.id, floor_id=floor_obj.id).all()
            if not curr_floor_spots and floor_obj.floor_number == 0:
                curr_floor_spots = ParkingSpot.query.filter_by(lot_id=lot.id, floor_id=None).all()
                for s in curr_floor_spots:
                    s.floor_id = floor_obj.id
                    
            for idx, des in enumerate(desired_spots):
                if idx < len(curr_floor_spots):
                    sp = curr_floor_spots[idx]
                    sp.spot_number = des["spot_number"]
                    sp.spot_type = des["spot_type"]
                    sp.row_idx = des["row_idx"]
                    sp.col_idx = des["col_idx"]
                    sp.floor_id = floor_obj.id
                    sp.floor_number = floor_obj.floor_number
                    sp.floor_name = floor_obj.floor_name
                else:
                    new_sp = ParkingSpot(
                        lot_id=lot.id,
                        floor_id=floor_obj.id,
                        floor_number=floor_obj.floor_number,
                        floor_name=floor_obj.floor_name,
                        spot_number=des["spot_number"],
                        spot_type=des["spot_type"],
                        row_idx=des["row_idx"],
                        col_idx=des["col_idx"],
                        status='A'
                    )
                    db.session.add(new_sp)
                    
            if len(curr_floor_spots) > len(desired_spots):
                surplus = curr_floor_spots[len(desired_spots):]
                for sp in surplus:
                    if sp.status == 'A':
                        db.session.delete(sp)
                        
        # Handle removed floors
        for fid, f_obj in existing_floors.items():
            if fid not in seen_floor_ids:
                f_spots = ParkingSpot.query.filter_by(floor_id=fid).all()
                occ = [s for s in f_spots if s.status == 'O']
                if occ:
                    return jsonify({"error": f"Cannot remove floor '{f_obj.floor_name}' because it contains active occupied spots."}), 400
                db.session.delete(f_obj)
                
        db.session.flush()
        current_floors = ParkingFloor.query.filter_by(lot_id=lot.id).all()
        total_p = sum(f.regular_spots or 0 for f in current_floors)
        total_h = sum(f.handicap_spots or 0 for f in current_floors)
        lot.number_of_spots = total_p + total_h
        lot.regular_spots = total_p
        lot.handicap_spots = total_h
        
        g_floor = next((f for f in current_floors if f.floor_number == 0), (current_floors[0] if current_floors else None))
        if g_floor:
            lot.grid_rows = g_floor.grid_rows
            lot.grid_cols = g_floor.grid_cols
            lot.grid_layout = g_floor.grid_layout
            
    elif grid_layout_raw is not None:
        grid_rows = data.get('grid_rows')
        grid_cols = data.get('grid_cols')
        if grid_rows is not None:
            lot.grid_rows = int(grid_rows)
        if grid_cols is not None:
            lot.grid_cols = int(grid_cols)

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
        
        # Ensure default Ground Floor exists and update it
        g_floor = next((f for f in lot.floors if f.floor_number == 0), None)
        if not g_floor:
            g_floor = ParkingFloor(lot_id=lot.id, floor_number=0, floor_name="Ground Floor")
            db.session.add(g_floor)
            db.session.flush()
        g_floor.grid_rows = lot.grid_rows
        g_floor.grid_cols = lot.grid_cols
        g_floor.grid_layout = lot.grid_layout
        g_floor.regular_spots = len(parking_cells)
        g_floor.handicap_spots = len(handicap_cells)
        
        # Build desired spot configurations
        desired = []
        for idx, (r, c) in enumerate(parking_cells, start=1):
            desired.append({
                "spot_number": f"G-P{idx}",
                "spot_type": "regular",
                "row_idx": r,
                "col_idx": c
            })
        for idx, (r, c) in enumerate(handicap_cells, start=1):
            desired.append({
                "spot_number": f"G-H{idx}",
                "spot_type": "handicap",
                "row_idx": r,
                "col_idx": c
            })
            
        for idx, des in enumerate(desired):
            if idx < len(current_spots):
                sp = current_spots[idx]
                sp.spot_number = des["spot_number"]
                sp.spot_type = des["spot_type"]
                sp.row_idx = des["row_idx"]
                sp.col_idx = des["col_idx"]
                sp.floor_id = g_floor.id
                sp.floor_number = 0
                sp.floor_name = "Ground Floor"
            else:
                new_sp = ParkingSpot(
                    lot_id=lot.id,
                    floor_id=g_floor.id,
                    floor_number=0,
                    floor_name="Ground Floor",
                    spot_number=des["spot_number"],
                    spot_type=des["spot_type"],
                    row_idx=des["row_idx"],
                    col_idx=des["col_idx"],
                    status='A'
                )
                db.session.add(new_sp)
                
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
        "daily_rate": lot.daily_rate,
        "overnight_rate": lot.overnight_rate,
        "peak_multiplier": lot.peak_multiplier,
        "grace_period_minutes": lot.grace_period_minutes,
        "overstay_penalty_rate": lot.overstay_penalty_rate,
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
    user = db.session.get(User, current_user_id)
    if not user or user.role not in ['admin', 'company']:
        return jsonify({"error": "Admin or Company access required"}), 403
    
    lot = db.session.get(ParkingLot, lot_id)
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


# ==================== VEHICLE GARAGE API (CUSTOMER MULTI-VEHICLE) ====================

@app.route('/api/vehicles', methods=['GET'])
@jwt_required()
def get_user_vehicles():
    """Get all registered vehicles in current customer's garage"""
    current_user_id = int(get_jwt_identity())
    vehicles = Vehicle.query.filter_by(user_id=current_user_id).order_by(Vehicle.is_default.desc(), Vehicle.created_at.desc()).all()
    return jsonify({
        "total": len(vehicles),
        "vehicles": [
            {
                "id": v.id,
                "license_plate": v.license_plate,
                "nickname": v.nickname or v.license_plate,
                "vehicle_type": v.vehicle_type,
                "is_default": v.is_default,
                "created_at": format_iso(v.created_at)
            }
            for v in vehicles
        ]
    }), 200


@app.route('/api/vehicles', methods=['POST'])
@jwt_required()
def add_vehicle():
    """Add a new vehicle to customer's garage"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data or not data.get('license_plate'):
        return jsonify({"error": "License plate number is required"}), 400
        
    plate = data['license_plate'].strip().upper()
    existing = Vehicle.query.filter_by(user_id=current_user_id, license_plate=plate).first()
    if existing:
        return jsonify({"error": f"Vehicle '{plate}' is already in your garage"}), 400
        
    v_type = data.get('vehicle_type', 'Car').strip()
    if v_type not in ['Car', 'SUV', 'Motorcycle', 'EV']:
        v_type = 'Car'
        
    is_default = bool(data.get('is_default', False))
    if is_default:
        Vehicle.query.filter_by(user_id=current_user_id).update({"is_default": False})
        
    nickname = data.get('nickname', '').strip() or f"{v_type} ({plate})"
    
    vehicle = Vehicle(
        user_id=current_user_id,
        license_plate=plate,
        nickname=nickname,
        vehicle_type=v_type,
        is_default=is_default
    )
    db.session.add(vehicle)
    db.session.commit()
    
    return jsonify({
        "message": f"Vehicle '{plate}' added to garage successfully",
        "vehicle": {
            "id": vehicle.id,
            "license_plate": vehicle.license_plate,
            "nickname": vehicle.nickname,
            "vehicle_type": vehicle.vehicle_type,
            "is_default": vehicle.is_default,
            "created_at": format_iso(vehicle.created_at)
        }
    }), 201


@app.route('/api/vehicles/<int:vehicle_id>', methods=['PUT'])
@jwt_required()
def update_vehicle(vehicle_id):
    """Update vehicle profile in customer garage"""
    current_user_id = int(get_jwt_identity())
    vehicle = db.session.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.user_id != current_user_id:
        return jsonify({"error": "Vehicle not found"}), 404
        
    data = request.get_json() or {}
    if 'license_plate' in data and data['license_plate']:
        new_plate = data['license_plate'].strip().upper()
        conflict = Vehicle.query.filter(Vehicle.user_id == current_user_id, Vehicle.license_plate == new_plate, Vehicle.id != vehicle_id).first()
        if conflict:
            return jsonify({"error": f"Another vehicle with plate '{new_plate}' already exists"}), 400
        vehicle.license_plate = new_plate
        
    if 'nickname' in data:
        vehicle.nickname = data['nickname'].strip()
    if 'vehicle_type' in data and data['vehicle_type'] in ['Car', 'SUV', 'Motorcycle', 'EV']:
        vehicle.vehicle_type = data['vehicle_type']
    if 'is_default' in data:
        if data['is_default']:
            Vehicle.query.filter_by(user_id=current_user_id).update({"is_default": False})
            vehicle.is_default = True
        else:
            vehicle.is_default = False
            
    db.session.commit()
    return jsonify({
        "message": "Vehicle profile updated successfully",
        "vehicle": {
            "id": vehicle.id,
            "license_plate": vehicle.license_plate,
            "nickname": vehicle.nickname,
            "vehicle_type": vehicle.vehicle_type,
            "is_default": vehicle.is_default
        }
    }), 200


@app.route('/api/vehicles/<int:vehicle_id>', methods=['DELETE'])
@jwt_required()
def delete_vehicle(vehicle_id):
    """Delete a vehicle from customer garage"""
    current_user_id = int(get_jwt_identity())
    vehicle = db.session.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.user_id != current_user_id:
        return jsonify({"error": "Vehicle not found"}), 404
        
    db.session.delete(vehicle)
    db.session.commit()
    return jsonify({"message": f"Vehicle '{vehicle.license_plate}' removed from garage"}), 200


# ==================== RESERVATION ROUTES ====================

@app.route('/api/reservations', methods=['POST'])
@jwt_required()
def create_reservation():
    """
    User books a parking spot:
    - Strictly enforced role: only Customer ('user') can book
    - Admin and Company accounts are strictly restricted from booking
    - Users can hold multiple active reservations simultaneously
    - Optimized "Book Any" Quick-Book Engine with atomic row-level locking (with_for_update)
    - Lowest floor / nearest-to-entrance heuristic
    - Full location hierarchy & vehicle garage association
    """
    current_user_id = int(get_jwt_identity())
    current_user = db.session.get(User, current_user_id)
    if not current_user or current_user.role != 'user':
        return jsonify({
            "error": "Only Customer users can book parking slots. Admin and Company accounts are strictly restricted from placing customer reservations."
        }), 403
        
    data = request.get_json() or {}
    
    # 1. Vehicle Garage Association & Plate resolution
    vehicle_id = data.get('vehicle_id')
    vehicle = None
    vehicle_number = None
    vehicle_type = data.get('vehicle_type', 'Car')
    
    if vehicle_id:
        vehicle = db.session.get(Vehicle, int(vehicle_id))
        if vehicle and vehicle.user_id == current_user_id:
            vehicle_number = vehicle.license_plate
            vehicle_type = vehicle.vehicle_type
            
    if not vehicle_number and data.get('vehicle_number'):
        vehicle_number = data.get('vehicle_number', '').strip().upper()
        
    if not vehicle_number:
        return jsonify({"error": "Vehicle registration number is required (select from garage or enter plate)"}), 400
        
    # Auto-save to garage if requested
    if data.get('save_to_garage') and vehicle_number:
        existing_v = Vehicle.query.filter_by(user_id=current_user_id, license_plate=vehicle_number).first()
        if not existing_v:
            new_v = Vehicle(
                user_id=current_user_id,
                license_plate=vehicle_number,
                nickname=data.get('vehicle_nickname') or f"{vehicle_type} ({vehicle_number})",
                vehicle_type=vehicle_type,
                is_default=False
            )
            db.session.add(new_v)
            db.session.flush()
            vehicle_id = new_v.id

    lot_id = data.get('lot_id') or data.get('parking_lot_id')
    floor_id = data.get('floor_id')
    floor_number = data.get('floor_number')
    remarks = data.get('remarks', '').strip()
    requested_type = data.get('spot_type', 'regular').strip().lower()
    if requested_type not in ['regular', 'handicap']:
        requested_type = 'regular'
        
    booking_type = data.get('booking_type', 'immediate').strip().lower()
    if booking_type not in ['immediate', 'scheduled']:
        booking_type = 'immediate'
        
    sched_start = None
    sched_end = None
    if booking_type == 'scheduled':
        start_str = data.get('scheduled_start_time') or data.get('start_time')
        end_str = data.get('scheduled_end_time') or data.get('end_time')
        if not start_str or not end_str:
            return jsonify({"error": "Both scheduled start time and scheduled end time are required for advance pre-bookings."}), 400
        try:
            sched_start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            sched_end = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            if sched_start.tzinfo is None:
                sched_start = sched_start.replace(tzinfo=timezone.utc)
            if sched_end.tzinfo is None:
                sched_end = sched_end.replace(tzinfo=timezone.utc)
        except Exception:
            return jsonify({"error": "Invalid scheduled datetime format."}), 400
            
        if sched_end <= sched_start:
            return jsonify({"error": "Scheduled end time must be after scheduled start time."}), 400
    
    spot = None
    reservation_status = 'active'
    if lot_id:
        lot = db.session.get(ParkingLot, lot_id)
        if not lot:
            return jsonify({"error": "Parking lot not found"}), 404
            
        if booking_type == 'scheduled':
            # Overlapping Interval Collision Detection:
            # Conflict exists if: existing.start < requested.end AND existing.end > requested.start
            conflicting_spot_ids = db.session.query(Reservation.spot_id).filter(
                Reservation.status.in_(['active', 'scheduled']),
                Reservation.scheduled_start_time.isnot(None),
                Reservation.scheduled_end_time.isnot(None),
                Reservation.scheduled_start_time < sched_end,
                Reservation.scheduled_end_time > sched_start
            ).scalar_subquery()
            
            query = ParkingSpot.query.filter(
                ParkingSpot.lot_id == lot_id,
                ParkingSpot.spot_type == requested_type,
                ~ParkingSpot.id.in_(conflicting_spot_ids)
            )
            if floor_id:
                query = query.filter_by(floor_id=int(floor_id))
            elif floor_number is not None:
                query = query.filter_by(floor_number=int(floor_number))
                
            spot = query.order_by(
                ParkingSpot.floor_number.asc(),
                (db.func.coalesce(ParkingSpot.row_idx, 0) + db.func.coalesce(ParkingSpot.col_idx, 0)).asc(),
                ParkingSpot.slot_order.asc(),
                ParkingSpot.id.asc()
            ).with_for_update(skip_locked=True).first()
            
            if not spot:
                return jsonify({"error": "No spots available for the requested advance time window. All spots are reserved during this period."}), 400
                
            now_utc = datetime.now(timezone.utc)
            if sched_start <= now_utc <= sched_end:
                spot.status = 'O'
                reservation_status = 'active'
            else:
                reservation_status = 'scheduled'
        else:
            # Immediate Park Now Quick-Book
            query = ParkingSpot.query.filter_by(lot_id=lot_id, status='A', spot_type=requested_type)
            if floor_id:
                query = query.filter_by(floor_id=int(floor_id))
            elif floor_number is not None:
                query = query.filter_by(floor_number=int(floor_number))
                
            spot = query.order_by(
                ParkingSpot.floor_number.asc(),
                (db.func.coalesce(ParkingSpot.row_idx, 0) + db.func.coalesce(ParkingSpot.col_idx, 0)).asc(),
                ParkingSpot.slot_order.asc(),
                ParkingSpot.id.asc()
            ).with_for_update(skip_locked=True).first()
            
            if not spot:
                type_label = "Handicap (Accessible)" if requested_type == 'handicap' else "Regular"
                fl_label = " on the requested floor" if (floor_id or floor_number is not None) else ""
                return jsonify({"error": f"No available {type_label} parking spots{fl_label} in this lot."}), 400
                
            spot.status = 'O'
            reservation_status = 'active'
            
    elif data.get('parking_spot_id') or data.get('spot_id'):
        spot_id = data.get('parking_spot_id') or data.get('spot_id')
        spot = ParkingSpot.query.filter_by(id=spot_id, status='A').with_for_update(skip_locked=True).first()
        if not spot:
            return jsonify({"error": "Selected spot is no longer available"}), 400
        requested_type = spot.spot_type or 'regular'
        spot.status = 'O'
        reservation_status = 'active'
            
    if not spot:
        return jsonify({"error": "No available parking spots found"}), 400
    
    venue_name = spot.parking_lot.prime_location_name if spot.parking_lot else 'Parking Venue'
    company_name = spot.parking_lot.company.company_name if (spot.parking_lot and spot.parking_lot.company) else 'Antigravity Parking'
    floor_name = spot.floor_name or (spot.floor.floor_name if spot.floor else 'Ground Floor')
    floor_id_val = spot.floor_id or (spot.floor.id if spot.floor else None)
    floor_num_val = spot.floor_number if spot.floor_number is not None else 0
    spot_num_val = spot.spot_number
    hierarchy_str = f"{venue_name} → {floor_name} → {spot_num_val}"
    
    # Save the time when the booking is selected (client-provided or current UTC time)
    client_ts = data.get('parking_timestamp') or data.get('entry_time') or data.get('start_time')
    parking_ts = None
    if client_ts:
        try:
            if isinstance(client_ts, str):
                cleaned_ts = client_ts.replace('Z', '+00:00')
                parsed_dt = datetime.fromisoformat(cleaned_ts)
                if parsed_dt.tzinfo is not None:
                    parking_ts = parsed_dt.astimezone(timezone.utc)
                else:
                    parking_ts = parsed_dt.replace(tzinfo=timezone.utc)
        except Exception as e:
            parking_ts = None
            
    if not parking_ts:
        parking_ts = sched_start if (booking_type == 'scheduled' and sched_start) else datetime.now(timezone.utc)
    
    # Create reservation with complete audit trail & location hierarchy
    reservation = Reservation(
        spot_id=spot.id,
        user_id=current_user_id,
        venue_name=venue_name,
        company_name=company_name,
        floor_id=floor_id_val,
        floor_number=floor_num_val,
        floor_name=floor_name,
        spot_number=spot_num_val,
        spot_type=requested_type,
        location_hierarchy=hierarchy_str,
        vehicle_id=vehicle_id,
        vehicle_number=vehicle_number,
        vehicle_type=vehicle_type,
        booking_type=booking_type,
        scheduled_start_time=sched_start,
        scheduled_end_time=sched_end,
        parking_timestamp=parking_ts,
        status=reservation_status,
        remarks=remarks
    )
    
    db.session.add(reservation)
    db.session.commit()
    
    cache.invalidate_prefix("lots_list")
    
    action_type_label = "Pre-booked for schedule" if booking_type == 'scheduled' else "Booked & Allotted"
    return jsonify({
        "message": f"{'Handicap' if requested_type == 'handicap' else 'Regular'} parking spot {action_type_label} on {floor_name} ({spot.spot_number}) successfully",
        "reservation_id": reservation.id,
        "spot_id": spot.id,
        "spot_number": spot.spot_number,
        "spot_type": spot.spot_type,
        "floor_id": floor_id_val,
        "floor_name": floor_name,
        "floor_number": spot.floor_number,
        "lot_name": venue_name,
        "venue_name": venue_name,
        "company_name": company_name,
        "location_hierarchy": hierarchy_str,
        "vehicle_id": vehicle_id,
        "vehicle_number": vehicle_number,
        "vehicle_type": vehicle_type,
        "booking_type": reservation.booking_type,
        "scheduled_start_time": format_iso(reservation.scheduled_start_time),
        "scheduled_end_time": format_iso(reservation.scheduled_end_time),
        "parking_timestamp": format_iso(reservation.parking_timestamp),
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
    reservation = db.session.get(Reservation, res_id)
    
    if not reservation:
        return jsonify({"error": "Reservation not found"}), 404
        
    user = db.session.get(User, current_user_id)
    if reservation.user_id != current_user_id and user.role != 'admin':
        return jsonify({"error": "Unauthorized to vacate this reservation"}), 403
        
    if reservation.status != 'active':
        return jsonify({"error": f"Reservation is already {reservation.status}"}), 400
        
    now = datetime.now(timezone.utc)
    reservation.leaving_timestamp = now
    reservation.status = 'completed'
    
    # Calculate duration and parking cost (handling naive or aware start timestamp)
    start_ts = reservation.parking_timestamp
    if start_ts.tzinfo is None:
        start_ts = start_ts.replace(tzinfo=timezone.utc)
    duration_seconds = max((now - start_ts).total_seconds(), 0)
    duration_hours = max(duration_seconds / 3600.0, 0.0)
    
    lot = reservation.parking_spot.parking_lot if reservation.parking_spot else None
    hourly_price = lot.price if lot else 0.0
    grace_mins = lot.grace_period_minutes if (lot and lot.grace_period_minutes is not None) else 15
    
    grace_applied = False
    parking_cost = 0.0
    overstay_penalty = 0.0
    
    # 1. 15-Minute Free Grace Period Check
    if duration_seconds <= (grace_mins * 60):
        grace_applied = True
        parking_cost = 0.0
    else:
        # Minimum 1 hour charge if past grace period
        billable_hours = max(duration_hours, 1.0)
        
        # Check Peak Hours (8:00 AM - 11:00 AM or 5:00 PM - 8:00 PM in local time)
        local_hour = now.astimezone().hour
        is_peak = (8 <= local_hour < 11) or (17 <= local_hour < 20)
        multiplier = (lot.peak_multiplier or 1.0) if (lot and is_peak) else 1.0
        
        # Check Overnight Window (10:00 PM - 7:00 AM)
        is_overnight = (local_hour >= 22 or local_hour < 7)
        if lot and lot.overnight_rate and lot.overnight_rate > 0 and is_overnight:
            base_cost = lot.overnight_rate
        else:
            base_cost = round(billable_hours * hourly_price * multiplier, 2)
            
        # Daily cap (if parked for full day / multiple days)
        if lot and lot.daily_rate and lot.daily_rate > 0:
            days = max(1.0, duration_seconds / 86400.0)
            daily_cap_total = days * lot.daily_rate
            if base_cost > daily_cap_total:
                base_cost = round(daily_cap_total, 2)
                
        parking_cost = base_cost
        
    # 2. Overstay Penalty for Scheduled Pre-bookings
    if reservation.booking_type == 'scheduled' and reservation.scheduled_end_time:
        sched_end_utc = reservation.scheduled_end_time
        if sched_end_utc.tzinfo is None:
            sched_end_utc = sched_end_utc.replace(tzinfo=timezone.utc)
        if now > sched_end_utc:
            overstay_secs = (now - sched_end_utc).total_seconds()
            overstay_hrs = max(1.0, overstay_secs / 3600.0)
            penalty_rate = (lot.overstay_penalty_rate or 50.0) if lot else 50.0
            overstay_penalty = round(overstay_hrs * penalty_rate, 2)
            parking_cost += overstay_penalty
            
    reservation.duration_seconds = int(duration_seconds)
    reservation.duration_formatted = format_duration(duration_seconds)
    reservation.parking_cost = round(parking_cost, 2)
    reservation.grace_period_applied = grace_applied
    reservation.overstay_penalty_cost = overstay_penalty
    
    # Release spot back to Available ('A')
    if reservation.parking_spot:
        reservation.parking_spot.status = 'A'
        
    db.session.commit()
    
    # Invalidate cache
    cache.invalidate_prefix("lots_list")
    
    msg = "Spot vacated within free grace period (₹0 fee charged)!" if grace_applied else "Parking spot vacated and released successfully"
    return jsonify({
        "message": msg,
        "reservation_id": reservation.id,
        "spot_number": reservation.parking_spot.spot_number if reservation.parking_spot else '',
        "location_hierarchy": reservation.location_hierarchy or reservation.location_path,
        "parking_timestamp": format_iso(reservation.parking_timestamp),
        "leaving_timestamp": format_iso(reservation.leaving_timestamp),
        "duration_hours": round(duration_hours, 2),
        "duration_seconds": reservation.duration_seconds,
        "duration_formatted": reservation.duration_formatted,
        "grace_period_applied": reservation.grace_period_applied,
        "overstay_penalty_cost": reservation.overstay_penalty_cost,
        "parking_cost": reservation.parking_cost,
        "status": reservation.status
    }), 200


@app.route('/api/reservations', methods=['GET'])
@jwt_required()
def get_reservations():
    """Get reservations for current user (or all reservations if admin)"""
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)
    
    if user.role == 'admin' and request.args.get('all') == 'true':
        reservations = Reservation.query.order_by(Reservation.parking_timestamp.desc()).all()
    else:
        reservations = Reservation.query.filter_by(user_id=current_user_id).order_by(Reservation.parking_timestamp.desc()).all()
        
    result = []
    for r in reservations:
        spot = r.parking_spot
        lot = spot.parking_lot if spot else None
        floor_name = r.floor_name or (spot.floor_name if spot else 'Ground Floor')
        floor_id_val = r.floor_id or (spot.floor_id if spot else None)
        floor_number_val = r.floor_number if r.floor_number is not None else (spot.floor_number if spot else 0)
        venue_name = r.venue_name or (lot.prime_location_name if lot else 'N/A')
        company_name = r.company_name or (lot.company.company_name if (lot and lot.company) else 'Antigravity Parking')
        spot_num = r.spot_number or (spot.spot_number if spot else 'N/A')
        hierarchy = r.location_hierarchy or f"{venue_name} → {floor_name} → {spot_num}"
        
        result.append({
            "id": r.id,
            "spot_id": r.spot_id,
            "parking_spot_id": r.spot_id,
            "spot_number": spot_num,
            "venue_name": venue_name,
            "company_name": company_name,
            "location_hierarchy": hierarchy,
            "location_path": hierarchy,
            "floor_id": floor_id_val,
            "floor_name": floor_name,
            "floor_number": floor_number_val,
            "lot_id": lot.id if lot else None,
            "lot_name": venue_name,
            "lot_price": lot.price if lot else 0.0,
            "vehicle_id": r.vehicle_id,
            "vehicle_number": r.vehicle_number,
            "vehicle_type": r.vehicle_type or 'Car',
            "spot_type": r.spot_type or (spot.spot_type if spot else 'regular'),
            "booking_type": r.booking_type or 'immediate',
            "scheduled_start_time": format_iso(r.scheduled_start_time),
            "scheduled_end_time": format_iso(r.scheduled_end_time),
            "parking_timestamp": format_iso(r.parking_timestamp),
            "start_time": format_iso(r.parking_timestamp),
            "leaving_timestamp": format_iso(r.leaving_timestamp),
            "end_time": format_iso(r.leaving_timestamp),
            "duration_seconds": r.duration_seconds,
            "duration_formatted": r.duration_formatted,
            "grace_period_applied": r.grace_period_applied or False,
            "overstay_penalty_cost": r.overstay_penalty_cost or 0.0,
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
    reservation = db.session.get(Reservation, res_id)
    
    if not reservation:
        return jsonify({"error": "Reservation not found"}), 404
        
    user = db.session.get(User, current_user_id)
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
    job = db.session.get(ExportJob, job_id)
    
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
    job = db.session.get(ExportJob, job_id)
    
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
    admin = db.session.get(User, current_user_id)
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
    admin = db.session.get(User, current_user_id)
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