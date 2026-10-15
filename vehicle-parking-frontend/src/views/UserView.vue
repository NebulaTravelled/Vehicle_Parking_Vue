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
          
          <!-- Active Reservation Banner -->
          <div v-if="activeReservation" class="card shadow-sm border-0 border-start border-warning border-5 mb-4 bg-white">
            <div class="card-body p-4">
              <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
                <div>
                  <div class="d-flex align-items-center gap-2 mb-2">
                    <span class="badge bg-warning text-dark">🟢 Active Parking Spot</span>
                    <span v-if="activeReservation.spot_type === 'handicap'" class="badge bg-info text-dark">♿ Handicap Spot</span>
                    <span v-else class="badge bg-secondary">🚗 Regular Spot</span>
                  </div>
                  <h4 class="fw-bold mb-1 text-primary">{{ activeReservation.lot_name }}</h4>
                  <p class="text-muted mb-0 small">
                    Allotted Spot: <strong class="text-dark">{{ activeReservation.spot_number }}</strong> | 
                    Vehicle: <strong>{{ activeReservation.vehicle_number }}</strong> | 
                    Entry Time: {{ formatTime(activeReservation.parking_timestamp) }}
                  </p>
                </div>
                <div>
                  <button class="btn btn-danger btn-lg px-4 shadow-sm" @click="handleVacateSpot(activeReservation.id)" :disabled="vacating">
                    {{ vacating ? 'Releasing Spot...' : '🚪 Vacate / Release Spot' }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Section: Available Parking Lots for 4-Wheeler Booking -->
          <div class="d-flex justify-content-between align-items-center mb-3">
            <div>
              <h4 class="fw-bold mb-1">Available Parking Lots</h4>
              <p class="text-muted small mb-0">Choose a parking lot. You can reserve Regular or Handicap accessible parking.</p>
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
                  <p class="text-muted small mb-3">PIN: {{ lot.pin_code }}</p>
                  
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
                      :disabled="lot.available_spots === 0 || activeReservation !== null"
                      @click="openBookingModal(lot)"
                    >
                      <span v-if="activeReservation !== null">Active spot already in use</span>
                      <span v-else-if="lot.available_spots === 0">Fully Booked (0 Available)</span>
                      <span v-else>Book Spot (Regular / Handicap)</span>
                    </button>
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
                  <h4 class="fw-bold mb-1">My Parking Reservations</h4>
                  <p class="text-muted small mb-0">Full record of your parking sessions, timestamps, and fees.</p>
                </div>
                <div class="d-flex gap-2">
                  <button class="btn btn-outline-primary btn-sm" @click="fetchReservations">🔄 Refresh</button>
                  <button class="btn btn-primary btn-sm" @click="handleExportCsv" :disabled="exporting">
                    {{ exporting ? 'Generating CSV...' : 'Export as CSV' }}
                  </button>
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

              <!-- Reservations Table -->
              <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                  <thead class="table-light">
                    <tr>
                      <th>#</th>
                      <th>Location / Lot</th>
                      <th>Spot Number</th>
                      <th>Type</th>
                      <th>Vehicle Number</th>
                      <th>Entry Time</th>
                      <th>Exit Time</th>
                      <th>Cost</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="res in reservations" :key="res.id">
                      <td>{{ res.id }}</td>
                      <td class="fw-semibold text-primary">{{ res.lot_name }}</td>
                      <td><span class="badge bg-secondary">{{ res.spot_number }}</span></td>
                      <td>
                        <span v-if="res.spot_type === 'handicap'" class="badge bg-info text-dark">♿ Handicap</span>
                        <span v-else class="badge bg-light text-dark border">🚗 Regular</span>
                      </td>
                      <td class="fw-bold">{{ res.vehicle_number }}</td>
                      <td>{{ formatTime(res.parking_timestamp) }}</td>
                      <td>{{ res.leaving_timestamp ? formatTime(res.leaving_timestamp) : 'In Progress' }}</td>
                      <td class="fw-bold text-success">₹{{ res.parking_cost ? res.parking_cost.toFixed(2) : '0.00' }}</td>
                      <td>
                        <span class="badge" :class="res.status === 'active' ? 'bg-warning text-dark' : 'bg-success'">
                          {{ res.status }}
                        </span>
                      </td>
                      <td>
                        <button
                          v-if="res.status === 'active'"
                          class="btn btn-danger btn-sm"
                          @click="handleVacateSpot(res.id)"
                        >
                          Vacate
                        </button>
                        <span v-else class="text-muted small">Completed</span>
                      </td>
                    </tr>
                    <tr v-if="reservations.length === 0">
                      <td colspan="10" class="text-center py-4 text-muted">You have no parking reservations yet.</td>
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
                  <div class="fw-bold text-primary fs-5">{{ selectedLot?.prime_location_name }}</div>
                  <div class="small text-muted">{{ selectedLot?.address }}</div>
                  <div class="mt-2 text-success fw-semibold">Rate: ₹{{ selectedLot?.price }}/hour</div>
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

                <div class="mb-3">
                  <label class="form-label fw-bold">Vehicle Registration Number *</label>
                  <input
                    v-model="bookingForm.vehicle_number"
                    type="text"
                    class="form-control"
                    placeholder="e.g. MH-02-CB-1234"
                    required
                  />
                  <div class="form-text">4-wheeler vehicle license plate number.</div>
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
      activeReservation: null,
      showBookingModal: false,
      selectedLot: null,
      bookingForm: {
        vehicle_number: '',
        remarks: ''
      },
      bookingSubmitting: false,
      vacating: false,
      exporting: false,
      exportJob: null,
      monthlyReport: {}
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
    }
  },
  methods: {
    getAuthHeaders() {
      const token = localStorage.getItem('userToken')
      return { headers: { Authorization: `Bearer ${token}` } }
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
      return new Date(isoStr).toLocaleString()
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
        // Look for any active reservation
        this.activeReservation = this.reservations.find(r => r.status === 'active') || null
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
      this.bookingForm = { vehicle_number: '', remarks: '', spot_type: defaultType }
      this.showBookingModal = true
    },
    async submitBooking() {
      if (!this.bookingForm.vehicle_number.trim()) return
      this.bookingSubmitting = true
      try {
        const payload = {
          lot_id: this.selectedLot.id,
          vehicle_number: this.bookingForm.vehicle_number.trim(),
          remarks: this.bookingForm.remarks.trim(),
          spot_type: this.bookingForm.spot_type || 'regular'
        }
        const res = await axios.post('http://localhost:5000/api/reservations', payload, this.getAuthHeaders())
        const typeLabel = res.data.spot_type === 'handicap' ? 'Handicap' : 'Regular'
        this.showAlert(`${typeLabel} spot "${res.data.spot_number}" automatically allotted in ${res.data.lot_name}!`)
        this.showBookingModal = false
        this.fetchLots()
        this.fetchReservations()
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