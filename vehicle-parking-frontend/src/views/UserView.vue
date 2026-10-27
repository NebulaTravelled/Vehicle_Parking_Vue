<template>
  <div class="bg-light min-vh-100">
    <div v-if="!isLoggedIn">
      <UserLogin
        v-if="!showRegister"
        :success-message="registerSuccessMessage"
        @login-success="handleLoginSuccess"
        @switch-to-register="openRegister"
      />
      <UserRegister
        v-else
        @register-success="handleRegisterSuccess"
        @switch-to-login="openLogin"
      />
    </div>
    
    <div v-else>
      <!-- Navigation Bar -->
      <nav class="navbar navbar-expand-lg navbar-dark bg-success shadow-sm px-4">
        <div class="container-fluid">
          <span class="navbar-brand fw-bold">
            🚘 User Parking Portal
          </span>
          <div class="d-flex align-items-center gap-3">
            <span class="text-white small">Welcome, <strong>{{ currentUser.username || 'User' }}</strong></span>
            <button class="btn btn-outline-light btn-sm" @click="logout">Logout</button>
          </div>
        </div>
      </nav>
      
      <!-- Tab Navigation -->
      <div class="bg-white border-bottom px-4">
        <ul class="nav nav-tabs border-0 pt-2">
          <li class="nav-item">
            <button
              class="nav-link"
              :class="{ active: activeTab === 'dashboard' }"
              @click="activeTab = 'dashboard'"
            >
              🅿️ Book & Active Spot
            </button>
          </li>
          <li class="nav-item">
            <button
              class="nav-link"
              :class="{ active: activeTab === 'garage' }"
              @click="activeTab = 'garage'"
            >
              🚘 My Garage <span v-if="vehicles.length" class="badge bg-secondary ms-1">{{ vehicles.length }}</span>
            </button>
          </li>
          <li class="nav-item">
            <button
              class="nav-link"
              :class="{ active: activeTab === 'reservations' }"
              @click="activeTab = 'reservations'"
            >
              📋 My Reservations
            </button>
          </li>
          <li class="nav-item">
            <button
              class="nav-link"
              :class="{ active: activeTab === 'report' }"
              @click="activeTab = 'report'"
            >
              📊 Monthly Activity Report
            </button>
          </li>
        </ul>
      </div>

      <!-- Main Container -->
      <div class="container p-4">
        <!-- Global Feedback Alert -->
        <div v-if="alertMessage" class="alert alert-dismissible fade show mb-4" :class="'alert-' + alertType">
          {{ alertMessage }}
          <button type="button" class="btn-close" @click="alertMessage = ''"></button>
        </div>

        <!-- ==================== TAB 1: DASHBOARD & BOOKING ==================== -->
        <div v-if="activeTab === 'dashboard'">
          
          <!-- Multi-Slot Active Reservations Section -->
          <div v-if="activeReservations.length > 0" class="mb-4">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <h5 class="fw-bold mb-0 text-dark d-flex align-items-center gap-2">
                <span class="badge bg-warning text-dark">{{ activeReservations.length }} Active</span>
                <span>My Active Parking Reservations</span>
              </h5>
              <small class="text-muted">Independent live timers & billing per active spot</small>
            </div>

            <div class="row g-3">
              <div v-for="res in activeReservations" :key="'active-' + res.id" class="col-md-6 col-lg-4">
                <div class="card shadow-sm border-0 border-start border-warning border-5 h-100 bg-white">
                  <div class="card-body p-3 d-flex flex-column justify-content-between">
                    <div>
                      <div class="d-flex justify-content-between align-items-center mb-2">
                        <div class="d-flex align-items-center gap-1">
                          <span class="badge" :class="res.status === 'scheduled' ? 'bg-info text-dark' : 'bg-warning text-dark'">
                            {{ res.status === 'scheduled' ? '📅 Scheduled' : '🟢 Active' }}
                          </span>
                          <span class="badge bg-light text-secondary border">
                            {{ res.booking_type === 'scheduled' ? 'Advance Pre-Book' : 'Park Now' }}
                          </span>
                        </div>
                        <span v-if="res.spot_type === 'handicap'" class="badge bg-info text-dark">♿ Handicap</span>
                        <span v-else class="badge bg-secondary">🚗 Regular</span>
                      </div>

                      <h5 class="fw-bold text-primary mb-1">{{ res.lot_name }}</h5>
                      <div class="badge bg-light text-secondary border mb-2">
                        🏢 {{ res.floor_name || 'Ground Floor' }}
                      </div>

                      <!-- Scheduled Window Info -->
                      <div v-if="res.booking_type === 'scheduled' && res.scheduled_start_time" class="p-2 bg-primary-subtle rounded-3 small mb-2 text-primary">
                        <div class="fw-semibold">📅 Reserved Window:</div>
                        <div>{{ formatTime(res.scheduled_start_time) }} ➔ {{ formatTime(res.scheduled_end_time) }}</div>
                      </div>

                      <div class="bg-light p-2.5 rounded-3 border small mb-3">
                        <div class="d-flex justify-content-between mb-1">
                          <span class="text-muted">Spot Number:</span>
                          <strong class="text-dark fs-6">{{ res.spot_number }}</strong>
                        </div>
                        <div class="d-flex justify-content-between mb-1">
                          <span class="text-muted">Vehicle Plate:</span>
                          <strong>{{ res.vehicle_number }}</strong>
                        </div>
                        <div class="d-flex justify-content-between mb-1">
                          <span class="text-muted">Entry Time:</span>
                          <span>{{ formatTime(res.parking_timestamp) }}</span>
                        </div>
                        <div class="d-flex justify-content-between text-primary border-top pt-1 mt-1">
                          <span>Elapsed Time:</span>
                          <strong class="font-monospace">⏱️ {{ getElapsed(res.parking_timestamp) }}</strong>
                        </div>
                        <div class="d-flex justify-content-between text-success">
                          <span>Est. Current Cost:</span>
                          <strong>₹{{ getRunningCost(res) }}</strong>
                        </div>
                      </div>
                    </div>

                    <button 
                      class="btn btn-outline-danger btn-sm w-100 fw-semibold shadow-sm"
                      @click="handleVacateSpot(res.id)" 
                      :disabled="vacating"
                    >
                      {{ vacating ? 'Releasing...' : '🚪 Vacate / Release Spot' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Section: Available Parking Lots for 4-Wheeler Booking -->
          <div class="d-flex justify-content-between align-items-center mb-3">
            <div>
              <h4 class="fw-bold mb-1">Available Parking Lots</h4>
              <p class="text-muted small mb-0">Choose a parking lot. Customers can reserve multiple spots simultaneously for families or fleets.</p>
            </div>
            <button class="btn btn-outline-success btn-sm" @click="fetchLots">🔄 Refresh Lots</button>
          </div>

          <div v-if="lots.length === 0" class="card text-center py-5 shadow-sm">
            <div class="card-body">
              <h5 class="text-muted">No parking lots currently available.</h5>
            </div>
          </div>

          <div class="row g-4">
            <div v-for="lot in lots" :key="lot.id" class="col-md-6 col-lg-4">
              <div class="card shadow-sm h-100 border-0 rounded-3">
                <div class="card-body d-flex flex-column p-4">
                  <div class="d-flex justify-content-between align-items-start mb-2">
                    <h5 class="fw-bold text-primary mb-0">{{ lot.prime_location_name }}</h5>
                    <span class="badge bg-success fs-6">₹{{ lot.price }}/hr</span>
                  </div>
                  <p class="text-muted small mb-1">{{ lot.address }}</p>
                  <p class="text-muted small mb-2">PIN: {{ lot.pin_code }}</p>
                  
                  <!-- Floor Count & Dynamic Pricing Badges -->
                  <div class="d-flex flex-wrap gap-1 mb-2">
                    <span class="badge bg-secondary-subtle text-secondary border">
                      🏢 {{ lot.floor_count || (lot.floors ? lot.floors.length : 1) }} Floor{{ (lot.floor_count || 1) > 1 ? 's' : '' }}
                    </span>
                    <span class="badge bg-light text-secondary border">⏱️ {{ lot.grace_period_minutes !== undefined ? lot.grace_period_minutes : 15 }}m Grace</span>
                    <span v-if="lot.daily_rate" class="badge bg-light text-success border">🛡️ ₹{{ lot.daily_rate }}/day Cap</span>
                    <span v-if="lot.overnight_rate" class="badge bg-light text-primary border">🌙 ₹{{ lot.overnight_rate }} Night</span>
                    <span v-if="lot.peak_multiplier > 1" class="badge bg-light text-warning-emphasis border">⚡ {{ lot.peak_multiplier }}x Peak</span>
                  </div>

                  <!-- Slot Type Breakdown -->
                  <div class="bg-light p-2.5 rounded-3 mb-3 small border">
                    <div class="d-flex justify-content-between mb-1">
                      <span>Total Available:</span>
                      <strong class="text-success">{{ lot.available_spots }} / {{ lot.number_of_spots }}</strong>
                    </div>
                    <div class="d-flex justify-content-between text-muted border-top pt-1 mt-1">
                      <span>🚗 Regular Available:</span>
                      <strong class="text-dark">{{ lot.regular_available_spots !== undefined ? lot.regular_available_spots : (lot.available_spots || 0) }}</strong>
                    </div>
                    <div class="d-flex justify-content-between text-muted">
                      <span>♿ Handicap Available:</span>
                      <strong class="text-primary">{{ lot.handicap_available_spots || 0 }}</strong>
                    </div>
                  </div>

                  <div class="mt-auto">
                    <button
                      class="btn btn-success w-100 py-2 fw-semibold shadow-sm"
                      :disabled="lot.available_spots === 0"
                      @click="openBookingModal(lot)"
                    >
                      <span v-if="lot.available_spots === 0">Fully Booked (0 Available)</span>
                      <span v-else>Book Spot (Regular / Handicap)</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div>

        <!-- ==================== TAB: CUSTOMER GARAGE ==================== -->
        <div v-if="activeTab === 'garage'">
          <div class="card shadow-sm border-0 mb-4">
            <div class="card-body p-4">
              <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
                <div>
                  <h4 class="fw-bold mb-1 d-flex align-items-center gap-2">
                    <span>🚘 My Vehicle Garage</span>
                    <span class="badge bg-primary fs-6">{{ vehicles.length }} Saved</span>
                  </h4>
                  <p class="text-muted small mb-0">Register your personal and family vehicles for seamless 1-click spot reservations.</p>
                </div>
                <div class="d-flex gap-2">
                  <button class="btn btn-outline-primary btn-sm" @click="fetchVehicles">🔄 Refresh</button>
                  <button class="btn btn-success btn-sm fw-semibold" @click="openAddVehicleModal">
                    ➕ Add Vehicle
                  </button>
                </div>
              </div>

              <!-- Vehicle Cards Grid -->
              <div v-if="vehicles.length === 0" class="text-center py-5 bg-light rounded-4 border">
                <div class="fs-1 mb-2">🚗</div>
                <h5 class="fw-bold text-dark">No vehicles registered yet</h5>
                <p class="text-muted small mb-3">Add your Car, SUV, EV, or Motorcycle to enable instant quick-booking without typing license plates.</p>
                <button class="btn btn-primary btn-sm fw-semibold" @click="openAddVehicleModal">
                  ➕ Add First Vehicle to Garage
                </button>
              </div>

              <div v-else class="row g-3">
                <div v-for="v in vehicles" :key="v.id" class="col-md-6 col-lg-4">
                  <div 
                    class="card h-100 border transition-card shadow-sm rounded-3 overflow-hidden"
                    :class="v.is_default ? 'border-primary border-2 bg-primary-subtle bg-opacity-10' : 'border-light-subtle bg-white'"
                  >
                    <div class="card-body p-3 d-flex flex-column justify-content-between">
                      <div>
                        <div class="d-flex justify-content-between align-items-center mb-2">
                          <span class="badge rounded-pill" :class="getVehicleBadgeClass(v.vehicle_type)">
                            {{ getVehicleTypeIcon(v.vehicle_type) }} {{ v.vehicle_type }}
                          </span>
                          <span v-if="v.is_default" class="badge bg-primary text-white rounded-pill px-2.5">
                            ⭐ Default Vehicle
                          </span>
                        </div>

                        <h4 class="fw-bold text-dark font-monospace mb-1">{{ v.license_plate }}</h4>
                        <div class="text-primary fw-semibold small mb-2">{{ v.nickname || 'Unnamed Vehicle' }}</div>
                        <div class="text-muted small">Registered: {{ formatTime(v.created_at) }}</div>
                      </div>

                      <div class="d-flex justify-content-between align-items-center mt-3 pt-2 border-top gap-1">
                        <button 
                          v-if="!v.is_default"
                          class="btn btn-xs btn-outline-secondary"
                          @click="setVehicleDefault(v)"
                          title="Set as Default Vehicle"
                        >
                          ⭐ Set Default
                        </button>
                        <span v-else class="text-primary small fw-semibold">
                          <i class="bi bi-check-circle-fill me-1"></i>Primary
                        </span>

                        <div class="d-flex gap-1 ms-auto">
                          <button class="btn btn-xs btn-outline-primary" @click="openEditVehicleModal(v)">
                            ✏️ Edit
                          </button>
                          <button class="btn btn-xs btn-outline-danger" @click="deleteVehicle(v.id)">
                            🗑️
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>

        <!-- ==================== TAB 2: MY RESERVATIONS ==================== -->
        <div v-if="activeTab === 'reservations'">
          <div class="card shadow-sm border-0">
            <div class="card-body p-4">
              <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
                <div>
                  <h4 class="fw-bold mb-1">My Parking Reservations & Audit Trail</h4>
                  <p class="text-muted small mb-0">Detailed location hierarchy (Venue → Floor → Spot), vehicle tags, and durations.</p>
                </div>
                <div class="d-flex gap-2">
                  <button class="btn btn-outline-primary btn-sm" @click="fetchReservations">🔄 Refresh</button>
                  <button class="btn btn-primary btn-sm" @click="handleExportCsv" :disabled="exporting">
                    {{ exporting ? 'Generating CSV...' : 'Export as CSV' }}
                  </button>
                </div>
              </div>

              <!-- Search and Filter Bar -->
              <div class="row g-2 mb-3 bg-light p-2.5 rounded-3 border">
                <div class="col-md-5">
                  <div class="input-group input-group-sm">
                    <span class="input-group-text bg-white"><i class="bi bi-search"></i> 🔍</span>
                    <input 
                      v-model="resSearchQuery" 
                      type="text" 
                      class="form-control" 
                      placeholder="Search venue, floor, spot, license plate, or hierarchy..."
                    />
                  </div>
                </div>
                <div class="col-md-3">
                  <select v-model="resVenueFilter" class="form-select form-select-sm">
                    <option value="all">All Venues / Facilities</option>
                    <option v-for="venue in uniqueVenues" :key="venue" :value="venue">{{ venue }}</option>
                  </select>
                </div>
                <div class="col-md-2">
                  <select v-model="resStatusFilter" class="form-select form-select-sm">
                    <option value="all">All Statuses</option>
                    <option value="active">Active (In Use)</option>
                    <option value="completed">Completed</option>
                  </select>
                </div>
                <div class="col-md-2 text-end text-muted small d-flex align-items-center justify-content-end">
                  Showing <strong>{{ filteredReservations.length }}</strong> of {{ reservations.length }}
                </div>
              </div>

              <!-- Export Job Alert / Download Pill -->
              <div v-if="exportJob" class="alert alert-info d-flex justify-content-between align-items-center py-2 mb-3">
                <span class="small">
                  CSV Export Job: <strong>{{ exportJob.status }}</strong>
                  <span v-if="exportJob.status === 'processing'"> (Batch processing in background...)</span>
                </span>
                <a
                  v-if="exportJob.status === 'completed'"
                  :href="'http://localhost:5000' + exportJob.download_url"
                  class="btn btn-sm btn-success fw-bold"
                  target="_blank"
                >
                  Download CSV
                </a>
              </div>

              <!-- Reservations Table with Full Location Hierarchy -->
              <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                  <thead class="table-light">
                    <tr>
                      <th>#</th>
                      <th>Location Hierarchy (Venue → Floor → Spot)</th>
                      <th>Vehicle</th>
                      <th>Space Type</th>
                      <th>Booking Mode</th>
                      <th>Entry Time</th>
                      <th>Exit Time</th>
                      <th>Duration</th>
                      <th>Total Cost</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="res in filteredReservations" :key="res.id">
                      <td>{{ res.id }}</td>
                      <td>
                        <div class="fw-semibold text-dark">
                          🏢 <span class="text-primary">{{ res.venue_name || res.lot_name }}</span>
                          <span class="text-muted mx-1">→</span>
                          <span class="badge bg-light text-secondary border">🏢 {{ res.floor_name || 'Ground Floor' }}</span>
                          <span class="text-muted mx-1">→</span>
                          <span class="badge bg-secondary font-monospace">{{ res.spot_number }}</span>
                        </div>
                      </td>
                      <td>
                        <div class="d-flex align-items-center gap-1.5">
                          <span>{{ getVehicleTypeIcon(res.vehicle_type) }}</span>
                          <span class="fw-bold font-monospace">{{ res.vehicle_number }}</span>
                        </div>
                      </td>
                      <td>
                        <span v-if="res.spot_type === 'handicap'" class="badge bg-info text-dark">♿ Handicap</span>
                        <span v-else class="badge bg-light text-dark border">🚗 Regular</span>
                      </td>
                      <td>
                        <span class="badge" :class="res.booking_type === 'scheduled' ? 'bg-primary-subtle text-primary border border-primary-subtle' : 'bg-light text-secondary border'">
                          {{ res.booking_type === 'scheduled' ? '📅 Advance' : '⚡ Park Now' }}
                        </span>
                      </td>
                      <td class="small">{{ formatTime(res.parking_timestamp) }}</td>
                      <td class="small">{{ res.leaving_timestamp ? formatTime(res.leaving_timestamp) : 'In Progress' }}</td>
                      <td class="small fw-semibold">
                        <span v-if="res.status === 'active'" class="text-primary font-monospace">
                          ⏱️ {{ getElapsed(res.parking_timestamp) }}
                        </span>
                        <span v-else class="text-muted">
                          {{ res.duration_formatted || `${res.duration_hours || 1}h` }}
                        </span>
                      </td>
                      <td>
                        <div class="fw-bold text-success">₹{{ res.parking_cost ? res.parking_cost.toFixed(2) : '0.00' }}</div>
                        <div v-if="res.grace_period_applied" class="badge bg-success-subtle text-success small">
                          ✨ 15m Grace (₹0)
                        </div>
                        <div v-if="res.overstay_penalty_cost > 0" class="badge bg-danger-subtle text-danger small">
                          ⚠️ +₹{{ res.overstay_penalty_cost.toFixed(2) }} Overstay
                        </div>
                      </td>
                      <td>
                        <span class="badge" :class="res.status === 'active' ? 'bg-warning text-dark' : (res.status === 'scheduled' ? 'bg-info text-dark' : 'bg-success')">
                          {{ res.status === 'active' ? '🟡 Active' : (res.status === 'scheduled' ? '📅 Scheduled' : '🟢 Completed') }}
                        </span>
                      </td>
                      <td>
                        <button
                          v-if="res.status === 'active' || res.status === 'scheduled'"
                          class="btn btn-danger btn-sm"
                          @click="handleVacateSpot(res.id)"
                        >
                          Vacate
                        </button>
                        <span v-else class="text-muted small">Released</span>
                      </td>
                    </tr>
                    <tr v-if="filteredReservations.length === 0">
                      <td colspan="11" class="text-center py-4 text-muted">No reservations found matching your search.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <!-- ==================== TAB 3: MONTHLY ACTIVITY REPORT ==================== -->
        <div v-if="activeTab === 'report'">
          <div class="card shadow-sm border-0 mb-4">
            <div class="card-body p-4">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <div>
                  <h4 class="fw-bold mb-1">Monthly Activity Report</h4>
                  <p class="text-muted small mb-0">Scheduled monthly summary of your parking usage and expenses.</p>
                </div>
                <div class="d-flex gap-2">
                  <button class="btn btn-outline-success btn-sm" @click="fetchMonthlyReport">🔄 Refresh Report</button>
                  <a
                    :href="'http://localhost:5000/api/reports/monthly?format=html'"
                    target="_blank"
                    class="btn btn-success btn-sm"
                  >
                    📄 View Full HTML Report
                  </a>
                </div>
              </div>

              <!-- Summary Metrics Cards -->
              <div class="row g-3 my-2">
                <div class="col-md-4">
                  <div class="card bg-light border-0 p-3">
                    <span class="text-muted small text-uppercase fw-bold">Spots Booked (This Month)</span>
                    <h2 class="fw-bold text-success mb-0 mt-2">{{ monthlyReport.total_spots_booked || 0 }}</h2>
                  </div>
                </div>
                <div class="col-md-4">
                  <div class="card bg-light border-0 p-3">
                    <span class="text-muted small text-uppercase fw-bold">Most Used Parking Lot</span>
                    <h4 class="fw-bold text-primary mb-0 mt-2">{{ monthlyReport.most_used_lot || 'None' }}</h4>
                  </div>
                </div>
                <div class="col-md-4">
                  <div class="card bg-light border-0 p-3">
                    <span class="text-muted small text-uppercase fw-bold">Amount Spent This Month</span>
                    <h2 class="fw-bold text-success mb-0 mt-2">₹{{ (monthlyReport.total_amount_spent || 0).toFixed(2) }}</h2>
                  </div>
                </div>
              </div>

              <!-- Embedded HTML View -->
              <div v-if="monthlyReport.html_content" class="mt-4 border rounded overflow-hidden">
                <iframe
                  :srcdoc="monthlyReport.html_content"
                  style="width: 100%; height: 500px; border: none;"
                ></iframe>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- ==================== BOOKING MODAL ==================== -->
      <div v-if="showBookingModal" class="modal-backdrop fade show"></div>
      <div v-if="showBookingModal" class="modal show d-block" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title fw-bold">Book Parking Spot</h5>
              <button type="button" class="btn-close" @click="showBookingModal = false"></button>
            </div>
            <form @submit.prevent="submitBooking">
              <div class="modal-body">
                <div class="p-3 bg-light rounded mb-3">
                  <div class="d-flex justify-content-between align-items-start">
                    <div>
                      <div class="fw-bold text-primary fs-5">{{ selectedLot?.prime_location_name }}</div>
                      <div class="small text-muted">{{ selectedLot?.address }}</div>
                    </div>
                    <span class="badge bg-success fs-6 fw-bold px-3 py-1.5 rounded-pill">
                      ₹{{ selectedLot?.price }}/hour
                    </span>
                  </div>
                  <!-- Facility Pricing Rules Overview -->
                  <div class="d-flex flex-wrap gap-1 mt-2 pt-2 border-top">
                    <span class="badge bg-white text-secondary border">⏱️ {{ selectedLot?.grace_period_minutes !== undefined ? selectedLot?.grace_period_minutes : 15 }}m Free Grace</span>
                    <span v-if="selectedLot?.daily_rate" class="badge bg-white text-success border">🛡️ ₹{{ selectedLot.daily_rate }}/day Cap</span>
                    <span v-if="selectedLot?.overnight_rate" class="badge bg-white text-primary border">🌙 ₹{{ selectedLot.overnight_rate }} Overnight</span>
                    <span v-if="selectedLot?.peak_multiplier > 1" class="badge bg-white text-warning border">⚡ {{ selectedLot.peak_multiplier }}x Peak Surge</span>
                    <span class="badge bg-white text-danger border">⚠️ ₹{{ selectedLot?.overstay_penalty_rate || 50 }}/h Overstay Penalty</span>
                  </div>
                </div>

                <!-- Booking Mode Selector (⚡ Park Now vs 📅 Advance Pre-Booking) -->
                <div class="mb-3">
                  <label class="form-label fw-bold">Reservation Mode *</label>
                  <div class="btn-group w-100" role="group">
                    <button
                      type="button"
                      class="btn py-2 fw-semibold"
                      :class="bookingForm.booking_type === 'immediate' ? 'btn-primary' : 'btn-outline-primary'"
                      @click="bookingForm.booking_type = 'immediate'"
                    >
                      ⚡ Park Now (Immediate)
                    </button>
                    <button
                      type="button"
                      class="btn py-2 fw-semibold"
                      :class="bookingForm.booking_type === 'scheduled' ? 'btn-primary' : 'btn-outline-primary'"
                      @click="bookingForm.booking_type = 'scheduled'"
                    >
                      📅 Advance Pre-Booking
                    </button>
                  </div>
                </div>

                <!-- Advance Pre-Booking Date/Time Windows -->
                <div v-if="bookingForm.booking_type === 'scheduled'" class="p-3 bg-primary-subtle rounded-3 mb-3 border border-primary-subtle">
                  <h6 class="fw-bold text-primary mb-2">📅 Schedule Future Parking Interval</h6>
                  <div class="row g-2">
                    <div class="col-sm-6">
                      <label class="form-label small fw-semibold text-dark mb-1">Scheduled Start *</label>
                      <input
                        v-model="bookingForm.scheduled_start_time"
                        type="datetime-local"
                        class="form-control form-control-sm"
                        required
                      />
                    </div>
                    <div class="col-sm-6">
                      <label class="form-label small fw-semibold text-dark mb-1">Scheduled End *</label>
                      <input
                        v-model="bookingForm.scheduled_end_time"
                        type="datetime-local"
                        class="form-control form-control-sm"
                        required
                      />
                    </div>
                  </div>
                  <!-- Dynamic Estimated Cost Widget -->
                  <div class="mt-2 pt-2 border-top border-primary-subtle d-flex justify-content-between align-items-center small">
                    <span class="text-secondary">Estimated Duration: <strong>{{ getScheduledDurationHours() }} hrs</strong></span>
                    <span class="text-success fw-bold fs-6">Estimated Tariff: ₹{{ getEstimatedCost() }}</span>
                  </div>
                  <div class="form-text x-small text-muted mt-1">
                    System verifies overlapping interval collisions and reserves your spot without race conditions.
                  </div>
                </div>

                <!-- Spot Type Selection: Regular or Handicap -->
                <div class="mb-3">
                  <label class="form-label fw-bold">Select Parking Space Type *</label>
                  <div class="row g-2">
                    <div class="col-6">
                      <div 
                        class="border rounded-3 p-3 text-center cursor-pointer h-100 transition-card"
                        :class="{
                          'border-success bg-success-subtle shadow-sm ring-2': bookingForm.spot_type === 'regular',
                          'opacity-50 pointer-events-none': (selectedLot?.regular_available_spots || 0) <= 0
                        }"
                        @click="(selectedLot?.regular_available_spots || 0) > 0 && (bookingForm.spot_type = 'regular')"
                      >
                        <div class="fs-3 mb-1">🚗</div>
                        <div class="fw-bold text-dark">Regular Space</div>
                        <span class="badge" :class="(selectedLot?.regular_available_spots || 0) > 0 ? 'bg-success' : 'bg-secondary'">
                          {{ selectedLot?.regular_available_spots || 0 }} Available
                        </span>
                      </div>
                    </div>
                    <div class="col-6">
                      <div 
                        class="border rounded-3 p-3 text-center cursor-pointer h-100 transition-card"
                        :class="{
                          'border-info bg-info-subtle shadow-sm ring-2': bookingForm.spot_type === 'handicap',
                          'opacity-50 pointer-events-none': (selectedLot?.handicap_available_spots || 0) <= 0
                        }"
                        @click="(selectedLot?.handicap_available_spots || 0) > 0 && (bookingForm.spot_type = 'handicap')"
                      >
                        <div class="fs-3 mb-1">♿</div>
                        <div class="fw-bold text-dark">Handicap Space</div>
                        <span class="badge" :class="(selectedLot?.handicap_available_spots || 0) > 0 ? 'bg-info text-dark' : 'bg-secondary'">
                          {{ selectedLot?.handicap_available_spots || 0 }} Available
                        </span>
                      </div>
                    </div>
                  </div>
                  <div class="form-text small mt-1">
                    Users can select standard 4-wheeler parking or dedicated handicap accessible parking.
                  </div>
                </div>

                <!-- Multi-Floor Selection (Optional Preference) -->
                <div v-if="selectedLot?.floors && selectedLot.floors.length > 1" class="mb-3">
                  <label class="form-label fw-bold">Select Preferred Floor (Optional)</label>
                  <select v-model="bookingForm.floor_id" class="form-select">
                    <option :value="null">Any Floor (Lowest Level First)</option>
                    <option v-for="fl in selectedLot.floors" :key="'modal-fl-' + fl.id" :value="fl.id">
                      🏢 {{ fl.floor_name }} ({{ fl.available_spots }} spots available)
                    </option>
                  </select>
                  <div class="form-text small">Multi-deck facility: pick a specific deck or let system auto-assign nearest to entrance.</div>
                </div>

                <!-- Vehicle Selection from Garage or Custom -->
                <div class="mb-3">
                  <div class="d-flex justify-content-between align-items-center mb-1">
                    <label class="form-label fw-bold mb-0">Select Vehicle *</label>
                    <span v-if="vehicles.length > 0" class="small text-muted">Pick from saved garage</span>
                  </div>

                  <!-- Quick Garage Selector Pills -->
                  <div v-if="vehicles.length > 0" class="d-flex flex-wrap gap-2 mb-2">
                    <button 
                      v-for="v in vehicles" 
                      :key="'garage-select-' + v.id"
                      type="button"
                      class="btn btn-sm rounded-pill text-start py-1 px-3"
                      :class="bookingForm.vehicle_id === v.id ? 'btn-primary text-white shadow-sm' : 'btn-outline-secondary bg-white'"
                      @click="selectGarageVehicle(v)"
                    >
                      <span>{{ getVehicleTypeIcon(v.vehicle_type) }} <strong>{{ v.license_plate }}</strong></span>
                      <span v-if="v.nickname" class="small opacity-75 ms-1">({{ v.nickname }})</span>
                    </button>
                    <button 
                      type="button" 
                      class="btn btn-sm rounded-pill py-1 px-3"
                      :class="bookingForm.vehicle_id === null ? 'btn-dark text-white' : 'btn-outline-dark bg-white'"
                      @click="bookingForm.vehicle_id = null"
                    >
                      ➕ Custom Plate
                    </button>
                  </div>

                  <!-- License Plate Input (editable if custom or auto-filled from garage) -->
                  <div class="input-group">
                    <span class="input-group-text bg-light fw-bold font-monospace">
                      {{ getVehicleTypeIcon(bookingForm.vehicle_type) }}
                    </span>
                    <input
                      v-model="bookingForm.vehicle_number"
                      type="text"
                      class="form-control font-monospace fw-bold"
                      placeholder="e.g. MH-02-CB-1234"
                      required
                    />
                    <select v-model="bookingForm.vehicle_type" class="form-select" style="max-width: 140px;">
                      <option value="Car">🚗 Car</option>
                      <option value="SUV">🚙 SUV</option>
                      <option value="EV">⚡ EV</option>
                      <option value="Motorcycle">🏍️ Bike</option>
                    </select>
                  </div>

                  <!-- Option to save to garage if typing a new custom plate -->
                  <div v-if="bookingForm.vehicle_id === null" class="form-check mt-2 small">
                    <input 
                      v-model="bookingForm.save_to_garage" 
                      class="form-check-input" 
                      type="checkbox" 
                      id="saveToGarageCheck"
                    />
                    <label class="form-check-label text-muted" for="saveToGarageCheck">
                      Save this vehicle to <strong>My Garage</strong> for 1-click booking next time
                    </label>
                  </div>
                </div>

                <div class="mb-3">
                  <label class="form-label">Remarks (Optional)</label>
                  <input
                    v-model="bookingForm.remarks"
                    type="text"
                    class="form-control"
                    placeholder="e.g. Blue Sedan, Gate 2"
                  />
                </div>

                <div class="alert alert-secondary small mb-0">
                  ℹ️ The system will automatically allocate the optimal available {{ bookingForm.spot_type }} spot.
                </div>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" @click="showBookingModal = false">Cancel</button>
                <button type="submit" class="btn btn-success" :disabled="bookingSubmitting">
                  {{ bookingSubmitting ? 'Allotting Spot...' : 'Confirm & Book Spot' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      <!-- ==================== VEHICLE MODAL (ADD / EDIT) ==================== -->
      <div v-if="showVehicleModal" class="modal-backdrop fade show"></div>
      <div v-if="showVehicleModal" class="modal show d-block" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title fw-bold">
                {{ vehicleModalMode === 'edit' ? '✏️ Edit Vehicle Profile' : '➕ Add Vehicle to Garage' }}
              </h5>
              <button type="button" class="btn-close" @click="showVehicleModal = false"></button>
            </div>
            <form @submit.prevent="saveVehicle">
              <div class="modal-body">
                <div class="mb-3">
                  <label class="form-label fw-bold">License Plate Number *</label>
                  <input
                    v-model="vehicleForm.license_plate"
                    type="text"
                    class="form-control font-monospace fw-bold"
                    placeholder="e.g. DL-01-AB-1234"
                    required
                  />
                  <div class="form-text small">Enter registration / number plate.</div>
                </div>

                <div class="mb-3">
                  <label class="form-label fw-bold">Vehicle Nickname / Alias</label>
                  <input
                    v-model="vehicleForm.nickname"
                    type="text"
                    class="form-control"
                    placeholder="e.g. Daily Commuter, Family Car, Red Sedan"
                  />
                  <div class="form-text small">Helpful label to identify which car or bike this is.</div>
                </div>

                <div class="mb-3">
                  <label class="form-label fw-bold">Vehicle Type *</label>
                  <div class="row g-2">
                    <div v-for="type in ['Car', 'SUV', 'EV', 'Motorcycle']" :key="type" class="col-6 col-sm-3">
                      <div 
                        class="border rounded-3 p-2 text-center cursor-pointer h-100"
                        :class="vehicleForm.vehicle_type === type ? 'border-primary bg-primary-subtle shadow-sm ring-2' : 'bg-light'"
                        @click="vehicleForm.vehicle_type = type"
                      >
                        <div class="fs-4">{{ getVehicleTypeIcon(type) }}</div>
                        <div class="small fw-bold mt-1">{{ type }}</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="form-check mt-3">
                  <input 
                    v-model="vehicleForm.is_default" 
                    class="form-check-input" 
                    type="checkbox" 
                    id="vehicleDefaultCheck"
                  />
                  <label class="form-check-label fw-semibold" for="vehicleDefaultCheck">
                    Set as Default Vehicle (automatically pre-selected when booking)
                  </label>
                </div>
              </div>

              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" @click="showVehicleModal = false">Cancel</button>
                <button type="submit" class="btn btn-primary fw-semibold" :disabled="savingVehicle">
                  {{ savingVehicle ? 'Saving...' : (vehicleModalMode === 'edit' ? 'Update Vehicle' : 'Save to Garage') }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import UserLogin from '../components/UserLogin.vue'
import UserRegister from '../components/UserRegister.vue'
import axios from 'axios'

export default {
  name: 'UserView',
  components: { UserLogin, UserRegister },
  data() {
    return {
      isLoggedIn: !!localStorage.getItem('userToken'),
      currentUser: JSON.parse(localStorage.getItem('userData') || '{}'),
      showRegister: this.$route.query.register === 'true',
      registerSuccessMessage: this.$route.query.registered ? 'Registration successful! Please log in.' : '',
      activeTab: 'dashboard',
      alertMessage: '',
      alertType: 'success',
      lots: [],
      reservations: [],
      activeReservations: [],
      activeReservation: null,
      vehicles: [],
      vehiclesLoading: false,
      showVehicleModal: false,
      vehicleModalMode: 'add',
      selectedVehicleId: null,
      vehicleForm: {
        license_plate: '',
        nickname: '',
        vehicle_type: 'Car',
        is_default: false
      },
      savingVehicle: false,
      resSearchQuery: '',
      resStatusFilter: 'all',
      resVenueFilter: 'all',
      nowTimestamp: Date.now(),
      timerInterval: null,
      showBookingModal: false,
      selectedLot: null,
      bookingForm: {
        booking_type: 'immediate',
        scheduled_start_time: '',
        scheduled_end_time: '',
        vehicle_id: null,
        vehicle_number: '',
        vehicle_type: 'Car',
        save_to_garage: false,
        vehicle_nickname: '',
        remarks: '',
        spot_type: 'regular',
        floor_id: null,
        parking_timestamp: ''
      },
      bookingSubmitting: false,
      vacating: false,
      exporting: false,
      exportJob: null,
      monthlyReport: {}
    }
  },
  computed: {
    filteredReservations() {
      let list = this.reservations
      if (this.resStatusFilter !== 'all') {
        list = list.filter(r => r.status === this.resStatusFilter)
      }
      if (this.resVenueFilter !== 'all') {
        list = list.filter(r => (r.venue_name || r.lot_name) === this.resVenueFilter)
      }
      if (this.resSearchQuery && this.resSearchQuery.trim()) {
        const q = this.resSearchQuery.toLowerCase().trim()
        list = list.filter(r => 
          (r.venue_name && r.venue_name.toLowerCase().includes(q)) ||
          (r.lot_name && r.lot_name.toLowerCase().includes(q)) ||
          (r.floor_name && r.floor_name.toLowerCase().includes(q)) ||
          (r.spot_number && r.spot_number.toLowerCase().includes(q)) ||
          (r.vehicle_number && r.vehicle_number.toLowerCase().includes(q)) ||
          (r.location_hierarchy && r.location_hierarchy.toLowerCase().includes(q))
        )
      }
      return list
    },
    uniqueVenues() {
      const set = new Set()
      this.reservations.forEach(r => {
        const name = r.venue_name || r.lot_name
        if (name) set.add(name)
      })
      return Array.from(set)
    }
  },
  watch: {
    '$route.query'(newQuery) {
      if (newQuery.register === 'true') {
        this.showRegister = true
      } else if (newQuery.register === 'false') {
        this.showRegister = false
      }
      if (newQuery.registered) {
        this.registerSuccessMessage = 'Registration successful! Please log in.'
      }
    },
    activeTab(newTab) {
      if (!this.isLoggedIn) return
      if (newTab === 'dashboard') {
        this.fetchLots()
        this.fetchReservations()
        this.fetchVehicles()
      } else if (newTab === 'garage') {
        this.fetchVehicles()
      } else if (newTab === 'reservations') {
        this.fetchReservations()
      } else if (newTab === 'report') {
        this.fetchMonthlyReport()
      }
    }
  },
  mounted() {
    if (this.isLoggedIn) {
      this.fetchLots()
      this.fetchReservations()
      this.fetchVehicles()
    }
    this.timerInterval = setInterval(() => {
      this.nowTimestamp = Date.now()
    }, 1000)
  },
  beforeUnmount() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval)
    }
  },
  methods: {
    getAuthHeaders() {
      const token = localStorage.getItem('userToken')
      return { headers: { Authorization: `Bearer ${token}` } }
    },
    getElapsed(parkingTimestamp) {
      if (!parkingTimestamp) return '0s'
      const safeStr = (parkingTimestamp.endsWith('Z') || parkingTimestamp.includes('+')) 
        ? parkingTimestamp 
        : `${parkingTimestamp}Z`
      const start = new Date(safeStr).getTime()
      if (isNaN(start)) return '0s'
      const diffSecs = Math.max(0, Math.floor((this.nowTimestamp - start) / 1000))
      const hours = Math.floor(diffSecs / 3600)
      const minutes = Math.floor((diffSecs % 3600) / 60)
      const seconds = diffSecs % 60
      if (hours > 0) {
        return `${hours}h ${minutes}m ${seconds}s`
      } else if (minutes > 0) {
        return `${minutes}m ${seconds}s`
      } else {
        return `${seconds}s`
      }
    },
    getRunningCost(res) {
      if (!res.parking_timestamp) return '0.00'
      const safeStr = (res.parking_timestamp.endsWith('Z') || res.parking_timestamp.includes('+')) 
        ? res.parking_timestamp 
        : `${res.parking_timestamp}Z`
      const start = new Date(safeStr).getTime()
      if (isNaN(start)) return '0.00'
      const diffHours = Math.max(1, (this.nowTimestamp - start) / 3600000)
      const price = res.price_per_hour || res.lot_price || 0
      return (diffHours * price).toFixed(2)
    },
    openRegister() {
      this.registerSuccessMessage = ''
      this.showRegister = true
    },
    openLogin() {
      this.showRegister = false
    },
    handleLoginSuccess() {
      this.isLoggedIn = true
      this.currentUser = JSON.parse(localStorage.getItem('userData') || '{}')
      this.registerSuccessMessage = ''
      this.fetchLots()
      this.fetchReservations()
    },
    handleRegisterSuccess() {
      this.showRegister = false
      this.registerSuccessMessage = 'Registration successful! Please log in.'
    },
    logout() {
      localStorage.removeItem('userToken')
      localStorage.removeItem('userData')
      this.isLoggedIn = false
      this.activeReservations = []
      this.activeReservation = null
      this.reservations = []
      this.lots = []
    },
    showAlert(msg, type = 'success') {
      this.alertMessage = msg
      this.alertType = type
      setTimeout(() => { this.alertMessage = '' }, 5000)
    },
    formatTime(isoStr) {
      if (!isoStr) return 'N/A'
      const safeStr = (isoStr.endsWith('Z') || isoStr.includes('+')) ? isoStr : `${isoStr}Z`
      const d = new Date(safeStr)
      return isNaN(d.getTime()) ? new Date(isoStr).toLocaleString() : d.toLocaleString()
    },
    async fetchLots() {
      try {
        const res = await axios.get('http://localhost:5000/api/parking-lots')
        this.lots = res.data.parking_lots || []
      } catch (err) {
        console.error(err)
      }
    },
    async fetchReservations() {
      try {
        const res = await axios.get('http://localhost:5000/api/reservations', this.getAuthHeaders())
        this.reservations = res.data.reservations || []
        this.activeReservations = this.reservations.filter(r => r.status === 'active')
        this.activeReservation = this.activeReservations[0] || null
      } catch (err) {
        if (err.response?.status === 401) {
          this.logout()
        }
      }
    },
    openBookingModal(lot) {
      this.selectedLot = lot
      const defaultType = (lot.regular_available_spots > 0 || lot.regular_available_spots === undefined)
        ? 'regular'
        : (lot.handicap_available_spots > 0 ? 'handicap' : 'regular')
      
      // Capture the exact local time when the booking is selected
      const now = new Date()
      const localIso = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16)

      // Default scheduled start to 1 hour from now, end to 4 hours from now
      const startSched = new Date(now.getTime() + 60 * 60 * 1000)
      const endSched = new Date(now.getTime() + 4 * 60 * 60 * 1000)
      const startSchedIso = new Date(startSched.getTime() - startSched.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
      const endSchedIso = new Date(endSched.getTime() - endSched.getTimezoneOffset() * 60000).toISOString().slice(0, 16)

      // Auto-select default vehicle from garage if available
      const defVehicle = this.vehicles.find(v => v.is_default) || this.vehicles[0] || null

      this.bookingForm = {
        booking_type: 'immediate',
        scheduled_start_time: startSchedIso,
        scheduled_end_time: endSchedIso,
        vehicle_id: defVehicle ? defVehicle.id : null,
        vehicle_number: defVehicle ? defVehicle.license_plate : '',
        vehicle_type: defVehicle ? defVehicle.vehicle_type : 'Car',
        save_to_garage: false,
        vehicle_nickname: '',
        remarks: '',
        spot_type: defaultType,
        floor_id: null,
        parking_timestamp: localIso
      }
      this.showBookingModal = true
    },
    getScheduledDurationHours() {
      if (!this.bookingForm.scheduled_start_time || !this.bookingForm.scheduled_end_time) return 0
      const s = new Date(this.bookingForm.scheduled_start_time).getTime()
      const e = new Date(this.bookingForm.scheduled_end_time).getTime()
      if (isNaN(s) || isNaN(e) || e <= s) return 0
      return Math.round(((e - s) / 3600000) * 10) / 10
    },
    getEstimatedCost() {
      if (!this.selectedLot) return '0.00'
      const hours = this.getScheduledDurationHours()
      if (hours <= 0) return '0.00'
      const lot = this.selectedLot
      const hourly = lot.price || 0
      let total = Math.max(hours, 1) * hourly
      if (lot.daily_rate && lot.daily_rate > 0) {
        const days = Math.max(1, hours / 24.0)
        const dailyCap = days * lot.daily_rate
        if (total > dailyCap) total = dailyCap
      }
      return total.toFixed(2)
    },
    selectGarageVehicle(v) {
      this.bookingForm.vehicle_id = v.id
      this.bookingForm.vehicle_number = v.license_plate
      this.bookingForm.vehicle_type = v.vehicle_type
    },
    getVehicleTypeIcon(type) {
      if (!type) return '🚗'
      const t = type.toLowerCase()
      if (t === 'suv') return '🚙'
      if (t === 'ev' || t === 'electric') return '⚡'
      if (t === 'motorcycle' || t === 'bike') return '🏍️'
      return '🚗'
    },
    getVehicleBadgeClass(type) {
      if (!type) return 'bg-secondary text-white'
      const t = type.toLowerCase()
      if (t === 'suv') return 'bg-primary text-white'
      if (t === 'ev' || t === 'electric') return 'bg-success text-white'
      if (t === 'motorcycle' || t === 'bike') return 'bg-warning text-dark'
      return 'bg-info-subtle text-info-emphasis border border-info-subtle'
    },
    async fetchVehicles() {
      if (!this.isLoggedIn) return
      this.vehiclesLoading = true
      try {
        const res = await axios.get('http://localhost:5000/api/vehicles', this.getAuthHeaders())
        this.vehicles = res.data.vehicles || []
      } catch (err) {
        console.error('Failed to fetch vehicles:', err)
      } finally {
        this.vehiclesLoading = false
      }
    },
    openAddVehicleModal() {
      this.vehicleModalMode = 'add'
      this.selectedVehicleId = null
      this.vehicleForm = {
        license_plate: '',
        nickname: '',
        vehicle_type: 'Car',
        is_default: this.vehicles.length === 0
      }
      this.showVehicleModal = true
    },
    openEditVehicleModal(v) {
      this.vehicleModalMode = 'edit'
      this.selectedVehicleId = v.id
      this.vehicleForm = {
        license_plate: v.license_plate,
        nickname: v.nickname,
        vehicle_type: v.vehicle_type,
        is_default: v.is_default
      }
      this.showVehicleModal = true
    },
    async saveVehicle() {
      if (!this.vehicleForm.license_plate.trim()) return
      this.savingVehicle = true
      try {
        const payload = {
          license_plate: this.vehicleForm.license_plate.trim().toUpperCase(),
          nickname: this.vehicleForm.nickname.trim(),
          vehicle_type: this.vehicleForm.vehicle_type,
          is_default: this.vehicleForm.is_default
        }
        if (this.vehicleModalMode === 'edit') {
          await axios.put(`http://localhost:5000/api/vehicles/${this.selectedVehicleId}`, payload, this.getAuthHeaders())
          this.showAlert('Vehicle profile updated successfully!')
        } else {
          await axios.post('http://localhost:5000/api/vehicles', payload, this.getAuthHeaders())
          this.showAlert('Vehicle registered to your garage successfully!')
        }
        this.showVehicleModal = false
        this.fetchVehicles()
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'Failed to save vehicle', 'danger')
      } finally {
        this.savingVehicle = false
      }
    },
    async deleteVehicle(vehicleId) {
      if (!confirm('Are you sure you want to remove this vehicle from your garage?')) return
      try {
        await axios.delete(`http://localhost:5000/api/vehicles/${vehicleId}`, this.getAuthHeaders())
        this.showAlert('Vehicle removed from your garage.')
        this.fetchVehicles()
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'Failed to delete vehicle', 'danger')
      }
    },
    async setVehicleDefault(v) {
      try {
        await axios.put(`http://localhost:5000/api/vehicles/${v.id}`, { is_default: true }, this.getAuthHeaders())
        this.showAlert(`${v.license_plate} set as default vehicle.`)
        this.fetchVehicles()
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'Failed to set default vehicle', 'danger')
      }
    },
    async submitBooking() {
      if (!this.bookingForm.vehicle_number.trim()) return
      this.bookingSubmitting = true
      try {
        // In "Park Now" (immediate), entry time is automatically captured as current time
        const isoTimestamp = this.bookingForm.booking_type === 'immediate'
          ? new Date().toISOString()
          : (this.bookingForm.scheduled_start_time ? new Date(this.bookingForm.scheduled_start_time).toISOString() : new Date().toISOString())

        const payload = {
          lot_id: this.selectedLot.id,
          booking_type: this.bookingForm.booking_type,
          vehicle_id: this.bookingForm.vehicle_id,
          vehicle_number: this.bookingForm.vehicle_number.trim(),
          vehicle_type: this.bookingForm.vehicle_type || 'Car',
          save_to_garage: this.bookingForm.save_to_garage,
          vehicle_nickname: this.bookingForm.vehicle_nickname,
          remarks: this.bookingForm.remarks.trim(),
          spot_type: this.bookingForm.spot_type || 'regular',
          floor_id: this.bookingForm.floor_id,
          parking_timestamp: isoTimestamp
        }

        if (this.bookingForm.booking_type === 'scheduled') {
          const sDate = new Date(this.bookingForm.scheduled_start_time)
          const eDate = new Date(this.bookingForm.scheduled_end_time)
          if (isNaN(sDate.getTime()) || isNaN(eDate.getTime()) || eDate <= sDate) {
            this.showAlert('Please provide valid scheduled start and end times (end must be after start).', 'danger')
            this.bookingSubmitting = false
            return
          }
          payload.scheduled_start_time = sDate.toISOString()
          payload.scheduled_end_time = eDate.toISOString()
        }

        const res = await axios.post('http://localhost:5000/api/reservations', payload, this.getAuthHeaders())
        const typeLabel = res.data.spot_type === 'handicap' ? 'Handicap' : 'Regular'
        const floorText = res.data.floor_name ? ` on ${res.data.floor_name}` : ''
        const modeLabel = res.data.booking_type === 'scheduled' ? 'pre-booked for your schedule' : 'allotted via Quick-Book engine'
        this.showAlert(`${typeLabel} spot "${res.data.spot_number}"${floorText} ${modeLabel} in ${res.data.lot_name}!`)
        this.showBookingModal = false
        this.fetchLots()
        this.fetchReservations()
        this.fetchVehicles()
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'Booking failed', 'danger')
      } finally {
        this.bookingSubmitting = false
      }
    },
    async handleVacateSpot(resId) {
      if (!confirm('Are you ready to vacate and release this parking spot?')) return
      this.vacating = true
      try {
        const res = await axios.post(`http://localhost:5000/api/reservations/${resId}/vacate`, {}, this.getAuthHeaders())
        this.showAlert(`Spot vacated successfully! Total Parking Cost: ₹${res.data.parking_cost.toFixed(2)} (Duration: ${res.data.duration_hours} hrs)`)
        this.fetchLots()
        this.fetchReservations()
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'Failed to vacate spot', 'danger')
      } finally {
        this.vacating = false
      }
    },
    async handleExportCsv() {
      this.exporting = true
      try {
        const res = await axios.post('http://localhost:5000/api/export/csv', {}, this.getAuthHeaders())
        this.exportJob = { id: res.data.job_id, status: 'processing' }
        this.pollExportStatus(res.data.job_id)
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'CSV export failed to initiate', 'danger')
        this.exporting = false
      }
    },
    async pollExportStatus(jobId) {
      const interval = setInterval(async () => {
        try {
          const res = await axios.get(`http://localhost:5000/api/export/${jobId}/status`, this.getAuthHeaders())
          this.exportJob = res.data
          if (res.data.status === 'completed' || res.data.status === 'failed') {
            clearInterval(interval)
            this.exporting = false
            if (res.data.status === 'completed') {
              this.showAlert('Parking history CSV export is ready for download!')
            }
          }
        } catch (err) {
          clearInterval(interval)
          this.exporting = false
        }
      }, 1000)
    },
    async fetchMonthlyReport() {
      try {
        const res = await axios.get('http://localhost:5000/api/reports/monthly', this.getAuthHeaders())
        this.monthlyReport = res.data
      } catch (err) {
        console.error(err)
      }
    }
  }
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1040;
}
.modal {
  z-index: 1050;
}
</style>