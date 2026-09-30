<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const items = ref([])
const filterPlatform = ref('')
const loading = ref(true)
const error = ref('')

const platforms = computed(() => {
  const set = new Set(items.value.map((i) => i.platform_slug))
  return [...set].sort()
})

const filtered = computed(() => {
  if (!filterPlatform.value) return items.value
  return items.value.filter((i) => i.platform_slug === filterPlatform.value)
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = await api.dashboard()
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
    <div style="display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap">
      <h1 style="margin: 0; font-size: 1.35rem">Status monitoring</h1>
      <div>
        <label class="muted" style="display: inline; margin-right: 0.5rem">Platform</label>
        <select v-model="filterPlatform" style="width: auto; min-width: 10rem">
          <option value="">Semua</option>
          <option v-for="p in platforms" :key="p" :value="p">{{ p }}</option>
        </select>
        <button type="button" style="margin-left: 0.5rem" @click="load">Refresh</button>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-else-if="loading" class="muted">Memuat…</p>
    <p v-else-if="!filtered.length" class="muted">Belum ada aturan. Admin dapat menambah di menu Aturan.</p>

    <div v-else class="grid cols-2" style="margin-top: 1rem">
      <article v-for="item in filtered" :key="item.rule.id" class="card">
        <div style="display: flex; justify-content: space-between; align-items: start; gap: 0.5rem">
          <div>
            <router-link :to="`/rules/${item.rule.id}`">{{ item.rule.name }}</router-link>
            <p class="muted" style="margin: 0.25rem 0 0">{{ item.platform_display_name }} · {{ item.rule.monitor_type }}</p>
          </div>
          <span v-if="item.status" :class="['badge', item.status.status]">{{ item.status.status }}</span>
          <span v-else class="badge unknown">unknown</span>
        </div>
        <p v-if="item.status?.message" class="muted" style="margin: 0.75rem 0 0">{{ item.status.message }}</p>
        <p v-if="item.status?.last_check_at" class="muted" style="margin: 0.35rem 0 0">
          Cek terakhir: {{ new Date(item.status.last_check_at).toLocaleString() }}
        </p>
      </article>
    </div>
  </div>
</template>
