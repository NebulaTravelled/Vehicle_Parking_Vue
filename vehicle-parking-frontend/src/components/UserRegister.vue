{% raw %}
<template>
  <div class="d-flex justify-content-center align-items-center min-vh-100" style="background: linear-gradient(135deg, #42b983 0%, #359268 100%);">
    <div class="card shadow" style="max-width: 400px; width: 100%;">
      <div class="card-body">
        <h2 class="card-title text-center mb-4">Register</h2>
        
        <form @submit.prevent="handleRegister">
          <div class="mb-3">
            <label class="form-label">Username</label>
            <input v-model="form.username" type="text" class="form-control" required />
          </div>
          <div class="mb-3">
            <label class="form-label">Email</label>
            <input v-model="form.email" type="email" class="form-control" required />
          </div>
          <div class="mb-3">
            <label class="form-label">Password</label>
            <input v-model="form.password" type="password" class="form-control" required />
          </div>
          <button type="submit" class="btn btn-success w-100" :disabled="loading">
            {{ loading ? 'Registering...' : 'Register' }}
          </button>
        </form>
        
        <div v-if="error" class="alert alert-danger mt-3 mb-0">{{ error }}</div>
        
        <p class="text-center mt-3 mb-0">
          Have account? <a href="#" @click.prevent="$emit('switch-to-login')" class="text-decoration-none">Login</a>
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
      loading: false,
      error: ''
    }
  },
  methods: {
    async handleRegister() {
      this.loading = true
      this.error = ''
      try {
        await axios.post('http://localhost:5000/api/auth/register', this.form)
        this.$emit('register-success')
      } catch (err) {
        this.error = err.response?.data?.error || 'Registration failed'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>
{% endraw %}