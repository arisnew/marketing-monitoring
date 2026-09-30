<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, clearToken, getToken } from './api'

const router = useRouter()
const user = ref(null)

async function loadMe() {
  if (!getToken()) {
    user.value = null
    return
  }
  try {
    user.value = await api.me()
  } catch {
    user.value = null
  }
}

function logout() {
  clearToken()
  user.value = null
  router.push('/login')
}

onMounted(loadMe)
</script>

<template>
  <div class="layout">
    <header v-if="user" class="app-header">
      <div>
        <strong>Marketing Monitoring</strong>
        <nav>
          <router-link to="/">Dashboard</router-link>
          <template v-if="user.role === 'admin'">
            <router-link to="/admin/platforms">Platform</router-link>
            <router-link to="/admin/rules">Aturan</router-link>
            <router-link to="/admin/users">User</router-link>
          </template>
        </nav>
      </div>
      <div class="muted">
        {{ user.email }} ({{ user.role }})
        <button type="button" style="margin-left: 0.75rem" @click="logout">Keluar</button>
      </div>
    </header>
    <router-view @authenticated="loadMe" />
  </div>
</template>
