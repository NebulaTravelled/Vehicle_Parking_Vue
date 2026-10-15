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

      <!-- Main Container -->
      <div class="container-fluid p-4 max-w-1400">
        <!-- Global Feedback Alert -->
        <div v-if="alertMessage" class="alert alert-dismissible fade show mb-4 shadow-sm" :class="'alert-' + alertType">
          <i class="bi me-2" :class="alertType === 'success' ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill'"></i>
          {{ alertMessage }}
          <button type="button" class="btn-close" @click="alertMessage = ''"></button>
        </div>

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

                <!-- Grid Dimension Pill -->
                <div class="d-flex justify-content-between align-items-center p-2 px-3 bg-secondary-subtle rounded-3 mb-3 small text-secondary">
                  <span><i class="bi bi-grid-3x3 me-1"></i> Grid Layout Size:</span>
                  <strong>{{ lot.grid_rows }} rows × {{ lot.grid_cols }} columns ({{ lot.number_of_spots }} Total Slots)</strong>
                </div>

                <!-- Mini Grid Preview Thumbnail -->
                <div v-if="lot.grid_layout" class="mini-grid-container mb-3 p-2 bg-light rounded-3 border">
                  <div class="small text-muted mb-1 fw-semibold d-flex justify-content-between">
                    <span>Layout Preview:</span>
                    <span class="text-success">{{ lot.number_of_spots }} Slots</span>
                  </div>
                  <div class="mini-grid" :style="{ gridTemplateColumns: `repeat(${lot.grid_cols}, 1fr)` }">
                    <template v-for="(row, rIdx) in lot.grid_layout" :key="'r' + rIdx">
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
              <!-- Top Form Row: 1) Edit name of slot, 2) Edit cost of parking, 3) Edit grid size -->
              <div class="card border-0 shadow-sm rounded-3 p-3 mb-4 bg-white">
                <div class="row g-3 align-items-end">
                  
                  <!-- 1) Edit name of slot / space -->
                  <div class="col-md-4">
                    <label class="form-label fw-bold small text-secondary">
                      1) Parking Space Name *
                    </label>
                    <div class="input-group">
                      <span class="input-group-text bg-light text-muted"><i class="bi bi-tag-fill"></i></span>
                      <input 
                        v-model="editSlotForm.prime_location_name" 
                        type="text" 
                        class="form-control" 
                        placeholder="e.g. Terminal A Plaza"
                        required 
                      />
                    </div>
                  </div>

                  <!-- 2) Edit cost of parking -->
                  <div class="col-md-3">
                    <label class="form-label fw-bold small text-secondary">
                      2) Cost of Parking (₹ / hr) *
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

                  <!-- 3) Edit grid size - row and column info -->
                  <div class="col-md-5">
                    <label class="form-label fw-bold small text-secondary">
                      3) Grid Size (Rows & Columns)
                    </label>
                    <div class="d-flex gap-2 align-items-center">
                      <div class="input-group input-group-sm">
                        <span class="input-group-text bg-light">Rows</span>
                        <input 
                          v-model.number="editSlotForm.grid_rows" 
                          type="number" 
                          min="2" 
                          max="15" 
                          class="form-control"
                        />
                      </div>
                      <div class="input-group input-group-sm">
                        <span class="input-group-text bg-light">Cols</span>
                        <input 
                          v-model.number="editSlotForm.grid_cols" 
                          type="number" 
                          min="2" 
                          max="15" 
                          class="form-control"
                        />
                      </div>
                      <button 
                        type="button" 
                        class="btn btn-outline-primary btn-sm text-nowrap fw-semibold"
                        @click="resizeGrid"
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
                      <span>4) Edit Grid Space (Clickable Grid)</span>
                    </h6>
                    <small class="text-muted">Select an element below, then click squares on the grid to mark them.</small>
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
                    :class="activeTool === 'road' ? 'btn-dark text-white shadow-sm ring-active' : 'btn-outline-dark bg-white'"
                    @click="activeTool = 'road'"
                  >
                    🛣️ Road / Driveway
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
                    Regular Parking: <strong>{{ computedRegularSlots }}</strong> | 
                    Handicap: <strong>{{ computedHandicapSlots }}</strong> | 
                    Roads: <strong>{{ computedRoads }}</strong> | 
                    Stairs: <strong>{{ computedStairs }}</strong>
                  </div>
                  <div class="badge bg-primary fs-6 fw-bold px-3 py-1.5 rounded-pill shadow-sm">
                    Total Bookable Slots: {{ computedTotalSlots }}
                  </div>
                </div>

                <!-- The Interactive Clickable Grid Canvas -->
                <div class="grid-canvas-wrapper p-3 bg-light rounded-3 border text-center overflow-auto">
                  <div 
                    class="clickable-grid mx-auto" 
                    :style="{ 
                      gridTemplateColumns: `repeat(${editSlotForm.grid_cols}, minmax(65px, 1fr))`,
                      maxWidth: `${editSlotForm.grid_cols * 85}px` 
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
                          <span v-else class="cell-icon text-muted">·</span>
                          
                          <span class="cell-label">{{ getCellLabel(cell, rIdx, cIdx) }}</span>
                        </div>
                      </div>
                    </template>
                  </div>
                </div>

                <div class="text-muted small mt-2">
                  <i class="bi bi-lightbulb me-1"></i>
                  <strong>Auto-calculation rule:</strong> The number of parking space and handicap space is added and saved as no. of slots in database upon saving.
                </div>

              </div>
            </div>

            <!-- Modal Footer: Save and Cancel -->
            <div class="modal-footer bg-white border-top p-3 px-4 d-flex justify-content-between align-items-center">
              <span class="text-muted small">
                Saving will update slot names, rates, dimensions, and register <strong>{{ computedTotalSlots }} slots</strong> into database.
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
                  <span>{{ savingSlots ? 'Saving Changes...' : '💾 Save & Update All Data' }}</span>
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
      activeTool: 'parking', // 'parking', 'handicap', 'road', 'stairs', 'empty'
      editSlotForm: {
        prime_location_name: '',
        price: 0,
        grid_rows: 5,
        grid_cols: 6
      },
      currentMatrix: [] // 2D array of { type: string }
    }
  },
  computed: {
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
    }
  },
  mounted() {
    if (this.isLoggedIn) {
      this.fetchDashboard()
      this.fetchProfile()
    }
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

    // ==================== EDIT SLOTS METHODS ====================
    openEditSlotsModal(lot) {
      this.editingLot = lot
      const rows = lot.grid_rows || 5
      const cols = lot.grid_cols || 6
      
      this.editSlotForm = {
        prime_location_name: lot.prime_location_name,
        price: lot.price,
        grid_rows: rows,
        grid_cols: cols
      }

      // Populate current matrix
      if (lot.grid_layout && Array.isArray(lot.grid_layout) && lot.grid_layout.length === rows) {
        // Deep copy existing grid
        this.currentMatrix = lot.grid_layout.map(r => r.map(c => ({
          type: typeof c === 'object' && c ? (c.type || 'parking') : String(c)
        })))
      } else {
        // Generate initial matrix
        this.currentMatrix = []
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
          this.currentMatrix.push(rowArr)
        }
      }

      this.activeTool = 'parking'
      this.showEditSlotsModal = true
    },
    closeEditSlotsModal() {
      this.showEditSlotsModal = false
      this.editingLot = null
    },
    resizeGrid() {
      const newRows = Math.min(Math.max(parseInt(this.editSlotForm.grid_rows) || 2, 2), 15)
      const newCols = Math.min(Math.max(parseInt(this.editSlotForm.grid_cols) || 2, 2), 15)
      this.editSlotForm.grid_rows = newRows
      this.editSlotForm.grid_cols = newCols

      const newMatrix = []
      for (let r = 0; r < newRows; r++) {
        const rowArr = []
        for (let c = 0; c < newCols; c++) {
          if (this.currentMatrix[r] && this.currentMatrix[r][c]) {
            rowArr.push({ type: this.currentMatrix[r][c].type || 'parking' })
          } else {
            rowArr.push({ type: r === 1 ? 'road' : 'parking' })
          }
        }
        newMatrix.push(rowArr)
      }
      this.currentMatrix = newMatrix
    },
    stampCell(r, c) {
      if (this.currentMatrix[r] && this.currentMatrix[r][c]) {
        this.currentMatrix[r][c].type = this.activeTool
      }
    },
    fillGrid(type) {
      for (let r = 0; r < this.editSlotForm.grid_rows; r++) {
        for (let c = 0; c < this.editSlotForm.grid_cols; c++) {
          if (this.currentMatrix[r] && this.currentMatrix[r][c]) {
            this.currentMatrix[r][c].type = type
          }
        }
      }
    },
    addRoadAisle() {
      const mid = Math.floor(this.editSlotForm.grid_rows / 2)
      for (let c = 0; c < this.editSlotForm.grid_cols; c++) {
        if (this.currentMatrix[mid] && this.currentMatrix[mid][c]) {
          this.currentMatrix[mid][c].type = 'road'
        }
      }
    },
    getCellLabel(cell, r, c) {
      if (cell.type === 'parking') return `P-${r + 1},${c + 1}`
      if (cell.type === 'handicap') return `H-${r + 1},${c + 1}`
      if (cell.type === 'road') return 'Road'
      if (cell.type === 'stairs') return 'Exit'
      return 'Empty'
    },
    async saveSlotsData() {
      if (this.computedTotalSlots <= 0) {
        alert('Please mark at least 1 Parking space or Handicap space in the grid!')
        return
      }

      this.savingSlots = true
      try {
        const payload = {
          prime_location_name: this.editSlotForm.prime_location_name.trim(),
          price: this.editSlotForm.price,
          grid_rows: this.editSlotForm.grid_rows,
          grid_cols: this.editSlotForm.grid_cols,
          grid_layout: this.currentMatrix
        }

        const res = await axios.put(
          `http://localhost:5000/api/company/lots/${this.editingLot.id}`,
          payload,
          this.getAuthHeaders()
        )

        this.showAlert(
          `Slot configuration updated! Total ${res.data.number_of_spots} slots saved (${res.data.regular_spots} Regular + ${res.data.handicap_spots} Handicap).`
        )
        this.closeEditSlotsModal()
        this.fetchDashboard()
      } catch (err) {
        alert(err.response?.data?.error || 'Failed to save slots and layout')
      } finally {
        this.savingSlots = false
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
</style>

