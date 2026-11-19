<template>
  <div class="user-portal-root min-vh-100 bg-slate-50">
    
    <!-- When Logged Out: Authentication Views -->
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
    
    <!-- When Logged In: Main User Dashboard -->
    <div v-else class="dashboard-shell">
      
      <!-- Top Navigation Header -->
      <header class="navbar navbar-expand-lg navbar-light bg-white border-bottom sticky-top py-2.5 px-3 px-md-4 shadow-xs">
        <div class="container-fluid px-0">
          
          <!-- Logo & Portal Indicator -->
          <div class="d-flex align-items-center gap-3">
            <router-link to="/" class="d-flex align-items-center gap-2 text-decoration-none text-dark">
              <div class="brand-icon-box bg-success text-white rounded-3 d-flex align-items-center justify-content-center shadow-xs">
                <i class="bi bi-p-square-fill fs-5"></i>
              </div>
              <span class="fw-bold fs-5 tracking-tight">Smart<span class="text-success">Park</span></span>
            </router-link>
            <span class="badge bg-light text-secondary border px-2.5 py-1 rounded-pill small fw-medium d-none d-sm-inline-block">
              <i class="bi bi-person-fill text-success me-1"></i> Driver Portal
            </span>
          </div>

          <!-- User Controls & Active Indicator -->
          <div class="d-flex align-items-center gap-2 gap-md-3 ms-auto">
            
            <!-- Quick Active Spots Pill (if any) -->
            <button 
              v-if="activeReservations.length > 0" 
              class="btn btn-warning-subtle text-warning-emphasis border border-warning-subtle btn-sm rounded-pill px-3 py-1 fw-semibold d-flex align-items-center gap-1.5 shadow-xs"
              @click="activeTab = 'dashboard'"
              title="View your active parking sessions"
            >
              <span class="pulse-dot-warning"></span>
              <span>{{ activeReservations.length }} Spot{{ activeReservations.length > 1 ? 's' : '' }} Active</span>
            </button>

            <!-- User Profile Chip -->
            <div class="d-flex align-items-center gap-2 bg-light border rounded-pill py-1 px-2.5 text-secondary">
              <div class="avatar-circle bg-success text-white rounded-circle d-flex align-items-center justify-content-center fw-bold small">
                {{ (currentUser.username || 'U').charAt(0).toUpperCase() }}
              </div>
              <span class="small fw-semibold text-dark d-none d-md-inline">{{ currentUser.username || 'Driver' }}</span>
            </div>

            <!-- Logout Button -->
            <button class="btn btn-outline-secondary btn-sm rounded-pill px-3 py-1 fw-medium" @click="logout" title="Sign out of portal">
              <i class="bi bi-box-arrow-right me-1"></i>
              <span class="d-none d-sm-inline">Sign Out</span>
            </button>
          </div>

        </div>
      </header>
      
      <!-- Clean Secondary Tab Navigation -->
      <div class="bg-white border-bottom px-3 px-md-4">
        <div class="container-fluid px-0">
          <ul class="nav nav-pills gap-1 py-2 user-nav-tabs">
            <li class="nav-item">
              <button
                class="nav-link py-1.5 px-3 rounded-pill fw-semibold small d-flex align-items-center gap-1.5"
                :class="{ active: activeTab === 'dashboard' }"
                @click="activeTab = 'dashboard'"
              >
                <i class="bi bi-geo-alt-fill"></i>
                <span>Find & Book</span>
              </button>
            </li>
            <li class="nav-item">
              <button
                class="nav-link py-1.5 px-3 rounded-pill fw-semibold small d-flex align-items-center gap-1.5"
                :class="{ active: activeTab === 'garage' }"
                @click="activeTab = 'garage'"
              >
                <i class="bi bi-car-front-fill"></i>
                <span>My Garage</span>
                <span v-if="vehicles.length" class="badge rounded-pill ms-1" :class="activeTab === 'garage' ? 'bg-white text-dark' : 'bg-secondary-subtle text-secondary'">
                  {{ vehicles.length }}
                </span>
              </button>
            </li>
            <li class="nav-item">
              <button
                class="nav-link py-1.5 px-3 rounded-pill fw-semibold small d-flex align-items-center gap-1.5"
                :class="{ active: activeTab === 'reservations' }"
                @click="activeTab = 'reservations'"
              >
                <i class="bi bi-clock-history"></i>
                <span>My Bookings</span>
                <span v-if="reservations.length" class="badge rounded-pill ms-1" :class="activeTab === 'reservations' ? 'bg-white text-dark' : 'bg-secondary-subtle text-secondary'">
                  {{ reservations.length }}
                </span>
              </button>
            </li>
            <li class="nav-item">
              <button
                class="nav-link py-1.5 px-3 rounded-pill fw-semibold small d-flex align-items-center gap-1.5"
                :class="{ active: activeTab === 'subscriptions' }"
                @click="activeTab = 'subscriptions'"
              >
                <i class="bi bi-ticket-perforated-fill"></i>
                <span>Commuter Passes</span>
                <span v-if="subscriptions.length" class="badge rounded-pill ms-1" :class="activeTab === 'subscriptions' ? 'bg-white text-dark' : 'bg-primary-subtle text-primary'">
                  {{ subscriptions.length }}
                </span>
              </button>
            </li>
            <li class="nav-item">
              <button
                class="nav-link py-1.5 px-3 rounded-pill fw-semibold small d-flex align-items-center gap-1.5"
                :class="{ active: activeTab === 'report' }"
                @click="activeTab = 'report'"
              >
                <i class="bi bi-file-earmark-bar-graph"></i>
                <span>Monthly Report</span>
              </button>
            </li>
          </ul>
        </div>
      </div>

      <!-- Main Dashboard Content Container -->
      <main class="container-fluid px-3 px-md-4 py-4 max-w-1400 mx-auto">
        
        <!-- Global Feedback Alert Banner -->
        <div v-if="alertMessage" class="alert alert-dismissible fade show rounded-3 shadow-xs mb-4" :class="'alert-' + alertType">
          <div class="d-flex align-items-center gap-2">
            <i class="bi" :class="alertType === 'success' ? 'bi-check-circle-fill text-success fs-5' : 'bi-exclamation-triangle-fill text-danger fs-5'"></i>
            <span class="fw-medium">{{ alertMessage }}</span>
          </div>
          <button type="button" class="btn-close" @click="alertMessage = ''"></button>
        </div>

        <!-- ========================================================= -->
        <!-- TAB 1: FIND & BOOK PARKING (DASHBOARD)                     -->
        <!-- ========================================================= -->
        <div v-if="activeTab === 'dashboard'">
          
          <!-- Active Sessions Banner (Only Shown When Parked) -->
          <section v-if="activeReservations.length > 0" class="mb-4">
            <div class="d-flex justify-content-between align-items-center mb-2.5">
              <h6 class="fw-bold text-dark mb-0 d-flex align-items-center gap-2">
                <span class="pulse-dot-green"></span>
                <span>Active Parking Sessions</span>
                <span class="badge bg-success-subtle text-success border border-success-subtle rounded-pill">
                  {{ activeReservations.length }} Active
                </span>
              </h6>
              <span class="text-muted small">Live timer running</span>
            </div>

            <div class="row g-3">
              <div v-for="res in activeReservations" :key="'active-' + res.id" class="col-md-6 col-xl-4">
                <div class="card h-100 border-0 shadow-sm rounded-4 bg-white active-session-card">
                  <div class="card-body p-3.5 d-flex flex-column justify-content-between">
                    <div>
                      
                      <!-- Header Row -->
                      <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                          <span class="badge bg-success-subtle text-success border border-success-subtle rounded-pill px-2 py-0.5 small fw-semibold">
                            🟢 In Session
                          </span>
                          <span class="badge bg-light text-secondary border rounded-pill ms-1 px-2 py-0.5 small">
                            {{ res.booking_type === 'scheduled' ? 'Advance' : 'Park Now' }}
                          </span>
                        </div>
                        <span v-if="res.spot_type === 'handicap'" class="badge bg-info-subtle text-info border border-info-subtle rounded-pill">
                          ♿ Handicap
                        </span>
                        <span v-else class="badge bg-light text-secondary border rounded-pill">
                          🚗 Regular
                        </span>
                      </div>

                      <!-- Facility & Location Hierarchy -->
                      <h5 class="fw-bold text-dark mb-1">{{ res.lot_name }}</h5>
                      <div class="text-muted small mb-3 d-flex align-items-center gap-1.5 flex-wrap">
                        <span class="badge bg-slate-100 text-dark border">Deck: {{ res.floor_name || 'Ground' }}</span>
                        <span class="text-secondary">•</span>
                        <span class="badge bg-dark text-white font-monospace">Bay #{{ res.spot_number }}</span>
                        <span class="text-secondary">•</span>
                        <span class="font-monospace fw-semibold text-dark">{{ res.vehicle_number }}</span>
                      </div>

                      <!-- Scheduled Window (if scheduled) -->
                      <div v-if="res.booking_type === 'scheduled' && res.scheduled_start_time" class="bg-primary-subtle text-primary p-2 rounded-3 small mb-2">
                        <i class="bi bi-calendar-event me-1"></i>
                        <span>{{ formatTime(res.scheduled_start_time) }} ➔ {{ formatTime(res.scheduled_end_time) }}</span>
                      </div>

                      <!-- Scheduled / Booked End Window & Overstay Alert -->
                      <div v-if="res.scheduled_end_time" class="p-2 rounded-3 small mb-2 border" :class="isOverstaying(res) ? 'bg-danger-subtle text-danger border-danger-subtle' : 'bg-primary-subtle text-primary border-primary-subtle'">
                        <div class="d-flex justify-content-between align-items-center flex-wrap gap-1">
                          <span>
                            <i class="bi" :class="isOverstaying(res) ? 'bi-exclamation-triangle-fill text-danger' : 'bi-calendar-check'"></i>
                            <strong class="ms-1">{{ isOverstaying(res) ? 'Overstaying!' : 'Booked Until:' }}</strong>
                            {{ formatTime(res.scheduled_end_time) }}
                          </span>
                          <span v-if="isOverstaying(res)" class="badge bg-danger text-white">
                            +₹{{ res.overstay_penalty_rate || 50 }}/hr Surcharge
                          </span>
                        </div>
                      </div>

                      <!-- Live Metrics Strip -->
                      <div class="bg-light p-2.5 rounded-3 border mb-3">
                        <div class="d-flex justify-content-between align-items-center mb-1 small">
                          <span class="text-muted">Parked Since:</span>
                          <span class="text-dark fw-medium">{{ formatTime(res.parking_timestamp) }}</span>
                        </div>
                        <div class="d-flex justify-content-between align-items-center mb-1">
                          <span class="text-muted small">Elapsed Time:</span>
                          <strong class="font-monospace text-primary">⏱️ {{ getElapsed(res.parking_timestamp) }}</strong>
                        </div>
                        <div class="d-flex justify-content-between align-items-center border-top pt-1 text-success">
                          <span class="small fw-semibold">Current Tariff:</span>
                          <strong class="fs-6 font-monospace">₹{{ getRunningCost(res) }}</strong>
                        </div>
                      </div>

                    </div>

                    <!-- Vacate / Release Action -->
                    <button 
                      class="btn btn-outline-danger btn-sm w-100 py-2 fw-semibold rounded-3 shadow-xs d-flex align-items-center justify-content-center gap-2"
                      @click="handleVacateSpot(res.id)" 
                      :disabled="vacating"
                    >
                      <i class="bi bi-box-arrow-left"></i>
                      <span>{{ vacating ? 'Releasing Spot...' : 'Vacate & End Session' }}</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- Search & Filter Controls (Streamlined, No Clutter) -->
          <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
            <div>
              <h4 class="fw-bold text-dark mb-0.5">Explore Parking Spaces</h4>
              <p class="text-muted small mb-0">Search facilities by name, street address, or postal PIN code.</p>
            </div>
            <button class="btn btn-outline-secondary btn-sm rounded-pill px-3 d-flex align-items-center gap-1.5" @click="fetchLots('')">
              <i class="bi bi-arrow-clockwise"></i>
              <span>Refresh</span>
            </button>
          </div>

          <!-- Clean Search & Filter Bar -->
          <div class="card border-0 shadow-xs rounded-4 bg-white mb-4 p-3">
            <div class="card-body p-0">
              <div class="row g-2 align-items-center">
                
                <!-- Search Input -->
                <div class="col-md-8 col-lg-9">
                  <div class="input-group">
                    <span class="input-group-text bg-light border-0 text-muted ps-3 pe-2 rounded-start-pill">
                      <i class="bi bi-search text-success"></i>
                    </span>
                    <input
                      v-model="lotSearchQuery"
                      type="text"
                      class="form-control bg-light border-0 shadow-none ps-1 fs-6 rounded-end-pill"
                      placeholder="Search parking facilities by name, address, or PIN code..."
                      @keydown.esc="lotSearchQuery = ''"
                    />
                    <button
                      v-if="lotSearchQuery"
                      class="btn btn-link text-muted border-0 pe-3 text-decoration-none"
                      type="button"
                      @click="lotSearchQuery = ''"
                      title="Clear search"
                    >
                      <i class="bi bi-x-circle-fill text-secondary"></i>
                    </button>
                  </div>
                </div>

                <!-- Results Counter Pill -->
                <div class="col-md-4 col-lg-3 text-md-end">
                  <span class="badge bg-light text-secondary border py-2 px-3 rounded-pill fw-normal w-100 text-center">
                    Showing <strong>{{ filteredLots.length }}</strong> of {{ lots.length }} Facilities
                  </span>
                </div>

              </div>

              <!-- Quick Filter Pills -->
              <div class="d-flex align-items-center gap-1.5 mt-3 pt-2.5 border-top flex-wrap">
                <span class="x-small text-muted fw-semibold me-1"><i class="bi bi-funnel-fill me-1"></i>Filter:</span>
                <button 
                  class="btn btn-xs rounded-pill px-2.5 py-1 fw-medium transition-all"
                  :class="activeQuickFilter === 'all' ? 'btn-dark text-white shadow-xs' : 'btn-outline-secondary bg-white'"
                  @click="activeQuickFilter = 'all'"
                >
                  All Facilities
                </button>
                <button 
                  class="btn btn-xs rounded-pill px-2.5 py-1 fw-medium transition-all"
                  :class="activeQuickFilter === 'available' ? 'btn-success text-white shadow-xs' : 'btn-outline-secondary bg-white'"
                  @click="activeQuickFilter = 'available'"
                >
                  🟢 Available Now
                </button>
                <button 
                  class="btn btn-xs rounded-pill px-2.5 py-1 fw-medium transition-all"
                  :class="activeQuickFilter === 'budget' ? 'btn-primary text-white shadow-xs' : 'btn-outline-secondary bg-white'"
                  @click="activeQuickFilter = 'budget'"
                >
                  💰 Under ₹50/hr
                </button>
                <button 
                  class="btn btn-xs rounded-pill px-2.5 py-1 fw-medium transition-all"
                  :class="activeQuickFilter === 'handicap' ? 'btn-info text-dark shadow-xs' : 'btn-outline-secondary bg-white'"
                  @click="activeQuickFilter = 'handicap'"
                >
                  ♿ Accessible
                </button>
                <button 
                  class="btn btn-xs rounded-pill px-2.5 py-1 fw-medium transition-all"
                  :class="activeQuickFilter === 'multi_deck' ? 'btn-secondary text-white shadow-xs' : 'btn-outline-secondary bg-white'"
                  @click="activeQuickFilter = 'multi_deck'"
                >
                  🏢 Multi-Deck
                </button>
                <button
                  v-if="lotSearchQuery || activeQuickFilter !== 'all'"
                  class="btn btn-xs btn-link text-danger text-decoration-none ms-auto fw-semibold"
                  @click="lotSearchQuery = ''; activeQuickFilter = 'all'"
                >
                  Reset Filters
                </button>
              </div>

            </div>
          </div>

          <!-- Empty State: No Facilities Found -->
          <div v-if="filteredLots.length === 0" class="card text-center py-5 shadow-xs border-0 rounded-4 bg-white my-4">
            <div class="card-body py-4">
              <div class="fs-1 text-muted mb-2">🔍</div>
              <h5 class="fw-bold text-dark">No parking facilities match your search</h5>
              <p class="text-muted small mb-3" style="max-width: 480px; margin: 0 auto;">
                We couldn't find any locations matching "<strong class="text-dark">{{ lotSearchQuery || activeQuickFilter }}</strong>". Try adjusting your search query or reset the filters.
              </p>
              <button class="btn btn-primary btn-sm rounded-pill px-4 fw-semibold" @click="lotSearchQuery = ''; activeQuickFilter = 'all'">
                Reset Search & Filters
              </button>
            </div>
          </div>

          <!-- Parking Lots Grid (Clean, Uncluttered Cards) -->
          <div v-else class="row g-3 g-md-4">
            <div v-for="lot in filteredLots" :key="lot.id" class="col-md-6 col-xl-4">
              <div class="card h-100 border-0 shadow-sm rounded-4 bg-white lot-card transition-card">
                <div class="card-body p-4 d-flex flex-column justify-content-between">
                  
                  <div>
                    <!-- Top Title & Tariff Header -->
                    <div class="d-flex justify-content-between align-items-start gap-2 mb-2">
                      <div>
                        <h5 class="fw-bold text-dark mb-1">{{ lot.prime_location_name }}</h5>
                        <p class="text-muted small mb-0 d-flex align-items-center gap-1">
                          <i class="bi bi-geo-alt-fill text-danger small"></i>
                          <span>{{ lot.address }} • PIN {{ lot.pin_code }}</span>
                        </p>
                      </div>
                      <span class="badge bg-success-subtle text-success border border-success-subtle fs-6 fw-bold px-2.5 py-1 rounded-pill whitespace-nowrap">
                        ₹{{ lot.price }}/hr
                      </span>
                    </div>

                    <!-- Clean Highlights (Only Relevant Ones, No Noise) -->
                    <div class="d-flex flex-wrap gap-1.5 my-3">
                      <span class="badge bg-light text-secondary border rounded-pill px-2.5 py-1 small">
                        🏢 {{ lot.floor_count || (lot.floors ? lot.floors.length : 1) }} Floor{{ (lot.floor_count || 1) > 1 ? 's' : '' }}
                      </span>
                      <span class="badge bg-light text-secondary border rounded-pill px-2.5 py-1 small">
                        ⏱️ {{ lot.grace_period_minutes !== undefined ? lot.grace_period_minutes : 15 }}m Grace
                      </span>
                      <span v-if="lot.daily_rate && lot.daily_rate > 0" class="badge bg-light text-success border rounded-pill px-2.5 py-1 small">
                        🛡️ ₹{{ lot.daily_rate }}/day Cap
                      </span>
                      <span v-if="lot.overnight_rate && lot.overnight_rate > 0" class="badge bg-light text-primary border rounded-pill px-2.5 py-1 small">
                        🌙 ₹{{ lot.overnight_rate }} Night
                      </span>
                      <span v-if="lot.peak_multiplier && lot.peak_multiplier > 1.0" class="badge bg-light text-warning-emphasis border rounded-pill px-2.5 py-1 small">
                        ⚡ {{ lot.peak_multiplier }}x Peak
                      </span>
                    </div>

                    <!-- Occupancy & Availability Meter -->
                    <div class="bg-light p-3 rounded-3 border mb-3">
                      <div class="d-flex justify-content-between align-items-center mb-1.5 small">
                        <span class="text-secondary fw-medium">Available Capacity:</span>
                        <strong :class="lot.available_spots > 0 ? 'text-success' : 'text-danger'">
                          {{ lot.available_spots }} / {{ lot.number_of_spots }} Free
                        </strong>
                      </div>
                      
                      <!-- Visual Capacity Bar -->
                      <div class="progress mb-2" style="height: 6px;">
                        <div 
                          class="progress-bar"
                          :class="lot.available_spots > 0 ? 'bg-success' : 'bg-danger'" 
                          role="progressbar" 
                          :style="{ width: ((lot.available_spots / Math.max(lot.number_of_spots, 1)) * 100) + '%' }"
                        ></div>
                      </div>

                      <div class="d-flex justify-content-between align-items-center text-muted x-small pt-1">
                        <span>🚗 <strong>{{ lot.regular_available_spots !== undefined ? lot.regular_available_spots : (lot.available_spots || 0) }}</strong> Regular</span>
                        <span>♿ <strong>{{ lot.handicap_available_spots || 0 }}</strong> Handicap</span>
                      </div>
                    </div>
                  </div>

                  <!-- Booking Button -->
                  <button
                    class="btn w-100 py-2.5 fw-semibold rounded-3 shadow-xs d-flex align-items-center justify-content-center gap-2"
                    :class="lot.available_spots > 0 ? 'btn-success' : 'btn-secondary disabled'"
                    :disabled="lot.available_spots === 0"
                    @click="openBookingModal(lot)"
                  >
                    <i class="bi" :class="lot.available_spots > 0 ? 'bi-check-circle-fill' : 'bi-slash-circle'"></i>
                    <span>{{ lot.available_spots > 0 ? 'Reserve Parking Spot' : 'Fully Booked (0 Free)' }}</span>
                  </button>

                </div>
              </div>
            </div>
          </div>

        </div>

        <!-- ========================================================= -->
        <!-- TAB 2: MY VEHICLE GARAGE                                  -->
        <!-- ========================================================= -->
        <div v-if="activeTab === 'garage'">
          <div class="card border-0 shadow-sm rounded-4 bg-white p-4">
            
            <!-- Section Header -->
            <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
              <div>
                <h4 class="fw-bold text-dark mb-0.5">My Vehicle Garage</h4>
                <p class="text-muted small mb-0">Saved vehicles for fast 1-click spot reservations.</p>
              </div>
              <div class="d-flex gap-2">
                <button class="btn btn-outline-secondary btn-sm rounded-pill px-3" @click="fetchVehicles">
                  <i class="bi bi-arrow-clockwise me-1"></i> Refresh
                </button>
                <button class="btn btn-success btn-sm rounded-pill px-3 fw-semibold shadow-xs" @click="openAddVehicleModal">
                  <i class="bi bi-plus-circle me-1"></i> Add Vehicle
                </button>
              </div>
            </div>

            <!-- Empty State -->
            <div v-if="vehicles.length === 0" class="text-center py-5 bg-light rounded-4 border my-2">
              <div class="fs-1 mb-2">🚗</div>
              <h5 class="fw-bold text-dark">No vehicles saved in your garage</h5>
              <p class="text-muted small mb-3" style="max-width: 440px; margin: 0 auto;">
                Save your primary Car, SUV, EV, or Motorcycle to avoid typing registration numbers every time you park.
              </p>
              <button class="btn btn-primary btn-sm rounded-pill px-4 fw-semibold" @click="openAddVehicleModal">
                ➕ Add First Vehicle
              </button>
            </div>

            <!-- Vehicle Cards Grid -->
            <div v-else class="row g-3 mt-1">
              <div v-for="v in vehicles" :key="v.id" class="col-md-6 col-lg-4">
                <div 
                  class="card h-100 border rounded-4 transition-card shadow-xs overflow-hidden"
                  :class="v.is_default ? 'border-primary bg-primary-subtle bg-opacity-10' : 'bg-white'"
                >
                  <div class="card-body p-3.5 d-flex flex-column justify-content-between">
                    <div>
                      <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="badge rounded-pill px-2.5 py-1" :class="getVehicleBadgeClass(v.vehicle_type)">
                          {{ getVehicleTypeIcon(v.vehicle_type) }} {{ v.vehicle_type }}
                        </span>
                        <span v-if="v.is_default" class="badge bg-primary text-white rounded-pill px-2.5 py-1 small">
                          ⭐ Default
                        </span>
                      </div>

                      <h4 class="fw-bold text-dark font-monospace mb-1">{{ v.license_plate }}</h4>
                      <div class="text-primary fw-medium small mb-2">{{ v.nickname || 'Unnamed Vehicle' }}</div>
                    </div>

                    <!-- Action Row -->
                    <div class="d-flex justify-content-between align-items-center mt-3 pt-2.5 border-top">
                      <button 
                        v-if="!v.is_default"
                        class="btn btn-link btn-sm text-secondary p-0 text-decoration-none small"
                        @click="setVehicleDefault(v)"
                        title="Set as Default Vehicle"
                      >
                        ⭐ Set Default
                      </button>
                      <span v-else class="text-primary small fw-semibold">
                        <i class="bi bi-check-circle-fill me-1"></i>Default
                      </span>

                      <div class="d-flex gap-1.5 ms-auto">
                        <button class="btn btn-outline-secondary btn-xs rounded-pill px-2.5" @click="openEditVehicleModal(v)">
                          ✏️ Edit
                        </button>
                        <button class="btn btn-outline-danger btn-xs rounded-pill px-2.5" @click="deleteVehicle(v.id)">
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

        <!-- ========================================================= -->
        <!-- TAB 3: MY RESERVATIONS & BOOKING HISTORY                  -->
        <!-- ========================================================= -->
        <div v-if="activeTab === 'reservations'">
          <div class="card border-0 shadow-sm rounded-4 bg-white p-4">
            
            <!-- Header Row -->
            <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
              <div>
                <h4 class="fw-bold text-dark mb-0.5">Booking History & Sessions</h4>
                <p class="text-muted small mb-0">Audit trail of all your past and active reservations.</p>
              </div>
              <div class="d-flex gap-2">
                <button class="btn btn-outline-secondary btn-sm rounded-pill px-3" @click="fetchReservations">
                  <i class="bi bi-arrow-clockwise me-1"></i> Refresh
                </button>
                <button class="btn btn-primary btn-sm rounded-pill px-3 fw-semibold shadow-xs" @click="handleExportCsv" :disabled="exporting">
                  <i class="bi bi-download me-1"></i>
                  <span>{{ exporting ? 'Exporting...' : 'Export CSV' }}</span>
                </button>
              </div>
            </div>

            <!-- Compact Search & Filter Row -->
            <div class="row g-2 mb-3 bg-light p-2 rounded-3 border align-items-center">
              <div class="col-md-5">
                <div class="input-group input-group-sm">
                  <span class="input-group-text bg-white border-end-0 text-muted"><i class="bi bi-search"></i></span>
                  <input 
                    v-model="resSearchQuery" 
                    type="text" 
                    class="form-control border-start-0 ps-0" 
                    placeholder="Search venue, deck, bay, or plate..."
                  />
                </div>
              </div>
              <div class="col-md-4">
                <select v-model="resVenueFilter" class="form-select form-select-sm">
                  <option value="all">All Facilities</option>
                  <option v-for="venue in uniqueVenues" :key="venue" :value="venue">{{ venue }}</option>
                </select>
              </div>
              <div class="col-md-3">
                <select v-model="resStatusFilter" class="form-select form-select-sm">
                  <option value="all">All Statuses</option>
                  <option value="active">Active (Parked)</option>
                  <option value="completed">Completed</option>
                </select>
              </div>
            </div>

            <!-- Export Job Ready Notification -->
            <div v-if="exportJob" class="alert alert-info py-2 px-3 rounded-3 d-flex justify-content-between align-items-center mb-3 small">
              <span>Status: <strong>{{ exportJob.status }}</strong></span>
              <a v-if="exportJob.status === 'completed'" :href="'http://localhost:5000' + exportJob.download_url" class="btn btn-xs btn-success fw-bold rounded-pill px-3" target="_blank">
                Download CSV
              </a>
            </div>

            <!-- Clean Reservations Table -->
            <div class="table-responsive">
              <table class="table table-hover align-middle mb-0 small">
                <thead class="table-light">
                  <tr>
                    <th>#</th>
                    <th>Facility & Location</th>
                    <th>Vehicle</th>
                    <th>Space</th>
                    <th>Mode</th>
                    <th>Entry</th>
                    <th>Exit</th>
                    <th>Duration</th>
                    <th>Cost</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="res in filteredReservations" :key="res.id">
                    <td class="text-muted">#{{ res.id }}</td>
                    <td>
                      <div class="fw-semibold text-dark">{{ res.venue_name || res.lot_name }}</div>
                      <div class="text-muted x-small">
                        Deck: {{ res.floor_name || 'Ground' }} • Bay <strong>{{ res.spot_number }}</strong>
                      </div>
                    </td>
                    <td>
                      <div class="d-flex align-items-center gap-1">
                        <span>{{ getVehicleTypeIcon(res.vehicle_type) }}</span>
                        <strong class="font-monospace text-dark">{{ res.vehicle_number }}</strong>
                      </div>
                    </td>
                    <td>
                      <span v-if="res.spot_type === 'handicap'" class="badge bg-info-subtle text-info">♿ Handicap</span>
                      <span v-else class="badge bg-light text-secondary border">🚗 Regular</span>
                    </td>
                    <td>
                      <span class="badge" :class="res.booking_type === 'scheduled' ? 'bg-primary-subtle text-primary' : 'bg-light text-secondary border'">
                        {{ res.booking_type === 'scheduled' ? '📅 Advance' : '⚡ Park Now' }}
                      </span>
                    </td>
                    <td class="text-secondary">{{ formatTime(res.parking_timestamp) }}</td>
                    <td class="text-secondary">{{ res.leaving_timestamp ? formatTime(res.leaving_timestamp) : 'In Session' }}</td>
                    <td class="fw-medium font-monospace">
                      <span v-if="res.status === 'active'" class="text-primary">{{ getElapsed(res.parking_timestamp) }}</span>
                      <span v-else class="text-muted">{{ res.duration_formatted || `${res.duration_hours || 1}h` }}</span>
                    </td>
                    <td>
                      <strong class="text-success">₹{{ res.parking_cost ? res.parking_cost.toFixed(2) : '0.00' }}</strong>
                      <div v-if="res.grace_period_applied" class="badge bg-success-subtle text-success x-small d-block mt-0.5">
                        Grace (₹0)
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
                        class="btn btn-danger btn-xs rounded-pill px-2.5"
                        @click="handleVacateSpot(res.id)"
                      >
                        Vacate
                      </button>
                      <span v-else class="text-muted x-small">Ended</span>
                    </td>
                  </tr>
                  <tr v-if="filteredReservations.length === 0">
                    <td colspan="11" class="text-center py-4 text-muted">No reservations found matching your filter.</td>
                  </tr>
                </tbody>
              </table>
            </div>

          </div>
        </div>

        <!-- ========================================================= -->
        <!-- TAB 4: COMMUTER PASSES & SUBSCRIPTIONS                    -->
        <!-- ========================================================= -->
        <div v-if="activeTab === 'subscriptions'">
          <div class="card border-0 shadow-sm rounded-4 bg-white p-4">
            
            <!-- Header Row -->
            <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
              <div>
                <h4 class="fw-bold text-dark mb-0.5">Commuter & Corporate Passes</h4>
                <p class="text-muted small mb-0">Recurring daily parking passes with guaranteed access and up to 35% discount.</p>
              </div>
              <div class="d-flex gap-2">
                <button class="btn btn-outline-secondary btn-sm rounded-pill px-3" @click="fetchSubscriptions" :disabled="subscriptionsLoading">
                  <i class="bi bi-arrow-clockwise me-1"></i> Refresh
                </button>
                <button class="btn btn-success btn-sm rounded-pill px-3 fw-semibold shadow-xs" @click="openBuyPassModal">
                  <i class="bi bi-plus-circle me-1"></i> Buy Commuter Pass
                </button>
              </div>
            </div>

            <!-- Empty State -->
            <div v-if="subscriptions.length === 0" class="text-center py-5 bg-light rounded-4 border my-2">
              <div class="fs-1 mb-2">🎟️</div>
              <h5 class="fw-bold text-dark">No active commuter passes</h5>
              <p class="text-muted small mb-3" style="max-width: 440px; margin: 0 auto;">
                Get a Monthly, Quarterly, or Annual pass for your daily workplace commute to skip repeated booking steps.
              </p>
              <button class="btn btn-primary btn-sm rounded-pill px-4 fw-semibold" @click="openBuyPassModal">
                ➕ Buy Your First Pass
              </button>
            </div>

            <!-- Passes Grid -->
            <div v-else class="row g-3 mt-1">
              <div v-for="sub in subscriptions" :key="'pass-' + sub.id" class="col-md-6 col-lg-4">
                <div 
                  class="card h-100 border rounded-4 transition-card shadow-xs overflow-hidden"
                  :class="sub.status === 'active' ? 'border-primary bg-primary-subtle bg-opacity-10' : 'bg-white'"
                >
                  <div class="card-body p-3.5 d-flex flex-column justify-content-between">
                    <div>
                      <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="badge rounded-pill px-2 py-0.5" :class="sub.pass_type === 'dedicated' ? 'bg-primary' : 'bg-secondary'">
                          {{ sub.pass_type === 'dedicated' ? '⭐ Dedicated Bay' : '🔄 Floating Access' }}
                        </span>
                        <span 
                          class="badge rounded-pill px-2 py-0.5" 
                          :class="sub.status === 'active' ? 'bg-success' : 'bg-secondary'"
                        >
                          {{ sub.status === 'active' ? '🟢 Active' : sub.status }}
                        </span>
                      </div>

                      <div class="bg-dark text-white p-2 rounded-3 text-center font-monospace fw-bold mb-2.5 small">
                        🎟️ {{ sub.pass_code }}
                      </div>

                      <h5 class="fw-bold text-dark mb-1">{{ sub.lot_name }}</h5>
                      <div class="text-muted small mb-2.5">
                        Deck: {{ sub.floor_name }} <span v-if="sub.spot_number !== 'Floating'">• Bay <strong>{{ sub.spot_number }}</strong></span>
                      </div>

                      <div class="bg-light p-2.5 rounded-3 small border mb-3">
                        <div class="d-flex justify-content-between mb-1">
                          <span class="text-muted">Vehicle Plate:</span>
                          <strong class="font-monospace text-dark">{{ sub.vehicle_plate }}</strong>
                        </div>
                        <div class="d-flex justify-content-between mb-1">
                          <span class="text-muted">Plan:</span>
                          <span class="text-capitalize fw-semibold">{{ sub.billing_cycle }} (₹{{ sub.price }})</span>
                        </div>
                        <div class="d-flex justify-content-between border-top pt-1 text-primary">
                          <span>Valid Until:</span>
                          <strong>{{ new Date(sub.end_date).toLocaleDateString() }}</strong>
                        </div>
                      </div>
                    </div>

                    <div class="d-flex justify-content-between align-items-center border-top pt-2">
                      <span class="x-small text-muted">Pass #{{ sub.id }}</span>
                      <button 
                        v-if="sub.status === 'active'"
                        class="btn btn-outline-danger btn-xs rounded-pill px-2.5"
                        @click="cancelPass(sub.id)"
                      >
                        Cancel Pass
                      </button>
                    </div>

                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>

        <!-- ========================================================= -->
        <!-- TAB 5: MONTHLY ACTIVITY REPORT                            -->
        <!-- ========================================================= -->
        <div v-if="activeTab === 'report'">
          <div class="card border-0 shadow-sm rounded-4 bg-white p-4">
            
            <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
              <div>
                <h4 class="fw-bold text-dark mb-0.5">Monthly Activity Summary</h4>
                <p class="text-muted small mb-0">Overview of your parking spots, expenses, and usage statistics.</p>
              </div>
              <div class="d-flex gap-2">
                <button class="btn btn-outline-secondary btn-sm rounded-pill px-3" @click="fetchMonthlyReport">
                  <i class="bi bi-arrow-clockwise me-1"></i> Refresh
                </button>
                <a
                  :href="'http://localhost:5000/api/reports/monthly?format=html'"
                  target="_blank"
                  class="btn btn-success btn-sm rounded-pill px-3 fw-semibold shadow-xs"
                >
                  <i class="bi bi-box-arrow-up-right me-1"></i> Open HTML Statement
                </a>
              </div>
            </div>

            <!-- KPI Metric Cards -->
            <div class="row g-3 mb-4">
              <div class="col-md-4">
                <div class="card bg-slate-50 border rounded-4 p-3.5">
                  <span class="text-muted small text-uppercase fw-semibold">Spots Booked (This Month)</span>
                  <h2 class="fw-bold text-success mb-0 mt-2">{{ monthlyReport.total_spots_booked || 0 }}</h2>
                </div>
              </div>
              <div class="col-md-4">
                <div class="card bg-slate-50 border rounded-4 p-3.5">
                  <span class="text-muted small text-uppercase fw-semibold">Top Visited Facility</span>
                  <h4 class="fw-bold text-primary mb-0 mt-2 text-truncate">{{ monthlyReport.most_used_lot || 'None' }}</h4>
                </div>
              </div>
              <div class="col-md-4">
                <div class="card bg-slate-50 border rounded-4 p-3.5">
                  <span class="text-muted small text-uppercase fw-semibold">Total Amount Spent</span>
                  <h2 class="fw-bold text-dark mb-0 mt-2">₹{{ (monthlyReport.total_amount_spent || 0).toFixed(2) }}</h2>
                </div>
              </div>
            </div>

            <!-- Embedded Report Frame -->
            <div v-if="monthlyReport.html_content" class="border rounded-4 overflow-hidden shadow-xs">
              <iframe
                :srcdoc="monthlyReport.html_content"
                style="width: 100%; height: 520px; border: none;"
              ></iframe>
            </div>

          </div>
        </div>

      </main>

      <!-- ========================================================= -->
      <!-- MODAL: BOOK PARKING SPOT                                  -->
      <!-- ========================================================= -->
      <div v-if="showBookingModal" class="modal-backdrop fade show"></div>
      <div v-if="showBookingModal" class="modal show d-block" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content rounded-4 border-0 shadow-lg overflow-hidden">
            
            <div class="modal-header border-0 pb-0 pt-4 px-4">
              <div>
                <h5 class="modal-title fw-bold text-dark">Reserve Parking Spot</h5>
                <p class="text-muted small mb-0">{{ selectedLot?.prime_location_name }} • ₹{{ selectedLot?.price }}/hr</p>
              </div>
              <button type="button" class="btn-close" @click="showBookingModal = false"></button>
            </div>

            <form @submit.prevent="submitBooking">
              <div class="modal-body p-4">
                
                <!-- Facility Pricing Rules Strip -->
                <div class="bg-light p-2.5 rounded-3 border mb-3 small d-flex flex-wrap gap-2 text-secondary">
                  <span>⏱️ {{ selectedLot?.grace_period_minutes || 15 }}m Free Grace</span>
                  <span v-if="selectedLot?.daily_rate">🛡️ ₹{{ selectedLot.daily_rate }}/day Cap</span>
                  <span v-if="selectedLot?.overnight_rate">🌙 ₹{{ selectedLot.overnight_rate }} Night</span>
                  <span v-if="selectedLot?.peak_multiplier > 1">⚡ {{ selectedLot.peak_multiplier }}x Surge</span>
                  <span class="text-danger fw-semibold">⚠️ ₹{{ selectedLot?.overstay_penalty_rate || 50 }}/hr Overstay Surcharge</span>
                </div>

                <!-- Reservation Mode (Park Now vs Schedule) -->
                <div class="mb-3">
                  <label class="form-label small fw-bold text-dark mb-1.5">Booking Mode</label>
                  <div class="btn-group w-100" role="group">
                    <button
                      type="button"
                      class="btn btn-sm py-2 fw-semibold"
                      :class="bookingForm.booking_type === 'immediate' ? 'btn-primary' : 'btn-outline-primary'"
                      @click="bookingForm.booking_type = 'immediate'"
                    >
                      ⚡ Park Now (Immediate)
                    </button>
                    <button
                      type="button"
                      class="btn btn-sm py-2 fw-semibold"
                      :class="bookingForm.booking_type === 'scheduled' ? 'btn-primary' : 'btn-outline-primary'"
                      @click="bookingForm.booking_type = 'scheduled'"
                    >
                      📅 Schedule Advance
                    </button>
                  </div>
                </div>

                <!-- Planned Duration (Hours) for Park Now Mode -->
                <div v-if="bookingForm.booking_type === 'immediate'" class="mb-3 p-3 bg-light rounded-3 border">
                  <div class="d-flex justify-content-between align-items-center mb-1.5">
                    <label class="form-label small fw-bold text-dark mb-0">Select Duration (Hours) *</label>
                    <span class="text-success fw-bold small">Est. Tariff: ₹{{ getImmediateEstimatedCost() }}</span>
                  </div>

                  <!-- Quick Hour Selection Pills -->
                  <div class="d-flex flex-wrap gap-1.5 mb-2">
                    <button 
                      v-for="h in [1, 2, 3, 4, 6, 8, 12, 24]" 
                      :key="'hr-pill-' + h"
                      type="button" 
                      class="btn btn-xs rounded-pill py-1 px-2.5 fw-semibold"
                      :class="Number(bookingForm.duration_hours) === h ? 'btn-primary text-white shadow-xs' : 'btn-outline-secondary bg-white'"
                      @click="bookingForm.duration_hours = h"
                    >
                      {{ h }} {{ h === 1 ? 'hr' : 'hrs' }}
                    </button>
                  </div>

                  <!-- Custom Duration Number Input -->
                  <div class="input-group input-group-sm">
                    <span class="input-group-text bg-white text-muted">
                      <i class="bi bi-clock"></i>
                    </span>
                    <input 
                      v-model.number="bookingForm.duration_hours" 
                      type="number" 
                      min="1" 
                      max="72" 
                      class="form-control" 
                      placeholder="Enter hours (e.g. 2)" 
                      required
                    />
                    <span class="input-group-text bg-white text-muted">hours</span>
                  </div>

                  <div class="d-flex justify-content-between align-items-center mt-2 pt-2 border-top x-small text-muted flex-wrap gap-1">
                    <span>Valid until: <strong class="text-dark">{{ getImmediateValidUntil() }}</strong></span>
                    <span class="text-danger fw-semibold">
                      ⚠️ ₹{{ selectedLot?.overstay_penalty_rate || 50 }}/hr penalty if parked past this time
                    </span>
                  </div>
                </div>

                <!-- Advance Scheduling Window -->
                <div v-if="bookingForm.booking_type === 'scheduled'" class="p-3 bg-primary-subtle rounded-3 mb-3 border border-primary-subtle">
                  <div class="row g-2">
                    <div class="col-sm-6">
                      <label class="form-label x-small fw-bold text-dark mb-1">Start Time *</label>
                      <input v-model="bookingForm.scheduled_start_time" type="datetime-local" class="form-control form-control-sm" required />
                    </div>
                    <div class="col-sm-6">
                      <label class="form-label x-small fw-bold text-dark mb-1">End Time *</label>
                      <input v-model="bookingForm.scheduled_end_time" type="datetime-local" class="form-control form-control-sm" required />
                    </div>
                  </div>
                  <div class="mt-2 pt-2 border-top border-primary-subtle d-flex justify-content-between align-items-center small">
                    <span class="text-secondary">Duration: <strong>{{ getScheduledDurationHours() }} hrs</strong></span>
                    <span class="text-success fw-bold">Est. Cost: ₹{{ getEstimatedCost() }}</span>
                  </div>
                  <div class="mt-1.5 x-small text-danger fw-semibold">
                    ⚠️ ₹{{ selectedLot?.overstay_penalty_rate || 50 }}/hr overstay surcharge applies after scheduled end time
                  </div>
                </div>

                <!-- Spot Type Selection: Regular or Handicap -->
                <div class="mb-3">
                  <label class="form-label small fw-bold text-dark mb-1.5">Space Type</label>
                  <div class="row g-2">
                    <div class="col-6">
                      <div 
                        class="border rounded-3 p-2.5 text-center cursor-pointer transition-card"
                        :class="bookingForm.spot_type === 'regular' ? 'border-success bg-success-subtle shadow-xs' : 'bg-light'"
                        @click="(selectedLot?.regular_available_spots || 0) > 0 && (bookingForm.spot_type = 'regular')"
                      >
                        <div class="fs-4 mb-0.5">🚗</div>
                        <div class="fw-bold small text-dark">Regular Bay</div>
                        <span class="badge bg-success small">{{ selectedLot?.regular_available_spots || 0 }} Free</span>
                      </div>
                    </div>
                    <div class="col-6">
                      <div 
                        class="border rounded-3 p-2.5 text-center cursor-pointer transition-card"
                        :class="bookingForm.spot_type === 'handicap' ? 'border-info bg-info-subtle shadow-xs' : 'bg-light'"
                        @click="(selectedLot?.handicap_available_spots || 0) > 0 && (bookingForm.spot_type = 'handicap')"
                      >
                        <div class="fs-4 mb-0.5">♿</div>
                        <div class="fw-bold small text-dark">Handicap Bay</div>
                        <span class="badge bg-info text-dark small">{{ selectedLot?.handicap_available_spots || 0 }} Free</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Optional Preferred Floor -->
                <div v-if="selectedLot?.floors && selectedLot.floors.length > 1" class="mb-3">
                  <label class="form-label small fw-bold text-dark mb-1">Preferred Deck (Optional)</label>
                  <select v-model="bookingForm.floor_id" class="form-select form-select-sm">
                    <option :value="null">Auto-Assign (Lowest / Nearest to Exit First)</option>
                    <option v-for="fl in selectedLot.floors" :key="'modal-fl-' + fl.id" :value="fl.id">
                      🏢 {{ fl.floor_name }} ({{ fl.available_spots }} spots free)
                    </option>
                  </select>
                </div>

                <!-- Vehicle Selection -->
                <div class="mb-3">
                  <label class="form-label small fw-bold text-dark mb-1">Vehicle Details *</label>
                  
                  <!-- Garage Chips -->
                  <div v-if="vehicles.length > 0" class="d-flex flex-wrap gap-1.5 mb-2">
                    <button 
                      v-for="v in vehicles" 
                      :key="'garage-select-' + v.id"
                      type="button"
                      class="btn btn-xs rounded-pill py-1 px-2.5"
                      :class="bookingForm.vehicle_id === v.id ? 'btn-primary text-white shadow-xs' : 'btn-outline-secondary bg-white'"
                      @click="selectGarageVehicle(v)"
                    >
                      {{ getVehicleTypeIcon(v.vehicle_type) }} <strong>{{ v.license_plate }}</strong>
                    </button>
                    <button 
                      type="button" 
                      class="btn btn-xs rounded-pill py-1 px-2.5"
                      :class="bookingForm.vehicle_id === null ? 'btn-dark text-white' : 'btn-outline-dark bg-white'"
                      @click="bookingForm.vehicle_id = null"
                    >
                      + Custom Plate
                    </button>
                  </div>

                  <div class="input-group input-group-sm">
                    <span class="input-group-text bg-light fw-bold">
                      {{ getVehicleTypeIcon(bookingForm.vehicle_type) }}
                    </span>
                    <input
                      v-model="bookingForm.vehicle_number"
                      type="text"
                      class="form-control font-monospace fw-bold"
                      placeholder="e.g. MH-02-CB-1234"
                      required
                    />
                    <select v-model="bookingForm.vehicle_type" class="form-select" style="max-width: 120px;">
                      <option value="Car">🚗 Car</option>
                      <option value="SUV">🚙 SUV</option>
                      <option value="EV">⚡ EV</option>
                      <option value="Motorcycle">🏍️ Bike</option>
                    </select>
                  </div>

                  <div v-if="bookingForm.vehicle_id === null" class="form-check mt-1.5 small">
                    <input v-model="bookingForm.save_to_garage" class="form-check-input" type="checkbox" id="saveToGarageCheck" />
                    <label class="form-check-label text-muted" for="saveToGarageCheck">
                      Save to My Garage for next time
                    </label>
                  </div>
                </div>

                <!-- Remarks -->
                <div class="mb-2">
                  <label class="form-label small text-muted mb-1">Remarks (Optional)</label>
                  <input v-model="bookingForm.remarks" type="text" class="form-control form-control-sm" placeholder="e.g. Blue Sedan, Gate 2" />
                </div>

              </div>

              <div class="modal-footer border-0 pt-0 pb-4 px-4">
                <button type="button" class="btn btn-light btn-sm rounded-pill px-3" @click="showBookingModal = false">Cancel</button>
                <button type="submit" class="btn btn-success btn-sm rounded-pill px-4 fw-semibold shadow-xs" :disabled="bookingSubmitting">
                  {{ bookingSubmitting ? 'Allotting Spot...' : 'Confirm & Reserve Spot' }}
                </button>
              </div>
            </form>

          </div>
        </div>
      </div>

      <!-- ========================================================= -->
      <!-- MODAL: ADD / EDIT VEHICLE                                 -->
      <!-- ========================================================= -->
      <div v-if="showVehicleModal" class="modal-backdrop fade show"></div>
      <div v-if="showVehicleModal" class="modal show d-block" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content rounded-4 border-0 shadow-lg overflow-hidden">
            <div class="modal-header border-0 pb-0 pt-4 px-4">
              <h5 class="modal-title fw-bold text-dark">
                {{ vehicleModalMode === 'edit' ? '✏️ Edit Vehicle Profile' : '➕ Add Vehicle to Garage' }}
              </h5>
              <button type="button" class="btn-close" @click="showVehicleModal = false"></button>
            </div>
            
            <form @submit.prevent="saveVehicle">
              <div class="modal-body p-4">
                
                <div class="mb-3">
                  <label class="form-label small fw-bold text-dark">License Plate Number *</label>
                  <input
                    v-model="vehicleForm.license_plate"
                    type="text"
                    class="form-control font-monospace fw-bold"
                    placeholder="e.g. DL-01-AB-1234"
                    required
                  />
                </div>

                <div class="mb-3">
                  <label class="form-label small fw-bold text-dark">Vehicle Nickname</label>
                  <input
                    v-model="vehicleForm.nickname"
                    type="text"
                    class="form-control"
                    placeholder="e.g. Daily Commuter, Red SUV"
                  />
                </div>

                <div class="mb-3">
                  <label class="form-label small fw-bold text-dark">Vehicle Type *</label>
                  <div class="row g-2">
                    <div v-for="type in ['Car', 'SUV', 'EV', 'Motorcycle']" :key="type" class="col-6 col-sm-3">
                      <div 
                        class="border rounded-3 p-2 text-center cursor-pointer"
                        :class="vehicleForm.vehicle_type === type ? 'border-primary bg-primary-subtle shadow-xs' : 'bg-light'"
                        @click="vehicleForm.vehicle_type = type"
                      >
                        <div class="fs-4">{{ getVehicleTypeIcon(type) }}</div>
                        <div class="small fw-semibold mt-1">{{ type }}</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="form-check mt-3">
                  <input v-model="vehicleForm.is_default" class="form-check-input" type="checkbox" id="vehicleDefaultCheck" />
                  <label class="form-check-label small fw-medium" for="vehicleDefaultCheck">
                    Set as default vehicle for quick booking
                  </label>
                </div>

              </div>

              <div class="modal-footer border-0 pt-0 pb-4 px-4">
                <button type="button" class="btn btn-light btn-sm rounded-pill px-3" @click="showVehicleModal = false">Cancel</button>
                <button type="submit" class="btn btn-primary btn-sm rounded-pill px-4 fw-semibold" :disabled="savingVehicle">
                  {{ savingVehicle ? 'Saving...' : (vehicleModalMode === 'edit' ? 'Update Vehicle' : 'Save Vehicle') }}
                </button>
              </div>
            </form>

          </div>
        </div>
      </div>

      <!-- ========================================================= -->
      <!-- MODAL: BUY COMMUTER PASS                                  -->
      <!-- ========================================================= -->
      <div v-if="showPassModal" class="modal-backdrop fade show"></div>
      <div v-if="showPassModal" class="modal show d-block" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content rounded-4 border-0 shadow-lg overflow-hidden">
            <div class="modal-header border-0 pb-0 pt-4 px-4">
              <h5 class="modal-title fw-bold text-dark">🎟️ Buy Commuter Pass</h5>
              <button type="button" class="btn-close" @click="showPassModal = false"></button>
            </div>

            <form @submit.prevent="submitBuyPass">
              <div class="modal-body p-4">
                
                <div class="mb-3">
                  <label class="form-label small fw-bold text-dark">Select Facility *</label>
                  <select v-model="passForm.lot_id" class="form-select form-select-sm" required>
                    <option value="" disabled>-- Select a Parking Lot --</option>
                    <option v-for="lot in lots" :key="'lot-pass-' + lot.id" :value="lot.id">
                      🏢 {{ lot.prime_location_name }} (₹{{ lot.price }}/hr base)
                    </option>
                  </select>
                </div>

                <div class="mb-3">
                  <label class="form-label small fw-bold text-dark">Pass Type *</label>
                  <div class="row g-2">
                    <div class="col-6">
                      <div 
                        class="border rounded-3 p-2.5 text-center cursor-pointer"
                        :class="passForm.pass_type === 'floating' ? 'border-primary bg-primary-subtle' : 'bg-light'"
                        @click="passForm.pass_type = 'floating'"
                      >
                        <div class="fs-4 mb-1">🔄</div>
                        <div class="fw-bold small">Floating Pass</div>
                        <div class="x-small text-muted">Guaranteed bay anywhere</div>
                      </div>
                    </div>
                    <div class="col-6">
                      <div 
                        class="border rounded-3 p-2.5 text-center cursor-pointer"
                        :class="passForm.pass_type === 'dedicated' ? 'border-primary bg-primary-subtle' : 'bg-light'"
                        @click="passForm.pass_type = 'dedicated'"
                      >
                        <div class="fs-4 mb-1">⭐</div>
                        <div class="fw-bold small">Dedicated Bay</div>
                        <div class="x-small text-muted">Private assigned spot</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="mb-3">
                  <label class="form-label small fw-bold text-dark">Billing Cycle *</label>
                  <div class="btn-group w-100" role="group">
                    <button
                      type="button"
                      class="btn btn-sm py-1.5 fw-semibold"
                      :class="passForm.billing_cycle === 'monthly' ? 'btn-primary' : 'btn-outline-primary'"
                      @click="passForm.billing_cycle = 'monthly'"
                    >
                      Monthly (30d)
                    </button>
                    <button
                      type="button"
                      class="btn btn-sm py-1.5 fw-semibold"
                      :class="passForm.billing_cycle === 'quarterly' ? 'btn-primary' : 'btn-outline-primary'"
                      @click="passForm.billing_cycle = 'quarterly'"
                    >
                      Quarterly (90d)
                    </button>
                    <button
                      type="button"
                      class="btn btn-sm py-1.5 fw-semibold"
                      :class="passForm.billing_cycle === 'annual' ? 'btn-primary' : 'btn-outline-primary'"
                      @click="passForm.billing_cycle = 'annual'"
                    >
                      Annual (365d)
                    </button>
                  </div>
                </div>

                <div class="mb-3">
                  <label class="form-label small fw-bold text-dark">Vehicle Plate *</label>
                  <div class="input-group input-group-sm">
                    <input
                      v-model="passForm.vehicle_plate"
                      type="text"
                      class="form-control font-monospace fw-bold"
                      placeholder="e.g. DL-01-AB-1234"
                      required
                    />
                    <select v-model="passForm.vehicle_type" class="form-select" style="max-width: 120px;">
                      <option value="Car">🚗 Car</option>
                      <option value="SUV">🚙 SUV</option>
                      <option value="EV">⚡ EV</option>
                      <option value="Motorcycle">🏍️ Bike</option>
                    </select>
                  </div>
                </div>

                <div class="p-3 bg-light rounded-3 d-flex justify-content-between align-items-center border">
                  <div>
                    <div class="x-small text-muted">Total Pass Price:</div>
                    <div class="fw-bold fs-5 text-success">₹{{ computeEstimatedPassPrice() }}</div>
                  </div>
                  <span class="badge bg-success-subtle text-success border border-success-subtle px-3 py-1.5 rounded-pill">
                    Instant Activation
                  </span>
                </div>

              </div>

              <div class="modal-footer border-0 pt-0 pb-4 px-4">
                <button type="button" class="btn btn-light btn-sm rounded-pill px-3" @click="showPassModal = false">Cancel</button>
                <button type="submit" class="btn btn-success btn-sm rounded-pill px-4 fw-bold shadow-xs" :disabled="purchasingPass">
                  {{ purchasingPass ? 'Activating Pass...' : 'Confirm & Activate' }}
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
        duration_hours: 2,
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
      monthlyReport: {},
      subscriptions: [],
      subscriptionsLoading: false,
      showPassModal: false,
      purchasingPass: false,
      passForm: {
        lot_id: '',
        pass_type: 'floating',
        billing_cycle: 'monthly',
        vehicle_plate: '',
        vehicle_type: 'Car'
      },
      lotSearchQuery: '',
      activeQuickFilter: 'all',
      eventSource: null
    }
  },
  computed: {
    filteredLots() {
      let list = this.lots || []

      // Quick filter
      if (this.activeQuickFilter === 'available') {
        list = list.filter(lot => (lot.available_spots || 0) > 0)
      } else if (this.activeQuickFilter === 'budget') {
        list = list.filter(lot => (lot.price || 0) <= 50)
      } else if (this.activeQuickFilter === 'handicap') {
        list = list.filter(lot => (lot.handicap_spots || 0) > 0)
      } else if (this.activeQuickFilter === 'multi_deck') {
        list = list.filter(lot => (lot.floor_count || (lot.floors ? lot.floors.length : 1)) > 1)
      }

      if (!this.lotSearchQuery || !this.lotSearchQuery.trim()) {
        return list
      }
      const q = this.lotSearchQuery.toLowerCase().trim()
      return list.filter(lot => {
        const nameMatch = lot.prime_location_name && lot.prime_location_name.toLowerCase().includes(q)
        const addrMatch = lot.address && lot.address.toLowerCase().includes(q)
        const pinMatch = lot.pin_code && String(lot.pin_code).toLowerCase().includes(q)
        const spotMatch = lot.floors && lot.floors.some(f => 
          f.spots && f.spots.some(s => s.spot_number && s.spot_number.toLowerCase().includes(q))
        )
        return nameMatch || addrMatch || pinMatch || spotMatch
      })
    },
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
      } else if (newTab === 'subscriptions') {
        this.fetchSubscriptions()
        this.fetchLots()
        this.fetchVehicles()
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
      this.initLiveStream()
    }
    this.timerInterval = setInterval(() => {
      this.nowTimestamp = Date.now()
    }, 1000)
  },
  beforeUnmount() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval)
    }
    this.closeLiveStream()
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
    isOverstaying(res) {
      if (!res || !res.scheduled_end_time || res.status !== 'active') return false
      const safeStr = (res.scheduled_end_time.endsWith('Z') || res.scheduled_end_time.includes('+')) 
        ? res.scheduled_end_time 
        : `${res.scheduled_end_time}Z`
      const end = new Date(safeStr).getTime()
      return !isNaN(end) && this.nowTimestamp > end
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
      let total = diffHours * price

      // Add overstay penalty surcharge if past scheduled end time
      if (this.isOverstaying(res)) {
        const endSafe = (res.scheduled_end_time.endsWith('Z') || res.scheduled_end_time.includes('+'))
          ? res.scheduled_end_time
          : `${res.scheduled_end_time}Z`
        const end = new Date(endSafe).getTime()
        if (!isNaN(end) && this.nowTimestamp > end) {
          const overstayHours = Math.max(1.0, (this.nowTimestamp - end) / 3600000)
          const penaltyRate = res.overstay_penalty_rate || 50.0
          total += overstayHours * penaltyRate
        }
      }
      return total.toFixed(2)
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
      this.fetchVehicles()
      this.initLiveStream()
    },
    handleRegisterSuccess() {
      this.showRegister = false
      this.registerSuccessMessage = 'Registration successful! Please log in.'
    },
    logout() {
      this.closeLiveStream()
      localStorage.removeItem('userToken')
      localStorage.removeItem('userData')
      this.isLoggedIn = false
      this.activeReservations = []
      this.activeReservation = null
      this.reservations = []
      this.lots = []
      this.subscriptions = []
      this.lotSearchQuery = ''
      this.activeQuickFilter = 'all'
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
    async fetchLots(searchQuery = null) {
      try {
        const params = {}
        const q = typeof searchQuery === 'string' ? searchQuery.trim() : (this.lotSearchQuery ? this.lotSearchQuery.trim() : '')
        if (q) {
          params.search = q
        }
        const res = await axios.get('http://localhost:5000/api/parking-lots', { params })
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
      
      const now = new Date()
      const localIso = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16)

      const startSched = new Date(now.getTime() + 60 * 60 * 1000)
      const endSched = new Date(now.getTime() + 4 * 60 * 60 * 1000)
      const startSchedIso = new Date(startSched.getTime() - startSched.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
      const endSchedIso = new Date(endSched.getTime() - endSched.getTimezoneOffset() * 60000).toISOString().slice(0, 16)

      const defVehicle = this.vehicles.find(v => v.is_default) || this.vehicles[0] || null

      this.bookingForm = {
        booking_type: 'immediate',
        duration_hours: 2,
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
    getImmediateEstimatedCost() {
      if (!this.selectedLot) return '0.00'
      const hours = Math.max(1, Number(this.bookingForm.duration_hours) || 1)
      const hourly = this.selectedLot.price || 0
      let total = hours * hourly
      if (this.selectedLot.daily_rate && this.selectedLot.daily_rate > 0) {
        const days = Math.max(1, hours / 24.0)
        const dailyCap = days * this.selectedLot.daily_rate
        if (total > dailyCap) total = dailyCap
      }
      return total.toFixed(2)
    },
    getImmediateValidUntil() {
      const hours = Math.max(1, Number(this.bookingForm.duration_hours) || 2)
      const d = new Date(Date.now() + hours * 3600000)
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
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
        const durationHours = Math.max(1, Number(this.bookingForm.duration_hours) || 2)
        const now = new Date()
        const isoTimestamp = this.bookingForm.booking_type === 'immediate'
          ? now.toISOString()
          : (this.bookingForm.scheduled_start_time ? new Date(this.bookingForm.scheduled_start_time).toISOString() : now.toISOString())

        const payload = {
          lot_id: this.selectedLot.id,
          booking_type: this.bookingForm.booking_type,
          duration_hours: durationHours,
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

        if (this.bookingForm.booking_type === 'immediate') {
          const end = new Date(now.getTime() + durationHours * 3600000)
          payload.scheduled_end_time = end.toISOString()
        } else if (this.bookingForm.booking_type === 'scheduled') {
          const sDate = new Date(this.bookingForm.scheduled_start_time)
          const eDate = new Date(this.bookingForm.scheduled_end_time)
          if (isNaN(sDate.getTime()) || isNaN(eDate.getTime()) || eDate <= sDate) {
            this.showAlert('Please provide valid scheduled start and end times (end must be after start).', 'danger')
            this.bookingSubmitting = false
            return
          }
          payload.scheduled_start_time = sDate.toISOString()
          payload.scheduled_end_time = eDate.toISOString()
          payload.duration_hours = Math.max(1, Math.round(((eDate - sDate) / 3600000) * 10) / 10)
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
    },
    async fetchSubscriptions() {
      if (!this.isLoggedIn) return
      this.subscriptionsLoading = true
      try {
        const res = await axios.get('http://localhost:5000/api/subscriptions', this.getAuthHeaders())
        this.subscriptions = res.data.subscriptions || []
      } catch (err) {
        console.error('Failed to fetch subscriptions:', err)
      } finally {
        this.subscriptionsLoading = false
      }
    },
    openBuyPassModal() {
      const defVehicle = this.vehicles.find(v => v.is_default) || this.vehicles[0] || null
      this.passForm = {
        lot_id: this.lots.length > 0 ? this.lots[0].id : '',
        pass_type: 'floating',
        billing_cycle: 'monthly',
        vehicle_plate: defVehicle ? defVehicle.license_plate : '',
        vehicle_type: defVehicle ? defVehicle.vehicle_type : 'Car'
      }
      this.showPassModal = true
    },
    computeEstimatedPassPrice() {
      const lot = this.lots.find(l => l.id === this.passForm.lot_id)
      const baseHourly = lot ? (lot.price || 40) : 40
      const cycleDays = { monthly: 120, quarterly: 320, annual: 1100 }
      const mult = cycleDays[this.passForm.billing_cycle] || 120
      const typeMult = this.passForm.pass_type === 'dedicated' ? 1.35 : 1.0
      return Math.round(baseHourly * mult * typeMult)
    },
    async submitBuyPass() {
      if (!this.passForm.lot_id || !this.passForm.vehicle_plate.trim()) return
      this.purchasingPass = true
      try {
        const payload = {
          lot_id: this.passForm.lot_id,
          pass_type: this.passForm.pass_type,
          billing_cycle: this.passForm.billing_cycle,
          vehicle_plate: this.passForm.vehicle_plate.trim().toUpperCase(),
          vehicle_type: this.passForm.vehicle_type || 'Car'
        }
        const res = await axios.post('http://localhost:5000/api/subscriptions', payload, this.getAuthHeaders())
        this.showAlert(`Pass activated successfully! Pass Code: ${res.data.pass_code}`)
        this.showPassModal = false
        this.fetchSubscriptions()
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'Failed to purchase pass', 'danger')
      } finally {
        this.purchasingPass = false
      }
    },
    async cancelPass(subId) {
      if (!confirm('Are you sure you want to cancel this commuter pass?')) return
      try {
        await axios.post(`http://localhost:5000/api/subscriptions/${subId}/cancel`, {}, this.getAuthHeaders())
        this.showAlert('Pass cancelled successfully.')
        this.fetchSubscriptions()
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'Failed to cancel pass', 'danger')
      }
    },
    initLiveStream() {
      if (this.eventSource) this.closeLiveStream()
      try {
        this.eventSource = new EventSource('http://localhost:5000/api/stream/spots')
        this.eventSource.addEventListener('spot_update', (e) => {
          try {
            const data = JSON.parse(e.data)
            this.handleRealtimeSpotUpdate(data)
          } catch (err) {
            console.error('SSE spot parse error:', err)
          }
        })
      } catch (err) {
        console.error('Could not connect to SSE live map stream:', err)
      }
    },
    closeLiveStream() {
      if (this.eventSource) {
        this.eventSource.close()
        this.eventSource = null
      }
    },
    handleRealtimeSpotUpdate(data) {
      this.fetchLots()
      if (this.activeTab === 'reservations' || this.activeTab === 'dashboard') {
        this.fetchReservations()
      }
    }
  }
}
</script>

<style scoped>
.user-portal-root {
  background-color: #f8fafc;
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
}

.bg-slate-50 {
  background-color: #f8fafc;
}

.bg-slate-100 {
  background-color: #f1f5f9;
}

.max-w-1400 {
  max-width: 1400px;
}

.brand-icon-box {
  width: 32px;
  height: 32px;
}

.avatar-circle {
  width: 26px;
  height: 26px;
  font-size: 0.75rem;
}

.shadow-xs {
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.tracking-tight {
  letter-spacing: -0.02em;
}

/* Tab Navigation Styling */
.user-nav-tabs .nav-link {
  color: #64748b;
  background: transparent;
  transition: all 0.18s ease;
}

.user-nav-tabs .nav-link:hover {
  color: #0f172a;
  background-color: #f1f5f9;
}

.user-nav-tabs .nav-link.active {
  color: #ffffff;
  background-color: #198754;
  box-shadow: 0 2px 6px rgba(25, 135, 84, 0.25);
}

/* Card Transitions */
.transition-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.transition-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.06) !important;
}

.active-session-card {
  border-left: 4px solid #198754 !important;
}

/* Pulsing Dots */
.pulse-dot-green {
  width: 8px;
  height: 8px;
  background-color: #198754;
  border-radius: 50%;
  display: inline-block;
  box-shadow: 0 0 0 0 rgba(25, 135, 84, 0.7);
  animation: pulse-green 2s infinite;
}

@keyframes pulse-green {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(25, 135, 84, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 5px rgba(25, 135, 84, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(25, 135, 84, 0); }
}

.pulse-dot-warning {
  width: 7px;
  height: 7px;
  background-color: #ffc107;
  border-radius: 50%;
  display: inline-block;
  box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.7);
  animation: pulse-warning 2s infinite;
}

@keyframes pulse-warning {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 5px rgba(255, 193, 7, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 193, 7, 0); }
}

.cursor-pointer {
  cursor: pointer;
}

.btn-xs {
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
}

.x-small {
  font-size: 0.75rem;
}

.whitespace-nowrap {
  white-space: nowrap;
}

/* Modal Backdrops */
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(2px);
  z-index: 1040;
}

.modal {
  z-index: 1050;
}
</style>
