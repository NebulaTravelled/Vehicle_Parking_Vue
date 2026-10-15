<template>
  <div class="landing-page-root">
    
    <!-- Top Navigation -->
    <header class="navbar navbar-expand-lg navbar-light bg-white border-bottom py-3 sticky-top shadow-sm">
      <div class="container">
        <router-link to="/" class="navbar-brand d-flex align-items-center gap-2 fw-bold text-dark fs-4">
          <div class="brand-icon-box bg-success text-white rounded-3 d-flex align-items-center justify-content-center shadow-sm">
            <i class="bi bi-p-square-fill fs-5"></i>
          </div>
          <span>Smart<span class="text-success">Park</span></span>
        </router-link>

        <div class="d-flex align-items-center gap-2">
          <router-link to="/user" class="btn btn-outline-success btn-sm fw-semibold rounded-pill px-3">
            <i class="bi bi-car-front-fill me-1"></i> User Portal
          </router-link>
          <router-link to="/company" class="btn btn-primary btn-sm fw-semibold rounded-pill px-3 shadow-sm">
            <i class="bi bi-building me-1"></i> Company Portal
          </router-link>
          <router-link to="/admin" class="btn btn-outline-secondary btn-sm fw-semibold rounded-pill px-3 d-none d-md-inline-block">
            <i class="bi bi-shield-lock-fill me-1"></i> Admin
          </router-link>
        </div>
      </div>
    </header>

    <!-- Hero Section -->
    <section class="hero-section text-center py-5 px-3 position-relative overflow-hidden">
      <div class="container py-4">
        
        

        <!-- Main Headline -->
        <h1 class="hero-headline fw-bolder text-dark mb-3 display-4">
          Effortless Parking for Drivers, <br class="d-none d-md-inline">
          <span class="gradient-text">Complete Control for Companies</span>
        </h1>

        <!-- Subtitle -->
        <p class="hero-subtext text-secondary mx-auto mb-4 lead" style="max-width: 720px;">
          Reserve regular or handicap accessible parking spaces instantly. Empower parking facility operators to design interactive slot grids, customize tariffs, and streamline physical space operations.
        </p>

        <!-- CTA Buttons -->
        <div class="d-flex justify-content-center gap-3 flex-wrap mb-5">
          <router-link to="/user" class="btn btn-success btn-lg px-4 py-2.5 rounded-pill fw-semibold shadow d-flex align-items-center gap-2">
            <i class="bi bi-geo-alt-fill"></i>
            <span>Find & Book Parking</span>
          </router-link>
          <router-link to="/company" class="btn btn-primary btn-lg px-4 py-2.5 rounded-pill fw-semibold shadow d-flex align-items-center gap-2">
            <i class="bi bi-grid-3x3-gap-fill"></i>
            <span>Company Slot Designer</span>
          </router-link>
        </div>

        <!-- Quick Platform Stats Pill Strip -->
        <div class="row g-3 justify-content-center max-w-900 mx-auto">
          <div class="col-6 col-md-3">
            <div class="stat-pill bg-white border rounded-4 p-3 shadow-sm text-center">
              <div class="fs-4 fw-bold text-success">100%</div>
              <div class="small text-muted fw-semibold">Auto-Allotment</div>
            </div>
          </div>
          <div class="col-6 col-md-3">
            <div class="stat-pill bg-white border rounded-4 p-3 shadow-sm text-center">
              <div class="fs-4 fw-bold text-primary">♿ Accessible</div>
              <div class="small text-muted fw-semibold">Handicap Bays</div>
            </div>
          </div>
          <div class="col-6 col-md-3">
            <div class="stat-pill bg-white border rounded-4 p-3 shadow-sm text-center">
              <div class="fs-4 fw-bold text-dark">Interactive</div>
              <div class="small text-muted fw-semibold">Clickable Grid</div>
            </div>
          </div>
          <div class="col-6 col-md-3">
            <div class="stat-pill bg-white border rounded-4 p-3 shadow-sm text-center">
              <div class="fs-4 fw-bold text-warning-emphasis">Real-Time</div>
              <div class="small text-muted fw-semibold">Live Occupancy</div>
            </div>
          </div>
        </div>

      </div>
    </section>

    <!-- Feature Spotlight: The Clickable Grid & Handicap Parking -->
    <section class="py-5 bg-light">
      <div class="container py-3">
        <div class="row g-5 align-items-center">
          
          <div class="col-lg-6">
            <span class="badge bg-primary-subtle text-primary fw-bold px-3 py-1.5 rounded-pill mb-3">
              Interactive Grid Designer
            </span>
            <h2 class="fw-bold text-dark mb-3">Empowering Operators with Visual Slot Layouts</h2>
            <p class="text-secondary mb-4">
              Parking lot layouts shouldn't be arbitrary numbers. With our company portal, operators can visually define parking rows and columns, place driving lanes, stairwells, regular bays, and handicap spaces on an interactive canvas.
            </p>

            <div class="row g-3">
              <div class="col-sm-6">
                <div class="bg-white p-3 rounded-3 border shadow-sm">
                  <div class="fs-4 mb-1">🅿️ / ♿</div>
                  <h6 class="fw-bold mb-1">Dual Slot Types</h6>
                  <p class="text-muted small mb-0">Total slots are automatically computed as Regular + Handicap spaces.</p>
                </div>
              </div>
              <div class="col-sm-6">
                <div class="bg-white p-3 rounded-3 border shadow-sm">
                  <div class="fs-4 mb-1">🛣️ / 🪜</div>
                  <h6 class="fw-bold mb-1">Roadways & Stairs</h6>
                  <p class="text-muted small mb-0">Paint driving lanes and pedestrian stairs to match real layout geometry.</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Interactive Grid Visual Preview Mockup -->
          <div class="col-lg-6">
            <div class="card shadow rounded-4 border-0 p-3 bg-white">
              <div class="d-flex justify-content-between align-items-center mb-3 px-1">
                <span class="fw-bold small text-secondary"><i class="bi bi-grid-3x3 me-1"></i> Interactive Layout Preview</span>
                <span class="badge bg-success-subtle text-success">8 Slots Saved</span>
              </div>

              <!-- Mock Grid -->
              <div class="mock-grid">
                <div class="mock-cell cell-parking">🅿️ P-1</div>
                <div class="mock-cell cell-parking">🅿️ P-2</div>
                <div class="mock-cell cell-handicap">♿ H-1</div>
                <div class="mock-cell cell-stairs">🪜 Exit</div>

                <div class="mock-cell cell-road">🛣️ Road</div>
                <div class="mock-cell cell-road">🛣️ Road</div>
                <div class="mock-cell cell-road">🛣️ Road</div>
                <div class="mock-cell cell-road">🛣️ Road</div>

                <div class="mock-cell cell-parking">🅿️ P-3</div>
                <div class="mock-cell cell-parking">🅿️ P-4</div>
                <div class="mock-cell cell-parking">🅿️ P-5</div>
                <div class="mock-cell cell-handicap">♿ H-2</div>
              </div>

              <div class="d-flex justify-content-between align-items-center mt-3 pt-2 border-top small text-muted">
                <span>🚗 Regular: <strong>6</strong> | ♿ Handicap: <strong>2</strong></span>
                <span class="text-primary fw-semibold">Clickable on Company Portal</span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="bg-dark text-white py-4 border-top">
      <div class="container d-flex flex-wrap justify-content-between align-items-center gap-3">
        <div class="d-flex align-items-center gap-2">
          <i class="bi bi-car-front-fill text-success fs-5"></i>
          <span class="fw-bold">SmartPark Enterprise</span>
          <span class="text-secondary small ms-2">© 2026 All Rights Reserved</span>
        </div>
        <div class="d-flex gap-4 small text-secondary">
          <router-link to="/user" class="text-white-50 text-decoration-none hover-white">User Portal</router-link>
          <router-link to="/company" class="text-white-50 text-decoration-none hover-white">Company Portal</router-link>
          <router-link to="/admin" class="text-white-50 text-decoration-none hover-white">Admin Portal</router-link>
          <router-link to="/register" class="text-white-50 text-decoration-none hover-white">Register</router-link>
        </div>
      </div>
    </footer>

  </div>
