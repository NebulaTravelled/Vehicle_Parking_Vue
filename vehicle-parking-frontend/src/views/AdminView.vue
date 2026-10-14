<template>
  <div>
    <AdminLogin v-if="!isLoggedIn" @login-success="handleLoginSuccess" />
    
    <div v-else>
      <div class="bg-white border-bottom px-4 py-3 d-flex justify-content-between align-items-center">
        <h2>Admin Dashboard</h2>
        <button class="btn btn-danger btn-sm" @click="logout">Logout</button>
      </div>
      
      <ul class="nav nav-tabs bg-white px-4">
        <li class="nav-item">
          <a href="#" class="nav-link" :class="{ active: activeTab === 'dashboard' }" @click.prevent="activeTab = 'dashboard'">Dashboard</a>
        </li>
        <li class="nav-item">
          <a href="#" class="nav-link" :class="{ active: activeTab === 'lots' }" @click.prevent="activeTab = 'lots'">Parking Lots</a>
        </li>
        <li class="nav-item">
          <a href="#" class="nav-link" :class="{ active: activeTab === 'users' }" @click.prevent="activeTab = 'users'">Users</a>
        </li>
      </ul>
      
      <div class="p-4">
        <div v-if="activeTab === 'dashboard'" class="card">
          <div class="card-body"><p>Dashboard content...</p></div>
        </div>
        <div v-if="activeTab === 'lots'" class="card">
          <div class="card-body"><p>Parking lots list...</p></div>
        </div>
        <div v-if="activeTab === 'users'" class="card">
          <div class="card-body"><p>Users list...</p></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import AdminLogin from '../components/AdminLogin.vue'
import axios from 'axios'

export default {
  components: { AdminLogin },
  data() {
    return {
      isLoggedIn: !!localStorage.getItem('adminToken'),
      activeTab: 'dashboard'
    }
  },
  methods: {
    handleLoginSuccess() {
      this.isLoggedIn = true
    },
    logout() {
      localStorage.removeItem('adminToken')
      localStorage.removeItem('adminUser')
      this.isLoggedIn = false
    }
  }
}
</script>