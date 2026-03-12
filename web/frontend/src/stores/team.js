import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTeamStore = defineStore('team', () => {
  const leaderboard = ref([])
  const weekStats = ref([])
  const cursedStats = ref({})
  const bookings = ref([])
  const loading = ref(false)

  async function fetchLeaderboard() {
    const res = await fetch('/api/leaderboard')
    leaderboard.value = await res.json()
  }

  async function fetchWeekStats() {
    const res = await fetch('/api/stats/week')
    weekStats.value = await res.json()
  }

  async function fetchCursedStats() {
    const res = await fetch('/api/stats/cursed')
    cursedStats.value = await res.json()
  }

  async function fetchBookings() {
    const res = await fetch('/api/bookings')
    bookings.value = await res.json()
  }

  async function fetchAll() {
    loading.value = true
    try {
      await Promise.all([
        fetchLeaderboard(),
        fetchWeekStats(),
        fetchCursedStats(),
        fetchBookings(),
      ])
    } finally {
      loading.value = false
    }
  }

  return {
    leaderboard,
    weekStats,
    cursedStats,
    bookings,
    loading,
    fetchLeaderboard,
    fetchWeekStats,
    fetchCursedStats,
    fetchBookings,
    fetchAll,
  }
})
