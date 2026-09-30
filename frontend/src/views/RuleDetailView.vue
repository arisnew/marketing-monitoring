<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const props = defineProps({ id: String })

const runs = ref([])
const daily = ref([])
const loading = ref(true)
const error = ref('')
const isAdmin = ref(false)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const me = await api.me()
    isAdmin.value = me.role === 'admin'
    ;[runs.value, daily.value] = await Promise.all([
      api.runs(props.id),
      api.dailyMetrics(props.id),
    ])
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function runNow() {
  await api.runCheck(props.id)
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <p><router-link to="/">← Dashboard</router-link></p>
    <h1 style="font-size: 1.25rem">Detail aturan</h1>
    <button v-if="isAdmin" type="button" class="primary" @click="runNow">Jalankan cek sekarang</button>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-else-if="loading" class="muted">Memuat…</p>

    <template v-else>
      <h2 style="font-size: 1rem; margin-top: 1.5rem">Histori cek (50 terakhir)</h2>
      <div class="card" style="overflow-x: auto">
        <table v-if="runs.length">
          <thead>
            <tr>
              <th>Waktu</th>
              <th>Status</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in runs" :key="r.id">
              <td>{{ new Date(r.started_at).toLocaleString() }}</td>
              <td><span :class="['badge', r.status]">{{ r.status }}</span></td>
              <td class="muted">{{ r.error_code || '—' }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else class="muted">Belum ada run.</p>
      </div>

      <h2 style="font-size: 1rem; margin-top: 1.5rem">Agregat harian</h2>
      <div class="card">
        <table v-if="daily.length">
          <thead>
            <tr>
              <th>Hari</th>
              <th>Total run</th>
              <th>Counts</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in daily" :key="d.day">
              <td>{{ new Date(d.day).toLocaleDateString() }}</td>
              <td>{{ d.stats.total_runs ?? '—' }}</td>
              <td class="muted">{{ JSON.stringify(d.stats.counts || {}) }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else class="muted">Belum ada agregat (job harian 01:00 UTC).</p>
      </div>
    </template>
  </div>
</template>
