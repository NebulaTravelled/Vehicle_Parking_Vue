<template>
  <div class="bg-light min-vh-100">
    <AdminLogin v-if="!isLoggedIn" @login-success="handleLoginSuccess" />
    
    <div v-else>
      <!-- Top Navigation Bar -->
      <nav class="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm px-4">
        <div class="container-fluid">
          <span class="navbar-brand fw-bold">
            <span class="badge bg-light text-primary me-2">Superuser</span>
            Parking Management Admin
          </span>
          <div class="d-flex align-items-center gap-3">
            <span class="text-white-50 small">Role: Root Admin</span>
            <button class="btn btn-outline-light btn-sm" @click="logout">Logout</button>
          </div>
        </div>
      </nav>
      
      <!-- Tab Bar -->
      <div class="bg-white border-bottom px-4">
        <ul class="nav nav-tabs border-0 pt-2">
          <li class="nav-item">
            <button
              class="nav-link"
              :class="{ active: activeTab === 'dashboard' }"
              @click="activeTab = 'dashboard'"
            >
              📊 Live Spot Status
            </button>
          </li>
          <li class="nav-item">
            <button
              class="nav-link"
              :class="{ active: activeTab === 'lots' }"
              @click="activeTab = 'lots'"
            >
              🅿️ Manage Parking Lots
            </button>
          </li>
          <li class="nav-item">
            <button
              class="nav-link"
              :class="{ active: activeTab === 'users' }"
              @click="activeTab = 'users'"
            >
              👥 Registered Users
            </button>
          </li>
          <li class="nav-item">
            <button
              class="nav-link"
              :class="{ active: activeTab === 'jobs' }"
              @click="activeTab = 'jobs'"
            >
              ⚙️ Jobs & Performance
            </button>
          </li>
          <li class="nav-item">
            <button
              class="nav-link"
              :class="{ active: activeTab === 'analytics' }"
              @click="activeTab = 'analytics'"
            >
              📈 Analytics & Heatmaps
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

      <!-- Main Content Area -->
      <div class="container-fluid p-4">
        <div v-if="alertMessage" class="alert alert-dismissible fade show mb-4" :class="'alert-' + alertType">
          {{ alertMessage }}
          <button type="button" class="btn-close" @click="alertMessage = ''"></button>
        </div>

        <!-- ==================== TAB 1: LIVE SPOT STATUS & DASHBOARD ==================== -->
        <div v-if="activeTab === 'dashboard'">
          <!-- Statistics Cards -->
          <div class="row g-3 mb-4">
            <div class="col-md-2 col-6">
              <div class="card shadow-sm border-0 border-start border-primary border-4">
                <div class="card-body">
                  <div class="text-muted small">Total Lots</div>
                  <h3 class="fw-bold mb-0 text-primary">{{ stats.total_lots || 0 }}</h3>
                </div>
              </div>
            </div>
            <div class="col-md-2 col-6">
              <div class="card shadow-sm border-0 border-start border-secondary border-4">
                <div class="card-body">
                  <div class="text-muted small">Total 4W Spots</div>
                  <h3 class="fw-bold mb-0">{{ stats.total_spots || 0 }}</h3>
                </div>
              </div>
            </div>
            <div class="col-md-2 col-6">
              <div class="card shadow-sm border-0 border-start border-success border-4">
                <div class="card-body">
                  <div class="text-muted small">Available (A)</div>
                  <h3 class="fw-bold mb-0 text-success">{{ stats.available_spots || 0 }}</h3>
                </div>
              </div>
            </div>
            <div class="col-md-2 col-6">
              <div class="card shadow-sm border-0 border-start border-danger border-4">
                <div class="card-body">
                  <div class="text-muted small">Occupied (O)</div>
                  <h3 class="fw-bold mb-0 text-danger">{{ stats.occupied_spots || 0 }}</h3>
                </div>
              </div>
            </div>
            <div class="col-md-2 col-6">
              <div class="card shadow-sm border-0 border-start border-info border-4">
                <div class="card-body">
                  <div class="text-muted small">Registered Users</div>
                  <h3 class="fw-bold mb-0 text-info">{{ stats.total_users || 0 }}</h3>
                </div>
              </div>
            </div>
            <div class="col-md-2 col-6">
              <div class="card shadow-sm border-0 border-start border-warning border-4">
                <div class="card-body">
                  <div class="text-muted small">Total Revenue</div>
                  <h3 class="fw-bold mb-0 text-warning">₹{{ stats.total_revenue || 0 }}</h3>
                </div>
              </div>
            </div>
          </div>

          <!-- Spot Matrix Overview per Parking Lot with Roads, Handicap, Regular, Stairs & Empty Slots -->
          <div class="card shadow-sm border-0 mb-4 p-3 bg-white">
            <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-2">
              <div>
                <h4 class="fw-bold mb-0 text-dark">Live Facility Grid & Spot Status</h4>
                <p class="text-muted small mb-0">Visual layout rendering of roads, regular bays, handicap bays, stairs, and empty slots.</p>
              </div>
              <button class="btn btn-outline-primary btn-sm fw-semibold" @click="fetchDashboard">
                <i class="bi bi-arrow-clockwise me-1"></i> Refresh Grid
              </button>
            </div>

            <!-- Complete Legend Strip -->
            <div class="d-flex flex-wrap gap-2 pt-2 border-top small align-items-center">
              <span class="fw-bold text-secondary me-1">Legend:</span>
              <span class="badge bg-success-subtle text-success border border-success-subtle px-2.5 py-1.5 rounded-pill">
                🅿️ Regular Available
              </span>
              <span class="badge bg-danger-subtle text-danger border border-danger-subtle px-2.5 py-1.5 rounded-pill">
                🅿️ Regular Occupied
              </span>
              <span class="badge bg-info-subtle text-info-emphasis border border-info-subtle px-2.5 py-1.5 rounded-pill">
                ♿ Handicap Available
              </span>
              <span class="badge bg-warning-subtle text-warning-emphasis border border-warning-subtle px-2.5 py-1.5 rounded-pill">
                ♿ Handicap Occupied
              </span>
              <span class="badge bg-dark text-white px-2.5 py-1.5 rounded-pill">
                🛣️ Road / Driveway
              </span>
              <span class="badge text-white px-2.5 py-1.5 rounded-pill" style="background-color: #6f42c1;">
                🚗⤴️ Ramp Up
              </span>
              <span class="badge text-white px-2.5 py-1.5 rounded-pill" style="background-color: #9333ea;">
                🚗⤵️ Ramp Down
              </span>
              <span class="badge bg-info-subtle text-info-emphasis border border-info-subtle px-2.5 py-1.5 rounded-pill">
                🛗 Elevator
              </span>
              <span class="badge bg-warning text-dark px-2.5 py-1.5 rounded-pill">
                🪜 Stairs / Exit
              </span>
              <span class="badge bg-light text-secondary border px-2.5 py-1.5 rounded-pill">
                ⬜ Empty Slot
              </span>
            </div>
          </div>

          <!-- Search Bar for Dashboard Lots / Slots -->
          <div class="card shadow-sm border-0 mb-4 rounded-3">
            <div class="card-body p-3">
              <div class="row g-2 align-items-center">
                <div class="col-md-8 col-lg-9">
                  <div class="input-group">
                    <span class="input-group-text bg-white border-end-0 text-muted">
                      🔍
                    </span>
                    <input
                      v-model="dashboardSearchQuery"
                      type="text"
                      class="form-control border-start-0 ps-0"
                      placeholder="Search parking slots by facility name, address, or pincode..."
                      @keydown.esc="dashboardSearchQuery = ''"
                    />
                    <button
                      v-if="dashboardSearchQuery"
                      class="btn btn-outline-secondary border-start-0"
                      type="button"
                      @click="dashboardSearchQuery = ''"
                      title="Clear search"
                    >
                      ✕
                    </button>
                  </div>
                </div>
                <div class="col-md-4 col-lg-3 text-md-end">
                  <span class="badge bg-light text-secondary border p-2 w-100 text-center fw-normal">
                    Showing <strong>{{ filteredDashboardLots.length }}</strong> of {{ dashboardLots.length }} Facilities
                  </span>
                </div>
              </div>
              <div v-if="dashboardSearchQuery.trim()" class="mt-2.5 small d-flex align-items-center gap-2 text-muted">
                <span>Active search filter:</span>
                <span class="badge bg-primary-subtle text-primary border font-monospace">"{{ dashboardSearchQuery.trim() }}"</span>
                <button class="btn btn-link btn-xs text-danger p-0 ms-1 text-decoration-none" @click="dashboardSearchQuery = ''">Clear filter</button>
              </div>
            </div>
          </div>

          <div v-if="dashboardLots.length === 0" class="card shadow-sm text-center py-5 border-0">
            <div class="card-body">
              <div class="fs-1 text-muted mb-2">🅿️</div>
              <h5 class="fw-bold">No parking lots created yet.</h5>
              <p class="text-muted small">Create a parking lot to start allocating spots.</p>
              <button class="btn btn-primary" @click="activeTab = 'lots'">Create Parking Lot</button>
            </div>
          </div>

          <!-- Empty State: Search Query Yields 0 Results -->
          <div v-else-if="filteredDashboardLots.length === 0" class="card text-center py-5 shadow-sm border-0 rounded-4 mb-4">
            <div class="card-body">
              <div class="fs-1 mb-2">🔍</div>
              <h5 class="fw-bold text-dark">No matching parking slots found</h5>
              <p class="text-muted small mb-3">
                No facilities or slots matched your search for "<strong>{{ dashboardSearchQuery }}</strong>".<br>
                Try searching by a different name, address, or PIN code.
              </p>
              <button class="btn btn-primary btn-sm fw-semibold" @click="dashboardSearchQuery = ''">
                ✕ Clear Search Filter
              </button>
            </div>
          </div>

          <div v-else class="row g-4">
            <div v-for="lot in filteredDashboardLots" :key="lot.id" class="col-12 col-xl-6">
              <div class="card shadow-sm h-100 border-0 rounded-4 overflow-hidden">
                
                <!-- Facility Header -->
                <div class="card-header bg-white border-bottom p-3 d-flex justify-content-between align-items-center flex-wrap gap-2">
                  <div>
                    <h5 class="fw-bold mb-0 text-primary">{{ lot.prime_location_name }}</h5>
                    <span class="text-muted small"><i class="bi bi-geo-alt me-1"></i>{{ lot.address }} (PIN: {{ lot.pin_code }})</span>
                  </div>
                  <div class="d-flex align-items-center gap-2">
                    <span class="badge bg-light text-dark border fw-bold px-2.5 py-1.5">₹{{ lot.price }}/hr</span>
                    <span class="badge bg-success-subtle text-success fw-bold px-2.5 py-1.5">{{ lot.available_count }} Free</span>
                    <span class="badge bg-danger-subtle text-danger fw-bold px-2.5 py-1.5">{{ lot.occupied_count }} In Use</span>
                  </div>
                </div>

                <div class="card-body p-4 bg-light">
                  <!-- Multi-Floor Deck Navigation Tabs -->
                  <div v-if="lot.floors && lot.floors.length > 1" class="d-flex flex-wrap align-items-center gap-1 mb-3 bg-white p-2 rounded-3 border">
                    <span class="small fw-bold text-secondary me-1">Floor Level:</span>
                    <button 
                      v-for="(fl, fIdx) in lot.floors" 
                      :key="'admin-fl-' + fl.id"
                      type="button"
                      class="btn btn-xs rounded-pill px-3 py-1 fw-semibold"
                      :class="(selectedFloorByLot[lot.id] || 0) === fIdx ? 'btn-primary text-white shadow-sm' : 'btn-outline-secondary bg-white'"
                      @click="setAdminActiveFloor(lot.id, fIdx)"
                    >
                      🏢 {{ fl.floor_name }} ({{ fl.available_count }} free)
                    </button>
                  </div>

                  <!-- Summary Pill Badges for All Elements -->
                  <div class="d-flex flex-wrap gap-2 mb-3 small bg-white p-2.5 rounded-3 border">
                    <span class="badge bg-light text-dark border">
                      🚗 Regular: <strong>{{ getAdminActiveFloor(lot).regular_available !== undefined ? getAdminActiveFloor(lot).regular_available : lot.regular_available }} / {{ getAdminActiveFloor(lot).regular_spots }}</strong> Free
                    </span>
                    <span class="badge bg-light text-primary border">
                      ♿ Handicap: <strong>{{ getAdminActiveFloor(lot).handicap_available !== undefined ? getAdminActiveFloor(lot).handicap_available : lot.handicap_available }} / {{ getAdminActiveFloor(lot).handicap_spots }}</strong> Free
                    </span>
                    <span class="badge bg-dark-subtle text-dark border">
                      🛣️ Roads: <strong>{{ getAdminActiveFloor(lot).roads_count || 0 }}</strong>
                    </span>
                    <span class="badge bg-warning-subtle text-dark border">
                      🪜 Stairs: <strong>{{ getAdminActiveFloor(lot).stairs_count || 0 }}</strong>
                    </span>
                    <span v-if="getAdminActiveFloor(lot).ramp_up_count > 0" class="badge text-white border" style="background-color: #6f42c1;">
                      🚗⤴️ Ramps Up: <strong>{{ getAdminActiveFloor(lot).ramp_up_count }}</strong>
                    </span>
                    <span v-if="getAdminActiveFloor(lot).ramp_down_count > 0" class="badge text-white border" style="background-color: #9333ea;">
                      🚗⤵️ Ramps Down: <strong>{{ getAdminActiveFloor(lot).ramp_down_count }}</strong>
                    </span>
                    <span v-if="getAdminActiveFloor(lot).elevator_count > 0" class="badge bg-info-subtle text-info border">
                      🛗 Elevators: <strong>{{ getAdminActiveFloor(lot).elevator_count }}</strong>
                    </span>
                    <span class="badge bg-light text-muted border">
                      ⬜ Empty: <strong>{{ getAdminActiveFloor(lot).empty_count || 0 }}</strong>
                    </span>
                    <span class="ms-auto text-muted small">
                      {{ getAdminActiveFloor(lot).floor_name || 'Ground' }} ({{ getAdminActiveFloor(lot).grid_rows }} × {{ getAdminActiveFloor(lot).grid_cols }})
                    </span>
                  </div>

                  <!-- Visual Grid Canvas (Roads, Handicap, Regular, Stairs, Ramps, Elevators, Empty) -->
                  <div v-if="getAdminActiveFloor(lot).grid_layout && getAdminActiveFloor(lot).grid_layout.length" class="admin-grid-wrapper p-3 bg-white rounded-3 border overflow-auto">
                    <div 
                      class="admin-grid mx-auto" 
                      :style="{ 
                        gridTemplateColumns: `repeat(${getAdminActiveFloor(lot).grid_cols}, minmax(75px, 1fr))`,
                        maxWidth: `${getAdminActiveFloor(lot).grid_cols * 105}px` 
                      }"
                    >
                      <template v-for="(row, rIdx) in getAdminActiveFloor(lot).grid_layout" :key="'admin-r-' + rIdx">
                        <div 
                          v-for="(cell, cIdx) in row" 
                          :key="'admin-cell-' + rIdx + '-' + cIdx"
                          class="admin-cell shadow-sm"
                          :class="getCellClasses(cell)"
                          :title="getCellTooltip(cell, rIdx, cIdx)"
                        >
                          <!-- Regular Parking Space -->
                          <div v-if="cell.type === 'parking'" class="cell-inner">
                            <span class="cell-icon">🅿️</span>
                            <span class="cell-title fw-bold">{{ cell.spot?.spot_number || `P-${rIdx+1},${cIdx+1}` }}</span>
                            <span 
                              class="cell-status-badge badge"
                              :class="cell.spot?.status === 'O' ? 'bg-danger text-white' : 'bg-success text-white'"
                            >
                              {{ cell.spot?.status === 'O' ? 'Occupied' : 'Free' }}
                            </span>
                          </div>

                          <!-- Handicap Space -->
                          <div v-else-if="cell.type === 'handicap'" class="cell-inner">
                            <span class="cell-icon">♿</span>
                            <span class="cell-title fw-bold">{{ cell.spot?.spot_number || `H-${rIdx+1},${cIdx+1}` }}</span>
                            <span 
                              class="cell-status-badge badge"
                              :class="cell.spot?.status === 'O' ? 'bg-warning text-dark' : 'bg-info text-dark'"
                            >
                              {{ cell.spot?.status === 'O' ? 'Occupied' : 'Free' }}
                            </span>
                          </div>

                          <!-- Road / Driveway -->
                          <div v-else-if="cell.type === 'road'" class="cell-inner">
                            <span class="cell-icon">🛣️</span>
                            <span class="cell-title">Road</span>
                            <span class="cell-sub-dash">────</span>
                          </div>

                          <!-- Ramp Up -->
                          <div v-else-if="cell.type === 'ramp_up'" class="cell-inner">
                            <span class="cell-icon">🚗⤴️</span>
                            <span class="cell-title">Ramp Up</span>
                            <span class="cell-sub text-muted">To Deck Above</span>
                          </div>

                          <!-- Ramp Down -->
                          <div v-else-if="cell.type === 'ramp_down'" class="cell-inner">
                            <span class="cell-icon">🚗⤵️</span>
                            <span class="cell-title">Ramp Down</span>
                            <span class="cell-sub text-muted">To Deck Below</span>
                          </div>

                          <!-- Elevator -->
                          <div v-else-if="cell.type === 'elevator'" class="cell-inner">
                            <span class="cell-icon">🛗</span>
                            <span class="cell-title">Elevator</span>
                            <span class="cell-sub text-muted">Lift Core</span>
                          </div>

                          <!-- Stairs / Exit -->
                          <div v-else-if="cell.type === 'stairs'" class="cell-inner">
                            <span class="cell-icon">🪜</span>
                            <span class="cell-title">Stairs</span>
                            <span class="cell-sub text-muted">Exit</span>
                          </div>

                          <!-- Empty Slot -->
                          <div v-else class="cell-inner">
                            <span class="cell-icon text-muted">⬜</span>
                            <span class="cell-title text-muted">Empty</span>
                            <span class="cell-sub text-muted">Slot</span>
                          </div>

                        </div>
                      </template>
                    </div>
                  </div>

                  <!-- Fallback Simple Wrap for Legacy Lots -->
                  <div v-else class="d-flex flex-wrap gap-2">
                    <div
                      v-for="spot in lot.spots"
                      :key="spot.id"
                      class="border rounded p-2 text-center"
                      :class="spot.status === 'A' ? 'bg-success text-white' : 'bg-danger text-white'"
                      style="min-width: 90px; flex: 0 0 calc(20% - 8px);"
                    >
                      <div class="small fw-bold">{{ spot.spot_number }}</div>
                      <div class="badge mt-1" :class="spot.status === 'A' ? 'bg-white text-success' : 'bg-white text-danger'">
                        {{ spot.status === 'A' ? 'A (Free)' : 'O (In Use)' }}
                      </div>
                    </div>
                  </div>

                </div>

              </div>
            </div>
          </div>
        </div>

        <!-- ==================== TAB 2: PARKING LOTS MANAGEMENT ==================== -->
        <div v-if="activeTab === 'lots'">
          <div class="card shadow-sm border-0 mb-4">
            <div class="card-body p-4">
              <div class="d-flex justify-content-between align-items-center mb-4">
                <div>
                  <h4 class="fw-bold mb-1">Manage Parking Lots</h4>
                  <p class="text-muted small mb-0">Create, edit, or delete parking lots and scale spots up or down.</p>
                </div>
                <button class="btn btn-success" @click="openCreateLotModal">
                  + Create New Parking Lot
                </button>
              </div>

              <!-- Search Bar for Lots Table -->
              <div class="row g-2 mb-3 align-items-center">
                <div class="col-md-6 col-lg-5">
                  <div class="input-group">
                    <span class="input-group-text bg-white border-end-0 text-muted">🔍</span>
                    <input
                      v-model="lotsSearchQuery"
                      type="text"
                      class="form-control border-start-0 ps-0"
                      placeholder="Search lots by name, address, or pincode..."
                      @keydown.esc="lotsSearchQuery = ''"
                    />
                    <button
                      v-if="lotsSearchQuery"
                      class="btn btn-outline-secondary border-start-0"
                      type="button"
                      @click="lotsSearchQuery = ''"
                      title="Clear search"
                    >
                      ✕
                    </button>
                  </div>
                </div>
                <div class="col-md-6 col-lg-7 text-md-end text-muted small">
                  Showing <strong>{{ filteredLots.length }}</strong> of {{ lots.length }} Facilities
                </div>
              </div>

              <!-- Lots Table -->
              <div class="table-responsive">
                <table class="table table-hover align-middle">
                  <thead class="table-light">
                    <tr>
                      <th>ID</th>
                      <th>Prime Location Name</th>
                      <th>Address</th>
                      <th>Pin Code</th>
                      <th>Price / Hour</th>
                      <th>Total Spots</th>
                      <th>Available (A)</th>
                      <th>Occupied (O)</th>
                      <th class="text-end">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="lot in filteredLots" :key="lot.id">
                      <td>{{ lot.id }}</td>
                      <td class="fw-bold text-primary">{{ lot.prime_location_name }}</td>
                      <td>{{ lot.address }}</td>
                      <td>{{ lot.pin_code }}</td>
                      <td class="fw-semibold text-success">₹{{ lot.price.toFixed(2) }}</td>
                      <td><span class="badge bg-secondary">{{ lot.number_of_spots }}</span></td>
                      <td><span class="badge bg-success">{{ lot.available_spots }}</span></td>
                      <td><span class="badge bg-danger">{{ lot.occupied_spots }}</span></td>
                      <td class="text-end">
                        <button class="btn btn-outline-primary btn-sm me-2" @click="openEditLotModal(lot)">
                          ✏️ Edit / Resize
                        </button>
                        <button class="btn btn-outline-danger btn-sm" @click="handleDeleteLot(lot)">
                          🗑️ Delete
                        </button>
                      </td>
                    </tr>
                    <tr v-if="lots.length === 0">
                      <td colspan="9" class="text-center py-4 text-muted">No parking lots found. Click "Create New Parking Lot" above.</td>
                    </tr>
                    <tr v-else-if="filteredLots.length === 0">
                      <td colspan="9" class="text-center py-4 text-muted">
                        No parking lots found matching "<strong>{{ lotsSearchQuery }}</strong>".
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <!-- ==================== TAB 3: REGISTERED USERS ==================== -->
        <div v-if="activeTab === 'users'">
          <div class="card shadow-sm border-0">
            <div class="card-body p-4">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <h4 class="fw-bold mb-0">Registered Users ({{ users.length }})</h4>
                <button class="btn btn-outline-primary btn-sm" @click="fetchUsers" :disabled="usersLoading">
                  {{ usersLoading ? 'Refreshing...' : '🔄 Refresh' }}
                </button>
              </div>
              <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                  <thead class="table-light">
                    <tr>
                      <th>ID</th>
                      <th>Username</th>
                      <th>Email</th>
                      <th>Role</th>
                      <th>Registration Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="user in users" :key="user.id">
                      <td>{{ user.id }}</td>
                      <td class="fw-semibold">{{ user.username }}</td>
                      <td>{{ user.email }}</td>
                      <td>
                        <span class="badge" :class="user.role === 'admin' ? 'bg-primary' : 'bg-success'">
                          {{ user.role === 'admin' ? 'Superuser Admin' : 'User' }}
                        </span>
                      </td>
                      <td>{{ user.created_at ? new Date(user.created_at).toLocaleString() : 'N/A' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <!-- ==================== TAB 4: JOBS & PERFORMANCE ==================== -->
        <div v-if="activeTab === 'jobs'">
          <div class="row g-4">
            <!-- Job A: Daily Reminders -->
            <div class="col-md-6">
              <div class="card shadow-sm border-0 h-100">
                <div class="card-body p-4">
                  <h5 class="fw-bold text-primary mb-3">📅 Daily Reminders (Scheduled Job)</h5>
                  <p class="text-muted small">
                    Checks if users have not visited or if parking lots were created. Sends alert to Google Chat Webhooks or generates daily reminder logs.
                  </p>
                  <div class="mb-3">
                    <label class="form-label small fw-bold">Google Chat Webhook URL (Optional)</label>
                    <input v-model="reminderWebhookUrl" type="url" class="form-control form-control-sm" placeholder="https://chat.googleapis.com/v1/spaces/.../messages?key=..." />
                  </div>
                  <button class="btn btn-primary btn-sm" @click="triggerDailyReminders" :disabled="reminderRunning">
                    {{ reminderRunning ? 'Dispatching Reminders...' : 'Trigger Daily Reminder Job' }}
                  </button>
                  <div v-if="reminderResult" class="alert alert-info mt-3 mb-0 small">
                    <strong>Result:</strong> {{ reminderResult.message }} (Targeted: {{ reminderResult.recipients_count }} users)
                  </div>
                </div>
              </div>
            </div>

            <!-- Performance and Caching -->
            <div class="col-md-6">
              <div class="card shadow-sm border-0 h-100">
                <div class="card-body p-4">
                  <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="fw-bold text-success mb-0">⚡ API Performance & Caching</h5>
                    <button class="btn btn-outline-success btn-sm" @click="fetchCacheStats">🔄 Refresh</button>
                  </div>
                  <p class="text-muted small">
                    High-performance in-memory caching with TTL expiry and real-time invalidation upon parking lot mutations or bookings.
                  </p>
                  <div class="row g-3 text-center my-2">
                    <div class="col-4">
                      <div class="bg-light p-3 rounded">
                        <div class="text-muted small">Cache Hits</div>
                        <h4 class="fw-bold text-success mb-0">{{ cacheStats.cache_hits || 0 }}</h4>
                      </div>
                    </div>
                    <div class="col-4">
                      <div class="bg-light p-3 rounded">
                        <div class="text-muted small">Cache Misses</div>
                        <h4 class="fw-bold text-secondary mb-0">{{ cacheStats.cache_misses || 0 }}</h4>
                      </div>
                    </div>
                    <div class="col-4">
                      <div class="bg-light p-3 rounded">
                        <div class="text-muted small">Active Keys</div>
                        <h4 class="fw-bold text-primary mb-0">{{ cacheStats.cached_entries_count || 0 }}</h4>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ==================== TAB 5: BUSINESS INTELLIGENCE & ANALYTICS ==================== -->
        <div v-if="activeTab === 'analytics'">
          <div class="card shadow-sm border-0 mb-4">
            <div class="card-body p-4">
              <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
                <div>
                  <h4 class="fw-bold mb-1 text-dark d-flex align-items-center gap-2">
                    <span>📈 Business Intelligence & Utilization Analytics</span>
                    <span class="badge bg-primary fs-6">Superuser Scope</span>
                  </h4>
                  <p class="text-muted small mb-0">Platform-wide multi-deck utilization heatmaps, vehicle dwell times, and revenue yields.</p>
                </div>
                <div class="d-flex gap-2">
                  <span class="badge bg-success-subtle text-success border border-success-subtle d-flex align-items-center px-3">
                    🟢 Live Event Stream Active
                  </span>
                  <button class="btn btn-outline-primary btn-sm fw-semibold" @click="fetchAnalytics" :disabled="analyticsLoading">
                    {{ analyticsLoading ? 'Loading Analytics...' : '🔄 Refresh Metrics' }}
                  </button>
                </div>
              </div>

              <!-- Top KPI Summary Cards -->
              <div v-if="analyticsData?.summary" class="row g-3 mb-4">
                <div class="col-lg-2 col-md-4 col-sm-6">
                  <div class="card bg-light border-0 p-3 h-100 rounded-3">
                    <span class="text-muted small fw-semibold text-uppercase">Total Revenue</span>
                    <h3 class="fw-bold text-success mb-1 mt-1">₹{{ (analyticsData.summary.total_revenue || 0).toFixed(2) }}</h3>
                    <small class="text-muted">{{ analyticsData.summary.total_bookings }} total sessions</small>
                  </div>
                </div>
                <div class="col-lg-2 col-md-4 col-sm-6">
                  <div class="card bg-light border-0 p-3 h-100 rounded-3">
                    <span class="text-muted small fw-semibold text-uppercase">Live Occupancy</span>
                    <h3 class="fw-bold text-primary mb-1 mt-1">{{ analyticsData.summary.active_occupancy_rate }}%</h3>
                    <small class="text-muted">{{ analyticsData.summary.occupied_spots }} / {{ analyticsData.summary.total_spots }} slots filled</small>
                  </div>
                </div>
                <div class="col-lg-2 col-md-4 col-sm-6">
                  <div class="card bg-light border-0 p-3 h-100 rounded-3">
                    <span class="text-muted small fw-semibold text-uppercase">Average Dwell Time</span>
                    <h3 class="fw-bold text-dark mb-1 mt-1">{{ analyticsData.summary.avg_dwell_time_formatted || '0m' }}</h3>
                    <small class="text-muted">{{ analyticsData.summary.avg_dwell_time_minutes }}m average stay</small>
                  </div>
                </div>
                <div class="col-lg-2 col-md-4 col-sm-6">
                  <div class="card bg-light border-0 p-3 h-100 rounded-3">
                    <span class="text-muted small fw-semibold text-uppercase">Turnover Rate</span>
                    <h3 class="fw-bold text-info mb-1 mt-1">{{ analyticsData.summary.vehicle_turnover_rate }}x</h3>
                    <small class="text-muted">Vehicle turnover index</small>
                  </div>
                </div>
                <div class="col-lg-2 col-md-4 col-sm-6">
                  <div class="card bg-light border-0 p-3 h-100 rounded-3">
                    <span class="text-muted small fw-semibold text-uppercase">Peak Rush Window</span>
                    <h5 class="fw-bold text-warning-emphasis mb-1 mt-2">⚡ {{ analyticsData.summary.peak_rush_hour || '8 - 11 AM' }}</h5>
                    <small class="text-muted">Highest arrival period</small>
                  </div>
                </div>
                <div class="col-lg-2 col-md-4 col-sm-6">
                  <div class="card bg-light border-0 p-3 h-100 rounded-3">
                    <span class="text-muted small fw-semibold text-uppercase">Busiest Deck</span>
                    <h5 class="fw-bold text-primary mb-1 mt-2">🏢 {{ analyticsData.summary.busiest_floor || 'Ground Floor' }}</h5>
                    <small class="text-muted">Top vehicle traffic</small>
                  </div>
                </div>
              </div>

              <!-- 24-Hour Utilization Heatmap -->
              <div class="card border mb-4 rounded-3 overflow-hidden shadow-sm">
                <div class="card-header bg-white border-bottom p-3 d-flex justify-content-between align-items-center">
                  <h6 class="fw-bold mb-0 text-dark">
                    <span>🔥 24-Hour Arrival & Utilization Heatmap (00:00 – 23:00)</span>
                  </h6>
                  <div class="small text-muted d-flex align-items-center gap-2">
                    <span class="badge bg-warning text-dark">⚡ Peak Window (8-11 AM, 5-8 PM)</span>
                    <span class="badge bg-primary text-white">Intensity: 0% → 100%</span>
                  </div>
                </div>
                <div class="card-body p-3">
                  <div class="row g-1 text-center">
                    <div 
                      v-for="h in analyticsData?.hourly_heatmap || []" 
                      :key="'heat-' + h.hour" 
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

              <!-- Two Column Layout: Multi-Floor Yield Table & Fleet / Dwell Brackets -->
              <div class="row g-4">
                <!-- Left: Multi-Floor Utilization & Yield Breakdown -->
                <div class="col-lg-7">
                  <div class="card border shadow-sm rounded-3 h-100">
                    <div class="card-header bg-white border-bottom p-3">
                      <h6 class="fw-bold mb-0 text-dark">🏢 Multi-Floor Utilization & Yield Breakdown</h6>
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
                          <tr v-for="fl in analyticsData?.floor_analytics || []" :key="'fl-an-' + fl.floor_id">
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

                <!-- Right: Fleet Distribution & Dwell Time Brackets -->
                <div class="col-lg-5">
                  <div class="card border shadow-sm rounded-3 mb-3">
                    <div class="card-header bg-white border-bottom p-3">
                      <h6 class="fw-bold mb-0 text-dark">🚗 Vehicle Fleet Distribution</h6>
                    </div>
                    <div class="card-body p-3">
                      <div v-for="v in analyticsData?.vehicle_breakdown || []" :key="'v-br-' + v.type" class="mb-2">
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
                      <div v-for="d in analyticsData?.dwell_time_distribution || []" :key="'dw-' + d.bracket" class="mb-2">
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

        <!-- ==================== TAB 6: SUBSCRIPTIONS & CORPORATE PASSES ==================== -->
        <div v-if="activeTab === 'subscriptions'">
          <div class="card shadow-sm border-0 mb-4">
            <div class="card-body p-4">
              <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
                <div>
                  <h4 class="fw-bold mb-1 text-dark">🎟️ Corporate & Monthly Passes</h4>
                  <p class="text-muted small mb-0">Platform-wide overview of recurring corporate and commuter passes.</p>
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
                      <th>Action</th>
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
                      <td>
                        <button 
                          v-if="sub.status === 'active'"
                          class="btn btn-outline-danger btn-sm"
                          @click="cancelSubscription(sub.id)"
                        >
                          Cancel
                        </button>
                        <span v-else class="text-muted small">N/A</span>
                      </td>
                    </tr>
                    <tr v-if="subscriptions.length === 0">
                      <td colspan="11" class="text-center py-4 text-muted">No corporate passes or commuter subscriptions found.</td>
                    </tr>
                  </tbody>
                </table>
              </div>

            </div>
          </div>
        </div>
      </div>

      <!-- ==================== CREATE / EDIT MODAL ==================== -->
      <div v-if="showModal" class="modal-backdrop fade show"></div>
      <div v-if="showModal" class="modal show d-block" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title fw-bold">
                {{ modalMode === 'create' ? 'Create New Parking Lot' : 'Edit Parking Lot & Scale Spots' }}
              </h5>
              <button type="button" class="btn-close" @click="showModal = false"></button>
            </div>
            <form @submit.prevent="handleSaveLot">
              <div class="modal-body">
                <div class="mb-3">
                  <label class="form-label">Prime Location Name</label>
                  <input v-model="lotForm.prime_location_name" type="text" class="form-control" required />
                </div>
                <div class="mb-3">
                  <label class="form-label">Address</label>
                  <input v-model="lotForm.address" type="text" class="form-control" required />
                </div>
                <div class="row g-2 mb-3">
                  <div class="col-6">
                    <label class="form-label">Pin Code</label>
                    <input v-model="lotForm.pin_code" type="text" class="form-control" required />
                  </div>
                  <div class="col-6">
                    <label class="form-label">Hourly Price (₹)</label>
                    <input v-model.number="lotForm.price" type="number" step="0.5" min="0" class="form-control" required />
                  </div>
                </div>
                <div class="mb-3">
                  <label class="form-label">Number of 4-Wheeler Spots</label>
                  <input v-model.number="lotForm.number_of_spots" type="number" min="1" class="form-control" required />
                  <div v-if="modalMode === 'edit'" class="form-text text-muted">
                    Increasing spots creates new available spots. Decreasing spots removes unused available spots.
                  </div>
                </div>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" @click="showModal = false">Cancel</button>
                <button type="submit" class="btn btn-primary" :disabled="lotSaving">
                  {{ lotSaving ? 'Saving...' : 'Save Parking Lot' }}
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
import AdminLogin from '../components/AdminLogin.vue'
import axios from 'axios'

export default {
  name: 'AdminView',
  components: { AdminLogin },
  data() {
    return {
      isLoggedIn: !!localStorage.getItem('adminToken'),
      activeTab: 'dashboard',
      alertMessage: '',
      alertType: 'success',
      stats: {},
      dashboardLots: [],
      lots: [],
      users: [],
      usersLoading: false,
      showModal: false,
      modalMode: 'create',
      selectedLotId: null,
      lotSaving: false,
      selectedFloorByLot: {},
      lotForm: {
        prime_location_name: '',
        address: '',
        pin_code: '',
        price: 30.0,
        number_of_spots: 5
      },
      reminderWebhookUrl: '',
      reminderRunning: false,
      reminderResult: null,
      cacheStats: {},
      analyticsData: null,
      analyticsLoading: false,
      subscriptions: [],
      subscriptionsLoading: false,
      dashboardSearchQuery: '',
      lotsSearchQuery: '',
      eventSource: null,
      realtimePulsingSpots: {}
    }
  },
  computed: {
    filteredDashboardLots() {
      if (!this.dashboardSearchQuery || !this.dashboardSearchQuery.trim()) {
        return this.dashboardLots
      }
      const q = this.dashboardSearchQuery.toLowerCase().trim()
      return this.dashboardLots.filter(lot => {
        const nameMatch = lot.prime_location_name && lot.prime_location_name.toLowerCase().includes(q)
        const addrMatch = lot.address && lot.address.toLowerCase().includes(q)
        const pinMatch = lot.pin_code && String(lot.pin_code).toLowerCase().includes(q)
        const spotMatch = (lot.spots && lot.spots.some(s => s.spot_number && s.spot_number.toLowerCase().includes(q))) ||
                          (lot.floors && lot.floors.some(f => f.spots && f.spots.some(s => s.spot_number && s.spot_number.toLowerCase().includes(q))))
        return nameMatch || addrMatch || pinMatch || spotMatch
      })
    },
    filteredLots() {
      if (!this.lotsSearchQuery || !this.lotsSearchQuery.trim()) {
        return this.lots
      }
      const q = this.lotsSearchQuery.toLowerCase().trim()
      return this.lots.filter(lot => {
        const nameMatch = lot.prime_location_name && lot.prime_location_name.toLowerCase().includes(q)
        const addrMatch = lot.address && lot.address.toLowerCase().includes(q)
        const pinMatch = lot.pin_code && String(lot.pin_code).toLowerCase().includes(q)
        return nameMatch || addrMatch || pinMatch
      })
    }
  },
  watch: {
    activeTab(newTab) {
      if (!this.isLoggedIn) return
      if (newTab === 'dashboard') this.fetchDashboard()
      if (newTab === 'lots') this.fetchLots()
      if (newTab === 'users') this.fetchUsers()
      if (newTab === 'jobs') this.fetchCacheStats()
      if (newTab === 'analytics') this.fetchAnalytics()
      if (newTab === 'subscriptions') this.fetchSubscriptions()
    }
  },
  mounted() {
    if (this.isLoggedIn) {
      this.fetchDashboard()
      this.initLiveStream()
    }
  },
  beforeUnmount() {
    this.closeLiveStream()
  },
  methods: {
    getAuthHeaders() {
      const token = localStorage.getItem('adminToken')
      return { headers: { Authorization: `Bearer ${token}` } }
    },
    handleLoginSuccess() {
      this.isLoggedIn = true
      this.fetchDashboard()
    },
    logout() {
      this.closeLiveStream()
      localStorage.removeItem('adminToken')
      localStorage.removeItem('adminUser')
      this.isLoggedIn = false
      this.activeTab = 'dashboard'
      this.dashboardSearchQuery = ''
      this.lotsSearchQuery = ''
    },
    showAlert(msg, type = 'success') {
      this.alertMessage = msg
      this.alertType = type
      setTimeout(() => { this.alertMessage = '' }, 4000)
    },
    async fetchDashboard(searchQuery = null) {
      try {
        const params = {}
        const q = searchQuery !== null ? searchQuery : (this.dashboardSearchQuery ? this.dashboardSearchQuery.trim() : '')
        if (q) params.search = q
        const res = await axios.get('http://localhost:5000/api/admin/dashboard', {
          headers: this.getAuthHeaders().headers,
          params
        })
        this.stats = res.data.statistics
        this.dashboardLots = res.data.lots
      } catch (err) {
        if (err.response?.status === 401 || err.response?.status === 403) {
          this.logout()
        }
      }
    },
    async fetchLots(searchQuery = null) {
      try {
        const params = {}
        const q = searchQuery !== null ? searchQuery : (this.lotsSearchQuery ? this.lotsSearchQuery.trim() : '')
        if (q) params.search = q
        const res = await axios.get('http://localhost:5000/api/parking-lots', { params })
        this.lots = res.data.parking_lots
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'Failed to fetch lots', 'danger')
      }
    },
    async fetchUsers() {
      this.usersLoading = true
      try {
        const res = await axios.get('http://localhost:5000/api/users', this.getAuthHeaders())
        this.users = res.data.users || []
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'Failed to fetch users', 'danger')
      } finally {
        this.usersLoading = false
      }
    },
    openCreateLotModal() {
      this.modalMode = 'create'
      this.selectedLotId = null
      this.lotForm = {
        prime_location_name: '',
        address: '',
        pin_code: '',
        price: 30.0,
        number_of_spots: 5
      }
      this.showModal = true
    },
    openEditLotModal(lot) {
      this.modalMode = 'edit'
      this.selectedLotId = lot.id
      this.lotForm = {
        prime_location_name: lot.prime_location_name,
        address: lot.address,
        pin_code: lot.pin_code,
        price: lot.price,
        number_of_spots: lot.number_of_spots
      }
      this.showModal = true
    },
    async handleSaveLot() {
      this.lotSaving = true
      try {
        if (this.modalMode === 'create') {
          await axios.post('http://localhost:5000/api/parking-lots', this.lotForm, this.getAuthHeaders())
          this.showAlert('Parking lot created with all 4-wheeler spots!')
        } else {
          await axios.put(`http://localhost:5000/api/parking-lots/${this.selectedLotId}`, this.lotForm, this.getAuthHeaders())
          this.showAlert('Parking lot and spots updated successfully!')
        }
        this.showModal = false
        this.fetchLots()
        this.fetchDashboard()
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'Failed to save parking lot', 'danger')
      } finally {
        this.lotSaving = false
      }
    },
    async handleDeleteLot(lot) {
      if (!confirm(`Are you sure you want to delete "${lot.prime_location_name}"?`)) return
      try {
        await axios.delete(`http://localhost:5000/api/parking-lots/${lot.id}`, this.getAuthHeaders())
        this.showAlert('Parking lot deleted successfully')
        this.fetchLots()
        this.fetchDashboard()
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'Failed to delete parking lot', 'danger')
      }
    },
    async triggerDailyReminders() {
      this.reminderRunning = true
      this.reminderResult = null
      try {
        const payload = this.reminderWebhookUrl ? { webhook_url: this.reminderWebhookUrl } : {}
        const res = await axios.post('http://localhost:5000/api/jobs/daily-reminders', payload, this.getAuthHeaders())
        this.reminderResult = res.data
        this.showAlert('Daily reminder job completed!')
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'Failed to trigger reminders', 'danger')
      } finally {
        this.reminderRunning = false
      }
    },
    async fetchCacheStats() {
      try {
        const res = await axios.get('http://localhost:5000/api/cache/stats', this.getAuthHeaders())
        this.cacheStats = res.data
      } catch (err) {
        console.error(err)
      }
    },
    getCellClasses(cell) {
      const type = cell.type
      let cls = 'cell-empty'
      if (type === 'parking') {
        cls = cell.spot?.status === 'O' ? 'cell-parking-occupied' : 'cell-parking-available'
      } else if (type === 'handicap') {
        cls = cell.spot?.status === 'O' ? 'cell-handicap-occupied' : 'cell-handicap-available'
      } else if (type === 'road') {
        cls = 'cell-road'
      } else if (type === 'ramp_up') {
        cls = 'cell-ramp-up'
      } else if (type === 'ramp_down') {
        cls = 'cell-ramp-down'
      } else if (type === 'elevator') {
        cls = 'cell-elevator'
      } else if (type === 'stairs') {
        cls = 'cell-stairs'
      }
      
      if (cell.spot?.id && this.realtimePulsingSpots[cell.spot.id]) {
        cls += ' pulse-live'
      }
      return cls
    },
    getCellTooltip(cell, rIdx, cIdx) {
      if (cell.type === 'parking') {
        const spotName = cell.spot?.spot_number || `P-${rIdx + 1},${cIdx + 1}`
        const status = cell.spot?.status === 'O' ? 'Occupied (In Use)' : 'Available (Free)'
        return `Regular Parking: ${spotName} - ${status}`
      }
      if (cell.type === 'handicap') {
        const spotName = cell.spot?.spot_number || `H-${rIdx + 1},${cIdx + 1}`
        const status = cell.spot?.status === 'O' ? 'Occupied (In Use)' : 'Available (Free)'
        return `Handicap Parking: ${spotName} - ${status}`
      }
      if (cell.type === 'road') return `Driveway / Road (Row ${rIdx + 1}, Col ${cIdx + 1})`
      if (cell.type === 'ramp_up') return `Ramp Up to upper floor (Row ${rIdx + 1}, Col ${cIdx + 1})`
      if (cell.type === 'ramp_down') return `Ramp Down to lower floor (Row ${rIdx + 1}, Col ${cIdx + 1})`
      if (cell.type === 'elevator') return `Elevator / Lift Core (Row ${rIdx + 1}, Col ${cIdx + 1})`
      if (cell.type === 'stairs') return `Stairs / Walkway Exit (Row ${rIdx + 1}, Col ${cIdx + 1})`
      return `Empty Slot (Row ${rIdx + 1}, Col ${cIdx + 1})`
    },
    getAdminActiveFloor(lot) {
      if (!lot.floors || lot.floors.length === 0) {
        return lot
      }
      const idx = this.selectedFloorByLot[lot.id] || 0
      return lot.floors[idx] || lot.floors[0] || lot
    },
    setAdminActiveFloor(lotId, floorIdx) {
      this.selectedFloorByLot = {
        ...this.selectedFloorByLot,
        [lotId]: floorIdx
      }
    },
    async fetchAnalytics() {
      this.analyticsLoading = true
      try {
        const res = await axios.get('http://localhost:5000/api/admin/analytics', this.getAuthHeaders())
        this.analyticsData = res.data
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'Failed to load analytics', 'danger')
      } finally {
        this.analyticsLoading = false
      }
    },
    async fetchSubscriptions() {
      this.subscriptionsLoading = true
      try {
        const res = await axios.get('http://localhost:5000/api/admin/subscriptions', this.getAuthHeaders())
        this.subscriptions = res.data.subscriptions || []
      } catch (err) {
        this.showAlert(err.response?.data?.error || 'Failed to load subscriptions', 'danger')
      } finally {
        this.subscriptionsLoading = false
      }
    },
    async cancelSubscription(subId) {
      if (!confirm('Are you sure you want to cancel this pass?')) return
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
      const spotId = data.spot_id
      const newStatus = data.status
      if (!spotId) return

      this.realtimePulsingSpots = { ...this.realtimePulsingSpots, [spotId]: true }
      setTimeout(() => {
        const copy = { ...this.realtimePulsingSpots }
        delete copy[spotId]
        this.realtimePulsingSpots = copy
      }, 1800)

      for (const lot of this.dashboardLots) {
        if (lot.id === data.lot_id) {
          if (lot.spots) {
            for (const sp of lot.spots) {
              if (sp.id === spotId) {
                sp.status = newStatus
              }
            }
          }
          if (lot.floors) {
            for (const fl of lot.floors) {
              if (fl.spots) {
                for (const sp of fl.spots) {
                  if (sp.id === spotId) {
                    sp.status = newStatus
                  }
                }
              }
            }
          }
        }
      }

      // If viewing analytics, quietly update KPIs
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

/* Admin Facility Grid */
.admin-grid-wrapper {
  background: #ffffff;
}

.admin-grid {
  display: grid;
  gap: 8px;
}

.admin-cell {
  aspect-ratio: 1;
  min-height: 70px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  text-align: center;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  border: 2px solid transparent;
}

.admin-cell:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.12) !important;
}

