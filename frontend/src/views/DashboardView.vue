<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { api } from '../api'

const items = ref([])
const user = ref(null)
const filterPlatform = ref('')
const filterStatus = ref('')
const showDisabled = ref(false)
const viewMode = ref('cards')
const initialLoad = ref(true)
const refreshing = ref(false)
const error = ref('')
const lastRefresh = ref(null)
let refreshTimer = null

const AUTO_REFRESH_MS = 60_000

const visibleItems = computed(() => {
  let list = items.value
  if (user.value?.role === 'viewer') {
    list = list.filter((i) => i.rule.enabled)
  } else if (!showDisabled.value) {
    list = list.filter((i) => i.rule.enabled)
  }
  return list
})

const platformOptions = computed(() => {
  const set = new Set(visibleItems.value.map((i) => i.platform_slug))
  return [...set].sort()
})

const filtered = computed(() => {
  let list = visibleItems.value
  if (filterPlatform.value) {
    list = list.filter((i) => i.platform_slug === filterPlatform.value)
  }
  if (filterStatus.value) {
    list = list.filter((i) => (i.status?.status || 'unknown') === filterStatus.value)
  }
  return list
})

const summary = computed(() => {
  const counts = { ok: 0, warning: 0, critical: 0, unknown: 0 }
  for (const item of visibleItems.value) {
    const s = item.status?.status || 'unknown'
    if (Object.prototype.hasOwnProperty.call(counts, s)) counts[s] += 1
    else counts.unknown += 1
  }
  return counts
})

const overallHealth = computed(() => {
  if (!visibleItems.value.length) return 'empty'
  if (summary.value.critical > 0) return 'critical'
  if (summary.value.warning > 0) return 'warning'
  if (summary.value.unknown > 0 && summary.value.ok === 0) return 'unknown'
  return 'ok'
})

const healthMessage = computed(() => {
  switch (overallHealth.value) {
    case 'ok':
      return 'Semua aturan dalam status OK.'
    case 'warning':
      return 'Ada aturan perlu perhatian (warning).'
    case 'critical':
      return 'Ada aturan critical — segera ditindaklanjuti.'
    case 'unknown':
      return 'Beberapa aturan belum pernah dicek atau status unknown.'
    default:
      return 'Tidak ada data monitoring.'
  }
})

const grouped = computed(() => {
  const map = new Map()
  for (const item of filtered.value) {
    const key = item.platform_slug
    if (!map.has(key)) {
      map.set(key, {
        slug: key,
        displayName: item.platform_display_name,
        items: [],
      })
    }
    map.get(key).items.push(item)
  }
  return [...map.values()].sort((a, b) => a.slug.localeCompare(b.slug))
})

const isViewer = computed(() => user.value?.role === 'viewer')

function toggleStatusFilter(status) {
  filterStatus.value = filterStatus.value === status ? '' : status
}

function relativeTime(iso) {
  if (!iso) return '—'
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'baru saja'
  if (mins < 60) return `${mins} mnt lalu`
  const hrs = Math.floor(mins / 60)
  if (hrs < 48) return `${hrs} jam lalu`
  return new Date(iso).toLocaleString()
}

async function load(silent = false) {
  if (!silent) refreshing.value = true
  error.value = ''
  try {
    if (!user.value) user.value = await api.me()
    items.value = await api.dashboard()
    lastRefresh.value = new Date()
  } catch (e) {
    error.value = e.message
  } finally {
    initialLoad.value = false
    refreshing.value = false
  }
}

watch(filterStatus, (v) => {
  if (typeof window !== 'undefined') {
    sessionStorage.setItem('mm_filter_status', v)
  }
})

