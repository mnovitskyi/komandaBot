<template>
  <nav class="navbar">
    <div class="navbar-inner">
      <router-link to="/" class="logo">
        <span class="logo-emoji">🐔</span>
        <span class="logo-text">Команда Лайна</span>
      </router-link>
      <button class="burger" :class="{ open: menuOpen }" @click="menuOpen = !menuOpen" aria-label="Menu">
        <span></span><span></span><span></span>
      </button>
      <ul class="nav-links" :class="{ open: menuOpen }">
        <li v-for="link in links" :key="link.to">
          <router-link
            :to="link.to"
            class="nav-link"
            :class="{ active: $route.path === link.to }"
            @click="menuOpen = false"
          >
            <span class="nav-icon">{{ link.icon }}</span>
            <span>{{ link.label }}</span>
          </router-link>
        </li>
      </ul>
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue'

const menuOpen = ref(false)

const links = [
  { to: '/', icon: '🏠', label: 'Головна' },
  { to: '/leaderboard', icon: '🏆', label: 'Рейтинг' },
  { to: '/cursed', icon: '😈', label: 'Жесть' },
  { to: '/spin', icon: '🎰', label: 'Рулетка' },
]
</script>

<style scoped>
.navbar {
  background: var(--bg2);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(12px);
}

.navbar-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: var(--primary);
  font-weight: 700;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.logo-emoji {
  font-size: 1.6rem;
  animation: logoFloat 3s ease-in-out infinite;
}

@keyframes logoFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

.logo-text {
  color: var(--text);
}

.nav-links {
  display: flex;
  list-style: none;
  gap: 0.25rem;
  align-items: center;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  text-decoration: none;
  color: var(--text-muted);
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.nav-link:hover {
  color: var(--text);
  background: var(--bg3);
}

.nav-link.active {
  color: var(--primary);
  background: rgba(240, 180, 41, 0.1);
  border: 1px solid rgba(240, 180, 41, 0.25);
}

.nav-icon {
  font-size: 1rem;
}

.burger {
  display: none;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 5px;
  width: 36px;
  height: 36px;
  background: none;
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  padding: 6px;
}

.burger span {
  display: block;
  width: 20px;
  height: 2px;
  background: var(--text);
  border-radius: 2px;
  transition: all 0.3s ease;
  transform-origin: center;
}

.burger.open span:nth-child(1) { transform: translateY(7px) rotate(45deg); }
.burger.open span:nth-child(2) { opacity: 0; }
.burger.open span:nth-child(3) { transform: translateY(-7px) rotate(-45deg); }

@media (max-width: 640px) {
  .burger {
    display: flex;
  }

  .nav-links {
    display: none;
    position: absolute;
    top: 60px;
    left: 0;
    right: 0;
    background: var(--bg2);
    border-bottom: 1px solid var(--border);
    flex-direction: column;
    padding: 0.75rem 1rem;
    gap: 0.25rem;
  }

  .nav-links.open {
    display: flex;
  }

  .nav-link {
    width: 100%;
    padding: 0.75rem 1rem;
  }
}
</style>
