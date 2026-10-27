# 🚗 Vehicle Parking Management System — Master Implementation Roadmap & TODO

This document details the complete feature architecture, technical specifications, and implementation checklist for the next phases of the Vehicle Parking Management System.

---

## 📋 Table of Contents
1. [Role Enforcement & Security (Admin, Company, Customer)](#1--role-enforcement--security)
2. [Multi-Slot & Multi-Venue Booking System](#2--multi-slot--multi-venue-booking-system)
3. [Multi-Floor & Multi-Deck Parking Facility Support](#3--multi-floor--multi-deck-parking-facility-support)
4. [Detailed History & Audit Tracking](#4--detailed-history--audit-tracking)
5. [Optimized "Book Any" Quick-Book Engine](#5--optimized-book-any-quick-book-engine)
6. [Digital Parking Pass & QR Code Check-in / Out](#6--digital-parking-pass--qr-code-check-in--out)
7. [Vehicle Profile Management (Customer Garage)](#7--vehicle-profile-management-customer-garage)
8. [Advance Scheduling & Pre-Booking Engine](#8--advance-scheduling--pre-booking-engine)
9. [Company & Facility Operations: Pricing & Penalties](#9--company--facility-operations-pricing--penalties)
10. [Monthly Subscriptions & Corporate Passes](#10--monthly-subscriptions--corporate-passes)
11. [Real-time Live Map (WebSocket / SSE)](#11--real-time-live-map-websocket--sse)
12. [Analytics, Utilization & Revenue Heatmaps](#12--analytics-utilization--revenue-heatmaps)
13. [Implementation Priority & Milestones](#13--implementation-priority--milestones)

---

## 1. 🛡️ Role Enforcement & Security

### Overview
Establish strict role-based authorization ensuring roles operate strictly within their boundaries.

- [x] **Customer-Only Booking Enforcement**:
  - Restrict `POST /api/reservations` endpoint to require `role == 'user'` (Customer).
  - Explicitly reject booking attempts from `role == 'admin'` and `role == 'company'` with HTTP `403 Forbidden` (`"Admins and Company accounts cannot place customer bookings"`).
- [x] **Frontend Route & Action Guards**:
  - Update login guards & view checks:
    - Protect Admin portal from non-admin accounts.
    - Protect Company portal from unauthorized accounts.
    - Protect Customer booking flows from admin/company accounts.
  - Hide booking buttons/modals if logged-in user is not a customer.

---

## 2. 🔀 Multi-Slot & Multi-Venue Booking System

### Overview
Enable customers to reserve and manage multiple spots simultaneously (e.g. for families, travel groups, or business fleets) across same or distinct venues.

- [x] **Data Model & Backend Updates**:
  - Remove single-active-reservation restriction per user.
  - Allow an arbitrary number of concurrent active reservations per customer ID.
- [x] **Independent Slot Life Cycles & Timers**:
  - Each active reservation tracks its own:
    - Independent start time and active elapsed timer.
    - Individual real-time cost counter on the Vue frontend.
    - Independent "Vacate / Check-out" trigger.
- [x] **Multi-Slot UI in Customer Dashboard**:
  - Dedicated "Active Reservations" panel displaying cards or a list for all active slots.
  - Grouping filter: View by Facility/Venue, Floor, or Vehicle.

---

## 3. 🏢 Multi-Floor & Multi-Deck Parking Facility Support

### Overview
Support multi-level parking structures (basements, ground floor, multi-storey decks, and rooftops), each with independent grid dimensions, layouts, and slot counts.

- [x] **Multi-Floor Data Model (`ParkingFloor`)**:
  - Create `ParkingFloor` model:
    - `id`: Primary key
    - `parking_lot_id`: Foreign key referencing `ParkingLot`
    - `floor_number`: Integer ordering (`-2` = B2, `-1` = B1, `0` = Ground Floor, `1` = Level 1, `2` = Level 2, etc.)
    - `floor_name`: Custom label (e.g., "Basement 2 (B2)", "Ground Floor", "Level 1 (Arrivals)", "Rooftop Deck")
    - `grid_rows` & `grid_cols`: Independent grid dimensions per floor (e.g., Ground can be 8x10, Level 1 can be 12x12)
    - `grid_layout`: JSON 2D matrix representing cell types for that specific floor
    - `regular_spots`, `handicap_spots`: Pre-computed counts per floor
  - Associate `ParkingSpot` records with `floor_id` and `floor_number`.
  - Automatically aggregate `ParkingLot.number_of_spots = sum(floor.spots)` across all facility floors.
- [x] **Inter-Floor Connectors (Ramps & Elevators)**:
  - Add vertical circulation elements to the grid stamp tools:
    - 🚗⤴️ **Ramp Up (`'ramp_up'`)**: Vehicle ramp leading to the floor above.
    - 🚗⤵️ **Ramp Down (`'ramp_down'`)**: Vehicle ramp leading to the floor below.
    - 🛗 **Elevator (`'elevator'`)**: Vertical pedestrian lift core.
    - 🪜 **Stairs (`'stairs'`)**: Vertical pedestrian staircase.
- [x] **Company Portal: Multi-Floor Management UI**:
  - **Floor Navigation Tabs**: Switch effortlessly between floors (`[ B1 ] [ Ground ] [ Level 1 ] [ + Add Floor ]`).
  - **Floor Controls**: Reorder floors, rename floors, set custom dimensions per floor, or delete empty floors.
  - **Per-Floor Grid Editor**: Visual clickable grid editor with dedicated toolbar per floor.
  - **Facility Rollup View**: Summary card showing total capacity breakdown by floor (e.g., Ground: 20 slots, B1: 40 slots, Level 1: 35 slots).
- [x] **Customer Portal: Multi-Floor Interactive Spot Picker**:
  - Floor switcher tabs displaying live vacancy counts (e.g. `Ground Floor (3 free)`, `Level 1 (14 free)`).
  - Visual 2D floor plan rendering with click-to-book spot selection.
  - Filter option to choose preferred floor level.
- [x] **Admin Dashboard: Multi-Floor Inspection**:
  - Floor-by-floor layout tabs to monitor live occupancy across each deck of multi-storey parking complexes.

---

## 4. 📜 Detailed History & Audit Tracking

### Overview
Comprehensive booking records storing complete location hierarchy, time audits, and duration metrics.

- [ ] **Location Hierarchy in Reservation Schema**:
  - Update `Reservation` model to record:
    - `venue_name` / `company_name` (Company/Venue).
    - `floor_name` / `floor_number` (e.g., "Ground Floor", "Level B1", "Floor 2").
    - `slot_number` (e.g., "G-14", "B1-08") and `slot_type` (Regular, Handicap, EV).
- [ ] **Audit Timestamps & Calculated Metrics**:
  - `booking_date`: Date the reservation was initiated.
  - `entry_timestamp`: Exact gate-in / check-in time (UTC and formatted local).
  - `exit_timestamp`: Exact gate-out / check-out time.
  - `duration_seconds` / `duration_formatted`: Formatted as X Days, Y Hours, Z Minutes.
  - `total_cost`: Final invoiced amount with tariff breakdown.
- [ ] **Audit Trail Export & View**:
  - Tabular history view with search, date range filter, and status pills (Completed, Active, Cancelled).
  - CSV / PDF export incorporating the full hierarchy: `Company/Venue → Floor → Slot Number`.

---

## 5. ⚡ Optimized "Book Any" Quick-Book Engine

### Overview
High-concurrency, zero-collision quick-booking engine using database indices, atomic row locking, and a Lowest Floor / Nearest-to-Entry heuristic.

- [ ] **Database Composite B-Tree Index**:
  - Add index on `ParkingSpot`:
    ```sql
    CREATE INDEX idx_spots_quickbook ON parking_spots (parking_lot_id, status, floor_id, slot_order);
    ```
- [ ] **Atomic Row Locking (`with_for_update`)**:
  - Query available spots with atomic row-level lock:
    ```python
    spot = ParkingSpot.query.filter_by(
        parking_lot_id=lot_id,
        status='A',
        spot_type=requested_type
    ).order_by(
        ParkingSpot.floor_number.asc(),       # Ground / lowest floor first
        ParkingSpot.distance_to_entry.asc(),  # Nearest to entrance/ramp/stairs
        ParkingSpot.slot_order.asc()
    ).with_for_update(skip_locked=True).first()
    ```
- [ ] **Intelligent Heuristic (Lowest Floor / Nearest to Entry)**:
  - Prioritize ground floor (`floor_number == 0`), then lowest upper/lower deck.
  - Prioritize spots closest to ramps, stairs, or elevators calculated from grid coordinates.
- [ ] **Zero Race Conditions**:
  - Concurrency test simulating 20 simultaneous booking requests to guarantee zero double bookings.

---

## 6. 🎫 Digital Parking Pass & QR Code Check-in / Out

### Overview
Contactless digital entry and exit automation via dynamic QR codes.

- [ ] **Frontend Dynamic QR Pass (Vue.js)**:
  - Generate a secure dynamic QR code upon booking confirmation using `qrcode.vue`.
  - Payload encodes a signed/encrypted token containing: `{ reservation_id, vehicle_number, lot_id, floor_name, spot_id, timestamp, hash }`.
  - Accessible on Customer Dashboard under "My Active Passes" with full details and print/save options.
- [ ] **Gate Scanner / Auto Check-in & Check-out**:
  - Create gate scanner endpoint: `POST /api/gate/scan`.
  - **First Scan (Entry)**: Validates pass, transitions status to `checked_in`, records exact `entry_timestamp`.
  - **Second Scan (Exit)**: Stops timer, records `exit_timestamp`, computes total fee, and marks spot `vacated` (or prompts instant checkout).
- [ ] **Gate Attendant / Simulator UI**:
  - Web-based simulator tool for gate cameras/attendants to scan or enter QR token.

---

## 7. 🚘 Vehicle Profile Management (Customer Garage)

### Overview
Allow customers to save multiple vehicles to their account for streamlined bookings, accurate billing, and security compliance.

- [ ] **Vehicle Data Model**:
  - Create `Vehicle` model:
    - `id`, `user_id` (foreign key)
    - `license_plate` (e.g. "DL-01-AB-1234", unique per user)
    - `nickname` / `alias` (e.g., "Dad's SUV", "Daily Commuter")
    - `vehicle_type`: `Car`, `SUV`, `Motorcycle`, `EV` (Electric Vehicle)
    - `is_default`: Boolean
- [ ] **Customer Garage UI**:
  - "My Garage" tab in Customer portal: Add, edit, remove vehicles.
- [ ] **Slot-to-Vehicle Association**:
  - When reserving, customer selects which saved vehicle is using the spot (or types a new plate).
  - Slot dimensions and type validation (e.g., preventing an SUV from booking a compact/motorcycle-only slot).

---

## 8. 📅 Advance Scheduling / Pre-Booking Engine

### Overview
Move beyond real-time "Park Now" bookings to support scheduled future reservations.

- [ ] **Time-Window Booking Schema**:
  - Update `Reservation` with:
    - `scheduled_start_time` (Datetime)
    - `scheduled_end_time` (Datetime)
    - `booking_type`: `'immediate'` vs. `'scheduled'`
- [ ] **Overlapping Interval Collision Detection**:
  - Backend validation ensuring a spot has no conflicting reservations:
    $$\text{RequestedStart} < \text{ExistingEnd} \quad \text{AND} \quad \text{RequestedEnd} > \text{ExistingStart}$$
- [ ] **Frontend Schedule Selector**:
  - Date and time range picker in the booking modal.
  - Visual time-slider showing availability of parking lots throughout the day.

---

## 9. 💰 Company & Facility Operations: Pricing & Penalties

### Overview
Comprehensive pricing engine for facilities with granular rules, grace periods, and overtime surcharges.

- [ ] **Dynamic & Tiered Pricing Rules**:
  - Company settings for:
    - **Hourly Rate**: Base hourly tariff.
    - **Daily / 24-Hour Cap**: Maximum ceiling for 24-hour periods.
    - **Overnight Rate**: Fixed or discounted tariff for overnight windows (e.g., 10 PM – 7 AM).
    - **Peak-Hour Multiplier**: Weekend rush multiplier (e.g., 1.5x) or morning office rush hours (8 AM – 11 AM).
    - **Slot Surcharges**: Surcharge for EV charging stations or premium wide spots.
- [ ] **Grace Period & Overstay Penalty Engine**:
  - **Grace Period**: 15-minute free window for cancellation or exit without charges.
  - **Overstay Penalty**: Surcharge rate per minute/hour if customer departs after their pre-booked scheduled window.
  - Automated penalty computation upon check-out/exit scan.

---

## 10. 🎟️ Monthly Subscriptions & Corporate Passes

### Overview
Enable recurring parking plans for corporate tenants, fleets, and daily commuters.

- [ ] **Subscription Plans**:
  - Types:
    - **Dedicated Slot**: Assigned specific fixed slot on a designated floor (e.g. Level 1, Slot #104 reserved 24/7).
    - **Floating Slot**: Guaranteed access to any available regular spot in the facility during business hours.
- [ ] **Subscription Management**:
  - Billing cycle: Monthly / Quarterly / Annual.
  - Automatic renewal status and active valid date range.
  - Digital Pass / QR code badge for subscribers for swift gate entry without daily payment steps.

---

## 11. 🔄 Real-time Live Map (WebSocket / SSE)

### Overview
Instant bi-directional state synchronization so parking spot changes reflect immediately across all connected browsers and floor views.

- [ ] **Live Event Streaming (Flask-SocketIO or SSE)**:
  - Broadcast events on spot status transitions:
    - `spot_reserved` → `{ lot_id, floor_id, spot_id, status: 'O' }`
    - `spot_vacated` → `{ lot_id, floor_id, spot_id, status: 'A' }`
- [ ] **Real-Time Vue Map Updates**:
  - Live 2D grid updates on the active floor without page refresh:
    - Spot instantly transitions color (Green to Red / Occupied).
    - Floor vacancy counter updates live (`Floor G: X vacant, Floor 1: Y vacant`).
  - Active visual feedback: momentary pulse animation on newly occupied/vacated spots.

---

## 12. 📊 Analytics, Utilization & Revenue Heatmaps

### Overview
Executive and facility-level business intelligence to optimize parking lot yield across multi-level facilities.

- [ ] **Multi-Floor Utilization & Occupancy Heatmaps**:
  - Visual matrix showing utilization intensity by floor, aisle, and time-of-day.
  - Compare floor efficiency (e.g., Ground Floor 98% utilization vs Basement 2 30% utilization).
- [ ] **Revenue & Yield Analytics**:
  - Total revenue per floor / per slot / per square foot.
  - Peak revenue days and hours.
- [ ] **Vehicle Turnover Metrics**:
  - Average dwell time (duration per vehicle).
  - Breakdown by vehicle type (Car vs SUV vs EV vs Motorcycle).
  - Customer return rate and repeat parker analytics.

---

## 13. 🎯 Implementation Priority & Milestones

| Milestone | Key Deliverables | Estimated Scope |
| :--- | :--- | :--- |
| **Milestone 1: Multi-Floor Architecture & Security** | • Multi-floor data model (`ParkingFloor`) with floor tabs & independent dimensions<br>• Ramps (Up/Down) & Elevators in grid editor<br>• Role enforcement (Customer-only booking, Admin/Company blocked)<br>• Multi-slot active booking for customers | **Completed ✅** |
| **Milestone 2: Quick-Book Engine & Garage** | • Atomic row locking (`with_for_update`) & Lowest Floor / Nearest-to-Entry heuristic<br>• Customer Vehicle Garage (multi-car management)<br>• Location hierarchy audit (`Venue → Floor → Slot`) | **Sprint 2** |
| **Milestone 3: Digital Pass & QR Automation** | • Dynamic QR code pass generation on Vue dashboard<br>• Gate QR scanner endpoint (check-in / check-out automation)<br>• Gate attendant / camera simulator UI | **Sprint 3** |
| **Milestone 4: Advance Booking & Tiered Pricing** | • Pre-booking / future time slot scheduler<br>• Tiered pricing (hourly, daily, overnight, peak surcharges)<br>• 15-minute grace period & overstay penalty engine | **Sprint 4** |
| **Milestone 5: Real-time Live Map & BI** | • WebSocket / SSE broadcast for multi-floor spot state changes<br>• Monthly/Corporate pass management<br>• Multi-floor utilization heatmaps & revenue charts | **Sprint 5** |

---

*Document created and maintained in project workspace.*
