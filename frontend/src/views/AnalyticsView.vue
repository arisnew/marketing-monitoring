<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const rows = ref([])
const windowDays = ref(7)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    rows.value = await api.compliance(windowDays.value)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem">
      <h1 style="margin: 0; font-size: 1.35rem">Analisa compliance</h1>
      <div>
        <label class="muted" style="display: inline; margin-right: 0.5rem">Window (hari)</label>
        <select v-model.number="windowDays" style="width: auto" @change="load">
          <option :value="7">7</option>
          <option :value="14">14</option>
          <option :value="30">30</option>
        </select>
        <button type="button" style="margin-left: 0.5rem" @click="load">Refresh</button>
      </div>
    </div>
    <p class="muted" style="margin-top: 0.5rem">
      Persentase run berstatus OK + indikator target publish/aktivitas terakhir.
    </p>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-else-if="loading" class="muted">Memuat…</p>

    <div v-else class="card" style="margin-top: 1rem; overflow-x: auto">
      <table v-if="rows.length">
        <thead>
          <tr>
            <th>Aturan</th>
            <th>Platform</th>
            <th>Status</th>
            <th>Run OK / total</th>
            <th>Compliance</th>
            <th>Target</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r.rule_id">
            <td>
              <router-link :to="`/rules/${r.rule_id}`">{{ r.rule_name }}</router-link>
            </td>
            <td>{{ r.platform_slug }}</td>
            <td><span :class="['badge', r.current_status]">{{ r.current_status }}</span></td>
            <td>{{ r.runs_ok }} / {{ r.runs_total }}</td>
            <td>{{ r.compliance_pct != null ? `${r.compliance_pct}%` : '—' }}</td>
            <td class="muted">
              <span v-if="r.target_met === true">✓ {{ r.target_detail }}</span>
              <span v-else-if="r.target_met === false">✗ {{ r.target_detail }}</span>
              <span v-else>—</span>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="muted">Belum ada aturan aktif.</p>
    </div>
  </div>
</template>
