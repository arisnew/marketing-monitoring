<script setup>
import { computed, onMounted, ref } from 'vue'
import AdminModal from '../components/AdminModal.vue'
import AdminPageHeader from '../components/AdminPageHeader.vue'
import { api } from '../api'

const platforms = ref([])
const rules = ref([])
const error = ref('')
const message = ref('')
const modalOpen = ref(false)
const editingId = ref(null)

const platformById = computed(() => Object.fromEntries(platforms.value.map((p) => [p.id, p])))

const emptyForm = () => ({
  platform_id: platforms.value[0]?.id || '',
  name: '',
  monitor_type: 'publish_frequency',
  window_days: 7,
  min_count: 3,
  max_age_hours: 48,
  every: '6h',
  enabled: true,
})

const form = ref(emptyForm())

function ruleToForm(r) {
  const every = r.schedule?.every || '6h'
  const base = {
    platform_id: r.platform_id,
    name: r.name,
    monitor_type: r.monitor_type,
    every,
    enabled: r.enabled,
    window_days: r.params?.window_days ?? 7,
    min_count: r.thresholds?.min_count ?? 3,
    max_age_hours: r.thresholds?.max_age_hours ?? 48,
  }
  return base
}

async function load() {
  ;[platforms.value, rules.value] = await Promise.all([api.platforms(), api.rules()])
}

function openCreate() {
  editingId.value = null
  form.value = emptyForm()
  if (!form.value.platform_id && platforms.value[0]) {
    form.value.platform_id = platforms.value[0].id
  }
  error.value = ''
  modalOpen.value = true
}

function openEdit(r) {
  editingId.value = r.id
  form.value = ruleToForm(r)
  error.value = ''
  modalOpen.value = true
}

function closeModal() {
  modalOpen.value = false
  editingId.value = null
}

async function submit() {
  error.value = ''
  message.value = ''
  const params = { window_days: Number(form.value.window_days) }
  const thresholds =
    form.value.monitor_type === 'publish_frequency'
      ? { min_count: Number(form.value.min_count), warning_below: Number(form.value.min_count) + 1 }
      : {
          max_age_hours: Number(form.value.max_age_hours),
          warning_hours: Math.floor(Number(form.value.max_age_hours) / 2),
        }
  const schedule = { kind: 'interval', every: form.value.every }
  try {
    if (editingId.value) {
      await api.updateRule(editingId.value, {
        name: form.value.name,
        params,
        schedule,
        thresholds,
        enabled: form.value.enabled,
      })
      message.value = 'Aturan diperbarui.'
    } else {
      await api.createRule({
        platform_id: form.value.platform_id,
        name: form.value.name,
        monitor_type: form.value.monitor_type,
        params,
        schedule,
        thresholds,
        enabled: form.value.enabled,
      })
      message.value = 'Aturan dibuat.'
    }
    closeModal()
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function toggleEnabled(rule) {
  error.value = ''
  try {
    await api.updateRule(rule.id, { enabled: !rule.enabled })
    message.value = rule.enabled ? 'Aturan dinonaktifkan.' : 'Aturan diaktifkan.'
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function duplicate(rule) {
  error.value = ''
  try {
    await api.duplicateRule(rule.id)
    message.value = 'Aturan diduplikasi (nonaktif).'
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function remove(rule) {
  if (!confirm(`Hapus aturan "${rule.name}" dan semua histori?`)) return
  error.value = ''
  try {
    await api.deleteRule(rule.id)
    message.value = 'Aturan dihapus.'
    await load()
  } catch (e) {
    error.value = e.message
  }
}

function scheduleLabel(r) {
  return r.schedule?.every || '—'
}

onMounted(load)
</script>

<template>
  <div class="admin-page">
    <AdminPageHeader
      title="Aturan monitor"
      subtitle="Metrik, jadwal cek, dan ambang status. Viewer hanya melihat aturan yang aktif."
    >
      <template #actions>
        <button type="button" class="primary" :disabled="!platforms.length" @click="openCreate">
          + Tambah aturan
        </button>
      </template>
    </AdminPageHeader>

    <p v-if="!platforms.length" class="admin-flash warning">
      Buat platform dulu di menu Platform sebelum menambah aturan.
    </p>
    <p v-if="message" class="admin-flash ok">{{ message }}</p>
    <p v-if="error && !modalOpen" class="admin-flash error">{{ error }}</p>

    <div class="card admin-table-card">
      <div v-if="!rules.length" class="empty-state">
        <p>Belum ada aturan.</p>
        <button type="button" class="primary" :disabled="!platforms.length" @click="openCreate">
          Tambah aturan
        </button>
      </div>
      <div v-else class="admin-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Nama</th>
              <th>Platform</th>
              <th>Tipe</th>
              <th>Jadwal</th>
              <th>Status</th>
              <th class="col-actions">Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in rules" :key="r.id">
              <td>
                <router-link :to="`/rules/${r.id}`">{{ r.name }}</router-link>
              </td>
              <td>{{ platformById[r.platform_id]?.display_name || r.platform_id.slice(0, 8) }}</td>
              <td><code>{{ r.monitor_type }}</code></td>
              <td>{{ scheduleLabel(r) }}</td>
              <td>
                <span v-if="r.enabled" class="badge ok">aktif</span>
                <span v-else class="badge unknown">nonaktif</span>
              </td>
              <td class="col-actions">
                <div class="action-group">
                  <button type="button" class="btn-sm" @click="openEdit(r)">Edit</button>
                  <button type="button" class="btn-sm" @click="toggleEnabled(r)">
                    {{ r.enabled ? 'Matikan' : 'Aktifkan' }}
                  </button>
                  <button type="button" class="btn-sm" @click="duplicate(r)">Duplikat</button>
                  <button type="button" class="btn-sm danger" @click="remove(r)">Hapus</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AdminModal
      :open="modalOpen"
      :title="editingId ? 'Edit aturan' : 'Tambah aturan'"
      wide
      @close="closeModal"
    >
      <form @submit.prevent="submit">
        <label>Platform</label>
        <select v-model="form.platform_id" required :disabled="!!editingId">
          <option v-for="p in platforms" :key="p.id" :value="p.id">{{ p.display_name }}</option>
        </select>
        <label>Nama aturan</label>
        <input v-model="form.name" required />
        <label>Tipe monitor</label>
        <select v-model="form.monitor_type" :disabled="!!editingId">
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
        <label class="toolbar-check">
          <input v-model="form.enabled" type="checkbox" />
          Aturan aktif (tampil di Monitoring untuk viewer)
        </label>
        <p v-if="error" class="error">{{ error }}</p>
        <div class="form-actions">
          <button class="primary" type="submit">{{ editingId ? 'Simpan' : 'Buat aturan' }}</button>
          <button type="button" @click="closeModal">Batal</button>
        </div>
      </form>
    </AdminModal>
  </div>
</template>
