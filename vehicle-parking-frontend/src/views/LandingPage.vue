<template>
  <div class="container-fluid d-flex justify-content-center align-items-center min-vh-100 bg-light">
    <div class="text-center">
      <h1 class="mb-4">Parking Management System</h1>
      <div class="row g-3">
        <div class="col-md-6">
          <div class="card cursor-pointer" @click="$router.push('/admin')">
            <div class="card-body">
              <h2 class="card-title">Admin Portal</h2>
              <p class="card-text">Manage parking lots and reservations</p>
            </div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card cursor-pointer" @click="$router.push('/user')">
            <div class="card-body">
              <h2 class="card-title">User Portal</h2>
              <p class="card-text">Make and manage reservations</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default { name: 'LandingPage' }
</script>

<style scoped>
.min-vh-100 { min-height: 100vh; }
.cursor-pointer { cursor: pointer; }
.card:hover { transform: translateY(-4px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
</style>