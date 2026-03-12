<template>
  <div class="member-card" :class="`level-${member.level_num}`">
    <div class="card-glow"></div>
    <div class="card-header">
      <div class="avatar">{{ member.level_emoji || '🥚' }}</div>
      <div class="member-info">
        <div class="username">{{ member.username || 'Анонім' }}</div>
        <div class="level-badge">{{ member.level_name }}</div>
      </div>
      <div class="xp-pill">{{ member.xp?.toLocaleString() }} XP</div>
    </div>
    <div class="card-stats">
      <div class="stat-item">
        <span class="stat-icon">💬</span>
        <span class="stat-val">{{ member.message_count?.toLocaleString() }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-icon">🔥</span>
        <span class="stat-val">{{ member.fire_reactions }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-icon">❤️</span>
        <span class="stat-val">{{ member.heart_reactions }}</span>
      </div>
      <div class="stat-item" v-if="member.mom_insult_count > 0">
        <span class="stat-icon">👩</span>
        <span class="stat-val">{{ member.mom_insult_count }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  member: {
    type: Object,
    required: true,
  },
})
</script>

<style scoped>
.member-card {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
  position: relative;
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
  cursor: pointer;
}

.member-card:hover {
  transform: translateY(-3px);
  border-color: var(--primary);
  box-shadow: 0 8px 24px rgba(240, 180, 41, 0.15);
}

.member-card:hover .card-glow {
  opacity: 1;
}

.card-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at top, rgba(240, 180, 41, 0.06), transparent 70%);
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.avatar {
  font-size: 2rem;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg3);
  border-radius: 50%;
  border: 2px solid var(--border);
  flex-shrink: 0;
}

.member-info {
  flex: 1;
  min-width: 0;
}

.username {
  font-weight: 700;
  font-size: 0.95rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.level-badge {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-top: 2px;
}

.xp-pill {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--primary);
  background: rgba(240, 180, 41, 0.1);
  border: 1px solid rgba(240, 180, 41, 0.3);
  padding: 3px 8px;
  border-radius: 999px;
  white-space: nowrap;
}

.card-stats {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.stat-icon {
  font-size: 0.85rem;
}

.stat-val {
  font-weight: 600;
  color: var(--text);
}
</style>