</template>

<script>
export default {
  name: 'LandingPage'
}
</script>

<style scoped>
.landing-page-root {
  background-color: #fafbfc;
  min-height: 100vh;
}

.brand-icon-box {
  width: 36px;
  height: 36px;
}

.hero-section {
  background: radial-gradient(circle at 50% 10%, rgba(25, 135, 84, 0.08) 0%, rgba(13, 110, 253, 0.03) 50%, #fafbfc 100%);
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background-color: #198754;
  border-radius: 50%;
  display: inline-block;
  box-shadow: 0 0 0 0 rgba(25, 135, 84, 0.7);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(25, 135, 84, 0.7);
  }
  70% {
    transform: scale(1);
    box-shadow: 0 0 0 6px rgba(25, 135, 84, 0);
  }
  100% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(25, 135, 84, 0);
  }
}

.gradient-text {
  background: linear-gradient(135deg, #0d6efd 0%, #198754 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.max-w-900 {
  max-width: 900px;
}

.stat-pill {
  transition: transform 0.2s ease;
}

.stat-pill:hover {
  transform: translateY(-3px);
}

/* Portal Cards */
.portal-card {
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  background: #ffffff;
  border: 1px solid #e9ecef !important;
}

.portal-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 16px 32px rgba(0, 0, 0, 0.09) !important;
}

.featured-portal {
  border: 2px solid #0d6efd !important;
}

.portal-card:hover .transition-arrow {
  transform: translateX(6px);
}

.transition-arrow {
  transition: transform 0.2s ease;
}

.card-accent-bar {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
}

.portal-icon-circle {
  width: 56px;
  height: 56px;
}

.cursor-pointer {
  cursor: pointer;
}

.hover-underline:hover {
  text-decoration: underline !important;
}

.hover-white:hover {
  color: #ffffff !important;
}

/* Mock Grid Preview */
.mock-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.mock-cell {
  aspect-ratio: 1.4;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  border: 1px solid transparent;
}

.cell-parking {
  background-color: #d1e7dd;
  border-color: #198754;
  color: #0f5132;
}

.cell-handicap {
  background-color: #cff4fc;
  border-color: #0dcaf0;
  color: #055160;
}

.cell-road {
  background-color: #343a40;
  border-color: #212529;
  color: #f8f9fa;
}

.cell-stairs {
  background-color: #fff3cd;
  border-color: #ffc107;
  color: #664d03;
}
</style>