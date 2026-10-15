<template>
  <div class="d-flex justify-content-center align-items-center min-vh-100" style="background: linear-gradient(135deg, #42b983 0%, #359268 100%);">
    <div class="card shadow" style="max-width: 420px; width: 100%;">
      <div class="card-body p-4">
        <h2 class="card-title text-center mb-4">Register User</h2>
        
        <form @submit.prevent="handleRegister">
          <div class="mb-3">
            <label class="form-label">Username</label>
            <input
              v-model="form.username"
              type="text"
              class="form-control"
              placeholder="Username"
              required
            />
          </div>
          <div class="mb-3">
            <label class="form-label">Email</label>
            <input
              v-model="form.email"
              type="email"
              class="form-control"
              placeholder="e.g. user@example.com"
              required
            />
          </div>
          <div class="mb-3">
            <label class="form-label">Password</label>
            <input
              v-model="form.password"
              type="password"
              class="form-control"
              placeholder="Password"
              required
            />
          </div>
          <div class="mb-3">
            <label class="form-label">Confirm Password</label>
            <input
              v-model="confirmPassword"
              type="password"
              class="form-control"
              placeholder="Re-enter password"
              required
            />
          </div>
          <button type="submit" class="btn btn-success w-100" :disabled="loading">
            {{ loading ? 'Registering...' : 'Register' }}
          </button>
        </form>
        
        <div v-if="error" class="alert alert-danger mt-3 mb-0">{{ error }}</div>
        
        <p class="text-center mt-3 mb-2">
          Already have an account? <a href="#" @click.prevent="goToLogin" class="text-decoration-none fw-semibold">Login</a>
        </p>
        <p class="text-center mb-0">
          <router-link to="/" class="text-decoration-none text-muted">← Back to Home</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'UserRegister',
  emits: ['register-success', 'switch-to-login'],
  data() {
    return {
      form: { username: '', email: '', password: '' },
      confirmPassword: '',
      loading: false,
      error: ''
    }
  },
  methods: {
    goToLogin() {
      this.$emit('switch-to-login')
      if (this.$router && this.$route && this.$route.path === '/register') {
        this.$router.push('/user')
      }
    },
    async handleRegister() {
      this.error = ''
      const username = this.form.username.trim()
      const email = this.form.email.trim()
      const password = this.form.password
      
      if (!username) {
        this.error = 'Username is required'
        return
      }
      
      if (/\s/.test(username)) {
        this.error = 'Username must be a single word without spaces'
        return
      }
      
      if (!email) {
        this.error = 'Email is required'
        return
      }
      
      if (!password) {
        this.error = 'Password is required'
        return
      }
      
      if (/\s/.test(password)) {
        this.error = 'Password must be a single word without spaces'
        return
      }
      
      if (password !== this.confirmPassword) {
        this.error = 'Passwords do not match'
        return
      }
      
      this.loading = true
      try {
        await axios.post('http://localhost:5000/api/auth/register', {
          username: username,
          email: email,
          password: password
        })
        this.$emit('register-success')
        if (this.$router && this.$route && this.$route.path === '/register') {
          this.$router.push({ path: '/user', query: { registered: 'true' } })
        }
      } catch (err) {
        this.error = err.response?.data?.error || 'Registration failed'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>