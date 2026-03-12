<template>
  <div class="cursed-view">
    <div class="container">
      <h1 class="page-title">😈 Жесть-статистика</h1>
      <p class="page-subtitle">Найбільш... своєрідні досягнення команди</p>

      <div v-if="store.loading" class="loading-state">
        <div class="spinner"></div>
        <p>Рахуємо злочини...</p>
      </div>

      <template v-else>
        <!-- Big Cursed Cards -->
        <div class="cursed-grid">
          <div class="cursed-card swear-card" ref="swearCard">
            <div class="card-glow-ring"></div>
            <div class="card-emoji">🤬</div>
            <div class="card-title">Свара-кінг</div>
            <div class="card-username">{{ cursed.swear_king?.username || '???' }}</div>
            <div class="card-big-num">{{ displayedNums.swear_count }}</div>
            <div class="card-sublabel">матюків за весь час</div>
          </div>

          <div class="cursed-card mom-card">
            <div class="card-glow-ring"></div>
            <div class="card-emoji">👩</div>
            <div class="card-title">Мамо-бласт</div>
            <div class="card-username">{{ cursed.mom_insulter?.username || '???' }}</div>
            <div class="card-big-num">{{ displayedNums.mom_count }}</div>
            <div class="card-sublabel">образ матусі</div>
          </div>

          <div class="cursed-card bot-card">
            <div class="card-glow-ring"></div>
            <div class="card-emoji">🤖</div>
            <div class="card-title">Бот-сталкер</div>
            <div class="card-username">{{ cursed.bot_stalker?.username || '???' }}</div>
            <div class="card-big-num">{{ displayedNums.bot_count }}</div>
            <div class="card-sublabel">звернень до бота</div>
          </div>

          <div class="cursed-card owl-card">
            <div class="card-glow-ring"></div>
            <div class="card-emoji">🦉</div>
            <div class="card-title">Нічна сова</div>
            <div class="card-username">{{ cursed.night_owl?.username || '???' }}</div>
            <div class="card-big-num">{{ displayedNums.night_count }}</div>
            <div class="card-sublabel">нічних сесій</div>
          </div>
        </div>

        <!-- Weekly Chatters -->
        <div class="chatters-section">
          <h2 class="section-title">💬 Топ-5 балакунів цього тижня</h2>
          <div class="chatters-list">
            <div
              class="chatter-row"
              v-for="(user, index) in (store.weekStats.slice(0, 5))"
              :key="user.user_id"
              :style="{ animationDelay: index * 0.1 + 's' }"
            >
              <div class="chatter-rank">{{ ['🥇','🥈','🥉','4️⃣','5️⃣'][index] }}</div>
              <div class="chatter-name">{{ user.username || 'Анонім' }}</div>
              <div class="chatter-bar-wrap">
                <div
                  class="chatter-bar"
                  :style="{ width: getBarWidth(user.message_count, store.weekStats) + '%' }"
                ></div>
              </div>
              <div class="chatter-count">{{ user.message_count?.toLocaleString() }}</div>
            </div>
            <div v-if="store.weekStats.length === 0" class="empty-week">
              <span>Тиша в ефірі 😶</span>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive, watch } from 'vue'
import { useTeamStore } from '../stores/team.js'

const store = useTeamStore()

const cursed = computed(() => store.cursedStats || {})

const displayedNums = reactive({
  swear_count: 0,
  mom_count: 0,
  bot_count: 0,
  night_count: 0,
})

function animateCounter(key, target, duration = 1200, delay = 0) {
  setTimeout(() => {
    const start = Date.now()
    const step = () => {
      const elapsed = Date.now() - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      displayedNums[key] = Math.round(target * eased)
      if (progress < 1) requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  }, delay)
}

function getBarWidth(count, list) {
  if (!list || list.length === 0) return 0
  const max = Math.max(...list.slice(0, 5).map(u => u.message_count || 0))
  if (max === 0) return 0
  return Math.round((count / max) * 100)
}

function runAnimations() {
  const stats = store.cursedStats
  if (!stats || Object.keys(stats).length === 0) return
  animateCounter('swear_count', stats.swear_king?.count || 0, 1200, 0)
  animateCounter('mom_count', stats.mom_insulter?.count || 0, 1200, 150)
  animateCounter('bot_count', stats.bot_stalker?.count || 0, 1200, 300)
  animateCounter('night_count', stats.night_owl?.count || 0, 1000, 450)
}

watch(() => store.cursedStats, (val) => {
  if (val && Object.keys(val).length > 0) {
    runAnimations()
  }
})

onMounted(async () => {
  if (!store.cursedStats || Object.keys(store.cursedStats).length === 0) {
    await Promise.all([store.fetchCursedStats(), store.fetchWeekStats()])
  }
  runAnimations()
})
</script>

<style scoped>
.cursed-view {
  padding: 2rem 0;
}

.container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.page-title {
  font-size: 2rem;
  font-weight: 900;
  text-align: center;
  margin-bottom: 0.5rem;
}

.page-subtitle {
  text-align: center;
  color: var(--text-muted);
  margin-bottom: 2.5rem;
}

.loading-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
}

