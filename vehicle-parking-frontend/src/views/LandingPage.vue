<template>
  <div class="landing-page-root">
    
    <!-- Top Navigation Header -->
    <header class="navbar navbar-expand-lg navbar-light bg-white border-bottom py-3 sticky-top shadow-sm">
      <div class="container">
        <!-- Brand Logo -->
        <router-link to="/" class="navbar-brand d-flex align-items-center gap-2 fw-bold text-dark fs-4 text-decoration-none">
          <div class="brand-icon-box bg-success text-white rounded-3 d-flex align-items-center justify-content-center shadow-sm">
            <i class="bi bi-p-square-fill fs-5"></i>
          </div>
          <span class="tracking-tight">Smart<span class="text-success">Park</span></span>
        </router-link>

        <!-- Navbar Links & Login Buttons (User, Company, Admin) -->
        <div class="d-flex align-items-center gap-2 ms-auto">
          <!-- User / Driver Portal Button -->
          <router-link to="/user" class="btn btn-success btn-sm fw-semibold rounded-pill px-3 shadow-sm d-flex align-items-center gap-1.5">
            <i class="bi bi-car-front-fill"></i>
            <span>Driver Portal</span>
          </router-link>

          <!-- Company Portal Button -->
          <router-link to="/company" class="btn btn-outline-primary btn-sm fw-semibold rounded-pill px-3 d-flex align-items-center gap-1.5">
            <i class="bi bi-building"></i>
            <span>Company Portal</span>
          </router-link>

          <!-- Admin Portal Button -->
          <router-link to="/admin" class="btn btn-outline-secondary btn-sm fw-semibold rounded-pill px-3 d-flex align-items-center gap-1.5">
            <i class="bi bi-shield-lock-fill"></i>
            <span>Admin</span>
          </router-link>
        </div>
      </div>
    </header>

    <!-- Hero Section (100% User / Driver Focused) -->
    <section class="hero-section text-center py-5 px-3 position-relative overflow-hidden">
      <div class="container py-4">
        
        <!-- Trust Pill Badge -->
        <div class="d-inline-flex align-items-center gap-2 bg-success-subtle border border-success-subtle text-success-emphasis rounded-pill px-3 py-1.5 mb-3 small fw-semibold">
          <span class="pulse-dot"></span>
          <span>Live Multi-Deck Real-Time Parking Availability</span>
        </div>

        <!-- Main Headline -->
        <h1 class="hero-headline fw-bolder text-dark mb-3 display-4">
          Smart, Seamless Parking <br class="d-none d-md-inline">
          <span class="gradient-text">Reserved in Seconds.</span>
        </h1>

        <!-- Subtitle -->
        <p class="hero-subtext text-secondary mx-auto mb-4 lead" style="max-width: 720px;">
          Never circle for parking again. Search nearby parking spaces, check real-time multi-deck availability, lock in regular or handicap bays, and enjoy contactless digital passes.
        </p>

        <!-- Hero Quick Search / Discovery Widget -->
        <div class="card shadow-lg border-0 rounded-4 max-w-760 mx-auto p-2 mb-2 bg-white">
          <div class="card-body p-2">
            <div class="row g-2 align-items-center">
              <div class="col-md-8">
                <div class="input-group">
                  <span class="input-group-text bg-white border-0 text-muted ps-3">
                    <i class="bi bi-search text-success fs-5"></i>
                  </span>
                  <input
                    type="text"
                    class="form-control border-0 shadow-none ps-2 fs-6"
                    placeholder="Search by facility name, address, or PIN code..."
                    @focus="goToUserPortal"
                    @click="goToUserPortal"
                  />
                </div>
              </div>
              <div class="col-md-4">
                <router-link to="/user" class="btn btn-success w-100 py-2.5 rounded-3 fw-semibold shadow-sm d-flex align-items-center justify-content-center gap-2">
                  <i class="bi bi-geo-alt-fill"></i>
                  <span>Find Parking Spot</span>
                </router-link>
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>

    <!-- Feature Spotlight: The Seamless Driver Experience -->
    <section class="py-5 bg-light border-top">
      <div class="container py-4">
        <div class="row g-5 align-items-center">
          
          <!-- Left Column: Driver Features -->
          <div class="col-lg-6">
            <span class="badge bg-success-subtle text-success fw-bold px-3 py-1.5 rounded-pill mb-3">
              Driver Experience
            </span>
            <h2 class="fw-bold text-dark mb-3">Everything You Need for Effortless Parking</h2>
            <p class="text-secondary mb-4">
              From finding spots near your office or shopping mall to managing your entire family or fleet vehicle garage, our driver portal makes parking completely stress-free.
            </p>

            <div class="row g-3">
              <div class="col-sm-6">
                <div class="bg-white p-3 rounded-3 border shadow-sm h-100">
                  <div class="fs-4 mb-2">⚡</div>
                  <h6 class="fw-bold mb-1 text-dark">Smart Quick-Book</h6>
                  <p class="text-muted small mb-0">Automatic allocation of the nearest available bay to the entrance without race conditions.</p>
                </div>
              </div>
              <div class="col-sm-6">
                <div class="bg-white p-3 rounded-3 border shadow-sm h-100">
                  <div class="fs-4 mb-2">📅</div>
                  <h6 class="fw-bold mb-1 text-dark">Advance Pre-Booking</h6>
                  <p class="text-muted small mb-0">Reserve a guaranteed spot for tomorrow's meeting, rush hours, or weekend dinner.</p>
                </div>
              </div>
              <div class="col-sm-6">
                <div class="bg-white p-3 rounded-3 border shadow-sm h-100">
                  <div class="fs-4 mb-2">🚗</div>
                  <h6 class="fw-bold mb-1 text-dark">My Garage</h6>
                  <p class="text-muted small mb-0">Save your Cars, SUVs, EVs, and Motorcycles for instant 1-click booking anytime.</p>
                </div>
              </div>
              <div class="col-sm-6">
                <div class="bg-white p-3 rounded-3 border shadow-sm h-100">
                  <div class="fs-4 mb-2">🎟️</div>
                  <h6 class="fw-bold mb-1 text-dark">Commuter Passes</h6>
                  <p class="text-muted small mb-0">Monthly and quarterly recurring passes for hassle-free daily parking with huge savings.</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Right Column: Interactive Digital Parking Pass Mockup -->
          <div class="col-lg-6">
            <div class="card shadow-lg rounded-4 border-0 p-4 bg-white position-relative">
              
              <!-- Mock Header -->
              <div class="d-flex justify-content-between align-items-center mb-3 pb-3 border-bottom">
                <div class="d-flex align-items-center gap-2">
                  <div class="badge bg-success p-2 rounded-circle">
                    <i class="bi bi-check-lg text-white"></i>
                  </div>
                  <div>
                    <h6 class="fw-bold text-dark mb-0">Active Parking Pass</h6>
                    <small class="text-muted">Digital Gate Clearance</small>
                  </div>
                </div>
                <span class="badge bg-success-subtle text-success border border-success-subtle px-2.5 py-1.5 rounded-pill fw-semibold">
                  🟢 Currently Parked
                </span>
              </div>

              <!-- Pass Details Card -->
              <div class="bg-light p-3 rounded-3 border mb-3">
                <div class="d-flex justify-content-between align-items-start mb-2">
                  <div>
                    <h5 class="fw-bold text-primary mb-0">Grand Central Parking Hub</h5>
                    <small class="text-muted"><i class="bi bi-geo-alt me-1"></i>Downtown Plaza • Gate 2 Entrance</small>
                  </div>
                  <span class="badge bg-dark font-monospace px-2.5 py-1.5">PASS #SP-8942</span>
                </div>

                <div class="row g-2 mt-2 pt-2 border-top small">
                  <div class="col-6">
                    <span class="text-muted d-block">Allocated Deck & Bay:</span>
                    <strong class="text-dark fs-6">Deck G • Bay #104</strong>
                  </div>
                  <div class="col-6 text-end">
                    <span class="text-muted d-block">Vehicle Registered:</span>
                    <strong class="font-monospace text-dark">DL-01-AB-1234 (SUV)</strong>
                  </div>
                  <div class="col-6 mt-2">
                    <span class="text-muted d-block">Live Parked Duration:</span>
                    <span class="badge bg-primary text-white font-monospace">01h 24m 10s</span>
                  </div>
                  <div class="col-6 text-end mt-2">
                    <span class="text-muted d-block">Running Tariff:</span>
                    <strong class="text-success fs-6">₹60.00</strong>
                  </div>
                </div>
              </div>

              <!-- Contactless QR Badge Demo -->
              <div class="d-flex align-items-center gap-3 p-3 bg-white border rounded-3">
                <div class="qr-box bg-dark text-white rounded-3 d-flex align-items-center justify-content-center p-2">
                  <i class="bi bi-qr-code fs-1"></i>
                </div>
                <div class="flex-grow-1">
                  <h6 class="fw-bold mb-1 text-dark">Contactless Gate Scanning</h6>
                  <p class="text-muted small mb-0">Present your digital pass QR code at the parking gate for automatic entry and exit clearance.</p>
                </div>
              </div>

              <div class="mt-3 text-center">
                <router-link to="/user" class="btn btn-success btn-sm w-100 py-2 fw-semibold rounded-pill">
                  Reserve Your Spot Now <i class="bi bi-arrow-right ms-1"></i>
                </router-link>
              </div>

            </div>
          </div>

        </div>
      </div>
    </section>

    <!-- How It Works in 3 Steps -->
    <section class="py-5 bg-white">
      <div class="container py-4 text-center">
        
        <span class="badge bg-primary-subtle text-primary fw-bold px-3 py-1.5 rounded-pill mb-2">
          Simple & Fast
        </span>
        <h2 class="fw-bold text-dark mb-2">How It Works in 3 Easy Steps</h2>
        <p class="text-secondary mx-auto mb-5" style="max-width: 600px;">
          Reserving verified parking is as simple as tap, park, and go.
        </p>

        <div class="row g-4">
          
          <div class="col-md-4">
            <div class="step-card h-100 p-4 rounded-4 border bg-light text-center transition-card">
              <div class="step-icon-circle bg-success text-white mx-auto mb-3 d-flex align-items-center justify-content-center shadow-sm">
                <span class="fs-4 fw-bold">1</span>
              </div>
              <h5 class="fw-bold text-dark mb-2">Find & Choose Lot</h5>
              <p class="text-muted small mb-0">
                Search by location, address, or PIN code. Compare hourly tariffs, multi-deck openings, and accessibility bays.
              </p>
            </div>
          </div>

          <div class="col-md-4">
            <div class="step-card h-100 p-4 rounded-4 border bg-light text-center transition-card">
              <div class="step-icon-circle bg-primary text-white mx-auto mb-3 d-flex align-items-center justify-content-center shadow-sm">
                <span class="fs-4 fw-bold">2</span>
              </div>
              <h5 class="fw-bold text-dark mb-2">Book Your Spot</h5>
              <p class="text-muted small mb-0">
                Select your vehicle from My Garage, choose Park Now or schedule a future window, and receive your instant pass.
              </p>
            </div>
          </div>

          <div class="col-md-4">
            <div class="step-card h-100 p-4 rounded-4 border bg-light text-center transition-card">
              <div class="step-icon-circle bg-dark text-white mx-auto mb-3 d-flex align-items-center justify-content-center shadow-sm">
                <span class="fs-4 fw-bold">3</span>
              </div>
              <h5 class="fw-bold text-dark mb-2">Scan & Park</h5>
              <p class="text-muted small mb-0">
                Drive straight to your allotted bay. Scan your digital QR pass at the gate for automatic seamless check-in and checkout.
              </p>
            </div>
          </div>

        </div>

      </div>
    </section>

    <!-- Bottom Call-To-Action Banner -->
    <section class="py-5 bg-dark text-white text-center position-relative overflow-hidden">
      <div class="container py-4">
        <h2 class="fw-bold mb-3 display-6">Ready to Park Without the Hassle?</h2>
        <p class="text-secondary mx-auto mb-4 lead" style="max-width: 600px;">
          Join thousands of drivers enjoying fast, guaranteed, and contactless parking.
        </p>
        <div class="d-flex justify-content-center gap-3 flex-wrap">
          <router-link to="/user" class="btn btn-success btn-lg px-4 py-2.5 rounded-pill fw-semibold shadow">
            <i class="bi bi-car-front-fill me-1"></i> Start Parking Now
          </router-link>
          <router-link to="/register" class="btn btn-outline-light btn-lg px-4 py-2.5 rounded-pill fw-semibold">
            Create Free Account
          </router-link>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="bg-dark text-white py-4 border-top border-secondary-subtle">
      <div class="container d-flex flex-wrap justify-content-between align-items-center gap-3">
        <div class="d-flex align-items-center gap-2">
          <div class="brand-icon-box bg-success text-white rounded-2 d-flex align-items-center justify-content-center" style="width: 28px; height: 28px;">
            <i class="bi bi-p-square-fill fs-6"></i>
          </div>
          <span class="fw-bold">SmartPark</span>
          <span class="text-secondary small ms-2">© 2026 Vehicle Parking System. All Rights Reserved.</span>
        </div>
        <div class="d-flex gap-4 small text-secondary">
          <router-link to="/user" class="text-white-50 text-decoration-none hover-white">Driver Portal</router-link>
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
  name: 'LandingPage',
  methods: {
    goToUserPortal() {
      this.$router.push('/user')
    }
  }
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

.tracking-tight {
  letter-spacing: -0.02em;
}

.hero-section {
  background: radial-gradient(circle at 50% 10%, rgba(25, 135, 84, 0.08) 0%, rgba(13, 110, 253, 0.04) 50%, #fafbfc 100%);
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
  background: linear-gradient(135deg, #198754 0%, #0d6efd 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.max-w-760 {
  max-width: 760px;
}

.qr-box {
  width: 54px;
  height: 54px;
}

.step-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.step-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.06);
}

.step-icon-circle {
  width: 50px;
  height: 50px;
  border-radius: 50%;
}

.hover-white:hover {
  color: #ffffff !important;
}
</style>
