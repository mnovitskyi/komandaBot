import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LeaderboardView from '../views/LeaderboardView.vue'
import CursedView from '../views/CursedView.vue'
import SpinView from '../views/SpinView.vue'

const routes = [
  { path: '/', component: HomeView },
  { path: '/leaderboard', component: LeaderboardView },
  { path: '/cursed', component: CursedView },
  { path: '/spin', component: SpinView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