.cell-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  line-height: 1.1;
  width: 100%;
}

.cell-icon {
  font-size: 1.25rem;
}

.cell-title {
  font-size: 0.72rem;
  font-weight: 700;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.cell-status-badge {
  font-size: 0.6rem;
  padding: 2px 5px;
  border-radius: 10px;
  margin-top: 3px;
}

.cell-sub {
  font-size: 0.62rem;
  font-weight: 600;
}

.cell-sub-dash {
  font-size: 0.6rem;
  letter-spacing: -1px;
  opacity: 0.5;
}

/* Parking Available */
.cell-parking-available {
  background-color: #d1e7dd;
  border-color: #198754;
  color: #0f5132;
}

/* Parking Occupied */
.cell-parking-occupied {
  background-color: #f8d7da;
  border-color: #dc3545;
  color: #842029;
}

/* Handicap Available */
.cell-handicap-available {
  background-color: #cff4fc;
  border-color: #0dcaf0;
  color: #055160;
}

/* Handicap Occupied */
.cell-handicap-occupied {
  background-color: #e2d9f3;
  border-color: #6f42c1;
  color: #432874;
}

/* Road / Driveway */
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

/* Stairs / Exit */
.cell-stairs {
  background-color: #fff3cd;
  border-color: #ffc107;
  color: #664d03;
}

/* Ramp Up */
.cell-ramp-up {
  background-color: #f3e8ff;
  border-color: #6f42c1;
  color: #432874;
}

/* Ramp Down */
.cell-ramp-down {
  background-color: #fae8ff;
  border-color: #9333ea;
  color: #581c87;
}

/* Elevator */
.cell-elevator {
  background-color: #e0f2fe;
  border-color: #0284c7;
  color: #0369a1;
}

/* Empty Slot */
.cell-empty {
  background-color: #f8f9fa;
  border-color: #dee2e6;
  border-style: dashed;
  color: #adb5bd;
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