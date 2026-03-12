<template>
  <div class="home">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-bg">
        <div class="hero-particle" v-for="n in 20" :key="n" :style="particleStyle(n)"></div>
      </div>
      <div class="hero-content">
        <h1 class="hero-title">🐔 Команда Лайна</h1>
        <p class="hero-subtitle">PUBG &middot; Хаос &middot; Перемога</p>
        <div class="hero-cta">
          <router-link to="/leaderboard" class="btn btn-primary">Рейтинг 🏆</router-link>
          <router-link to="/spin" class="btn btn-secondary">Рулетка 🎰</router-link>
        </div>
      </div>
    </section>

    <!-- Stat Cards -->
    <section class="stats-section">
      <div class="container">
        <div class="stats-grid">
          <div class="stat-card" v-for="stat in statCards" :key="stat.label">
            <div class="stat-card-icon">{{ stat.icon }}</div>
            <div class="stat-card-value counter">{{ formatNumber(displayedValues[stat.key]) }}</div>
            <div class="stat-card-label">{{ stat.label }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Current Bookings -->
    <section class="bookings-section">
      <div class="container">
        <h2 class="section-title">🎮 Поточні бронювання</h2>
        <div v-if="store.loading" class="loading-state">
          <div class="spinner"></div>
          <p>Завантаження...</p>
        </div>
        <div v-else-if="store.bookings.length === 0" class="empty-state">
          <span class="empty-icon">😴</span>
          <p>Немає відкритих сесій</p>
        </div>
        <div v-else class="bookings-grid">
          <div class="booking-card" v-for="session in store.bookings" :key="session.session_id">
            <div class="booking-header">
              <div class="game-info">
                <span class="game-icon">🎮</span>
                <span class="game-name">{{ session.game_name }}</span>
              </div>
              <div class="session-day">{{ formatDay(session.day) }}</div>
            </div>
            <div class="slots-bar">
              <div
                class="slots-fill"
                :style="{ width: (session.confirmed_count / session.max_slots * 100) + '%' }"
                :class="{ full: session.confirmed_count >= session.max_slots }"
              ></div>
            </div>
            <div class="slots-label">
              {{ session.confirmed_count }} / {{ session.max_slots }} слотів
            </div>
            <div class="booking-players" v-if="session.confirmed.length > 0">
              <div class="player-chip" v-for="player in session.confirmed" :key="player.username">
                <span>{{ player.username }}</span>
              </div>
            </div>
            <div class="waitlist" v-if="session.waitlist.length > 0">
              <span class="waitlist-label">Черга: </span>
              <span class="waitlist-names">{{ session.waitlist.map(p => p.username).join(', ') }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Top Members Preview -->
    <section class="top-section" v-if="store.leaderboard.length > 0">
      <div class="container">
        <h2 class="section-title">🌟 Топ гравці</h2>
        <div class="top-grid">
          <MemberCard
            v-for="member in store.leaderboard.slice(0, 3)"
            :key="member.user_id"
            :member="member"
          />
        </div>
        <div class="see-all">
          <router-link to="/leaderboard" class="btn btn-outline">Повний рейтинг →</router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useTeamStore } from '../stores/team.js'
import MemberCard from '../components/MemberCard.vue'

const store = useTeamStore()

const displayedValues = reactive({
  members: 0,
  messages: 0,
})

const statCards = [
  { key: 'members', icon: '👥', label: 'Активних гравців' },
  { key: 'messages', icon: '💬', label: 'Повідомлень цього тижня' },
]

function animateCounter(key, target, duration = 1500) {
  const start = Date.now()
  const startVal = 0
  const step = () => {
    const elapsed = Date.now() - start
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    displayedValues[key] = Math.round(startVal + (target - startVal) * eased)
    if (progress < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

function formatNumber(n) {
  return (n || 0).toLocaleString('uk-UA')
}

function formatDay(day) {
  const map = { saturday: 'Субота', sunday: 'Неділя' }
  return map[day] || day
}

function particleStyle(n) {
  const size = Math.random() * 4 + 2
  return {
    left: (n * 5.3 % 100) + '%',
    top: (n * 7.1 % 100) + '%',
    width: size + 'px',
    height: size + 'px',
    animationDelay: (n * 0.3) + 's',
    animationDuration: (Math.random() * 6 + 4) + 's',
  }
}

onMounted(async () => {
  await store.fetchAll()

  const memberCount = store.leaderboard.length
  const totalMessages = store.weekStats.reduce((s, u) => s + u.message_count, 0)

  animateCounter('members', memberCount)
  animateCounter('messages', totalMessages, 1800)
})
</script>

<style scoped>
.home {
  min-height: 100vh;
}

/* Hero */
.hero {
  position: relative;
  min-height: 480px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: linear-gradient(180deg, #0e0e1f 0%, var(--bg) 100%);
}

.hero-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.hero-particle {
  position: absolute;
  background: var(--secondary);
  border-radius: 50%;
  opacity: 0.3;
  animation: particleDrift linear infinite;
}

@keyframes particleDrift {
  0% { transform: translateY(0) scale(1); opacity: 0.3; }
  50% { opacity: 0.6; }
  100% { transform: translateY(-80px) scale(0.5); opacity: 0; }
}

.hero-content {
  position: relative;
  text-align: center;
  padding: 4rem 1.5rem;
  z-index: 1;
}

.hero-title {
  font-size: clamp(2.5rem, 8vw, 5rem);
  font-weight: 900;
  margin-bottom: 1rem;
  line-height: 1.1;
  position: relative;
}


.hero-subtitle {
  font-size: 1.1rem;
  color: var(--text-muted);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  margin-bottom: 2rem;
}

.hero-cta {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.75rem;
  border-radius: var(--radius);
  font-weight: 600;
  font-size: 0.95rem;
  text-decoration: none;
  transition: all 0.2s ease;
  cursor: pointer;
  border: none;
}

.btn-primary {
  background: var(--primary);
  color: #0a0a12;
}

.btn-primary:hover {
  background: #ffcc50;
  box-shadow: 0 0 20px rgba(240, 180, 41, 0.4);
  transform: translateY(-2px);
}

.btn-secondary {
  background: var(--secondary);
  color: white;
}

.btn-secondary:hover {
  background: #9052ff;
  box-shadow: 0 0 20px rgba(124, 58, 237, 0.4);
  transform: translateY(-2px);
}

.btn-outline {
  background: transparent;
  color: var(--primary);
  border: 1px solid var(--primary);
}

.btn-outline:hover {
  background: rgba(240, 180, 41, 0.1);
  transform: translateY(-2px);
}

/* Sections */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  color: var(--text);
}

/* Stats Grid */
.stats-section {
  padding: 3rem 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
  text-align: center;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--secondary), var(--primary));
}

.stat-card:hover {
  border-color: var(--primary);
  transform: translateY(-3px);
}

.stat-card-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.stat-card-value {
  font-size: 2.2rem;
  font-weight: 900;
  color: var(--primary);
  line-height: 1;
  margin-bottom: 0.5rem;
}

.stat-card-label {
  font-size: 0.85rem;
  color: var(--text-muted);
}

/* Bookings */
.bookings-section {
  padding: 2rem 0;
}

.loading-state, .empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
}

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 0.5rem;
}

.bookings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.booking-card {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.25rem;
}

.booking-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.game-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 700;
}

.game-icon { font-size: 1.2rem; }
.game-name { font-size: 1rem; }

.session-day {
  font-size: 0.8rem;
  color: var(--text-muted);
  background: var(--bg3);
  padding: 3px 10px;
  border-radius: 999px;
}

.slots-bar {
  height: 6px;
  background: var(--bg3);
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 0.4rem;
}

.slots-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--green), #16a34a);
  border-radius: 999px;
  transition: width 0.6s ease;
}

.slots-fill.full {
  background: linear-gradient(90deg, var(--accent), #dc2626);
}

.slots-label {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
}

.booking-players {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.player-chip {
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 0.78rem;
  color: var(--text);
}

.waitlist {
  margin-top: 0.5rem;
  font-size: 0.78rem;
  color: var(--text-muted);
}

.waitlist-label {
  font-weight: 600;
  color: var(--accent);
}

/* Top section */
.top-section {
  padding: 2rem 0 3rem;
}

.top-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.see-all {
  text-align: center;
}
</style>
