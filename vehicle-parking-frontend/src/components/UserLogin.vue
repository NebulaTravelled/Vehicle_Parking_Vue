{% raw %}
<template>
  <div class="d-flex justify-content-center align-items-center min-vh-100" style="background: linear-gradient(135deg, #42b983 0%, #359268 100%);">
    <div class="card shadow" style="max-width: 400px; width: 100%;">
      <div class="card-body p-4">
        <h2 class="card-title text-center mb-4">User Login</h2>
        
        <div v-if="successText" class="alert alert-success mb-3">{{ successText }}</div>
        
        <form @submit.prevent="handleLogin">
          <div class="mb-3">
            <label class="form-label">Username</label>
            <input v-model="form.username" type="text" class="form-control" required />
          </div>
          <div class="mb-3">
            <label class="form-label">Password</label>
            <input v-model="form.password" type="password" class="form-control" required />
          </div>
          <button type="submit" class="btn btn-success w-100" :disabled="loading">
            {{ loading ? 'Logging in...' : 'Login' }}
          </button>
        </form>
        
        <div v-if="error" class="alert alert-danger mt-3 mb-0">{{ error }}</div>
        
        <p class="text-center mt-3 mb-2">
          Don't have account? <a href="#" @click.prevent="goToRegister" class="text-decoration-none fw-semibold">Register</a>
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
        this.error = err.response?.data?.error || 'Login failed'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>
{% endraw %}