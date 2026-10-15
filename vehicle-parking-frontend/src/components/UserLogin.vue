<template>
  <div class="user-login-wrapper d-flex justify-content-center align-items-center min-vh-100 px-3">
    <div class="login-card card shadow-lg rounded-4 border-0 p-4 p-md-5 bg-white">
      <div class="card-body p-0">
        
        <!-- Header with Icon Badge -->
        <div class="text-center mb-4">
          <div class="icon-circle bg-success-subtle text-success mx-auto mb-3 shadow-sm d-flex align-items-center justify-content-center rounded-circle">
            <i class="bi bi-person-fill fs-3"></i>
          </div>
          <h2 class="card-title fw-bold text-dark mb-1">User Portal</h2>
          <p class="text-muted small">Sign in to find and manage your parking reservations</p>
        </div>

        <!-- Success Alert -->
        <div v-if="successText" class="alert alert-success alert-dismissible fade show mb-3 py-2 small" role="alert">
          <i class="bi bi-check-circle-fill me-2"></i>{{ successText }}
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
                placeholder="Enter your username"
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

          <button type="submit" class="btn btn-success w-100 py-2.5 fw-semibold shadow-sm d-flex align-items-center justify-content-center gap-2" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            <span>{{ loading ? 'Signing in...' : 'Sign In' }}</span>
          </button>
        </form>
        
        <!-- Error Alert -->
        <div v-if="error" class="alert alert-danger alert-dismissible fade show mt-3 mb-0 py-2 small" role="alert">
          <i class="bi bi-exclamation-triangle-fill me-2"></i>{{ error }}
        </div>

        <!-- Footer Links -->
        <div class="text-center mt-4 pt-3 border-top">
          <p class="text-muted small mb-2">
            Don't have an account? 
            <a href="#" @click.prevent="goToRegister" class="text-success text-decoration-none fw-semibold hover-underline">Register here</a>
          </p>
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
  name: 'UserLogin',
  props: {
    successMessage: {
      type: String,
      default: ''
    }
  },
  emits: ['login-success', 'switch-to-register'],
  data() {
    return {
      form: { username: '', password: '' },
      loading: false,
      error: ''
    }
  },
  computed: {
    successText() {
      if (this.successMessage) return this.successMessage
      if (this.$route && this.$route.query && this.$route.query.registered) {
        return 'Registration successful! Please log in.'
      }
      return ''
    }
  },
  methods: {
    goToRegister() {
      this.$emit('switch-to-register')
      if (this.$router && this.$route && this.$route.path !== '/user') {
        this.$router.push('/register')
      }
    },
    async handleLogin() {
      this.loading = true
      this.error = ''
      try {
        const res = await axios.post('http://localhost:5000/api/auth/login', {
          username: this.form.username.trim(),
          password: this.form.password
        })
        localStorage.setItem('userToken', res.data.access_token)
        localStorage.setItem('userData', JSON.stringify(res.data.user))
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
.user-login-wrapper {
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
  border-color: #a3cfbb;
  box-shadow: none;
}

.input-group-text {
  border-top-left-radius: 0.375rem;
  border-bottom-left-radius: 0.375rem;
}

.hover-underline:hover {
  text-decoration: underline !important;
}

.back-link {
  transition: color 0.2s ease;
}

.back-link:hover {
  color: #198754 !important;
}
</style>