.spinner {
  width: 36px; height: 36px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* Cursed Grid */
.cursed-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1.25rem;
  margin-bottom: 3rem;
}

.cursed-card {
  position: relative;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.75rem 1.25rem;
  text-align: center;
  overflow: hidden;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.cursed-card:hover {
  transform: translateY(-6px);
}

.cursed-card:hover .card-glow-ring {
  opacity: 1;
}

.card-glow-ring {
  position: absolute;
  inset: -1px;
  border-radius: 16px;
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
}

.swear-card { border-color: rgba(239,68,68,0.3); }
.swear-card:hover { box-shadow: 0 12px 40px rgba(239,68,68,0.2); }
.swear-card .card-glow-ring { background: linear-gradient(135deg, rgba(239,68,68,0.15), transparent); }
.swear-card .card-emoji { animation: shake 2s ease-in-out infinite; }
.swear-card .card-big-num { color: var(--accent); }

.mom-card { border-color: rgba(236,72,153,0.3); }
.mom-card:hover { box-shadow: 0 12px 40px rgba(236,72,153,0.2); }
.mom-card .card-glow-ring { background: linear-gradient(135deg, rgba(236,72,153,0.15), transparent); }
.mom-card .card-emoji { animation: pulse 1.5s ease-in-out infinite; }
.mom-card .card-big-num { color: #ec4899; }

.bot-card { border-color: rgba(99,102,241,0.3); }
.bot-card:hover { box-shadow: 0 12px 40px rgba(99,102,241,0.2); }
.bot-card .card-glow-ring { background: linear-gradient(135deg, rgba(99,102,241,0.15), transparent); }
.bot-card .card-emoji { animation: spin-slow 4s linear infinite; }
.bot-card .card-big-num { color: #818cf8; }

.owl-card { border-color: rgba(34,197,94,0.3); }
.owl-card:hover { box-shadow: 0 12px 40px rgba(34,197,94,0.2); }
.owl-card .card-glow-ring { background: linear-gradient(135deg, rgba(34,197,94,0.15), transparent); }
.owl-card .card-emoji { animation: float 3s ease-in-out infinite; }
.owl-card .card-big-num { color: var(--green); }

@keyframes shake {
  0%, 100% { transform: rotate(0); }
  20% { transform: rotate(-5deg); }
  40% { transform: rotate(5deg); }
  60% { transform: rotate(-3deg); }
  80% { transform: rotate(3deg); }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.15); }
}

@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.card-emoji {
  font-size: 3rem;
  display: block;
  margin-bottom: 0.75rem;
}

.card-title {
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.card-username {
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--text);
  margin-bottom: 0.75rem;
}

.card-big-num {
  font-size: 3rem;
  font-weight: 900;
  line-height: 1;
  margin-bottom: 0.5rem;
  font-variant-numeric: tabular-nums;
}

.card-sublabel {
  font-size: 0.78rem;
  color: var(--text-muted);
}

/* Weekly chatters */
.chatters-section {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.5rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 1.25rem;
}

.chatters-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.chatter-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  animation: slideIn 0.4s ease both;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(-15px); }
  to { opacity: 1; transform: translateX(0); }
}

.chatter-rank { font-size: 1.1rem; width: 28px; flex-shrink: 0; }

.chatter-name {
  font-weight: 600;
  font-size: 0.9rem;
  min-width: 100px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chatter-bar-wrap {
  flex: 1;
  height: 10px;
  background: var(--bg3);
  border-radius: 999px;
  overflow: hidden;
}

.chatter-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--secondary), var(--primary));
  border-radius: 999px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.chatter-count {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--primary);
  min-width: 50px;
  text-align: right;
}

.empty-week {
  text-align: center;
  color: var(--text-muted);
  padding: 1rem;
}
</style>
