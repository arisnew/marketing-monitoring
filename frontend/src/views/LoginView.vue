<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, setToken } from '../api'

const emit = defineEmits(['authenticated'])
const router = useRouter()
const email = ref('admin@example.com')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const { access_token } = await api.login(email.value, password.value)
    setToken(access_token)
    emit('authenticated')
    router.push('/')
  } catch (e) {
    error.value = e.message || 'Login gagal'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="card" style="max-width: 400px; margin: 4rem auto">
    <h1 style="margin-top: 0; font-size: 1.35rem">Masuk</h1>
    <form @submit.prevent="submit">
      <label>Email</label>
      <input v-model="email" type="email" required autocomplete="username" />
      <label>Password</label>
      <input v-model="password" type="password" required autocomplete="current-password" />
      <p v-if="error" class="error">{{ error }}</p>
      <button class="primary" type="submit" :disabled="loading" style="margin-top: 1rem; width: 100%">
        {{ loading ? '…' : 'Login' }}
      </button>
    </form>
  </div>
</template>
