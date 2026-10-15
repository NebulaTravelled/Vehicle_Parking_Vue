<template>
  <div class="company-login-wrapper d-flex justify-content-center align-items-center min-vh-100 px-3 py-5">
    <div class="login-card card shadow-lg rounded-4 border-0 p-4 p-md-5 bg-white">
      <div class="card-body p-0">
        
        <!-- Header Badge -->
        <div class="text-center mb-4">
          <div class="icon-circle bg-primary-subtle text-primary mx-auto mb-3 shadow-sm d-flex align-items-center justify-content-center rounded-circle">
            <i class="bi bi-building fs-3"></i>
          </div>
          <h2 class="card-title fw-bold text-dark mb-1">Company Portal</h2>
          <p class="text-muted small">Manage parking facilities, slot grids, and rates</p>
          
          <!-- Mode Tabs: Sign In / Register Company -->
          <div class="btn-group w-100 mt-2 p-1 bg-light rounded-pill border" role="group">
            <button 
              type="button" 
              class="btn btn-sm rounded-pill fw-semibold" 
              :class="isRegister ? 'btn-light text-muted' : 'btn-primary text-white shadow-sm'"
              @click="isRegister = false; error = '';"
            >
              Sign In
            </button>
            <button 
              type="button" 
              class="btn btn-sm rounded-pill fw-semibold" 
              :class="isRegister ? 'btn-primary text-white shadow-sm' : 'btn-light text-muted'"
              @click="isRegister = true; error = '';"
            >
              Register Company
            </button>
          </div>
        </div>

        <!-- Success Alert -->
        <div v-if="successText" class="alert alert-success alert-dismissible fade show mb-3 py-2 small" role="alert">
          <i class="bi bi-check-circle-fill me-2"></i>{{ successText }}
        </div>

        <!-- Demo Account Banner (Only in Sign In mode) -->
        <div v-if="!isRegister" class="card bg-primary-subtle border-0 rounded-3 p-3 mb-3 text-start small">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="fw-bold text-primary"><i class="bi bi-info-circle me-1"></i> Demo Company Account:</span>
            <button class="btn btn-xs btn-outline-primary py-0 px-2 fw-semibold" @click="fillDemo">Quick Fill</button>
          </div>
          <div class="text-muted font-monospace small">Username: <strong>company</strong> | Password: <strong>company123</strong></div>
        </div>

        <!-- ==================== SIGN IN FORM ==================== -->
        <form v-if="!isRegister" @submit.prevent="handleLogin">
          <div class="mb-3">
            <label class="form-label fw-semibold small text-secondary">Username</label>
            <div class="input-group">
              <span class="input-group-text bg-light border-end-0 text-muted"><i class="bi bi-person-badge"></i></span>
              <input 
                v-model="loginForm.username" 
                type="text" 
                class="form-control bg-light border-start-0 ps-0 shadow-none" 
                placeholder="Enter company username"
                required 
              />
            </div>
          </div>

          <div class="mb-4">
            <label class="form-label fw-semibold small text-secondary">Password</label>
            <div class="input-group">
              <span class="input-group-text bg-light border-end-0 text-muted"><i class="bi bi-key-fill"></i></span>
              <input 
                v-model="loginForm.password" 
                type="password" 
                class="form-control bg-light border-start-0 ps-0 shadow-none" 
                placeholder="Enter password"
                required 
              />
            </div>
          </div>

          <button type="submit" class="btn btn-primary w-100 py-2.5 fw-semibold shadow-sm d-flex align-items-center justify-content-center gap-2" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            <span>{{ loading ? 'Signing in...' : 'Sign In to Portal' }}</span>
          </button>
        </form>

        <!-- ==================== REGISTER COMPANY FORM ==================== -->
        <form v-else @submit.prevent="handleRegister">
          <div class="mb-2">
            <label class="form-label fw-semibold small text-secondary">Company Name *</label>
            <input 
              v-model="regForm.company_name" 
              type="text" 
              class="form-control form-control-sm bg-light" 
              placeholder="e.g. Metro Park Corp."
              required 
            />
          </div>

          <div class="row g-2 mb-2">
            <div class="col-6">
              <label class="form-label fw-semibold small text-secondary">Contact Name</label>
              <input 
                v-model="regForm.name" 
                type="text" 
                class="form-control form-control-sm bg-light" 
                placeholder="Manager name" 
              />
            </div>
            <div class="col-6">
              <label class="form-label fw-semibold small text-secondary">Mobile Number *</label>
              <input 
                v-model="regForm.mobile_number" 
                type="text" 
                class="form-control form-control-sm bg-light" 
                placeholder="+91 98765 43210"
                required 
              />
            </div>
          </div>

          <div class="mb-2">
            <label class="form-label fw-semibold small text-secondary">Company Description</label>
            <textarea 
              v-model="regForm.description" 
              rows="2" 
              class="form-control form-control-sm bg-light" 
              placeholder="About your parking spaces, operations, services..."
            ></textarea>
          </div>

          <div class="mb-2">
            <label class="form-label fw-semibold small text-secondary">Official Email *</label>
            <input 
              v-model="regForm.email" 
              type="email" 
              class="form-control form-control-sm bg-light" 
              placeholder="contact@company.com"
              required 
            />
          </div>

          <div class="row g-2 mb-2">
            <div class="col-6">
              <label class="form-label fw-semibold small text-secondary">Username (Single Word) *</label>
              <input 
                v-model="regForm.username" 
                type="text" 
                class="form-control form-control-sm bg-light" 
                placeholder="username"
                required 
              />
            </div>
            <div class="col-6">
              <label class="form-label fw-semibold small text-secondary">Password *</label>
              <input 
                v-model="regForm.password" 
                type="password" 
                class="form-control form-control-sm bg-light" 
                placeholder="Password"
                required 
              />
            </div>
          </div>

          <button type="submit" class="btn btn-primary w-100 py-2 fw-semibold shadow-sm mt-3" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            <span>{{ loading ? 'Registering Company...' : 'Create Company Account' }}</span>
          </button>
        </form>
        
        <!-- Error Alert -->
        <div v-if="error" class="alert alert-danger alert-dismissible fade show mt-3 mb-0 py-2 small" role="alert">
          <i class="bi bi-exclamation-triangle-fill me-2"></i>{{ error }}
        </div>

        <!-- Footer Links -->
        <div class="text-center mt-4 pt-3 border-top">
          <router-link to="/" class="text-decoration-none text-muted fw-semibold small back-link">
            <i class="bi bi-arrow-left me-1"></i> Back to Home
          </router-link>
        </div>

      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'CompanyLogin',
  emits: ['login-success'],
  data() {
    return {
      isRegister: false,
      loginForm: { username: '', password: '' },
      regForm: {
        company_name: '',
        name: '',
        mobile_number: '',
        description: '',
        email: '',
        username: '',
        password: '',
        address: ''
      },
      loading: false,
      error: '',
      successText: ''
    }
  },
  methods: {
    fillDemo() {
      this.loginForm.username = 'company'
      this.loginForm.password = 'company123'
    },
    async handleLogin() {
      this.loading = true
      this.error = ''
      this.successText = ''
      try {
        const res = await axios.post('http://localhost:5000/api/auth/login', {
          username: this.loginForm.username.trim(),
          password: this.loginForm.password
        })
        
        // Ensure user is company or admin
        const role = res.data.user.role
        if (role !== 'company' && role !== 'admin') {
          this.error = 'This portal is restricted to Company Operators and Admins. Please use User Portal for driver bookings.'
          return
        }

        localStorage.setItem('companyToken', res.data.access_token)
        localStorage.setItem('companyData', JSON.stringify(res.data.user))
        this.$emit('login-success')
      } catch (err) {
        this.error = err.response?.data?.error || 'Login failed. Please verify credentials.'
      } finally {
        this.loading = false
      }
    },
    async handleRegister() {
      this.loading = true
      this.error = ''
      this.successText = ''
      try {
        const payload = {
          role: 'company',
          company_name: this.regForm.company_name.trim(),
          name: this.regForm.name.trim() || this.regForm.company_name.trim(),
          mobile_number: this.regForm.mobile_number.trim(),
          description: this.regForm.description.trim(),
          email: this.regForm.email.trim(),
          username: this.regForm.username.trim(),
          password: this.regForm.password,
          address: this.regForm.address.trim()
        }
        
        await axios.post('http://localhost:5000/api/auth/register', payload)
        this.successText = 'Company account registered successfully! You can now sign in.'
        this.loginForm.username = this.regForm.username
        this.loginForm.password = this.regForm.password
        this.isRegister = false
      } catch (err) {
        this.error = err.response?.data?.error || 'Registration failed'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.company-login-wrapper {
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  min-height: 100vh;
}

.login-card {
  max-width: 480px;
  width: 100%;
}

.icon-circle {
  width: 64px;
  height: 64px;
}

.back-link {
  transition: color 0.2s ease;
}

.back-link:hover {
  color: #0d6efd !important;
}
</style>

