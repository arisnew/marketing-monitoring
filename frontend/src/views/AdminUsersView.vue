<script setup>
import { onMounted, ref } from 'vue'
import AdminModal from '../components/AdminModal.vue'
import AdminPageHeader from '../components/AdminPageHeader.vue'
import { api } from '../api'

const users = ref([])
const me = ref(null)
const error = ref('')
const message = ref('')
const modalOpen = ref(false)
const editingId = ref(null)
const form = ref({ email: '', password: '', role: 'viewer', is_active: true })

async function load() {
  ;[users.value, me.value] = await Promise.all([api.users(), api.me()])
}

function openCreate() {
  editingId.value = null
  form.value = { email: '', password: '', role: 'viewer', is_active: true }
  error.value = ''
  modalOpen.value = true
}

function openEdit(u) {
  editingId.value = u.id
  form.value = {
    email: u.email,
    password: '',
    role: u.role,
    is_active: u.is_active,
  }
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
  try {
    if (editingId.value) {
      const body = { role: form.value.role, is_active: form.value.is_active }
      if (form.value.password) body.password = form.value.password
      await api.updateUser(editingId.value, body)
      message.value = `User ${form.value.email} diperbarui.`
    } else {
      await api.createUser({
        email: form.value.email,
        password: form.value.password,
        role: form.value.role,
      })
      message.value = `User ${form.value.email} dibuat.`
    }
    closeModal()
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function toggleActive(u) {
  if (u.id === me.value?.id) {
    error.value = 'Tidak bisa menonaktifkan akun sendiri.'
    return
  }
  error.value = ''
  try {
    await api.updateUser(u.id, { is_active: !u.is_active })
    message.value = u.is_active ? 'User dinonaktifkan.' : 'User diaktifkan.'
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function remove(u) {
  if (u.id === me.value?.id) {
    error.value = 'Tidak bisa menghapus akun sendiri.'
    return
  }
  if (!confirm(`Hapus user ${u.email}?`)) return
  error.value = ''
  try {
    await api.deleteUser(u.id)
    message.value = 'User dihapus.'
    await load()
  } catch (e) {
    error.value = e.message
  }
}

onMounted(load)
</script>

<template>
  <div class="admin-page">
    <AdminPageHeader
      title="Pengguna"
      subtitle="Kelola akses admin dan viewer untuk tim monitoring."
    >
      <template #actions>
        <button type="button" class="primary" @click="openCreate">+ Tambah user</button>
      </template>
    </AdminPageHeader>

    <p v-if="message" class="admin-flash ok">{{ message }}</p>
    <p v-if="error && !modalOpen" class="admin-flash error">{{ error }}</p>

    <div class="card admin-table-card">
      <div v-if="!users.length" class="empty-state">
        <p>Belum ada user terdaftar.</p>
      </div>
      <div v-else class="admin-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th class="col-actions">Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>
                {{ u.email }}
                <span v-if="u.id === me?.id" class="muted table-sub"> (Anda)</span>
              </td>
              <td>
                <span class="badge" :class="u.role === 'admin' ? 'warning' : 'unknown'">{{ u.role }}</span>
              </td>
              <td>
                <span v-if="u.is_active" class="badge ok">aktif</span>
                <span v-else class="badge critical">nonaktif</span>
              </td>
              <td class="col-actions">
                <div class="action-group">
                  <button type="button" class="btn-sm" @click="openEdit(u)">Edit</button>
                  <button
                    type="button"
                    class="btn-sm"
                    :disabled="u.id === me?.id"
                    @click="toggleActive(u)"
                  >
                    {{ u.is_active ? 'Nonaktifkan' : 'Aktifkan' }}
                  </button>
                  <button
                    type="button"
                    class="btn-sm danger"
                    :disabled="u.id === me?.id"
                    @click="remove(u)"
                  >
                    Hapus
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AdminModal
      :open="modalOpen"
      :title="editingId ? 'Edit user' : 'Tambah user'"
      @close="closeModal"
    >
      <form @submit.prevent="submit">
        <template v-if="!editingId">
          <label>Email</label>
          <input v-model="form.email" type="email" required autocomplete="off" />
          <label>Password (min. 8 karakter)</label>
          <input
            v-model="form.password"
            type="password"
            required
            minlength="8"
            autocomplete="new-password"
          />
        </template>
        <template v-else>
          <label>Email</label>
          <input :value="form.email" type="email" disabled />
          <label>Password baru (kosongkan jika tidak diubah)</label>
          <input
            v-model="form.password"
            type="password"
            minlength="8"
            autocomplete="new-password"
          />
        </template>
        <label>Role</label>
        <select v-model="form.role">
          <option value="viewer">viewer — Monitoring & Analisa</option>
          <option value="admin">admin — kelola konfigurasi</option>
        </select>
        <label v-if="editingId" class="toolbar-check">
          <input v-model="form.is_active" type="checkbox" :disabled="editingId === me?.id" />
          Akun aktif (bisa login)
        </label>
        <p v-if="error" class="error">{{ error }}</p>
        <div class="form-actions">
          <button class="primary" type="submit">{{ editingId ? 'Simpan' : 'Buat user' }}</button>
          <button type="button" @click="closeModal">Batal</button>
        </div>
      </form>
    </AdminModal>
  </div>
</template>
