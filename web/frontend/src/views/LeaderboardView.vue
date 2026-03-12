<template>
  <div class="leaderboard-view">
    <div class="container">
      <h1 class="page-title">🏆 Рейтинг</h1>

      <div v-if="store.loading" class="loading-state">
        <div class="spinner"></div>
        <p>Завантаження рейтингу...</p>
      </div>

      <template v-else-if="store.leaderboard.length > 0">
        <!-- Podium Top 3 -->
        <div class="podium" v-if="store.leaderboard.length >= 3">
          <div class="podium-item podium-2" @click="toggleExpand(store.leaderboard[1].user_id)">
            <div class="podium-medal">🥈</div>
            <div class="podium-avatar">{{ store.leaderboard[1].level_emoji }}</div>
            <div class="podium-username">{{ store.leaderboard[1].username }}</div>
            <div class="podium-xp">{{ store.leaderboard[1].xp?.toLocaleString() }} XP</div>
            <div class="podium-level">{{ store.leaderboard[1].level_name }}</div>
            <div class="podium-block h-2"></div>
          </div>
          <div class="podium-item podium-1" @click="toggleExpand(store.leaderboard[0].user_id)">
            <div class="podium-crown">👑</div>
            <div class="podium-medal">🥇</div>
            <div class="podium-avatar large">{{ store.leaderboard[0].level_emoji }}</div>
            <div class="podium-username">{{ store.leaderboard[0].username }}</div>
            <div class="podium-xp gold">{{ store.leaderboard[0].xp?.toLocaleString() }} XP</div>
            <div class="podium-level">{{ store.leaderboard[0].level_name }}</div>
            <div class="podium-block h-1"></div>
          </div>
          <div class="podium-item podium-3" @click="toggleExpand(store.leaderboard[2].user_id)">
            <div class="podium-medal">🥉</div>
            <div class="podium-avatar">{{ store.leaderboard[2].level_emoji }}</div>
            <div class="podium-username">{{ store.leaderboard[2].username }}</div>
            <div class="podium-xp">{{ store.leaderboard[2].xp?.toLocaleString() }} XP</div>
            <div class="podium-level">{{ store.leaderboard[2].level_name }}</div>
            <div class="podium-block h-3"></div>
          </div>
        </div>

        <!-- Full List -->
        <div class="leaderboard-list">
          <div
            class="lb-row"
            v-for="(member, index) in store.leaderboard"
            :key="member.user_id"
            :class="{ expanded: expandedId === member.user_id, 'top-3': index < 3 }"
            :style="{ animationDelay: index * 0.05 + 's' }"
            @click="toggleExpand(member.user_id)"
          >
            <div class="lb-main">
              <div class="lb-rank" :class="rankClass(index)">
                <span v-if="index === 0">🥇</span>
                <span v-else-if="index === 1">🥈</span>
                <span v-else-if="index === 2">🥉</span>
                <span v-else>#{{ index + 1 }}</span>
              </div>
              <div class="lb-avatar">{{ member.level_emoji }}</div>
              <div class="lb-info">
                <div class="lb-username">{{ member.username || 'Анонім' }}</div>
                <div class="lb-xpbar">
                  <XPBar
                    :xp="member.xp"
                    :progress="member.progress"
                    :level_name="member.level_name"
                    :xp_to_next="member.xp_to_next"
                    :is_max="member.is_max"
                  />
                </div>
              </div>
              <div class="lb-xp">{{ member.xp?.toLocaleString() }}</div>
              <div class="lb-expand-icon">{{ expandedId === member.user_id ? '▲' : '▼' }}</div>
            </div>

            <transition name="expand">
              <div class="lb-details" v-if="expandedId === member.user_id">
                <div class="details-grid">
                  <div class="detail-item">
                    <span class="detail-icon">💬</span>
                    <span class="detail-label">Повідомлень</span>
                    <span class="detail-val">{{ member.message_count?.toLocaleString() }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-icon">🔥</span>
                    <span class="detail-label">Вогні</span>
                    <span class="detail-val">{{ member.fire_reactions }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-icon">❤️</span>
                    <span class="detail-label">Серця</span>
                    <span class="detail-val">{{ member.heart_reactions }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-icon">👩</span>
                    <span class="detail-label">Мама-інсулти</span>
                    <span class="detail-val">{{ member.mom_insult_count }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-icon">🤖</span>
                    <span class="detail-label">Бот-згадки</span>
                    <span class="detail-val">{{ (member.bot_mentions || 0) + (member.bot_replies || 0) }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-icon">📝</span>
                    <span class="detail-label">Символів</span>
                    <span class="detail-val">{{ member.total_chars?.toLocaleString() }}</span>
                  </div>
                </div>
              </div>
            </transition>
          </div>
        </div>
      </template>

      <div v-else class="empty-state">
        <span class="empty-icon">😴</span>
        <p>Поки що немає даних</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useTeamStore } from '../stores/team.js'
import XPBar from '../components/XPBar.vue'

const store = useTeamStore()
const expandedId = ref(null)

function toggleExpand(userId) {
  expandedId.value = expandedId.value === userId ? null : userId
}

function rankClass(index) {
  if (index === 0) return 'rank-gold'
  if (index === 1) return 'rank-silver'
  if (index === 2) return 'rank-bronze'
  return ''
}

onMounted(async () => {
  if (store.leaderboard.length === 0) {
    await store.fetchLeaderboard()
  }
})
</script>

<style scoped>
.leaderboard-view {
  padding: 2rem 0;
}

.container {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.page-title {
  font-size: 2rem;
  font-weight: 900;
  margin-bottom: 2rem;
  text-align: center;
}

/* Loading / Empty */
.loading-state, .empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
}
.spinner {
  width: 36px; height: 36px;
  border: 3px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}
@keyframes spin { to { transform: rotate(360deg); } }
.empty-icon { font-size: 3rem; display: block; margin-bottom: 0.5rem; }

/* Podium */
.podium {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 3rem;
  padding: 0 1rem;
}

.podium-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: transform 0.2s ease;
  flex: 1;
  max-width: 200px;
}

.podium-item:hover { transform: translateY(-5px); }

.podium-crown {
  font-size: 1.5rem;
  animation: bounce 1.5s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

.podium-medal { font-size: 1.6rem; margin-bottom: 0.25rem; }

.podium-avatar {
  font-size: 2rem;
  width: 52px; height: 52px;
  background: var(--bg3);
  border: 2px solid var(--border);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 0.5rem;
}

.podium-avatar.large {
  font-size: 2.5rem;
  width: 64px; height: 64px;
  border-color: var(--primary);
  box-shadow: 0 0 20px rgba(240, 180, 41, 0.3);
}

.podium-username {
  font-weight: 700;
  font-size: 0.9rem;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

.podium-xp {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-weight: 600;
}

.podium-xp.gold { color: var(--primary); }

.podium-level {
  font-size: 0.7rem;
  color: var(--text-muted);
  text-align: center;
  margin-bottom: 0.5rem;
}

.podium-block {
  width: 100%;
  border-radius: 8px 8px 0 0;
}

.h-1 { height: 80px; background: linear-gradient(180deg, rgba(240,180,41,0.3), rgba(240,180,41,0.1)); border: 1px solid rgba(240,180,41,0.4); }
.h-2 { height: 56px; background: linear-gradient(180deg, rgba(148,163,184,0.3), rgba(148,163,184,0.1)); border: 1px solid rgba(148,163,184,0.3); }
.h-3 { height: 40px; background: linear-gradient(180deg, rgba(205,127,50,0.3), rgba(205,127,50,0.1)); border: 1px solid rgba(205,127,50,0.3); }

/* List */
.leaderboard-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.lb-row {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  animation: slideIn 0.4s ease both;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(-20px); }
  to { opacity: 1; transform: translateX(0); }
}

.lb-row:hover, .lb-row.expanded {
  border-color: var(--secondary);
  box-shadow: 0 2px 12px rgba(124, 58, 237, 0.15);
}

.lb-row.top-3 {
  border-color: rgba(240,180,41,0.3);
}

.lb-main {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.875rem 1rem;
}

.lb-rank {
  font-size: 0.9rem;
  font-weight: 700;
  min-width: 36px;
  text-align: center;
  color: var(--text-muted);
}

.rank-gold { color: #ffd700; }
.rank-silver { color: #c0c0c0; }
.rank-bronze { color: #cd7f32; }

.lb-avatar {
  font-size: 1.6rem;
  width: 40px; height: 40px;
  background: var(--bg3);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.lb-info {
  flex: 1;
  min-width: 0;
}

.lb-username {
  font-weight: 700;
  font-size: 0.95rem;
  margin-bottom: 0.35rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.lb-xpbar {
  max-width: 360px;
}

.lb-xp {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--primary);
  white-space: nowrap;
  min-width: 70px;
  text-align: right;
}

.lb-expand-icon {
  font-size: 0.7rem;
  color: var(--text-muted);
  flex-shrink: 0;
}

/* Details */
.lb-details {
  padding: 1rem;
  border-top: 1px solid var(--border);
  background: var(--bg3);
}

.details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 0.75rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.6rem;
  text-align: center;
}

.detail-icon { font-size: 1.2rem; }
.detail-label { font-size: 0.7rem; color: var(--text-muted); }
.detail-val { font-size: 1rem; font-weight: 700; color: var(--primary); }

/* Expand transition */
.expand-enter-active, .expand-leave-active {
  transition: all 0.25s ease;
  max-height: 300px;
  overflow: hidden;
}

.expand-enter-from, .expand-leave-to {
  max-height: 0;
  opacity: 0;
}

@media (max-width: 600px) {
  .lb-xpbar { display: none; }
  .podium { gap: 0.5rem; }
}
</style>
