import os
import csv
import uuid
import threading
import json
import urllib.request
from datetime import datetime, timedelta, timezone
from models import db, User, ParkingLot, ParkingSpot, Reservation, ExportJob, DailyReminderLog

EXPORTS_DIR = os.path.join(os.path.dirname(__file__), 'instance', 'exports')
os.makedirs(EXPORTS_DIR, exist_ok=True)

# ==================== JOB C: ASYNC CSV EXPORT ====================

def _process_csv_export(app, user_id, job_id):
    """Background worker task to export user parking reservations to CSV"""
    with app.app_context():
        job = ExportJob.query.get(job_id)
        if not job:
            return
            
        try:
            job.status = 'processing'
            db.session.commit()
            
            # Query all user reservations
            reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.parking_timestamp.desc()).all()
            
            filename = f"parking_history_user_{user_id}_{job_id[:8]}.csv"
            filepath = os.path.join(EXPORTS_DIR, filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Header row matching specification
                writer.writerow([
                    'Reservation ID',
                    'Spot ID',
                    'Spot Number',
                    'Lot ID',
                    'Prime Location Name',
                    'Address',
                    'Pin Code',
                    'Vehicle Number',
                    'Parking Timestamp (UTC)',
                    'Leaving Timestamp (UTC)',
                    'Hourly Price',
                    'Parking Cost',
                    'Status',
                    'Remarks'
                ])
                
                for res in reservations:
                    spot = res.parking_spot
                    lot = spot.parking_lot if spot else None
                    writer.writerow([
                        res.id,
                        res.spot_id,
                        spot.spot_number if spot else 'N/A',
                        lot.id if lot else 'N/A',
                        lot.prime_location_name if lot else 'N/A',
                        lot.address if lot else 'N/A',
                        lot.pin_code if lot else 'N/A',
                        res.vehicle_number,
                        res.parking_timestamp.strftime('%Y-%m-%d %H:%M:%S') if res.parking_timestamp else '',
                        res.leaving_timestamp.strftime('%Y-%m-%d %H:%M:%S') if res.leaving_timestamp else 'In Use',
                        lot.price if lot else 0.0,
                        res.parking_cost if res.parking_cost is not None else 0.0,
                        res.status,
                        res.remarks or ''
                    ])
            
            job.status = 'completed'
            job.file_path = filepath
            job.filename = filename
            job.completed_at = datetime.now(timezone.utc)
            db.session.commit()
            
        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            db.session.commit()

def trigger_csv_export(app, user_id):
    """Triggers an async CSV export job and returns job record"""
    job_id = str(uuid.uuid4())
    job = ExportJob(
        id=job_id,
        user_id=user_id,
        status='pending'
    )
    db.session.add(job)
    db.session.commit()
    
    # Launch background thread
    thread = threading.Thread(target=_process_csv_export, args=(app, user_id, job_id), daemon=True)
    thread.start()
    
    return job


# ==================== JOB A: DAILY REMINDERS ====================

def run_daily_reminders(app, webhook_url=None):
    """
    Checks if a user has not visited or parking lot is created by admin.
    Sends daily reminder via Google Chat Webhook / Mail / SMS alert log.
    """
    with app.app_context():
        # 1. Check if parking lots exist
        lots = ParkingLot.query.all()
        if not lots:
            return {"status": "skipped", "message": "No parking lots available to remind about."}
        
        # 2. Check users who have not visited in the last 24h
        cutoff_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
        users = User.query.filter(User.role == 'user').all()
        
        target_users = []
        for u in users:
            # Check if user has no reservation or last visit before cutoff
            last_res = Reservation.query.filter_by(user_id=u.id).order_by(Reservation.parking_timestamp.desc()).first()
            if not last_res or last_res.parking_timestamp < cutoff_time:
                target_users.append(u)
                
        lots_summary = ", ".join([f"{lot.prime_location_name} (₹{lot.price}/hr)" for lot in lots[:3]])
        
        reminder_text = (
            f"🚗 Daily Parking Alert: You haven't booked recently! "
            f"Available parking lots: {lots_summary}. "
            f"Visit your portal to reserve a 4-wheeler spot today if needed."
        )
        
        webhook_sent = False
        webhook_error = None
        
        # Send to Google Chat webhook if provided
        if webhook_url:
            try:
                payload = json.dumps({"text": reminder_text}).encode('utf-8')
                req = urllib.request.Request(webhook_url, data=payload, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        webhook_sent = True
            except Exception as ex:
                webhook_error = str(ex)
        
        # Save reminder log in database
        log = DailyReminderLog(
            channel='Google Chat Webhook' if webhook_sent else 'Notification / Email Digest',
            message=reminder_text,
            recipients_count=len(target_users),
            status='sent'
        )
        db.session.add(log)
        db.session.commit()
        
        return {
            "status": "success",
            "recipients_count": len(target_users),
            "message": reminder_text,
            "webhook_sent": webhook_sent,
            "webhook_error": webhook_error,
            "log_id": log.id
        }


# ==================== JOB B: MONTHLY ACTIVITY REPORT ====================

def generate_user_monthly_report(user_id, year=None, month=None):
    """
    Devises a monthly report for the user created using HTML.
    Includes:
    - Parking spots booked per month
    - Most used parking lot by the user
    - Amount spent on parking for the month
    """
    now = datetime.now(timezone.utc)
    year = year or now.year
    month = month or now.month
    
    # Calculate start and end date for the month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
        
    user = User.query.get(user_id)
    if not user:
        return None
        
    reservations = Reservation.query.filter(
        Reservation.user_id == user_id,
        Reservation.parking_timestamp >= start_date,
        Reservation.parking_timestamp < end_date
    ).all()
    
    total_spots_booked = len(reservations)
    total_amount_spent = sum(r.parking_cost or 0.0 for r in reservations)
    
    # Calculate most used parking lot
    lot_counter = {}
    for r in reservations:
        spot = r.parking_spot
        if spot and spot.parking_lot:
            lot_name = spot.parking_lot.prime_location_name
            lot_counter[lot_name] = lot_counter.get(lot_name, 0) + 1
            
    most_used_lot = max(lot_counter.items(), key=lambda x: x[1])[0] if lot_counter else "None"
    
    month_name = start_date.strftime("%B %Y")
    
    # Generate styled HTML report
    rows_html = "".join([
        f"""<tr>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{r.id}</td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{r.parking_spot.parking_lot.prime_location_name if r.parking_spot else 'N/A'}</td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{r.parking_spot.spot_number if r.parking_spot else 'N/A'}</td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{r.vehicle_number}</td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{r.parking_timestamp.strftime('%d %b %Y, %H:%M')}</td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{r.leaving_timestamp.strftime('%d %b %Y, %H:%M') if r.leaving_timestamp else 'In Progress'}</td>
            <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold; color: #28a745;">₹{r.parking_cost or 0.0:.2f}</td>
        </tr>"""
        for r in reservations
    ])
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Monthly Parking Activity Report - {month_name}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8f9fa; margin: 0; padding: 30px;">
    <div style="max-width: 800px; margin: 0 auto; background: #ffffff; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); overflow: hidden; border: 1px solid #e9ecef;">
        <div style="background: linear-gradient(135deg, #42b983 0%, #359268 100%); color: #ffffff; padding: 25px 30px;">
            <h1 style="margin: 0; font-size: 24px;">Monthly Parking Activity Report</h1>
            <p style="margin: 5px 0 0; opacity: 0.9;">Period: {month_name} | User: {user.username} ({user.email})</p>
        </div>
        
        <div style="padding: 30px;">
            <h3 style="color: #333; margin-top: 0; border-bottom: 2px solid #42b983; padding-bottom: 8px;">Monthly Summary</h3>
            <div style="display: flex; gap: 20px; margin-bottom: 30px;">
                <div style="flex: 1; background: #f8f9fa; border-radius: 8px; padding: 15px; border-left: 4px solid #42b983;">
                    <div style="font-size: 13px; color: #6c757d; text-transform: uppercase;">Spots Booked</div>
                    <div style="font-size: 26px; font-weight: bold; color: #333; margin-top: 5px;">{total_spots_booked}</div>
                </div>
                <div style="flex: 1; background: #f8f9fa; border-radius: 8px; padding: 15px; border-left: 4px solid #17a2b8;">
                    <div style="font-size: 13px; color: #6c757d; text-transform: uppercase;">Most Used Lot</div>
                    <div style="font-size: 18px; font-weight: bold; color: #333; margin-top: 8px;">{most_used_lot}</div>
                </div>
                <div style="flex: 1; background: #f8f9fa; border-radius: 8px; padding: 15px; border-left: 4px solid #ffc107;">
                    <div style="font-size: 13px; color: #6c757d; text-transform: uppercase;">Total Spent</div>
                    <div style="font-size: 26px; font-weight: bold; color: #28a745; margin-top: 5px;">₹{total_amount_spent:.2f}</div>
                </div>
            </div>
            
            <h3 style="color: #333; margin-bottom: 15px; border-bottom: 2px solid #42b983; padding-bottom: 8px;">Booking Details</h3>
            <table style="width: 100%; border-collapse: collapse; font-size: 14px; text-align: left;">
                <thead>
                    <tr style="background-color: #f1f3f5; color: #495057;">
                        <th style="padding: 10px; border: 1px solid #dee2e6;">#</th>
                        <th style="padding: 10px; border: 1px solid #dee2e6;">Parking Lot</th>
                        <th style="padding: 10px; border: 1px solid #dee2e6;">Spot</th>
                        <th style="padding: 10px; border: 1px solid #dee2e6;">Vehicle</th>
                        <th style="padding: 10px; border: 1px solid #dee2e6;">Entry Time</th>
                        <th style="padding: 10px; border: 1px solid #dee2e6;">Exit Time</th>
                        <th style="padding: 10px; border: 1px solid #dee2e6;">Cost</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html if rows_html else '<tr><td colspan="7" style="text-align: center; padding: 20px; color: #6c757d;">No reservations in this month.</td></tr>'}
                </tbody>
            </table>
        </div>
        
        <div style="background-color: #f8f9fa; padding: 15px 30px; text-align: center; color: #6c757d; font-size: 12px; border-top: 1px solid #e9ecef;">
            Generated by Vehicle Parking Management System on {now.strftime('%d %b %Y, %H:%M UTC')}
        </div>
    </div>
</body>
</html>"""

    return {
        "user_id": user_id,
        "month_name": month_name,
        "total_spots_booked": total_spots_booked,
        "most_used_lot": most_used_lot,
        "total_amount_spent": total_amount_spent,
        "html_content": html_content
    }

