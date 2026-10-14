{% raw %}
<template>
  <div class="d-flex justify-content-center align-items-center min-vh-100" style="background: linear-gradient(135deg, #42b983 0%, #359268 100%);">
    <div class="card shadow" style="max-width: 400px; width: 100%;">
      <div class="card-body">
        <h2 class="card-title text-center mb-4">User Login</h2>
        
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
          Don't have account? <a href="#" @click.prevent="$emit('switch-to-register')" class="text-decoration-none">Register</a>
        </p>
        <p class="text-center mb-0">
          <router-link to="/" class="text-decoration-none">← Back</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'UserLogin',
  emits: ['login-success', 'switch-to-register'],
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