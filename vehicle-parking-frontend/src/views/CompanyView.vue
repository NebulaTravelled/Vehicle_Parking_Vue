<template>
  <div class="company-wrapper bg-light min-vh-100">
    <!-- Unauthenticated View: Company Login & Register -->
    <CompanyLogin v-if="!isLoggedIn" @login-success="handleLoginSuccess" />

    <!-- Authenticated View: Company Portal Dashboard -->
    <div v-else>
      <!-- Navigation Bar -->
      <nav class="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm px-4">
        <div class="container-fluid">
          <div class="d-flex align-items-center gap-2">
            <span class="fs-4">🏢</span>
            <span class="navbar-brand fw-bold mb-0">Company Operator Portal</span>
            <span class="badge bg-light text-primary fw-semibold ms-2">
              {{ companyUser.company_name || 'Parking Operator' }}
            </span>
          </div>

          <div class="d-flex align-items-center gap-3">
            <span class="text-white-50 small d-none d-md-inline">
              User: <strong class="text-white">{{ companyUser.name || companyUser.username }}</strong>
            </span>
            
            <!-- Profile Button -->
            <button class="btn btn-outline-light btn-sm fw-semibold shadow-sm" @click="openProfileModal">
              <i class="bi bi-person-gear me-1"></i> Profile
            </button>
            
            <!-- Logout Button -->
            <button class="btn btn-danger btn-sm fw-semibold shadow-sm" @click="logout">
              <i class="bi bi-box-arrow-right me-1"></i> Logout
            </button>
          </div>
        </div>
      </nav>

      <!-- Company Portal Navigation Tab Bar -->
      <div class="bg-white border-bottom px-4 shadow-xs">
        <div class="max-w-1400">
          <ul class="nav nav-tabs border-0 pt-2">
            <li class="nav-item">
              <button
                class="nav-link"
                :class="{ active: activeTab === 'facilities' }"
                @click="activeTab = 'facilities'"
              >
                🅿️ Facilities & Grid Management
              </button>
            </li>
            <li class="nav-item">
              <button
                class="nav-link"
                :class="{ active: activeTab === 'analytics' }"
                @click="activeTab = 'analytics'"
              >
                📈 Facility Analytics & Heatmaps
              </button>
            </li>
            <li class="nav-item">
              <button
                class="nav-link"
                :class="{ active: activeTab === 'subscriptions' }"
                @click="activeTab = 'subscriptions'"
              >
                🎟️ Subscriptions & Passes
              </button>
            </li>
          </ul>
        </div>
      </div>

      <!-- Main Container -->
      <div class="container-fluid p-4 max-w-1400">
        <!-- Global Feedback Alert -->
        <div v-if="alertMessage" class="alert alert-dismissible fade show mb-4 shadow-sm" :class="'alert-' + alertType">
          <i class="bi me-2" :class="alertType === 'success' ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill'"></i>
          {{ alertMessage }}
          <button type="button" class="btn-close" @click="alertMessage = ''"></button>
        </div>

        <!-- ==================== TAB 1: FACILITIES & GRID MANAGEMENT ==================== -->
        <div v-if="activeTab === 'facilities'">

        <!-- Dashboard Header & Top Stats -->
        <div class="row g-3 mb-4">
          <div class="col-md-3 col-sm-6">
            <div class="card shadow-sm border-0 border-start border-primary border-4 h-100">
              <div class="card-body">
                <span class="text-muted small fw-semibold text-uppercase">Total Facilities</span>
                <h3 class="fw-bold mb-0 text-primary mt-1">{{ stats.total_lots || 0 }}</h3>
                <small class="text-muted">Managed parking spaces</small>
              </div>
            </div>
          </div>
          <div class="col-md-3 col-sm-6">
            <div class="card shadow-sm border-0 border-start border-success border-4 h-100">
              <div class="card-body">
                <span class="text-muted small fw-semibold text-uppercase">Total Slots</span>
                <h3 class="fw-bold mb-0 text-success mt-1">{{ stats.total_spots || 0 }}</h3>
                <small class="text-muted">
                  🚗 {{ stats.regular_spots || 0 }} Regular | ♿ {{ stats.handicap_spots || 0 }} Handicap
                </small>
              </div>
            </div>
          </div>
          <div class="col-md-3 col-sm-6">
            <div class="card shadow-sm border-0 border-start border-info border-4 h-100">
              <div class="card-body">
                <span class="text-muted small fw-semibold text-uppercase">Live Availability</span>
                <h3 class="fw-bold mb-0 text-info mt-1">{{ stats.available_spots || 0 }} <span class="fs-6 text-muted">/ {{ stats.total_spots || 0 }}</span></h3>
                <small class="text-muted">🔴 {{ stats.occupied_spots || 0 }} Currently Occupied</small>
              </div>
            </div>
          </div>
          <div class="col-md-3 col-sm-6">
            <div class="card shadow-sm border-0 border-start border-warning border-4 h-100">
              <div class="card-body">
                <span class="text-muted small fw-semibold text-uppercase">Active Bookings & Revenue</span>
                <h3 class="fw-bold mb-0 text-dark mt-1">₹{{ (stats.total_revenue || 0).toFixed(2) }}</h3>
                <small class="text-warning-emphasis fw-semibold">{{ stats.active_reservations || 0 }} Active session(s)</small>
              </div>
            </div>
          </div>
        </div>

        <!-- Section Header & Actions -->
        <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
          <div>
            <h4 class="fw-bold text-dark mb-1">Parking Spaces & Slot Grid Management</h4>
            <p class="text-muted small mb-0">Design interactive slot layouts, mark handicap bays, configure tariffs, and manage facilities.</p>
          </div>
          <div class="d-flex gap-2">
            <button class="btn btn-outline-primary btn-sm fw-semibold" @click="fetchDashboard">
              <i class="bi bi-arrow-clockwise me-1"></i> Refresh
            </button>
            <button class="btn btn-primary btn-sm fw-semibold shadow-sm" @click="openCreateModal">
              <i class="bi bi-plus-circle me-1"></i> Create New Parking Space
            </button>
          </div>
        </div>

        <!-- Lots Cards Grid -->
        <div v-if="lots.length === 0" class="card text-center py-5 shadow-sm border-0">
          <div class="card-body">
            <div class="fs-1 text-muted mb-2">🅿️</div>
            <h5 class="fw-bold text-muted">No parking spaces created yet</h5>
            <p class="text-muted small">Click "Create New Parking Space" above to add your first parking facility and design its grid layout.</p>
            <button class="btn btn-primary" @click="openCreateModal">Create Parking Space</button>
          </div>
        </div>

        <div class="row g-4">
          <div v-for="lot in lots" :key="lot.id" class="col-lg-6 col-xl-4">
            <div class="card shadow-sm h-100 border-0 rounded-4 overflow-hidden lot-card">
              <div class="card-header bg-white border-bottom p-3 d-flex justify-content-between align-items-center">
                <div>
                  <h5 class="fw-bold text-primary mb-0">{{ lot.prime_location_name }}</h5>
                  <small class="text-muted"><i class="bi bi-geo-alt me-1"></i>{{ lot.address }} (PIN: {{ lot.pin_code }})</small>
                </div>
                <span class="badge bg-success-subtle text-success fs-6 fw-bold px-3 py-1.5 rounded-pill">
                  ₹{{ lot.price }}/hr
                </span>
              </div>

              <div class="card-body p-4 d-flex flex-column">
                <!-- Slot Stats Badges -->
                <div class="row g-2 mb-3">
                  <div class="col-6">
                    <div class="bg-light p-2.5 rounded-3 border text-center">
                      <div class="small text-muted">🚗 Regular Slots</div>
                      <div class="fw-bold fs-5 text-dark">{{ lot.regular_spots }}</div>
                      <span class="badge bg-success-subtle text-success small">{{ lot.regular_available }} Available</span>
                    </div>
                  </div>
                  <div class="col-6">
                    <div class="bg-light p-2.5 rounded-3 border text-center">
                      <div class="small text-muted">♿ Handicap Slots</div>
                      <div class="fw-bold fs-5 text-primary">{{ lot.handicap_spots }}</div>
                      <span class="badge bg-info-subtle text-info-emphasis small">{{ lot.handicap_available }} Available</span>
                    </div>
                  </div>
                </div>

                <!-- Floor Selector / Indicator -->
                <div class="d-flex justify-content-between align-items-center p-2 px-3 bg-secondary-subtle rounded-3 mb-2 small text-secondary">
                  <span><i class="bi bi-layers-fill me-1"></i> Multi-Floor Facility:</span>
                  <strong>🏢 {{ lot.floor_count || (lot.floors ? lot.floors.length : 1) }} Floor{{ (lot.floor_count || 1) > 1 ? 's' : '' }} ({{ lot.number_of_spots }} Total Slots)</strong>
                </div>

                <!-- Dynamic & Tiered Pricing Policy Badges -->
                <div class="d-flex flex-wrap gap-1 mb-2">
                  <span class="badge bg-light text-secondary border">⏱️ {{ lot.grace_period_minutes !== undefined ? lot.grace_period_minutes : 15 }}m Grace</span>
                  <span v-if="lot.daily_rate" class="badge bg-light text-success border">🛡️ ₹{{ lot.daily_rate }}/day</span>
                  <span v-if="lot.overnight_rate" class="badge bg-light text-primary border">🌙 ₹{{ lot.overnight_rate }} Night</span>
                  <span v-if="lot.peak_multiplier > 1" class="badge bg-light text-warning-emphasis border">⚡ {{ lot.peak_multiplier }}x Peak</span>
                  <span class="badge bg-light text-danger border">⚠️ ₹{{ lot.overstay_penalty_rate || 50 }}/h Overstay</span>
                </div>

                <!-- Mini Grid Preview Thumbnail with Floor Selector -->
                <div v-if="getLotPreviewFloor(lot)" class="mini-grid-container mb-3 p-2 bg-light rounded-3 border">
                  <div class="small text-muted mb-1 fw-semibold d-flex justify-content-between align-items-center">
                    <span class="d-flex align-items-center gap-1">
                      <span>Floor:</span>
                      <select 
                        v-if="lot.floors && lot.floors.length > 1"
                        :value="previewFloorIndex[lot.id] || 0"
                        @change="setPreviewFloor(lot.id, $event.target.value)"
                        class="form-select form-select-sm py-0 px-2 d-inline-block w-auto border-secondary-subtle"
                        style="font-size: 0.75rem;"
                      >
                        <option v-for="(fl, fIdx) in lot.floors" :key="'preview-opt-' + fl.id" :value="fIdx">
                          {{ fl.floor_name }} ({{ fl.regular_spots + fl.handicap_spots }} slots)
                        </option>
                      </select>
                      <strong v-else class="text-primary">{{ getLotPreviewFloor(lot).floor_name || 'Ground Floor' }}</strong>
                    </span>
                    <span class="badge bg-success-subtle text-success small">
                      {{ getLotPreviewFloor(lot).available_spots !== undefined ? getLotPreviewFloor(lot).available_spots : lot.available_spots }} Free
                    </span>
                  </div>
                  
                  <div 
                    v-if="getLotPreviewFloor(lot).grid_layout && getLotPreviewFloor(lot).grid_layout.length"
                    class="mini-grid" 
                    :style="{ gridTemplateColumns: `repeat(${getLotPreviewFloor(lot).grid_cols || lot.grid_cols}, 1fr)` }"
                  >
                    <template v-for="(row, rIdx) in getLotPreviewFloor(lot).grid_layout" :key="'r' + rIdx">
                      <div 
                        v-for="(cell, cIdx) in row" 
                        :key="'c' + rIdx + '-' + cIdx"
                        class="mini-cell"
                        :class="'cell-' + (cell.type || cell)"
                        :title="(cell.type || cell)"
                      ></div>
                    </template>
                  </div>
                </div>

                <!-- Actions: Edit Slots Button & Delete -->
                <div class="mt-auto pt-2 d-flex gap-2">
                  <!-- The REQUIRED extra button: "Edit Slots" -->
                  <button 
                    class="btn btn-primary flex-grow-1 fw-semibold shadow-sm d-flex align-items-center justify-content-center gap-2 py-2"
                    @click="openEditSlotsModal(lot)"
                  >
                    <i class="bi bi-grid-fill"></i>
                    <span>Edit Slots</span>
                  </button>

                  <button 
                    class="btn btn-outline-danger btn-sm px-3"
                    @click="deleteLot(lot)"
                    title="Delete parking space"
                  >
                    <i class="bi bi-trash"></i>
                  </button>
                </div>

              </div>
            </div>
          </div>
        </div>

        </div>

        <!-- ==================== TAB 2: FACILITY ANALYTICS & HEATMAPS ==================== -->
        <div v-if="activeTab === 'analytics'">
          <div class="card shadow-sm border-0 mb-4">
            <div class="card-body p-4">
              <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
                <div>
                  <h4 class="fw-bold mb-1 text-dark d-flex align-items-center gap-2">
                    <span>📈 Facility Utilization & Business Analytics</span>
                    <span class="badge bg-primary fs-6">{{ companyUser.company_name || 'Operator' }} Scope</span>
                  </h4>
                  <p class="text-muted small mb-0">Multi-deck floor yield, hourly arrival rush patterns, vehicle dwell time and turnover for your facilities.</p>
                </div>
                <div class="d-flex gap-2">
                  <span class="badge bg-success-subtle text-success border border-success-subtle d-flex align-items-center px-3">
                    🟢 Live Event Stream Active
                  </span>
                  <button class="btn btn-outline-primary btn-sm fw-semibold" @click="fetchAnalytics" :disabled="analyticsLoading">
                    {{ analyticsLoading ? 'Refreshing Metrics...' : '🔄 Refresh Analytics' }}
                  </button>
                </div>
              </div>

              <!-- Top KPI Summary Cards -->
              <div v-if="analyticsData?.summary" class="row g-3 mb-4">
                <div class="col-lg-2 col-md-4 col-sm-6">
                  <div class="card bg-light border-0 p-3 h-100 rounded-3">
                    <span class="text-muted small fw-semibold text-uppercase">Total Earned</span>
                    <h3 class="fw-bold text-success mb-1 mt-1">₹{{ (analyticsData.summary.total_revenue || 0).toFixed(2) }}</h3>
                    <small class="text-muted">{{ analyticsData.summary.total_bookings }} total bookings</small>
                  </div>
                </div>
                <div class="col-lg-2 col-md-4 col-sm-6">
                  <div class="card bg-light border-0 p-3 h-100 rounded-3">
                    <span class="text-muted small fw-semibold text-uppercase">Live Occupancy</span>
                    <h3 class="fw-bold text-primary mb-1 mt-1">{{ analyticsData.summary.active_occupancy_rate }}%</h3>
                    <small class="text-muted">{{ analyticsData.summary.occupied_spots }} / {{ analyticsData.summary.total_spots }} slots occupied</small>
                  </div>
                </div>
                <div class="col-lg-2 col-md-4 col-sm-6">
                  <div class="card bg-light border-0 p-3 h-100 rounded-3">
                    <span class="text-muted small fw-semibold text-uppercase">Average Stay</span>
                    <h3 class="fw-bold text-dark mb-1 mt-1">{{ analyticsData.summary.avg_dwell_time_formatted || '0m' }}</h3>
                    <small class="text-muted">{{ analyticsData.summary.avg_dwell_time_minutes }}m average dwell time</small>
                  </div>
                </div>
                <div class="col-lg-2 col-md-4 col-sm-6">
                  <div class="card bg-light border-0 p-3 h-100 rounded-3">
                    <span class="text-muted small fw-semibold text-uppercase">Turnover Ratio</span>
                    <h3 class="fw-bold text-info mb-1 mt-1">{{ analyticsData.summary.vehicle_turnover_rate }}x</h3>
                    <small class="text-muted">Vehicle turnover frequency</small>
                  </div>
                </div>
                <div class="col-lg-2 col-md-4 col-sm-6">
                  <div class="card bg-light border-0 p-3 h-100 rounded-3">
                    <span class="text-muted small fw-semibold text-uppercase">Busiest Hour</span>
                    <h5 class="fw-bold text-warning-emphasis mb-1 mt-2">⚡ {{ analyticsData.summary.peak_rush_hour || '8 - 11 AM' }}</h5>
                    <small class="text-muted">Peak rush period</small>
                  </div>
                </div>
                <div class="col-lg-2 col-md-4 col-sm-6">
                  <div class="card bg-light border-0 p-3 h-100 rounded-3">
                    <span class="text-muted small fw-semibold text-uppercase">Top Floor</span>
                    <h5 class="fw-bold text-primary mb-1 mt-2">🏢 {{ analyticsData.summary.busiest_floor || 'Ground Floor' }}</h5>
                    <small class="text-muted">Highest occupancy floor</small>
                  </div>
                </div>
              </div>

              <!-- 24-Hour Utilization Heatmap -->
              <div class="card border mb-4 rounded-3 overflow-hidden shadow-sm">
                <div class="card-header bg-white border-bottom p-3 d-flex justify-content-between align-items-center">
                  <h6 class="fw-bold mb-0 text-dark">
                    <span>🔥 24-Hour Utilization & Arrival Heatmap (00:00 – 23:00)</span>
                  </h6>
                  <div class="small text-muted d-flex align-items-center gap-2">
                    <span class="badge bg-warning text-dark">⚡ Peak Hours (8-11 AM, 5-8 PM)</span>
                    <span class="badge bg-primary text-white">Intensity: 0% → 100%</span>
                  </div>
                </div>
                <div class="card-body p-3">
                  <div class="row g-1 text-center">
                    <div 
                      v-for="h in analyticsData?.hourly_heatmap || []" 
                      :key="'comp-heat-' + h.hour" 
                      class="col-12 col-sm-6 col-md-3 col-xl"
                    >
                      <div 
                        class="p-2 rounded-2 border transition-card h-100"
                        :class="h.is_peak ? 'border-warning bg-warning-subtle' : 'bg-light'"
                        :title="`${h.time_range}: ${h.count} arrivals (${h.utilization_pct}%)`"
                      >
                        <div class="fw-bold small text-dark">{{ h.label }}</div>
                        <div class="fs-6 fw-bold my-1 text-primary">{{ h.count }}</div>
                        <div class="progress" style="height: 6px;">
                          <div 
                            class="progress-bar" 
                            :class="h.is_peak ? 'bg-warning' : (h.utilization_pct > 60 ? 'bg-danger' : 'bg-success')" 
                            :style="{ width: `${Math.max(h.utilization_pct, 5)}%` }"
                          ></div>
                        </div>
                        <div class="x-small text-muted mt-1">{{ h.utilization_pct }}%</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Multi-Floor Yield Table & Fleet / Dwell Brackets -->
              <div class="row g-4">
                <div class="col-lg-7">
                  <div class="card border shadow-sm rounded-3 h-100">
                    <div class="card-header bg-white border-bottom p-3">
                      <h6 class="fw-bold mb-0 text-dark">🏢 Facility Decks Yield & Occupancy Breakdown</h6>
                    </div>
                    <div class="table-responsive">
                      <table class="table table-hover align-middle mb-0 small">
                        <thead class="table-light">
                          <tr>
                            <th>Facility & Deck</th>
                            <th>Total Slots</th>
                            <th>Occupied</th>
                            <th>Occupancy %</th>
                            <th>Revenue</th>
                            <th>Yield / Spot</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="fl in analyticsData?.floor_analytics || []" :key="'comp-fl-an-' + fl.floor_id">
                            <td>
                              <div class="fw-bold text-dark">{{ fl.lot_name }}</div>
                              <div class="text-muted x-small">🏢 {{ fl.floor_name }} (L{{ fl.floor_number }})</div>
                            </td>
                            <td>{{ fl.total_spots }}</td>
                            <td><span class="text-danger fw-bold">{{ fl.occupied_spots }}</span> / {{ fl.total_spots }}</td>
                            <td>
                              <div class="d-flex align-items-center gap-1">
                                <span class="fw-semibold">{{ fl.occupancy_rate }}%</span>
                                <div class="progress flex-grow-1" style="height: 5px; min-width: 40px;">
                                  <div 
                                    class="progress-bar"
                                    :class="fl.occupancy_rate >= 70 ? 'bg-danger' : (fl.occupancy_rate >= 30 ? 'bg-warning' : 'bg-success')"
                                    :style="{ width: `${fl.occupancy_rate}%` }"
                                  ></div>
                                </div>
                              </div>
                            </td>
                            <td class="fw-bold text-success">₹{{ (fl.total_revenue || 0).toFixed(2) }}</td>
                            <td class="text-muted">₹{{ fl.avg_revenue_per_spot }}</td>
                            <td>
                              <span 
                                class="badge"
                                :class="fl.utilization_level === 'High' ? 'bg-danger' : (fl.utilization_level === 'Moderate' ? 'bg-warning text-dark' : 'bg-success')"
                              >
                                {{ fl.utilization_level }}
                              </span>
                            </td>
                          </tr>
                          <tr v-if="!analyticsData?.floor_analytics?.length">
                            <td colspan="7" class="text-center py-3 text-muted">No floor metrics available.</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>

                <div class="col-lg-5">
                  <div class="card border shadow-sm rounded-3 mb-3">
                    <div class="card-header bg-white border-bottom p-3">
                      <h6 class="fw-bold mb-0 text-dark">🚗 Vehicle Fleet Distribution</h6>
                    </div>
                    <div class="card-body p-3">
                      <div v-for="v in analyticsData?.vehicle_breakdown || []" :key="'comp-v-br-' + v.type" class="mb-2">
                        <div class="d-flex justify-content-between align-items-center small mb-1">
                          <span class="fw-semibold">{{ v.icon }} {{ v.type }}</span>
                          <span class="text-muted">{{ v.count }} bookings ({{ v.percentage }}%)</span>
                        </div>
                        <div class="progress" style="height: 6px;">
                          <div 
                            class="progress-bar" 
                            :class="v.type === 'EV' ? 'bg-success' : (v.type === 'SUV' ? 'bg-primary' : 'bg-info')"
                            :style="{ width: `${v.percentage}%` }"
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="card border shadow-sm rounded-3">
                    <div class="card-header bg-white border-bottom p-3">
                      <h6 class="fw-bold mb-0 text-dark">⏱️ Vehicle Dwell Time Turnover</h6>
                    </div>
                    <div class="card-body p-3">
                      <div v-for="d in analyticsData?.dwell_time_distribution || []" :key="'comp-dw-' + d.bracket" class="mb-2">
                        <div class="d-flex justify-content-between align-items-center small mb-1">
                          <span class="text-dark">{{ d.bracket }}</span>
                          <span class="text-muted">{{ d.count }} sessions ({{ d.percentage }}%)</span>
                        </div>
                        <div class="progress" style="height: 6px;">
                          <div 
                            class="progress-bar bg-secondary"
                            :style="{ width: `${d.percentage}%` }"
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>

        <!-- ==================== TAB 3: SUBSCRIPTIONS & CORPORATE PASSES ==================== -->
        <div v-if="activeTab === 'subscriptions'">
          <div class="card shadow-sm border-0 mb-4">
            <div class="card-body p-4">
              <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
                <div>
                  <h4 class="fw-bold mb-1 text-dark">🎟️ Facility Passes & Subscriptions</h4>
                  <p class="text-muted small mb-0">Active corporate and recurring commuter passes registered for your parking spaces.</p>
                </div>
                <button class="btn btn-outline-primary btn-sm" @click="fetchSubscriptions" :disabled="subscriptionsLoading">
                  {{ subscriptionsLoading ? 'Refreshing...' : '🔄 Refresh Passes' }}
                </button>
              </div>

              <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                  <thead class="table-light">
                    <tr>
                      <th>Pass Code</th>
                      <th>Customer</th>
                      <th>Facility & Deck</th>
                      <th>Slot Allocation</th>
                      <th>Pass Type</th>
                      <th>Billing Cycle</th>
                      <th>Vehicle Plate</th>
                      <th>Fee</th>
                      <th>Validity Period</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="sub in subscriptions" :key="sub.id">
                      <td><span class="badge bg-dark font-monospace">{{ sub.pass_code }}</span></td>
                      <td>
                        <div class="fw-semibold text-dark">{{ sub.customer_name }}</div>
                        <div class="text-muted x-small">{{ sub.customer_email }}</div>
                      </td>
                      <td>
                        <div class="fw-semibold text-primary">{{ sub.lot_name }}</div>
                        <div class="text-muted x-small">🏢 {{ sub.floor_name }}</div>
                      </td>
                      <td>
                        <span class="badge bg-light text-secondary border font-monospace">
                          {{ sub.spot_number || 'Floating' }}
                        </span>
                      </td>
                      <td>
                        <span class="badge" :class="sub.pass_type === 'dedicated' ? 'bg-primary' : 'bg-secondary'">
                          {{ sub.pass_type === 'dedicated' ? '⭐ Dedicated' : '🔄 Floating' }}
                        </span>
                      </td>
                      <td class="text-capitalize">{{ sub.billing_cycle }}</td>
                      <td><span class="font-monospace fw-bold">{{ sub.vehicle_plate }}</span></td>
                      <td class="fw-bold text-success">₹{{ sub.price }}</td>
                      <td class="small">
                        <div>{{ new Date(sub.start_date).toLocaleDateString() }} ➔</div>
                        <div>{{ new Date(sub.end_date).toLocaleDateString() }}</div>
                      </td>
                      <td>
                        <span 
                          class="badge"
                          :class="sub.status === 'active' ? 'bg-success' : (sub.status === 'expired' ? 'bg-secondary' : 'bg-danger')"
                        >
                          {{ sub.status }}
                        </span>
                      </td>
                    </tr>
                    <tr v-if="subscriptions.length === 0">
                      <td colspan="10" class="text-center py-4 text-muted">No commuter passes or corporate subscriptions registered for your facilities yet.</td>
                    </tr>
                  </tbody>
                </table>
              </div>

            </div>
          </div>
        </div>

      </div>

      <!-- ==================== POPUP FORM 1: "EDIT SLOTS" MODAL ==================== -->
      <div v-if="showEditSlotsModal" class="modal-backdrop fade show"></div>
      <div v-if="showEditSlotsModal" class="modal show d-block" tabindex="-1">
        <div class="modal-dialog modal-xl modal-dialog-scrollable">
          <div class="modal-content border-0 shadow-lg rounded-4 overflow-hidden">
            
            <div class="modal-header bg-primary text-white p-3 px-4">
              <div class="d-flex align-items-center gap-2">
                <i class="bi bi-grid-3x3-gap-fill fs-4"></i>
                <div>
                  <h5 class="modal-title fw-bold mb-0">Edit Slots & Parking Grid</h5>
                  <small class="text-white-50">Configure slot names, hourly tariff, grid dimensions, and clickable space elements</small>
                </div>
              </div>
              <button type="button" class="btn-close btn-close-white" @click="closeEditSlotsModal"></button>
            </div>

            <div class="modal-body p-4 bg-light">
              <!-- Facility Meta Row: 1) Edit name of slot, 2) Edit cost of parking -->
              <div class="card border-0 shadow-sm rounded-3 p-3 mb-3 bg-white">
                <div class="row g-3">
                  <!-- 1) Edit name of slot / space -->
                  <div class="col-md-6">
                    <label class="form-label fw-bold small text-secondary">
                      1) Facility / Parking Space Name *
                    </label>
                    <div class="input-group">
                      <span class="input-group-text bg-light text-muted"><i class="bi bi-building"></i></span>
                      <input 
                        v-model="editSlotForm.prime_location_name" 
                        type="text" 
                        class="form-control" 
                        placeholder="e.g. Grand Central Multi-Tier Parking"
                        required 
                      />
                    </div>
                  </div>

                  <!-- 2) Edit cost of parking -->
                  <div class="col-md-6">
                    <label class="form-label fw-bold small text-secondary">
                      2) Base Cost of Parking (₹ / hr) *
                    </label>
                    <div class="input-group">
                      <span class="input-group-text bg-light text-muted fw-bold">₹</span>
                      <input 
                        v-model.number="editSlotForm.price" 
                        type="number" 
                        step="0.5" 
                        min="0"
                        class="form-control" 
                        placeholder="Rate per hour"
                        required 
                      />
                    </div>
                  </div>
                </div>
              </div>

              <!-- Dynamic & Tiered Pricing Rules Configuration -->
              <div class="card border-0 shadow-sm rounded-3 p-3 mb-3 bg-white">
                <div class="fw-bold small text-secondary text-uppercase mb-2 d-flex align-items-center gap-1">
                  <i class="bi bi-tag-fill text-primary"></i> Dynamic & Tiered Pricing Engine
                </div>
                <div class="row g-3">
                  <div class="col-md-4 col-sm-6">
                    <label class="form-label small fw-semibold text-muted mb-1">
                      🛡️ Daily Rate / 24-hr Cap (₹)
                    </label>
                    <input 
                      v-model.number="editSlotForm.daily_rate" 
                      type="number" 
                      step="5" 
                      min="0" 
                      class="form-control form-control-sm"
                      placeholder="e.g. 500 (0 for no cap)"
                    />
                    <div class="form-text x-small">Max ceiling per 24 hours</div>
                  </div>

                  <div class="col-md-4 col-sm-6">
                    <label class="form-label small fw-semibold text-muted mb-1">
                      🌙 Overnight Flat Tariff (₹)
                    </label>
                    <input 
                      v-model.number="editSlotForm.overnight_rate" 
                      type="number" 
                      step="5" 
                      min="0" 
                      class="form-control form-control-sm"
                      placeholder="e.g. 200 (0 for regular hourly)"
                    />
                    <div class="form-text x-small">Flat rate for 10 PM - 7 AM</div>
                  </div>

                  <div class="col-md-4 col-sm-6">
                    <label class="form-label small fw-semibold text-muted mb-1">
                      ⚡ Peak Hours Multiplier (x)
                    </label>
                    <input 
                      v-model.number="editSlotForm.peak_multiplier" 
                      type="number" 
                      step="0.05" 
                      min="1.0" 
                      class="form-control form-control-sm"
                      placeholder="e.g. 1.25"
                    />
                    <div class="form-text x-small">Rush hours: 8-11 AM & 5-8 PM</div>
                  </div>

                  <div class="col-md-6 col-sm-6">
                    <label class="form-label small fw-semibold text-muted mb-1">
                      ⏱️ Free Grace Period (Minutes)
                    </label>
                    <input 
                      v-model.number="editSlotForm.grace_period_minutes" 
                      type="number" 
                      step="1" 
                      min="0" 
                      class="form-control form-control-sm"
                      placeholder="e.g. 15"
                    />
                    <div class="form-text x-small">Free exit window with ₹0 fee</div>
                  </div>

                  <div class="col-md-6 col-sm-6">
                    <label class="form-label small fw-semibold text-muted mb-1">
                      ⚠️ Overstay Penalty Rate (₹ / hr)
                    </label>
                    <input 
                      v-model.number="editSlotForm.overstay_penalty_rate" 
                      type="number" 
                      step="5" 
                      min="0" 
                      class="form-control form-control-sm"
                      placeholder="e.g. 50"
                    />
                    <div class="form-text x-small">Surcharge past scheduled checkout</div>
                  </div>
                </div>
              </div>

              <!-- Multi-Floor Management Section -->
              <div class="card border-0 shadow-sm rounded-3 p-3 mb-3 bg-white">
                <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-2">
                  <div class="d-flex align-items-center gap-2">
                    <span class="fw-bold small text-secondary text-uppercase">Multi-Floor Management:</span>
                    <span class="badge bg-primary text-white">{{ editSlotForm.floors.length }} Floor{{ editSlotForm.floors.length > 1 ? 's' : '' }}</span>
                  </div>
                  <div class="d-flex gap-2">
                    <button type="button" class="btn btn-sm btn-outline-success fw-semibold" @click="addNewFloor">
                      <i class="bi bi-plus-lg me-1"></i> Add Floor
                    </button>
                    <button 
                      v-if="editSlotForm.floors.length > 1" 
                      type="button" 
                      class="btn btn-sm btn-outline-danger" 
                      @click="removeActiveFloor"
                      title="Remove current floor"
                    >
                      <i class="bi bi-trash me-1"></i> Remove Floor
                    </button>
                  </div>
                </div>

                <!-- Floor Switcher Tabs -->
                <ul class="nav nav-pills gap-1 p-1 bg-light rounded-3 border mb-3">
                  <li v-for="(fl, idx) in editSlotForm.floors" :key="'fl-tab-' + idx" class="nav-item">
                    <button 
                      type="button" 
                      class="nav-link py-1.5 px-3 rounded-2 fw-semibold small"
                      :class="activeFloorIdx === idx ? 'active bg-primary text-white shadow-sm' : 'text-dark'"
                      @click="activeFloorIdx = idx"
                    >
                      🏢 {{ fl.floor_name }}
                      <span class="badge ms-1" :class="activeFloorIdx === idx ? 'bg-white text-primary' : 'bg-secondary text-white'">
                        {{ getFloorSlotCount(fl) }} slots
                      </span>
                    </button>
                  </li>
                </ul>

                <!-- Active Floor Configuration Bar -->
                <div class="row g-2 align-items-center bg-light p-2.5 rounded-3 border">
                  <div class="col-md-5">
                    <div class="input-group input-group-sm">
                      <span class="input-group-text bg-white text-muted">Floor Label</span>
                      <input 
                        v-model="currentFloor.floor_name" 
                        type="text" 
                        class="form-control" 
                        placeholder="e.g. Ground Floor, Basement 1, Level 2"
                      />
                    </div>
                  </div>
                  <div class="col-md-7">
                    <div class="d-flex gap-2 align-items-center">
                      <div class="input-group input-group-sm">
                        <span class="input-group-text bg-white">Rows</span>
                        <input 
                          v-model.number="currentFloor.grid_rows" 
                          type="number" 
                          min="2" 
                          max="15" 
                          class="form-control"
                        />
                      </div>
                      <div class="input-group input-group-sm">
                        <span class="input-group-text bg-white">Cols</span>
                        <input 
                          v-model.number="currentFloor.grid_cols" 
                          type="number" 
                          min="2" 
                          max="15" 
                          class="form-control"
                        />
                      </div>
                      <button 
                        type="button" 
                        class="btn btn-outline-primary btn-sm text-nowrap fw-semibold"
                        @click="resizeActiveFloorGrid"
                      >
                        Apply Size
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 4) Edit Grid Space - Clickable Grid Section -->
              <div class="card border-0 shadow-sm rounded-3 p-3 mb-3 bg-white">
                <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
                  <div>
                    <h6 class="fw-bold text-dark mb-0 d-flex align-items-center gap-2">
                      <i class="bi bi-cursor-fill text-primary"></i>
                      <span>Edit Floor Grid: {{ currentFloor.floor_name }}</span>
                    </h6>
                    <small class="text-muted">Select an element below, then click squares on the floor layout to mark them.</small>
                  </div>

                  <!-- Quick Preset Buttons -->
                  <div class="d-flex gap-2">
                    <button class="btn btn-xs btn-outline-secondary" @click="fillGrid('parking')">Fill All Parking</button>
                    <button class="btn btn-xs btn-outline-secondary" @click="addRoadAisle">Add Center Road</button>
                    <button class="btn btn-xs btn-outline-danger" @click="fillGrid('empty')">Clear Grid</button>
                  </div>
                </div>

                <!-- Element Palette Tool Selection -->
                <div class="d-flex flex-wrap gap-2 p-2 bg-light rounded-3 mb-3 border align-items-center">
                  <span class="small fw-bold text-secondary me-1">Active Tool:</span>
                  
                  <button 
                    type="button" 
                    class="btn btn-sm palette-btn"
                    :class="activeTool === 'parking' ? 'btn-success text-white shadow-sm ring-active' : 'btn-outline-success bg-white'"
                    @click="activeTool = 'parking'"
                  >
                    🅿️ Parking Space (Regular)
                  </button>

                  <button 
                    type="button" 
                    class="btn btn-sm palette-btn"
                    :class="activeTool === 'handicap' ? 'btn-info text-dark shadow-sm ring-active' : 'btn-outline-info bg-white text-dark'"
                    @click="activeTool = 'handicap'"
                  >
                    ♿ Handicap Space
                  </button>

                  <button 
                    type="button" 
                    class="btn btn-sm palette-btn"
                    :class="activeTool === 'ramp_up' ? 'btn-info text-white shadow-sm ring-active' : 'btn-outline-secondary bg-white text-dark'"
                    @click="activeTool = 'ramp_up'"
                  >
                    🚗⤴️ Ramp Up
                  </button>

                  <button 
                    type="button" 
                    class="btn btn-sm palette-btn"
                    :class="activeTool === 'ramp_down' ? 'btn-secondary text-white shadow-sm ring-active' : 'btn-outline-secondary bg-white text-dark'"
                    @click="activeTool = 'ramp_down'"
                  >
                    🚗⤵️ Ramp Down
                  </button>

                  <button 
                    type="button" 
                    class="btn btn-sm palette-btn"
                    :class="activeTool === 'elevator' ? 'btn-primary text-white shadow-sm ring-active' : 'btn-outline-primary bg-white text-dark'"
                    @click="activeTool = 'elevator'"
                  >
                    🛗 Elevator
                  </button>

                  <button 
                    type="button" 
                    class="btn btn-sm palette-btn"
                    :class="activeTool === 'stairs' ? 'btn-warning text-dark shadow-sm ring-active' : 'btn-outline-warning bg-white text-dark'"
                    @click="activeTool = 'stairs'"
                  >
                    🪜 Stairs / Exit
                  </button>

                  <button 
                    type="button" 
                    class="btn btn-sm palette-btn"
                    :class="activeTool === 'road' ? 'btn-dark text-white shadow-sm ring-active' : 'btn-outline-dark bg-white'"
                    @click="activeTool = 'road'"
                  >
                    🛣️ Road
                  </button>

                  <button 
                    type="button" 
                    class="btn btn-sm palette-btn"
                    :class="activeTool === 'empty' ? 'btn-secondary text-white shadow-sm ring-active' : 'btn-outline-secondary bg-white'"
                    @click="activeTool = 'empty'"
                  >
                    ⬜ Empty Space
                  </button>
                </div>

                <!-- Live Slot Counters Pill -->
                <div class="alert alert-info py-2 px-3 mb-3 d-flex justify-content-between align-items-center flex-wrap gap-2 small">
                  <div>
                    <i class="bi bi-info-circle-fill me-1"></i>
                    <strong>{{ currentFloor.floor_name }}:</strong> 
                    Regular: <strong>{{ computedRegularSlots }}</strong> | 
                    Handicap: <strong>{{ computedHandicapSlots }}</strong> | 
                    Roads: <strong>{{ computedRoads }}</strong> | 
                    Stairs: <strong>{{ computedStairs }}</strong>
                    <span v-if="computedRampsUp > 0"> | Ramps Up: <strong>{{ computedRampsUp }}</strong></span>
                    <span v-if="computedRampsDown > 0"> | Ramps Down: <strong>{{ computedRampsDown }}</strong></span>
                    <span v-if="computedElevators > 0"> | Elevators: <strong>{{ computedElevators }}</strong></span>
                  </div>
                  <div class="badge bg-primary fs-6 fw-bold px-3 py-1.5 rounded-pill shadow-sm">
                    Total Facility Capacity: {{ computedGrandTotalSlots }} Slots
                  </div>
                </div>

                <!-- The Interactive Clickable Grid Canvas -->
                <div class="grid-canvas-wrapper p-3 bg-light rounded-3 border text-center overflow-auto">
                  <div 
                    class="clickable-grid mx-auto" 
                    :style="{ 
                      gridTemplateColumns: `repeat(${currentFloor.grid_cols || 6}, minmax(65px, 1fr))`,
                      maxWidth: `${(currentFloor.grid_cols || 6) * 85}px` 
                    }"
                  >
                    <template v-for="(row, rIdx) in currentMatrix" :key="'grid-r-' + rIdx">
                      <div 
                        v-for="(cell, cIdx) in row" 
                        :key="'grid-cell-' + rIdx + '-' + cIdx"
                        class="grid-cell shadow-sm"
                        :class="'cell-' + cell.type"
                        @click="stampCell(rIdx, cIdx)"
                        :title="`Row ${rIdx + 1}, Col ${cIdx + 1}: ${cell.type}`"
                      >
                        <div class="cell-content">
                          <span v-if="cell.type === 'parking'" class="cell-icon">🅿️</span>
                          <span v-else-if="cell.type === 'handicap'" class="cell-icon">♿</span>
                          <span v-else-if="cell.type === 'road'" class="cell-icon">🛣️</span>
                          <span v-else-if="cell.type === 'stairs'" class="cell-icon">🪜</span>
                          <span v-else-if="cell.type === 'ramp_up'" class="cell-icon">🚗⤴️</span>
                          <span v-else-if="cell.type === 'ramp_down'" class="cell-icon">🚗⤵️</span>
                          <span v-else-if="cell.type === 'elevator'" class="cell-icon">🛗</span>
                          <span v-else class="cell-icon text-muted">·</span>
                          
                          <span class="cell-label">{{ getCellLabel(cell, rIdx, cIdx) }}</span>
                        </div>
                      </div>
                    </template>
                  </div>
                </div>

                <div class="text-muted small mt-2">
                  <i class="bi bi-lightbulb me-1"></i>
                  <strong>Auto-calculation rule:</strong> The total number of parking spaces and handicap spaces across all floors is aggregated and saved as total facility spots.
                </div>

              </div>
            </div>

            <!-- Modal Footer: Save and Cancel -->
            <div class="modal-footer bg-white border-top p-3 px-4 d-flex justify-content-between align-items-center">
              <span class="text-muted small">
                Saving will update all <strong>{{ editSlotForm.floors.length }} floor layouts</strong>, dimensions, and register <strong>{{ computedGrandTotalSlots }} bookable slots</strong> in the database.
              </span>
              <div class="d-flex gap-2">
                <button type="button" class="btn btn-secondary px-3" @click="closeEditSlotsModal">Cancel</button>
                <button 
                  type="button" 
                  class="btn btn-primary px-4 fw-semibold shadow-sm d-flex align-items-center gap-2"
                  @click="saveSlotsData"
                  :disabled="savingSlots"
                >
                  <span v-if="savingSlots" class="spinner-border spinner-border-sm"></span>
                  <span>{{ savingSlots ? 'Saving Changes...' : '💾 Save & Update All Floors' }}</span>
                </button>
              </div>
            </div>

          </div>
        </div>
      </div>

      <!-- ==================== POPUP FORM 2: COMPANY PROFILE MODAL ==================== -->
      <div v-if="showProfileModal" class="modal-backdrop fade show"></div>
      <div v-if="showProfileModal" class="modal show d-block" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content border-0 shadow-lg rounded-4 overflow-hidden">
            <div class="modal-header bg-primary text-white p-3 px-4">
              <h5 class="modal-title fw-bold">Company Profile Settings</h5>
              <button type="button" class="btn-close btn-close-white" @click="showProfileModal = false"></button>
            </div>
            <form @submit.prevent="updateCompanyProfile">
              <div class="modal-body p-4 bg-light">
                
                <div class="mb-3">
                  <label class="form-label fw-bold small text-secondary">Company Name *</label>
                  <input 
                    v-model="profileForm.company_name" 
                    type="text" 
                    class="form-control" 
                    placeholder="Company Name" 
                    required 
                  />
                </div>

                <div class="row g-2 mb-3">
                  <div class="col-6">
                    <label class="form-label fw-bold small text-secondary">Contact Person Name</label>
                    <input 
                      v-model="profileForm.name" 
                      type="text" 
                      class="form-control" 
                      placeholder="Your Full Name" 
                    />
                  </div>
                  <div class="col-6">
                    <label class="form-label fw-bold small text-secondary">Mobile Number *</label>
                    <input 
                      v-model="profileForm.mobile_number" 
                      type="text" 
                      class="form-control" 
                      placeholder="+91 98765 43210" 
                      required 
                    />
                  </div>
                </div>

                <div class="mb-3">
                  <label class="form-label fw-bold small text-secondary">Company Description</label>
                  <textarea 
                    v-model="profileForm.description" 
                    rows="3" 
                    class="form-control" 
                    placeholder="Describe your company, parking facilities, operating hours, etc."
                  ></textarea>
                </div>

                <div class="mb-3">
                  <label class="form-label fw-bold small text-secondary">Facility / Office Address</label>
                  <input 
                    v-model="profileForm.address" 
                    type="text" 
                    class="form-control" 
                    placeholder="Full address" 
                  />
                </div>

                <div class="mb-3">
                  <label class="form-label fw-bold small text-secondary">Official Email Address</label>
                  <input 
                    v-model="profileForm.email" 
                    type="email" 
                    class="form-control" 
                    placeholder="email@company.com" 
                  />
                </div>

              </div>
              <div class="modal-footer bg-white border-top p-3 px-4">
                <button type="button" class="btn btn-secondary" @click="showProfileModal = false">Cancel</button>
                <button type="submit" class="btn btn-primary fw-semibold" :disabled="savingProfile">
                  {{ savingProfile ? 'Saving...' : 'Save Profile Changes' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      <!-- ==================== POPUP FORM 3: CREATE NEW PARKING SPACE ==================== -->
      <div v-if="showCreateModal" class="modal-backdrop fade show"></div>
      <div v-if="showCreateModal" class="modal show d-block" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content border-0 shadow-lg rounded-4 overflow-hidden">
            <div class="modal-header bg-primary text-white p-3 px-4">
              <h5 class="modal-title fw-bold">Create New Parking Space</h5>
              <button type="button" class="btn-close btn-close-white" @click="showCreateModal = false"></button>
            </div>
            <form @submit.prevent="createParkingSpace">
              <div class="modal-body p-4 bg-light">
                
                <div class="mb-3">
                  <label class="form-label fw-bold small text-secondary">Prime Location Name *</label>
                  <input 
                    v-model="createForm.prime_location_name" 
                    type="text" 
                    class="form-control" 
                    placeholder="e.g. Metro Grand Parking Mall" 
                    required 
                  />
                </div>

                <div class="row g-2 mb-3">
                  <div class="col-6">
                    <label class="form-label fw-bold small text-secondary">Tariff (₹ / hr) *</label>
                    <input 
                      v-model.number="createForm.price" 
                      type="number" 
                      min="0" 
                      step="0.5" 
                      class="form-control" 
                      placeholder="40" 
                      required 
                    />
                  </div>
                  <div class="col-6">
                    <label class="form-label fw-bold small text-secondary">Postal PIN Code *</label>
                    <input 
                      v-model="createForm.pin_code" 
                      type="text" 
                      class="form-control" 
                      placeholder="560001" 
                      required 
                    />
                  </div>
                </div>

                <div class="mb-3">
                  <label class="form-label fw-bold small text-secondary">Address / Location *</label>
                  <input 
                    v-model="createForm.address" 
                    type="text" 
                    class="form-control" 
                    placeholder="Street, District, City" 
                    required 
                  />
                </div>

                <div class="row g-2 mb-3">
                  <div class="col-6">
                    <label class="form-label fw-bold small text-secondary">Grid Rows</label>
                    <input 
                      v-model.number="createForm.grid_rows" 
                      type="number" 
                      min="2" 
                      max="15" 
                      class="form-control" 
                    />
                  </div>
                  <div class="col-6">
                    <label class="form-label fw-bold small text-secondary">Grid Columns</label>
                    <input 
                      v-model.number="createForm.grid_cols" 
                      type="number" 
                      min="2" 
                      max="15" 
                      class="form-control" 
                    />
                  </div>
                </div>

                <div class="alert alert-secondary small mb-0">
                  💡 After creating, you can click <strong>"Edit Slots"</strong> anytime to customize each square as Parking, Handicap, Road, or Stairs!
                </div>

              </div>
              <div class="modal-footer bg-white border-top p-3 px-4">
                <button type="button" class="btn btn-secondary" @click="showCreateModal = false">Cancel</button>
                <button type="submit" class="btn btn-primary fw-semibold" :disabled="creatingLot">
                  {{ creatingLot ? 'Creating...' : 'Create Parking Space' }}
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
import axios from 'axios'
import CompanyLogin from '../components/CompanyLogin.vue'

export default {
  name: 'CompanyView',
  components: { CompanyLogin },
  data() {
    return {
      isLoggedIn: !!localStorage.getItem('companyToken'),
      companyUser: JSON.parse(localStorage.getItem('companyData') || '{}'),
      stats: {},
      lots: [],
      alertMessage: '',
      alertType: 'success',

      // Profile Modal State
      showProfileModal: false,
      savingProfile: false,
      profileForm: {
        company_name: '',
        name: '',
        mobile_number: '',
        description: '',
        address: '',
        email: ''
      },

      // Create Lot Modal State
      showCreateModal: false,
      creatingLot: false,
      createForm: {
        prime_location_name: '',
        price: 40,
        address: '',
        pin_code: '560001',
        grid_rows: 5,
        grid_cols: 6
      },

      // Edit Slots Modal State
      showEditSlotsModal: false,
      savingSlots: false,
      editingLot: null,
      activeTool: 'parking', // 'parking', 'handicap', 'ramp_up', 'ramp_down', 'elevator', 'stairs', 'road', 'empty'
      activeFloorIdx: 0,
      previewFloorIndex: {},
      activeTab: 'facilities', // 'facilities', 'analytics', 'subscriptions'
      analyticsData: null,
      analyticsLoading: false,
      subscriptions: [],
      subscriptionsLoading: false,
      eventSource: null,
      realtimePulsingSpots: {},
      editSlotForm: {
        prime_location_name: '',
        price: 0,
        floors: []
      }
    }
  },
  computed: {
    currentFloor() {
      if (this.editSlotForm.floors && this.editSlotForm.floors.length > 0) {
        return this.editSlotForm.floors[this.activeFloorIdx] || this.editSlotForm.floors[0]
      }
      return { floor_name: 'Ground Floor', floor_number: 0, grid_rows: 5, grid_cols: 6, matrix: [] }
    },
    currentMatrix() {
      return this.currentFloor.matrix || []
    },
    computedRegularSlots() {
      let count = 0
      for (const row of this.currentMatrix) {
        for (const cell of row) {
          if (cell.type === 'parking') count++
        }
      }
      return count
    },
    computedHandicapSlots() {
      let count = 0
      for (const row of this.currentMatrix) {
        for (const cell of row) {
          if (cell.type === 'handicap') count++
        }
      }
      return count
    },
    computedTotalSlots() {
      return this.computedRegularSlots + this.computedHandicapSlots
    },
    computedRoads() {
      let count = 0
      for (const row of this.currentMatrix) {
        for (const cell of row) {
          if (cell.type === 'road') count++
        }
      }
      return count
    },
    computedStairs() {
      let count = 0
      for (const row of this.currentMatrix) {
        for (const cell of row) {
          if (cell.type === 'stairs') count++
        }
      }
      return count
    },
    computedRampsUp() {
      let count = 0
      for (const row of this.currentMatrix) {
        for (const cell of row) {
          if (cell.type === 'ramp_up') count++
        }
      }
      return count
    },
    computedRampsDown() {
      let count = 0
      for (const row of this.currentMatrix) {
        for (const cell of row) {
          if (cell.type === 'ramp_down') count++
        }
      }
      return count
    },
    computedElevators() {
      let count = 0
      for (const row of this.currentMatrix) {
        for (const cell of row) {
          if (cell.type === 'elevator') count++
        }
      }
      return count
    },
    computedGrandTotalSlots() {
      if (!this.editSlotForm.floors) return 0
      let total = 0
      for (const fl of this.editSlotForm.floors) {
        if (fl.matrix) {
          for (const row of fl.matrix) {
            for (const cell of row) {
              if (cell.type === 'parking' || cell.type === 'handicap') {
                total++
              }
            }
          }
        }
      }
      return total
    }
  },
  watch: {
    activeTab(newTab) {
      if (!this.isLoggedIn) return
      if (newTab === 'facilities') this.fetchDashboard()
      if (newTab === 'analytics') this.fetchAnalytics()
      if (newTab === 'subscriptions') this.fetchSubscriptions()
    }
  },
  mounted() {
    if (this.isLoggedIn) {
      this.fetchDashboard()
      this.fetchProfile()
      this.initLiveStream()
    }
  },
  beforeUnmount() {
    this.closeLiveStream()
  },
  methods: {
    getAuthHeaders() {
      const token = localStorage.getItem('companyToken')
      return { headers: { Authorization: `Bearer ${token}` } }
    },
    handleLoginSuccess() {
      this.isLoggedIn = true
      this.companyUser = JSON.parse(localStorage.getItem('companyData') || '{}')
      this.fetchDashboard()
      this.fetchProfile()
    },
    logout() {
      localStorage.removeItem('companyToken')
      localStorage.removeItem('companyData')
      this.isLoggedIn = false
      this.companyUser = {}
      this.lots = []
      this.stats = {}
    },
    showAlert(msg, type = 'success') {
      this.alertMessage = msg
      this.alertType = type
      setTimeout(() => { this.alertMessage = '' }, 6000)
    },
    async fetchDashboard() {
      try {
        const res = await axios.get('http://localhost:5000/api/company/dashboard', this.getAuthHeaders())
        this.stats = res.data.statistics || {}
        this.lots = res.data.lots || []
      } catch (err) {
        if (err.response?.status === 401) {
          this.logout()
        }
      }
    },
    async fetchProfile() {
      try {
        const res = await axios.get('http://localhost:5000/api/auth/profile', this.getAuthHeaders())
        this.companyUser = res.data
        localStorage.setItem('companyData', JSON.stringify(res.data))
        this.profileForm = {
          company_name: res.data.company_name || '',
          name: res.data.name || '',
          mobile_number: res.data.mobile_number || '',
          description: res.data.description || '',
          address: res.data.address || '',
          email: res.data.email || ''
        }
      } catch (err) {
        console.error(err)
      }
    },
    openProfileModal() {
      this.fetchProfile()
      this.showProfileModal = true
    },
    async updateCompanyProfile() {
      this.savingProfile = true
      try {
        const res = await axios.put('http://localhost:5000/api/auth/profile', this.profileForm, this.getAuthHeaders())
        this.companyUser = res.data
        localStorage.setItem('companyData', JSON.stringify(res.data))
        this.showAlert('Company profile updated successfully!')
        this.showProfileModal = false
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'Failed to update profile', 'danger')
      } finally {
        this.savingProfile = false
      }
    },
    openCreateModal() {
      this.createForm = {
        prime_location_name: '',
        price: 40,
        address: '',
        pin_code: '560001',
        grid_rows: 5,
        grid_cols: 6
      }
      this.showCreateModal = true
    },
    async createParkingSpace() {
      this.creatingLot = true
      try {
        await axios.post('http://localhost:5000/api/company/lots', this.createForm, this.getAuthHeaders())
        this.showAlert(`Parking space "${this.createForm.prime_location_name}" created successfully!`)
        this.showCreateModal = false
        this.fetchDashboard()
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'Failed to create parking space', 'danger')
      } finally {
        this.creatingLot = false
      }
    },
    async deleteLot(lot) {
      if (!confirm(`Are you sure you want to delete "${lot.prime_location_name}"?`)) return
      try {
        await axios.delete(`http://localhost:5000/api/company/lots/${lot.id}`, this.getAuthHeaders())
        this.showAlert(`Parking space "${lot.prime_location_name}" deleted successfully!`)
        this.fetchDashboard()
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'Failed to delete parking space', 'danger')
      }
    },

    getLotPreviewFloor(lot) {
      if (lot.floors && lot.floors.length > 0) {
        const idx = this.previewFloorIndex[lot.id] || 0
        return lot.floors[idx] || lot.floors[0]
      }
      return lot
    },
    setPreviewFloor(lotId, floorIdx) {
      this.previewFloorIndex = {
        ...this.previewFloorIndex,
        [lotId]: parseInt(floorIdx) || 0
      }
    },
    getFloorSlotCount(fl) {
      if (!fl || !fl.matrix) return 0
      let c = 0
      for (const row of fl.matrix) {
        for (const cell of row) {
          if (cell.type === 'parking' || cell.type === 'handicap') c++
        }
      }
      return c
    },
    generateDefaultMatrix(rows, cols) {
      const matrix = []
      for (let r = 0; r < rows; r++) {
        const rowArr = []
        for (let c = 0; c < cols; c++) {
          if (r === 1) {
            rowArr.push({ type: 'road' })
          } else if (r === rows - 1 && c === 0) {
            rowArr.push({ type: 'handicap' })
          } else if (r === rows - 1 && c === cols - 1) {
            rowArr.push({ type: 'stairs' })
          } else {
            rowArr.push({ type: 'parking' })
          }
        }
        matrix.push(rowArr)
      }
      return matrix
    },

    // ==================== EDIT SLOTS METHODS ====================
    openEditSlotsModal(lot) {
      this.editingLot = lot
      this.editSlotForm = {
        prime_location_name: lot.prime_location_name,
        price: lot.price,
        daily_rate: lot.daily_rate !== undefined ? lot.daily_rate : 0.0,
        overnight_rate: lot.overnight_rate !== undefined ? lot.overnight_rate : 0.0,
        peak_multiplier: lot.peak_multiplier !== undefined ? lot.peak_multiplier : 1.0,
        grace_period_minutes: lot.grace_period_minutes !== undefined ? lot.grace_period_minutes : 15,
        overstay_penalty_rate: lot.overstay_penalty_rate !== undefined ? lot.overstay_penalty_rate : 50.0,
        floors: []
      }

      if (lot.floors && lot.floors.length > 0) {
        this.editSlotForm.floors = lot.floors.map(f => {
          const rows = f.grid_rows || 5
          const cols = f.grid_cols || 6
          let matrix = []
          if (f.grid_layout && Array.isArray(f.grid_layout) && f.grid_layout.length === rows) {
            matrix = f.grid_layout.map(r => r.map(c => ({
              type: typeof c === 'object' && c ? (c.type || 'parking') : String(c)
            })))
          } else {
            matrix = this.generateDefaultMatrix(rows, cols)
          }
          return {
            id: f.id,
            floor_number: f.floor_number,
            floor_name: f.floor_name || (f.floor_number === 0 ? 'Ground Floor' : `Floor ${f.floor_number}`),
            grid_rows: rows,
            grid_cols: cols,
            matrix: matrix
          }
        })
      } else {
        const rows = lot.grid_rows || 5
        const cols = lot.grid_cols || 6
        let matrix = []
        if (lot.grid_layout && Array.isArray(lot.grid_layout) && lot.grid_layout.length === rows) {
          matrix = lot.grid_layout.map(r => r.map(c => ({
            type: typeof c === 'object' && c ? (c.type || 'parking') : String(c)
          })))
        } else {
          matrix = this.generateDefaultMatrix(rows, cols)
        }
        this.editSlotForm.floors = [{
          id: null,
          floor_number: 0,
          floor_name: 'Ground Floor',
          grid_rows: rows,
          grid_cols: cols,
          matrix: matrix
        }]
      }

      this.activeFloorIdx = 0
      this.activeTool = 'parking'
      this.showEditSlotsModal = true
    },
    closeEditSlotsModal() {
      this.showEditSlotsModal = false
      this.editingLot = null
    },
    addNewFloor() {
      const existingNumbers = this.editSlotForm.floors.map(f => f.floor_number)
      const nextNumber = existingNumbers.length > 0 ? (Math.max(0, ...existingNumbers) + 1) : 1
      const floorName = nextNumber > 0 ? `Level ${nextNumber}` : `Floor ${nextNumber}`
      const defaultRows = 5
      const defaultCols = 6
      const newFloor = {
        id: null,
        floor_number: nextNumber,
        floor_name: floorName,
        grid_rows: defaultRows,
        grid_cols: defaultCols,
        matrix: this.generateDefaultMatrix(defaultRows, defaultCols)
      }
      this.editSlotForm.floors.push(newFloor)
      this.activeFloorIdx = this.editSlotForm.floors.length - 1
    },
    removeActiveFloor() {
      if (this.editSlotForm.floors.length <= 1) {
        alert('A facility must contain at least one floor.')
        return
      }
      const fl = this.currentFloor
      if (!confirm(`Are you sure you want to remove ${fl.floor_name}? Any slots on this floor will be deleted.`)) return
      this.editSlotForm.floors.splice(this.activeFloorIdx, 1)
      this.activeFloorIdx = Math.max(0, this.activeFloorIdx - 1)
    },
    resizeActiveFloorGrid() {
      const fl = this.currentFloor
      const newRows = Math.min(Math.max(parseInt(fl.grid_rows) || 2, 2), 15)
      const newCols = Math.min(Math.max(parseInt(fl.grid_cols) || 2, 2), 15)
      fl.grid_rows = newRows
      fl.grid_cols = newCols

      const newMatrix = []
      for (let r = 0; r < newRows; r++) {
        const rowArr = []
        for (let c = 0; c < newCols; c++) {
          if (fl.matrix[r] && fl.matrix[r][c]) {
            rowArr.push({ type: fl.matrix[r][c].type || 'parking' })
          } else {
            rowArr.push({ type: r === 1 ? 'road' : 'parking' })
          }
        }
        newMatrix.push(rowArr)
      }
      fl.matrix = newMatrix
    },
    stampCell(r, c) {
      if (this.currentMatrix[r] && this.currentMatrix[r][c]) {
        this.currentMatrix[r][c].type = this.activeTool
      }
    },
    fillGrid(type) {
      for (let r = 0; r < this.currentFloor.grid_rows; r++) {
        for (let c = 0; c < this.currentFloor.grid_cols; c++) {
          if (this.currentMatrix[r] && this.currentMatrix[r][c]) {
            this.currentMatrix[r][c].type = type
          }
        }
      }
    },
    addRoadAisle() {
      const mid = Math.floor(this.currentFloor.grid_rows / 2)
      for (let c = 0; c < this.currentFloor.grid_cols; c++) {
        if (this.currentMatrix[mid] && this.currentMatrix[mid][c]) {
          this.currentMatrix[mid][c].type = 'road'
        }
      }
    },
    getCellLabel(cell, r, c) {
      const pfx = this.currentFloor.floor_number === 0 
        ? 'G' 
        : (this.currentFloor.floor_number < 0 ? `B${Math.abs(this.currentFloor.floor_number)}` : `L${this.currentFloor.floor_number}`)
      if (cell.type === 'parking') return `${pfx}-P${r + 1},${c + 1}`
      if (cell.type === 'handicap') return `${pfx}-H${r + 1},${c + 1}`
      if (cell.type === 'road') return 'Road'
      if (cell.type === 'stairs') return 'Exit'
      if (cell.type === 'ramp_up') return 'Ramp Up'
      if (cell.type === 'ramp_down') return 'Ramp Down'
      if (cell.type === 'elevator') return 'Elevator'
      return 'Empty'
    },
    async saveSlotsData() {
      if (this.computedGrandTotalSlots <= 0) {
        alert('Please mark at least 1 Parking space or Handicap space across your facility floors!')
        return
      }

      this.savingSlots = true
      try {
        const payload = {
          prime_location_name: this.editSlotForm.prime_location_name.trim(),
          price: this.editSlotForm.price,
          daily_rate: this.editSlotForm.daily_rate,
          overnight_rate: this.editSlotForm.overnight_rate,
          peak_multiplier: this.editSlotForm.peak_multiplier,
          grace_period_minutes: this.editSlotForm.grace_period_minutes,
          overstay_penalty_rate: this.editSlotForm.overstay_penalty_rate,
          floors: this.editSlotForm.floors.map(f => ({
            id: f.id,
            floor_number: f.floor_number,
            floor_name: f.floor_name,
            grid_rows: f.grid_rows,
            grid_cols: f.grid_cols,
            grid_layout: f.matrix
          }))
        }

        const res = await axios.put(
          `http://localhost:5000/api/company/lots/${this.editingLot.id}`,
          payload,
          this.getAuthHeaders()
        )

        this.showAlert(
          `Facility updated! Registered ${res.data.number_of_spots} total bookable slots across ${this.editSlotForm.floors.length} floors.`
        )
        this.closeEditSlotsModal()
        this.fetchDashboard()
      } catch (err) {
        alert(err.response?.data?.error || 'Failed to save slots and multi-floor layouts')
      } finally {
        this.savingSlots = false
      }
    },
    async fetchAnalytics() {
      this.analyticsLoading = true
      try {
        const res = await axios.get('http://localhost:5000/api/company/analytics', this.getAuthHeaders())
        this.analyticsData = res.data
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'Failed to load facility analytics', 'danger')
      } finally {
        this.analyticsLoading = false
      }
    },
    async fetchSubscriptions() {
      this.subscriptionsLoading = true
      try {
        const res = await axios.get('http://localhost:5000/api/company/subscriptions', this.getAuthHeaders())
        this.subscriptions = res.data.subscriptions || []
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'Failed to load subscriptions', 'danger')
      } finally {
        this.subscriptionsLoading = false
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
            console.error('SSE spot update error:', err)
          }
        })
      } catch (err) {
        console.error('SSE stream error:', err)
      }
    },
    closeLiveStream() {
      if (this.eventSource) {
        this.eventSource.close()
        this.eventSource = null
      }
    },
    handleRealtimeSpotUpdate(data) {
      const spotId = data.spot_id
      const newStatus = data.status
      if (!spotId) return

      this.realtimePulsingSpots = { ...this.realtimePulsingSpots, [spotId]: true }
      setTimeout(() => {
        const copy = { ...this.realtimePulsingSpots }
        delete copy[spotId]
        this.realtimePulsingSpots = copy
      }, 1800)

      for (const lot of this.lots) {
        if (lot.id === data.lot_id) {
          if (newStatus === 'O') {
            lot.available_spots = Math.max(0, (lot.available_spots || 1) - 1)
            lot.occupied_spots = (lot.occupied_spots || 0) + 1
          } else if (newStatus === 'A') {
            lot.available_spots = (lot.available_spots || 0) + 1
            lot.occupied_spots = Math.max(0, (lot.occupied_spots || 1) - 1)
          }
          if (lot.spots) {
            for (const sp of lot.spots) {
              if (sp.id === spotId) sp.status = newStatus
            }
          }
          if (lot.floors) {
            for (const fl of lot.floors) {
              if (fl.spots) {
                for (const sp of fl.spots) {
                  if (sp.id === spotId) sp.status = newStatus
                }
              }
            }
          }
        }
      }

      if (this.activeTab === 'analytics' && this.analyticsData?.summary) {
        if (newStatus === 'O') {
          this.analyticsData.summary.occupied_spots = (this.analyticsData.summary.occupied_spots || 0) + 1
          this.analyticsData.summary.available_spots = Math.max(0, (this.analyticsData.summary.available_spots || 1) - 1)
        } else if (newStatus === 'A') {
          this.analyticsData.summary.occupied_spots = Math.max(0, (this.analyticsData.summary.occupied_spots || 1) - 1)
          this.analyticsData.summary.available_spots = (this.analyticsData.summary.available_spots || 0) + 1
        }
      }
    }
  }
}
</script>

