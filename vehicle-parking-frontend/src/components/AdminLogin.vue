<template>
  <div class="admin-login-wrapper d-flex justify-content-center align-items-center min-vh-100 px-3">
    <div class="login-card card shadow-lg rounded-4 border-0 p-4 p-md-5 bg-white">
      <div class="card-body p-0">
        
        <!-- Header with Icon Badge -->
        <div class="text-center mb-4">
          <div class="icon-circle bg-primary-subtle text-primary mx-auto mb-3 shadow-sm d-flex align-items-center justify-content-center rounded-circle">
            <i class="bi bi-shield-lock-fill fs-3"></i>
          </div>
          <h2 class="card-title fw-bold text-dark mb-1">Admin Portal</h2>
          <p class="text-muted small">Please sign in to manage parking lots and reservations</p>
        </div>
        
        <!-- Login Form -->
        <form @submit.prevent="handleLogin">
          
          <div class="mb-3">
            <label class="form-label fw-semibold small text-secondary">Username</label>
            <div class="input-group">
              <span class="input-group-text bg-light border-end-0 text-muted"><i class="bi bi-person-fill"></i></span>
              <input 
                v-model="form.username" 
                type="text" 
                class="form-control bg-light border-start-0 ps-0 shadow-none" 
                placeholder="Enter admin username"
                required 
              />
            </div>
          </div>

          <div class="mb-4">
            <label class="form-label fw-semibold small text-secondary">Password</label>
            <div class="input-group">
              <span class="input-group-text bg-light border-end-0 text-muted"><i class="bi bi-key-fill"></i></span>
              <input 
                v-model="form.password" 
                type="password" 
                class="form-control bg-light border-start-0 ps-0 shadow-none" 
                placeholder="Enter password"
                required 
              />
            </div>
          </div>

          <button type="submit" class="btn btn-primary w-100 py-2.5 fw-semibold shadow-sm d-flex align-items-center justify-content-center gap-2" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            <span>{{ loading ? 'Authenticating...' : 'Sign In' }}</span>
          </button>
        </form>
        
        <!-- Error Alert -->
        <div v-if="error" class="alert alert-danger alert-dismissible fade show mt-3 mb-0 py-2 small" role="alert">
          <i class="bi bi-exclamation-triangle-fill me-2"></i>{{ error }}
        </div>

        <!-- Back Link -->
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
  name: 'AdminLogin',
  emits: ['login-success'],
  data() {
    return {
      form: { username: '', password: '' },
      loading: false,
      error: ''
    }
  },
  methods: {
    async handleLogin() {
      this.loading = true
      this.error = ''
      try {
        const res = await axios.post('http://localhost:5000/api/auth/login', this.form)
        localStorage.setItem('adminToken', res.data.access_token)
        localStorage.setItem('adminUser', JSON.stringify(res.data.user))
        this.$emit('login-success')
      } catch (err) {
        this.error = err.response?.data?.error || 'Login failed. Please check your credentials.'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.admin-login-wrapper {
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e9f2 100%);
  min-height: 100vh;
}

.login-card {
  max-width: 420px;
  width: 100%;
}

.icon-circle {
  width: 64px;
  height: 64px;
}

.form-control:focus {
  background-color: #ffffff !important;
  border-color: #86b7fe;
}

.input-group-text {
  border-top-left-radius: 0.375rem;
  border-bottom-left-radius: 0.375rem;
}

.back-link {
  transition: color 0.2s ease;
}

.back-link:hover {
  color: #0d6efd !important;
}
</style>