<template>
  <div class="landing-wrapper d-flex justify-content-center align-items-center min-vh-100 px-3">
    <div class="landing-card text-center p-4 p-md-5 shadow-lg rounded-4 bg-white border border-light">
      
      <!-- Top Badge / Header -->
      <div class="badge bg-success-subtle text-success px-3 py-2 rounded-pill fw-semibold mb-3">
        <i class="bi bi-car-front-fill me-1"></i> Smart Parking Solution
      </div>

      <h1 class="fw-bold text-dark mb-2 display-6">Parking Management System</h1>
      <p class="text-secondary mb-5">Streamline your parking operations and reserve spots seamlessly.</p>

      <!-- Portal Cards -->
      <div class="row g-4 justify-content-center">
        
        <!-- Admin Portal -->
        <div class="col-md-6">
          <div class="portal-card card h-100 border-0 shadow-sm p-3 text-start position-relative overflow-hidden cursor-pointer" @click="$router.push('/admin')">
            <div class="accent-bar bg-primary"></div>
            <div class="card-body d-flex flex-column justify-content-between">
              <div>
                <div class="icon-box bg-primary-subtle text-primary rounded-3 d-inline-flex align-items-center justify-content-center mb-3">
                  <i class="bi bi-shield-lock-fill fs-4"></i>
                </div>
                <h3 class="card-title h5 fw-bold text-dark mb-1">Admin Portal</h3>
                <p class="card-text text-muted small mb-4">Manage parking lots, monitor slots, and oversee user reservations.</p>
              </div>
              <div class="d-flex align-items-center text-primary fw-semibold small">
                <span>Access Dashboard</span>
                <i class="bi bi-arrow-right ms-2 transition-icon"></i>
              </div>
            </div>
          </div>
        </div>

        <!-- User Portal -->
        <div class="col-md-6">
          <div class="portal-card card h-100 border-0 shadow-sm p-3 text-start position-relative overflow-hidden cursor-pointer" @click="$router.push('/user')">
            <div class="accent-bar bg-success"></div>
            <div class="card-body d-flex flex-column justify-content-between">
              <div>
                <div class="icon-box bg-success-subtle text-success rounded-3 d-inline-flex align-items-center justify-content-center mb-3">
                  <i class="bi bi-person-fill fs-4"></i>
                </div>
                <h3 class="card-title h5 fw-bold text-dark mb-1">User Portal</h3>
                <p class="card-text text-muted small mb-4">Find available parking spaces, make bookings, and manage active reservations.</p>
              </div>
              <div class="d-flex align-items-center text-success fw-semibold small">
                <span>Book a Spot</span>
                <i class="bi bi-arrow-right ms-2 transition-icon"></i>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- Footer Register Link -->
      <div class="mt-5 pt-3 border-top">
        <span class="text-muted">New to the platform? </span>
        <router-link to="/register" class="fw-bold text-success text-decoration-none hover-underline">
          Create an account <i class="bi bi-chevron-right small"></i>
        </router-link>
      </div>

    </div>
  </div>
</template>

<script>
export default {
  name: 'LandingPage'
}
</script>

<style scoped>
.landing-wrapper {
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e9f2 100%);
  min-height: 100vh;
}

.landing-card {
  max-width: 800px;
  width: 100%;
}

.portal-card {
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  background: #fafbfc;
  border: 1px solid #edf2f7 !important;
}

.portal-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08) !important;
  background: #ffffff;
}

.portal-card:hover .transition-icon {
  transform: translateX(4px);
}

.transition-icon {
  transition: transform 0.2s ease;
}

.accent-bar {
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
}

.icon-box {
  width: 48px;
  height: 48px;
}

.cursor-pointer {
  cursor: pointer;
}

.hover-underline:hover {
  text-decoration: underline !important;
}
</style>