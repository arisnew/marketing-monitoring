<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const platforms = ref([])
const rules = ref([])
const error = ref('')
const message = ref('')
const form = ref({
  platform_id: '',
  name: '',
  monitor_type: 'publish_frequency',
  window_days: 7,
  min_count: 3,
  max_age_hours: 48,
  every: '6h',
})

async function load() {
  ;[platforms.value, rules.value] = await Promise.all([api.platforms(), api.rules()])
  if (!form.value.platform_id && platforms.value[0]) {
    form.value.platform_id = platforms.value[0].id
  }
}

async function submit() {
  error.value = ''
  message.value = ''
  const params =
    form.value.monitor_type === 'publish_frequency'
      ? { window_days: Number(form.value.window_days) }
      : { window_days: Number(form.value.window_days) }
  const thresholds =
    form.value.monitor_type === 'publish_frequency'
      ? { min_count: Number(form.value.min_count), warning_below: Number(form.value.min_count) + 1 }
      : { max_age_hours: Number(form.value.max_age_hours), warning_hours: Math.floor(form.value.max_age_hours / 2) }
  try {
    await api.createRule({
      platform_id: form.value.platform_id,
      name: form.value.name,
      monitor_type: form.value.monitor_type,
      params,
      schedule: { kind: 'interval', every: form.value.every },
      thresholds,
      enabled: true,
    })
    message.value = 'Aturan dibuat.'
    form.value.name = ''
    await load()
  } catch (e) {
    error.value = e.message
  }
}

onMounted(load)
</script>

<template>
  <div>
    <h1 style="font-size: 1.35rem">Aturan monitor</h1>
    <div class="grid cols-2">
      <div class="card">
        <h2 style="margin-top: 0; font-size: 1rem">Daftar</h2>
        <ul v-if="rules.length" style="padding-left: 1.2rem">
          <li v-for="r in rules" :key="r.id">
            <router-link :to="`/rules/${r.id}`">{{ r.name }}</router-link>
            — {{ r.monitor_type }}
          </li>
        </ul>
        <p v-else class="muted">Kosong.</p>
      </div>
      <div class="card">
        <h2 style="margin-top: 0; font-size: 1rem">Tambah aturan</h2>
        <form @submit.prevent="submit">
          <label>Platform</label>
          <select v-model="form.platform_id" required>
            <option v-for="p in platforms" :key="p.id" :value="p.id">{{ p.display_name }}</option>
          </select>
          <label>Nama</label>
          <input v-model="form.name" required />
          <label>Tipe monitor</label>
          <select v-model="form.monitor_type">
            <option value="publish_frequency">publish_frequency</option>
            <option value="last_activity">last_activity</option>
          </select>
          <label>Interval cek (contoh 6h, 30m)</label>
          <input v-model="form.every" required />
          <template v-if="form.monitor_type === 'publish_frequency'">
            <label>Window (hari)</label>
            <input v-model.number="form.window_days" type="number" min="1" />
            <label>Min publish count</label>
            <input v-model.number="form.min_count" type="number" min="0" />
          </template>
          <template v-else>
            <label>Max usia aktivitas (jam)</label>
            <input v-model.number="form.max_age_hours" type="number" min="1" />
          </template>
          <p v-if="error" class="error">{{ error }}</p>
          <p v-if="message" class="muted">{{ message }}</p>
          <button class="primary" type="submit" style="margin-top: 1rem" :disabled="!platforms.length">Simpan</button>
        </form>
      </div>
    </div>
  </div>
</template>
