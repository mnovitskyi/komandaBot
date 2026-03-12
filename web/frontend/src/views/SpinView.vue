<template>
  <div class="spin-view">
    <div class="container">
      <h1 class="page-title">🎰 Рулетка</h1>
      <p class="page-subtitle">Хто сьогодні <em>{{ selectedTask.label }}</em>?</p>

      <!-- Task Selector -->
      <div class="task-selector">
        <button
          v-for="task in tasks"
          :key="task.value"
          class="task-btn"
          :class="{ active: selectedTask.value === task.value }"
          @click="selectedTask = task; winner = null"
          :disabled="isSpinning"
        >
          {{ task.label }}
        </button>
      </div>

      <!-- Wheel Area -->
      <div class="wheel-area">
        <div class="wheel-wrapper">
          <div class="wheel-pointer">▼</div>
          <canvas
            ref="wheelCanvas"
            class="wheel-canvas"
            :width="wheelSize"
            :height="wheelSize"
          ></canvas>
          <div class="wheel-center-dot"></div>
        </div>

        <div class="spin-controls">
          <button
            class="spin-btn"
            :class="{ spinning: isSpinning }"
            @click="spin"
            :disabled="isSpinning || members.length === 0"
          >
            <span v-if="!isSpinning">КРУТИТИ! 🎯</span>
            <span v-else>Крутиться...</span>
          </button>
          <p v-if="members.length === 0" class="no-members">Завантажте рейтинг спочатку</p>
        </div>
      </div>

      <!-- Winner Display -->
      <transition name="winner-appear">
        <div class="winner-display" v-if="winner">
          <div class="winner-glow"></div>
          <div class="winner-emoji">🎉</div>
          <div class="winner-label">Переможець!</div>
          <div class="winner-name">{{ winner }}</div>
          <div class="winner-task">{{ selectedTask.label }}</div>
          <button class="reset-btn" @click="winner = null">Ще раз 🔄</button>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useTeamStore } from '../stores/team.js'
import confetti from 'canvas-confetti'

const store = useTeamStore()

const wheelCanvas = ref(null)
const winner = ref(null)
const isSpinning = ref(false)
const currentAngle = ref(0)
const wheelSize = 440

const tasks = [
  { value: 'beer', label: 'купує пиво 🍺' },
  { value: 'queue', label: 'перший в черзі 🎮' },
  { value: 'joke', label: 'розповідає анекдот 😂' },
  { value: 'tactic', label: 'тактик сьогодні 🧠' },
]

const selectedTask = ref(tasks[0])

const SLICE_COLORS = [
  '#7c3aed', '#ef4444', '#f0b429', '#22c55e',
  '#3b82f6', '#ec4899', '#f97316', '#06b6d4',
  '#84cc16', '#a855f7', '#14b8a6', '#f59e0b',
]

const members = computed(() => {
  if (store.leaderboard.length > 0) return store.leaderboard
  return []
})

function drawWheel(angle = 0) {
  const canvas = wheelCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const names = members.value.map(m => m.username || 'Анонім')
  if (names.length === 0) {
    ctx.clearRect(0, 0, wheelSize, wheelSize)
    return
  }

  const cx = wheelSize / 2
  const cy = wheelSize / 2
  const radius = wheelSize / 2 - 8
  const sliceAngle = (2 * Math.PI) / names.length

  ctx.clearRect(0, 0, wheelSize, wheelSize)

  // Shadow
  ctx.save()
  ctx.shadowColor = 'rgba(124, 58, 237, 0.4)'
  ctx.shadowBlur = 24
  ctx.beginPath()
  ctx.arc(cx, cy, radius, 0, Math.PI * 2)
  ctx.fillStyle = 'transparent'
  ctx.fill()
  ctx.restore()

  for (let i = 0; i < names.length; i++) {
    const startAngle = angle + i * sliceAngle
    const endAngle = startAngle + sliceAngle

    // Slice fill
    ctx.beginPath()
    ctx.moveTo(cx, cy)
    ctx.arc(cx, cy, radius, startAngle, endAngle)
    ctx.closePath()
    ctx.fillStyle = SLICE_COLORS[i % SLICE_COLORS.length]
    ctx.fill()

    // Slice border
    ctx.strokeStyle = 'rgba(0,0,0,0.4)'
    ctx.lineWidth = 2
    ctx.stroke()

    // Text
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(startAngle + sliceAngle / 2)
    ctx.textAlign = 'right'
    ctx.fillStyle = '#fff'
    ctx.font = `bold ${Math.max(11, Math.min(14, 200 / names.length))}px Segoe UI, system-ui, sans-serif`
    ctx.shadowColor = 'rgba(0,0,0,0.7)'
    ctx.shadowBlur = 4

    const name = names[i].length > 12 ? names[i].slice(0, 11) + '…' : names[i]
    ctx.fillText(name, radius - 12, 5)
    ctx.restore()
  }

  // Center circle
  ctx.beginPath()
  ctx.arc(cx, cy, 20, 0, Math.PI * 2)
  ctx.fillStyle = '#0a0a12'
  ctx.fill()
  ctx.strokeStyle = '#f0b429'
  ctx.lineWidth = 3
  ctx.stroke()
}

function easeOut(t) {
  return 1 - Math.pow(1 - t, 4)
}