onMounted(() => {
  const saved = sessionStorage.getItem('mm_filter_status')
  if (saved) filterStatus.value = saved
  load(false)
  refreshTimer = setInterval(() => load(true), AUTO_REFRESH_MS)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<template>
  <div class="monitor-dashboard">
    <div class="dashboard-hero">
      <div>
        <h1 class="page-title">
          Monitoring
          <span v-if="refreshing" class="refresh-dot" title="Memperbarui…" />
        </h1>
        <p class="muted hero-sub">
          {{
            isViewer
              ? 'Tampilan untuk stakeholder — hanya aturan aktif, refresh otomatis 60 detik.'
              : 'Status aturan monitor — refresh otomatis setiap 60 detik.'
          }}
        </p>
      </div>
      <div class="hero-actions">
        <select v-model="viewMode" class="toolbar-select" aria-label="Tampilan">
          <option value="cards">Kartu</option>
          <option value="table">Tabel</option>
        </select>
        <button type="button" @click="load(false)" :disabled="refreshing">Refresh</button>
      </div>
    </div>

    <div
      v-if="!initialLoad && visibleItems.length"
      :class="['health-banner', 'health-' + overallHealth]"
      role="status"
    >
      {{ healthMessage }}
    </div>

    <div v-if="!initialLoad && visibleItems.length" class="summary-bar">
      <button
        type="button"
        :class="['summary-chip', 'ok', { active: filterStatus === 'ok' }]"
        @click="toggleStatusFilter('ok')"
      >
        <span class="summary-count">{{ summary.ok }}</span>
        <span class="summary-label">OK</span>
      </button>
      <button
        type="button"
        :class="['summary-chip', 'warning', { active: filterStatus === 'warning' }]"
        @click="toggleStatusFilter('warning')"
      >
        <span class="summary-count">{{ summary.warning }}</span>
        <span class="summary-label">Warning</span>
      </button>
      <button
        type="button"
        :class="['summary-chip', 'critical', { active: filterStatus === 'critical' }]"
        @click="toggleStatusFilter('critical')"
      >
        <span class="summary-count">{{ summary.critical }}</span>
        <span class="summary-label">Critical</span>
      </button>
      <button
        type="button"
        :class="['summary-chip', 'unknown', { active: filterStatus === 'unknown' }]"
        @click="toggleStatusFilter('unknown')"
      >
        <span class="summary-count">{{ summary.unknown }}</span>
        <span class="summary-label">Unknown</span>
      </button>
    </div>

    <div class="dashboard-toolbar">
      <label class="muted toolbar-label">Platform</label>
      <select v-model="filterPlatform" class="toolbar-select">
        <option value="">Semua</option>
        <option v-for="p in platformOptions" :key="p" :value="p">{{ p }}</option>
      </select>

      <label class="muted toolbar-label">Status</label>
      <select v-model="filterStatus" class="toolbar-select">
        <option value="">Semua</option>
        <option value="ok">OK</option>
        <option value="warning">Warning</option>
        <option value="critical">Critical</option>
        <option value="unknown">Unknown</option>
      </select>

      <button v-if="filterPlatform || filterStatus" type="button" class="link-btn" @click="filterPlatform = ''; filterStatus = ''">
        Reset filter
      </button>

      <label v-if="!isViewer" class="toolbar-check muted">
        <input v-model="showDisabled" type="checkbox" />
        Aturan nonaktif
      </label>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-else-if="initialLoad" class="muted">Memuat…</p>
    <p v-else-if="!filtered.length" class="muted empty-state">
      {{
        visibleItems.length
          ? 'Tidak ada aturan untuk filter ini.'
          : isViewer
            ? 'Belum ada aturan aktif untuk ditampilkan.'
            : 'Belum ada aturan. Tambah di menu Aturan (admin).'
      }}
    </p>

    <div v-else-if="viewMode === 'table'" class="card monitor-table-wrap">
      <table class="monitor-table">
        <thead>
          <tr>
            <th>Aturan</th>
            <th>Platform</th>
            <th>Status</th>
            <th>Pesan</th>
            <th>Cek terakhir</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filtered" :key="item.rule.id">
            <td>
              <router-link :to="`/rules/${item.rule.id}`">{{ item.rule.name }}</router-link>
              <div class="muted table-sub">{{ item.rule.monitor_type }}</div>
            </td>
            <td>{{ item.platform_display_name }}</td>
            <td>
              <span :class="['badge', item.status?.status || 'unknown']">
                {{ item.status?.status || 'unknown' }}
              </span>
            </td>
            <td class="table-msg">{{ item.status?.message || '—' }}</td>
            <td class="muted">{{ relativeTime(item.status?.last_check_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <template v-else>
      <section v-for="group in grouped" :key="group.slug" class="platform-group">
        <h2 class="platform-group-title">
          {{ group.displayName }}
          <span class="muted">@{{ group.slug }}</span>
          <span class="muted group-count">({{ group.items.length }})</span>
        </h2>
        <div class="monitor-grid">
          <article
            v-for="item in group.items"
            :key="item.rule.id"
            :class="['monitor-card', 'card', 'status-border-' + (item.status?.status || 'unknown')]"
          >
            <div class="monitor-card-head">
              <router-link :to="`/rules/${item.rule.id}`" class="monitor-title">{{ item.rule.name }}</router-link>
              <span :class="['badge', item.status?.status || 'unknown']">
                {{ item.status?.status || 'unknown' }}
              </span>
            </div>
            <p class="muted monitor-meta">{{ item.rule.monitor_type }}</p>
            <p v-if="item.status?.message" class="monitor-message">{{ item.status.message }}</p>
            <p v-if="item.status?.last_check_at" class="muted monitor-time">
              Cek terakhir: {{ relativeTime(item.status.last_check_at) }}
            </p>
            <p v-if="item.status?.next_run_at" class="muted monitor-time">
              Berikutnya: {{ new Date(item.status.next_run_at).toLocaleString() }}
            </p>
          </article>
        </div>
      </section>
    </template>

    <p v-if="lastRefresh && !initialLoad" class="muted footer-updated">
      Diperbarui: {{ lastRefresh.toLocaleString() }}
      <span v-if="isViewer"> · Mode viewer</span>
    </p>
  </div>
</template>
