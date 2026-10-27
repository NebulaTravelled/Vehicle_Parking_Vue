import json
import os
import re
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify, request, send_file, make_response
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

import config
from models import db, User, ParkingLot, ParkingSpot, Reservation, ExportJob, DailyReminderLog, ParkingFloor
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
        
    # 3) Multi-Floor or Single-Floor Grid Updates
    floors_input = data.get('floors')
    
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
    - Strictly enforced role: only Customer ('user') can book
    - Admin and Company accounts are strictly restricted from booking
    - Users can hold multiple active reservations simultaneously
    - Supports multi-floor selection or auto-allots on lowest floor
    """
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    if not current_user or current_user.role != 'user':
        return jsonify({
            "error": "Only Customer users can book parking slots. Admin and Company accounts are strictly restricted from placing customer reservations."
        }), 403
        
    data = request.get_json()
    if not data or not data.get('vehicle_number'):
        return jsonify({"error": "Vehicle number is required"}), 400
        
    vehicle_number = data.get('vehicle_number', '').strip().upper()
    lot_id = data.get('lot_id') or data.get('parking_lot_id')
    floor_id = data.get('floor_id')
    floor_number = data.get('floor_number')
    remarks = data.get('remarks', '').strip()
    requested_type = data.get('spot_type', 'regular').strip().lower()
    if requested_type not in ['regular', 'handicap']:
        requested_type = 'regular'
    
    spot = None
    if lot_id:
        lot = ParkingLot.query.get(lot_id)
        if not lot:
            return jsonify({"error": "Parking lot not found"}), 404
            
        # Find first available spot matching requested type and optional floor preference
        query = ParkingSpot.query.filter_by(lot_id=lot_id, status='A', spot_type=requested_type)
        if floor_id:
            query = query.filter_by(floor_id=int(floor_id))
        elif floor_number is not None:
            query = query.filter_by(floor_number=int(floor_number))
            
        # Lowest floor first heuristic
        spot = query.order_by(ParkingSpot.floor_number.asc(), ParkingSpot.id.asc()).first()
        if not spot:
            type_label = "Handicap (Accessible)" if requested_type == 'handicap' else "Regular"
            fl_label = " on the requested floor" if (floor_id or floor_number is not None) else ""
            return jsonify({"error": f"No available {type_label} parking spots{fl_label} in this lot."}), 400
            
    elif data.get('parking_spot_id') or data.get('spot_id'):
        spot_id = data.get('parking_spot_id') or data.get('spot_id')
        spot = ParkingSpot.query.get(spot_id)
        if spot and spot.status != 'A':
            spot = None
        if not spot:
            return jsonify({"error": "Selected spot is not available"}), 400
        requested_type = spot.spot_type or 'regular'
            
    if not spot:
        return jsonify({"error": "No available parking spots found"}), 400
        
    # Mark spot as Occupied ('O')
    spot.status = 'O'
    
    floor_name = spot.floor_name or (spot.floor.floor_name if spot.floor else 'Ground Floor')
    floor_id_val = spot.floor_id or (spot.floor.id if spot.floor else None)
    
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
            print("Failed to parse client parking_timestamp:", e)
            parking_ts = None
            
    if not parking_ts:
        parking_ts = datetime.now(timezone.utc)
    
    # Create reservation
    reservation = Reservation(
        spot_id=spot.id,
        user_id=current_user_id,
        floor_id=floor_id_val,
        floor_name=floor_name,
        vehicle_number=vehicle_number,
        spot_type=requested_type,
        parking_timestamp=parking_ts,
        status='active',
        remarks=remarks
    )
    
    db.session.add(reservation)
    db.session.commit()
    
    cache.invalidate_prefix("lots_list")
    
    return jsonify({
        "message": f"{'Handicap' if requested_type == 'handicap' else 'Regular'} parking spot allotted on {floor_name} ({spot.spot_number}) and booked successfully",
        "reservation_id": reservation.id,
        "spot_id": spot.id,
        "spot_number": spot.spot_number,
        "spot_type": spot.spot_type,
        "floor_id": floor_id_val,
        "floor_name": floor_name,
        "floor_number": spot.floor_number,
        "lot_name": spot.parking_lot.prime_location_name,
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
    reservation = Reservation.query.get(res_id)
    
    if not reservation:
        return jsonify({"error": "Reservation not found"}), 404
        
    user = User.query.get(current_user_id)
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
    duration_hours = max(duration_seconds / 3600.0, 1.0)
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
        "parking_timestamp": format_iso(reservation.parking_timestamp),
        "leaving_timestamp": format_iso(reservation.leaving_timestamp),
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
        floor_name = r.floor_name or (spot.floor_name if spot else 'Ground Floor')
        floor_id_val = r.floor_id or (spot.floor_id if spot else None)
        floor_number_val = spot.floor_number if spot else 0
        result.append({
            "id": r.id,
            "spot_id": r.spot_id,
            "parking_spot_id": r.spot_id,
            "spot_number": spot.spot_number if spot else 'N/A',
            "floor_id": floor_id_val,
            "floor_name": floor_name,
            "floor_number": floor_number_val,
            "lot_id": lot.id if lot else None,
            "lot_name": lot.prime_location_name if lot else 'N/A',
            "lot_price": lot.price if lot else 0.0,
            "vehicle_number": r.vehicle_number,
            "spot_type": r.spot_type or (spot.spot_type if spot else 'regular'),
            "parking_timestamp": format_iso(r.parking_timestamp),
            "start_time": format_iso(r.parking_timestamp),
            "leaving_timestamp": format_iso(r.leaving_timestamp),
            "end_time": format_iso(r.leaving_timestamp),
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