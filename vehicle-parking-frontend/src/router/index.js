import { createRouter, createWebHistory } from 'vue-router'
import LandingPage from '../views/LandingPage.vue'
import AdminView from '../views/AdminView.vue'
import UserView from '../views/UserView.vue'

const routes = [
  { path: '/', component: LandingPage },
  { path: '/admin', component: AdminView },
  { path: '/user', component: UserView },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router