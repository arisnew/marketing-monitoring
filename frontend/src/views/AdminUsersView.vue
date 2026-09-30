<script setup>
import { ref } from 'vue'
import { api } from '../api'

const error = ref('')
const message = ref('')
const form = ref({ email: '', password: '', role: 'viewer' })

async function submit() {
  error.value = ''
  message.value = ''
  try {
    await api.createUser(form.value)
    message.value = `User ${form.value.email} dibuat.`
    form.value = { email: '', password: '', role: 'viewer' }
  } catch (e) {
    error.value = e.message
  }
}
</script>

<template>
  <div class="card" style="max-width: 480px">
    <h1 style="margin-top: 0; font-size: 1.35rem">Tambah user</h1>
    <form @submit.prevent="submit">
      <label>Email</label>
      <input v-model="form.email" type="email" required />
      <label>Password</label>
      <input v-model="form.password" type="password" required minlength="8" />
      <label>Role</label>
      <select v-model="form.role">
        <option value="viewer">viewer</option>
        <option value="admin">admin</option>
      </select>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="message" class="muted">{{ message }}</p>
      <button class="primary" type="submit" style="margin-top: 1rem">Buat user</button>
    </form>
  </div>
</template>
