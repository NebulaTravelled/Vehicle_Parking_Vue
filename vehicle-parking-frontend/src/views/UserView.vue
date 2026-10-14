<template>
  <div>
    <div v-if="!isLoggedIn">
      <AdminLogin v-if="!showRegister" @login-success="handleLoginSuccess" @switch-to-register="showRegister = true" />
      <UserRegister v-else @register-success="handleRegisterSuccess" @switch-to-login="showRegister = false" />
    </div>
    
    <div v-else>
      <div class="bg-white border-bottom px-4 py-3 d-flex justify-content-between align-items-center">
        <h2>User Dashboard</h2>
        <button class="btn btn-danger btn-sm" @click="logout">Logout</button>
      </div>
      
      <ul class="nav nav-tabs bg-white px-4">
        <li class="nav-item">
          <a href="#" class="nav-link" :class="{ active: activeTab === 'dashboard' }" @click.prevent="activeTab = 'dashboard'">Dashboard</a>
        </li>
        <li class="nav-item">
          <a href="#" class="nav-link" :class="{ active: activeTab === 'reservations' }" @click.prevent="activeTab = 'reservations'">My Reservations</a>
        </li>
      </ul>
      
      <div class="p-4">
        <div v-if="activeTab === 'dashboard'" class="card">
          <div class="card-body"><p>Dashboard content...</p></div>
        </div>
        <div v-if="activeTab === 'reservations'" class="card">
          <div class="card-body"><p>Your reservations...</p></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import AdminLogin from '../components/AdminLogin.vue'
import UserRegister from '../components/UserRegister.vue'

export default {
  components: { AdminLogin, UserRegister },
  data() {
    return {
      isLoggedIn: !!localStorage.getItem('userToken'),
      showRegister: false,
      activeTab: 'dashboard'
    }
  },
  methods: {
    handleLoginSuccess() {
      this.isLoggedIn = true
    },
    handleRegisterSuccess() {
      this.showRegister = false
    },
    logout() {
      localStorage.removeItem('userToken')
      localStorage.removeItem('userData')
      this.isLoggedIn = false
    }
  }
}
</script>