function spin() {
  if (isSpinning.value || members.value.length === 0) return
  winner.value = null
  isSpinning.value = true

  const names = members.value.map(m => m.username || 'Анонім')
  const sliceAngle = (2 * Math.PI) / names.length
  const extraSpins = (8 + Math.random() * 5) * Math.PI * 2
  const winnerIndex = Math.floor(Math.random() * names.length)
  // The pointer is at the top (angle = -PI/2). We want winnerIndex slice centered under the pointer.
  const targetAngleOffset = -(winnerIndex * sliceAngle + sliceAngle / 2) - Math.PI / 2
  const totalRotation = extraSpins + targetAngleOffset - (currentAngle.value % (2 * Math.PI))
  const startAngle = currentAngle.value
  const endAngle = startAngle + totalRotation

  const duration = 5000 + Math.random() * 1500
  const startTime = performance.now()

  function frame(now) {
    const elapsed = now - startTime
    const t = Math.min(elapsed / duration, 1)
    const easedT = easeOut(t)
    const angle = startAngle + (endAngle - startAngle) * easedT
    currentAngle.value = angle
    drawWheel(angle)

    if (t < 1) {
      requestAnimationFrame(frame)
    } else {
      currentAngle.value = endAngle
      isSpinning.value = false
      winner.value = names[winnerIndex]
      fireConfetti()
    }
  }

  requestAnimationFrame(frame)
}

function fireConfetti() {
  const duration = 3000
  const end = Date.now() + duration

  const frame = () => {
    confetti({
      particleCount: 3,
      angle: 60,
      spread: 55,
      origin: { x: 0 },
      colors: ['#f0b429', '#7c3aed', '#ef4444', '#22c55e'],
    })
    confetti({
      particleCount: 3,
      angle: 120,
      spread: 55,
      origin: { x: 1 },
      colors: ['#f0b429', '#7c3aed', '#ef4444', '#22c55e'],
    })
    if (Date.now() < end) requestAnimationFrame(frame)
  }
  frame()
}

watch(members, () => {
  nextTick(() => drawWheel(currentAngle.value))
})

onMounted(async () => {
  if (store.leaderboard.length === 0) {
    await store.fetchLeaderboard()
  }
  nextTick(() => drawWheel(currentAngle.value))
})
</script>

<style scoped>
.spin-view {
  padding: 2rem 0;
}

.container {
  max-width: 700px;
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
  margin-bottom: 2rem;
  font-size: 1rem;
}

.page-subtitle em {
  color: var(--primary);
  font-style: normal;
  font-weight: 600;
}

/* Task selector */
.task-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  margin-bottom: 2.5rem;
}

.task-btn {
  padding: 0.5rem 1.1rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--bg2);
  color: var(--text-muted);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.task-btn:hover:not(:disabled) {
  border-color: var(--primary);
  color: var(--text);
}

.task-btn.active {
  background: rgba(240, 180, 41, 0.15);
  border-color: var(--primary);
  color: var(--primary);
  font-weight: 700;
}

.task-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Wheel */
.wheel-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
  margin-bottom: 2rem;
}

.wheel-wrapper {
  position: relative;
  display: inline-block;
}

.wheel-pointer {
  position: absolute;
  top: -4px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 1.75rem;
  color: var(--primary);
  z-index: 10;
  text-shadow: 0 0 12px rgba(240,180,41,0.8);
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.8));
}

.wheel-canvas {
  display: block;
  border-radius: 50%;
  max-width: 100%;
  height: auto;
}

.wheel-center-dot {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 16px;
  height: 16px;
  background: var(--primary);
  border-radius: 50%;
  border: 3px solid #0a0a12;
  box-shadow: 0 0 12px rgba(240,180,41,0.6);
  z-index: 5;
  pointer-events: none;
}

.spin-controls {
  text-align: center;
}

.spin-btn {
  padding: 1rem 3rem;
  font-size: 1.2rem;
  font-weight: 900;
  letter-spacing: 0.05em;
  background: linear-gradient(135deg, var(--primary), #ff9500);
  color: #0a0a12;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s ease;
  text-transform: uppercase;
  box-shadow: 0 4px 20px rgba(240, 180, 41, 0.3);
}

.spin-btn:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 8px 30px rgba(240, 180, 41, 0.5);
}

.spin-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.spin-btn.spinning {
  animation: spinPulse 0.5s ease-in-out infinite alternate;
}

@keyframes spinPulse {
  from { box-shadow: 0 4px 20px rgba(240,180,41,0.3); }
  to { box-shadow: 0 4px 30px rgba(240,180,41,0.7); }
}

.no-members {
  margin-top: 0.75rem;
  font-size: 0.85rem;
  color: var(--text-muted);
}

/* Winner */
.winner-display {
  position: relative;
  background: var(--bg2);
  border: 2px solid var(--primary);
  border-radius: 20px;
  padding: 2.5rem;
  text-align: center;
  overflow: hidden;
  margin-top: 1rem;
}

.winner-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at center, rgba(240,180,41,0.1), transparent 70%);
  pointer-events: none;
}

.winner-emoji {
  font-size: 3rem;
  animation: bounce 1s ease-in-out infinite;
  display: block;
  margin-bottom: 0.5rem;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.winner-label {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.winner-name {
  font-size: 2.5rem;
  font-weight: 900;
  color: var(--primary);
  margin-bottom: 0.5rem;
  text-shadow: 0 0 20px rgba(240,180,41,0.5);
}

.winner-task {
  font-size: 1rem;
  color: var(--text);
  margin-bottom: 1.5rem;
}

.reset-btn {
  padding: 0.6rem 1.5rem;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--text-muted);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.reset-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

/* Winner appear transition */
.winner-appear-enter-active {
  transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.winner-appear-leave-active {
  transition: all 0.3s ease;
}
.winner-appear-enter-from {
  opacity: 0;
  transform: scale(0.7) translateY(20px);
}
.winner-appear-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

@media (max-width: 480px) {
  .wheel-canvas {
    width: 320px;
    height: 320px;
  }
}
</style>
