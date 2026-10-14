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

          <!-- Spot Matrix Overview per Parking Lot -->
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h4 class="fw-bold mb-0">Live Parking Spots Grid (4-Wheeler)</h4>
            <div class="d-flex gap-2">
              <span class="badge bg-success py-2 px-3">🟢 A = Available</span>
              <span class="badge bg-danger py-2 px-3">🔴 O = Occupied</span>
              <button class="btn btn-outline-primary btn-sm ms-2" @click="fetchDashboard">🔄 Refresh Grid</button>
            </div>
          </div>

          <div v-if="dashboardLots.length === 0" class="card shadow-sm text-center py-5">
            <div class="card-body">
              <h5>No parking lots created yet.</h5>
              <p class="text-muted">Create a parking lot to start allocating 4-wheeler spots.</p>
              <button class="btn btn-primary" @click="activeTab = 'lots'">Create Parking Lot</button>
            </div>
          </div>

          <div v-else class="row g-4">
            <div v-for="lot in dashboardLots" :key="lot.id" class="col-lg-6">
              <div class="card shadow-sm h-100">
                <div class="card-header bg-white d-flex justify-content-between align-items-center py-3">
                  <div>
                    <h5 class="fw-bold mb-1 text-primary">{{ lot.prime_location_name }}</h5>
                    <span class="text-muted small">{{ lot.address }} (PIN: {{ lot.pin_code }})</span>
                  </div>
                  <div class="text-end">
                    <span class="badge bg-light text-dark border me-1">₹{{ lot.price }}/hr</span>
                    <span class="badge bg-success me-1">{{ lot.available_count }} Available</span>
                    <span class="badge bg-danger">{{ lot.occupied_count }} Occupied</span>
                  </div>
                </div>
                <div class="card-body">
                  <div class="d-flex flex-wrap gap-2">
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
                    <tr v-for="lot in lots" :key="lot.id">
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
      cacheStats: {}
    }
  },
  watch: {
    activeTab(newTab) {
      if (!this.isLoggedIn) return
      if (newTab === 'dashboard') this.fetchDashboard()
      if (newTab === 'lots') this.fetchLots()
      if (newTab === 'users') this.fetchUsers()
      if (newTab === 'jobs') this.fetchCacheStats()
    }
  },
  mounted() {
    if (this.isLoggedIn) {
      this.fetchDashboard()
    }
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
      localStorage.removeItem('adminToken')
      localStorage.removeItem('adminUser')
      this.isLoggedIn = false
      this.activeTab = 'dashboard'
    },
    showAlert(msg, type = 'success') {
      this.alertMessage = msg
      this.alertType = type
      setTimeout(() => { this.alertMessage = '' }, 4000)
    },
    async fetchDashboard() {
      try {
        const res = await axios.get('http://localhost:5000/api/admin/dashboard', this.getAuthHeaders())
        this.stats = res.data.statistics
        this.dashboardLots = res.data.lots
      } catch (err) {
        if (err.response?.status === 401 || err.response?.status === 403) {
          this.logout()
        }
      }
    },
    async fetchLots() {
      try {
        const res = await axios.get('http://localhost:5000/api/parking-lots')
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