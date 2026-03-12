<template>
  <div class="xpbar">
    <div class="xpbar-header">
      <span class="level-name">{{ level_name }}</span>
      <span v-if="is_max" class="max-badge">MAX</span>
      <span v-else class="xp-label">{{ xp_to_next }} XP до наступного</span>
    </div>
    <div class="xpbar-track">
      <div
        class="xpbar-fill"
        :style="{ width: animatedWidth + '%' }"
      ></div>
    </div>
    <div class="xpbar-footer">
      <span class="xp-total">{{ xp.toLocaleString() }} XP</span>
      <span class="xp-percent">{{ progress }}%</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  xp: { type: Number, default: 0 },
  progress: { type: Number, default: 0 },
  level_name: { type: String, default: '' },
  xp_to_next: { type: Number, default: 0 },
  is_max: { type: Boolean, default: false },
})

const animatedWidth = ref(0)

onMounted(() => {
  requestAnimationFrame(() => {
    setTimeout(() => {
      animatedWidth.value = props.progress
    }, 100)
  })
})
</script>

<style scoped>
.xpbar {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.xpbar-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.level-name {
  font-size: 0.85rem;
  color: var(--primary);
  font-weight: 600;
}

.max-badge {
  font-size: 0.65rem;
  font-weight: 700;
  color: #0a0a12;
  background: var(--primary);
  padding: 2px 6px;
  border-radius: 4px;
  letter-spacing: 0.05em;
}

.xp-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-left: auto;
}

.xpbar-track {
  height: 8px;
  background: var(--bg3);
  border-radius: 999px;
  overflow: hidden;
  border: 1px solid var(--border);
}

.xpbar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), #ff9500);
  border-radius: 999px;
  transition: width 0.9s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 8px rgba(240, 180, 41, 0.5);
  position: relative;
}

.xpbar-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  animation: shimmer 2s ease-in-out infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.xpbar-footer {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.xp-total {
  font-weight: 600;
  color: var(--text);
}
</style>