<style scoped>
.company-wrapper {
  background-color: #f8fafc;
}

.max-w-1400 {
  max-width: 1400px;
  margin: 0 auto;
}

.lot-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.lot-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08) !important;
}

/* Palette Buttons */
.palette-btn {
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.15s ease;
}

.ring-active {
  transform: scale(1.05);
  box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.3) !important;
}

/* Interactive Clickable Grid Canvas */
.clickable-grid {
  display: grid;
  gap: 8px;
  user-select: none;
}

.grid-cell {
  aspect-ratio: 1;
  min-height: 65px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
  border: 2px solid transparent;
}

.grid-cell:hover {
  transform: scale(1.06);
  z-index: 2;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
}

.cell-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  line-height: 1.1;
}

.cell-icon {
  font-size: 1.3rem;
}

.cell-label {
  font-size: 0.65rem;
  font-weight: 700;
  margin-top: 2px;
}

/* Cell Types */
.cell-parking {
  background-color: #d1e7dd;
  border-color: #198754;
  color: #0f5132;
}

.cell-handicap {
  background-color: #cff4fc;
  border-color: #0dcaf0;
  color: #055160;
}

.cell-road {
  background-color: #343a40;
  border-color: #212529;
  color: #f8f9fa;
  background-image: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 10px,
    rgba(255, 255, 255, 0.05) 10px,
    rgba(255, 255, 255, 0.05) 20px
  );
}

.cell-stairs {
  background-color: #fff3cd;
  border-color: #ffc107;
  color: #664d03;
}

.cell-ramp_up {
  background-color: #e0cffc;
  border-color: #6f42c1;
  color: #3d1a78;
}

.cell-ramp_down {
  background-color: #d8b4fe;
  border-color: #9333ea;
  color: #581c87;
}

.cell-elevator {
  background-color: #cff4fc;
  border-color: #0dcaf0;
  color: #055160;
}

.cell-empty {
  background-color: #f8f9fa;
  border-color: #dee2e6;
  color: #6c757d;
}

/* Mini Thumbnail Grid */
.mini-grid {
  display: grid;
  gap: 3px;
  max-width: 200px;
}

.mini-cell {
  height: 12px;
  border-radius: 2px;
}

/* Real-time SSE Pulse Animation */
@keyframes spot-pulse {
  0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(13, 110, 253, 0.7); }
  50% { transform: scale(1.08); box-shadow: 0 0 0 10px rgba(13, 110, 253, 0); }
  100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(13, 110, 253, 0); }
}

.pulse-live {
  animation: spot-pulse 1.2s ease-out;
  z-index: 10;
}
</style>

