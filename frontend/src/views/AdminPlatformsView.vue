<script setup>
import { computed, onMounted, ref } from 'vue'
import AdminModal from '../components/AdminModal.vue'
import AdminPageHeader from '../components/AdminPageHeader.vue'
import PlatformFormFields from '../components/PlatformFormFields.vue'
import {
  adapterConfigFromForm,
  emptyPlatformForm,
  formFromPlatform,
  parseCredentialsJson,
} from '../lib/platformForm'
import { api } from '../api'

const platforms = ref([])
const error = ref('')
const message = ref('')
const form = ref(emptyPlatformForm())
const editingId = ref(null)
const modalOpen = ref(false)
const testResult = ref(null)
const testingId = ref(null)
const testModalOpen = ref(false)

const sortedPlatforms = computed(() =>
  [...platforms.value].sort((a, b) => a.slug.localeCompare(b.slug)),
)

async function load() {
  platforms.value = await api.platforms()
}

function openCreate() {
  editingId.value = null
  form.value = emptyPlatformForm()
  error.value = ''
  message.value = ''
  modalOpen.value = true
}

function openEdit(p) {
  editingId.value = p.id
  form.value = formFromPlatform(p)
  error.value = ''
  message.value = ''
  modalOpen.value = true
}

function closeModal() {
  modalOpen.value = false
  editingId.value = null
}

async function submit() {
  error.value = ''
  message.value = ''
  let credentials
  try {
    credentials = parseCredentialsJson(form.value.credentials_json)
  } catch {
    error.value = 'Credentials harus JSON valid'
    return
  }

  const adapter_config = adapterConfigFromForm(form.value)
  try {
    if (editingId.value) {
      const body = { display_name: form.value.display_name, adapter_config }
      if (credentials !== undefined) body.credentials = credentials
      await api.updatePlatform(editingId.value, body)
      message.value = 'Platform diperbarui.'
    } else {
      const body = {
        slug: form.value.slug,
        display_name: form.value.display_name,
        adapter_type: form.value.adapter_type,
        adapter_config,
      }
      if (credentials !== undefined) body.credentials = credentials
      await api.createPlatform(body)
      message.value = 'Platform ditambahkan.'
    }
    closeModal()
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function removePlatform(p) {
  if (!confirm(`Hapus platform "${p.slug}" dan semua aturannya?`)) return
  error.value = ''
  try {
    await api.deletePlatform(p.id)
    message.value = 'Platform dihapus.'
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function testPlatform(p) {
  testingId.value = p.id
  testResult.value = null
  error.value = ''
  testModalOpen.value = true
  try {
    testResult.value = await api.testPlatform(p.id)
  } catch (e) {
    testResult.value = { error: e.message }
  } finally {
    testingId.value = null
  }
}

onMounted(load)
</script>

<template>
  <div class="admin-page">
    <AdminPageHeader
      title="Platform"
      subtitle="Sumber data untuk monitoring (RSS, YouTube, Meta, dll.). Lihat menu Petunjuk untuk detail adapter."
    >
      <template #actions>
        <button type="button" class="primary" @click="openCreate">+ Tambah platform</button>
      </template>
    </AdminPageHeader>

    <p v-if="message" class="admin-flash ok">{{ message }}</p>
    <p v-if="error && !modalOpen" class="admin-flash error">{{ error }}</p>

    <div class="card admin-table-card">
      <div v-if="!platforms.length" class="empty-state">
        <p>Belum ada platform.</p>
        <button type="button" class="primary" @click="openCreate">Tambah platform pertama</button>
      </div>
      <div v-else class="admin-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Slug</th>
              <th>Nama</th>
              <th>Adapter</th>
              <th>Mode</th>
              <th class="col-actions">Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in sortedPlatforms" :key="p.id">
              <td><code>{{ p.slug }}</code></td>
              <td>{{ p.display_name }}</td>
              <td>{{ p.adapter_type }}</td>
              <td>
                <span v-if="p.adapter_config?.mock" class="badge unknown">mock</span>
                <span v-else class="muted">live</span>
              </td>
              <td class="col-actions">
                <div class="action-group">
                  <button type="button" class="btn-sm" @click="openEdit(p)">Edit</button>
                  <button
                    type="button"
                    class="btn-sm"
                    :disabled="testingId === p.id"
                    @click="testPlatform(p)"
                  >
                    {{ testingId === p.id ? '…' : 'Test' }}
                  </button>
                  <button type="button" class="btn-sm danger" @click="removePlatform(p)">Hapus</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AdminModal
      :open="modalOpen"
      :title="editingId ? 'Edit platform' : 'Tambah platform'"
      wide
      @close="closeModal"
    >
      <form @submit.prevent="submit">
        <PlatformFormFields
          v-model="form"
          :slug-readonly="!!editingId"
          :adapter-readonly="!!editingId"
        />
        <p v-if="error" class="error">{{ error }}</p>
        <div class="form-actions">
          <button class="primary" type="submit">{{ editingId ? 'Simpan' : 'Buat platform' }}</button>
          <button type="button" @click="closeModal">Batal</button>
        </div>
      </form>
    </AdminModal>

    <AdminModal :open="testModalOpen" title="Hasil test koneksi" @close="testModalOpen = false">
      <pre class="test-result">{{ JSON.stringify(testResult, null, 2) }}</pre>
      <div class="form-actions">
        <button type="button" @click="testModalOpen = false">Tutup</button>
      </div>
    </AdminModal>
  </div>
</template>
