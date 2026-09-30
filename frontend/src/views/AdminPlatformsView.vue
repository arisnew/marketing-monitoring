<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const platforms = ref([])
const error = ref('')
const message = ref('')
const form = ref({
  slug: '',
  display_name: '',
  adapter_type: 'rss',
  feed_url: '',
  channel_id: '',
  ig_user_id: '',
  page_id: '',
  author_urn: '',
  credentials_json: '',
  mock: false,
})

const testResult = ref(null)
const testingId = ref(null)

const adapterTypes = [
  'rss',
  'generic_webhook',
  'youtube',
  'instagram',
  'linkedin',
  'tiktok',
  'facebook',
]

const configHint = computed(() => {
  const t = form.value.adapter_type
  if (t === 'youtube') return 'channel_id (UC…)'
  if (t === 'instagram') return 'ig_user_id dari Meta Graph'
  if (t === 'facebook') return 'page_id halaman Facebook'
  if (t === 'linkedin') return 'author_urn, contoh urn:li:organization:123'
  if (t === 'tiktok') return 'Hanya access_token di credentials'
  if (t === 'generic_webhook') return 'poll_url'
  return 'feed_url'
})

function buildAdapterConfig() {
  const t = form.value.adapter_type
  let cfg = {}
  if (t === 'rss') cfg = { feed_url: form.value.feed_url }
  else if (t === 'generic_webhook') cfg = { poll_url: form.value.feed_url }
  else if (t === 'youtube') cfg = { channel_id: form.value.channel_id }
  else if (t === 'instagram') cfg = { ig_user_id: form.value.ig_user_id }
  else if (t === 'facebook') cfg = { page_id: form.value.page_id }
  else if (t === 'linkedin') cfg = { author_urn: form.value.author_urn }
  if (form.value.mock) cfg.mock = true
  return cfg
}

function parseCredentials() {
  const raw = form.value.credentials_json.trim()
  if (!raw) return null
  return JSON.parse(raw)
}

async function load() {
  platforms.value = await api.platforms()
}

async function submit() {
  error.value = ''
  message.value = ''
  let credentials = null
  try {
    credentials = parseCredentials()
  } catch {
    error.value = 'Credentials harus JSON valid'
    return
  }
  try {
    await api.createPlatform({
      slug: form.value.slug,
      display_name: form.value.display_name,
      adapter_type: form.value.adapter_type,
      adapter_config: buildAdapterConfig(),
      credentials,
    })
    message.value = 'Platform ditambahkan.'
    form.value = {
      slug: '',
      display_name: '',
      adapter_type: 'rss',
      feed_url: '',
      channel_id: '',
      ig_user_id: '',
      page_id: '',
      author_urn: '',
      credentials_json: '',
      mock: false,
    }
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function testPlatform(id) {
  testingId.value = id
  testResult.value = null
  error.value = ''
  try {
    testResult.value = await api.testPlatform(id)
  } catch (e) {
    error.value = e.message
  } finally {
    testingId.value = null
  }
}

onMounted(load)
</script>

<template>
  <div>
    <h1 style="font-size: 1.35rem">Platform</h1>
    <p class="muted">Panduan adapter & kredensial: <code>docs/adapters.md</code></p>
    <div class="grid cols-2">
      <div class="card">
        <h2 style="margin-top: 0; font-size: 1rem">Daftar</h2>
        <ul v-if="platforms.length" style="padding-left: 0; list-style: none">
          <li v-for="p in platforms" :key="p.id" style="margin-bottom: 0.75rem">
            <strong>{{ p.slug }}</strong> — {{ p.display_name }} ({{ p.adapter_type }})
            <span v-if="p.adapter_config?.mock" class="badge unknown">mock</span>
            <button
              type="button"
              style="margin-left: 0.5rem"
              :disabled="testingId === p.id"
              @click="testPlatform(p.id)"
            >
              {{ testingId === p.id ? '…' : 'Test koneksi' }}
            </button>
          </li>
        </ul>
        <pre
          v-if="testResult"
          class="card muted"
          style="margin-top: 1rem; font-size: 0.75rem; overflow: auto"
          >{{ JSON.stringify(testResult, null, 2) }}</pre
        >
        <p v-else class="muted">Kosong.</p>
      </div>
      <div class="card">
        <h2 style="margin-top: 0; font-size: 1rem">Tambah platform</h2>
        <form @submit.prevent="submit">
          <label>Slug</label>
          <input v-model="form.slug" required pattern="[a-z0-9-]+" />
          <label>Nama tampilan</label>
          <input v-model="form.display_name" required />
          <label>Tipe adapter</label>
          <select v-model="form.adapter_type">
            <option v-for="t in adapterTypes" :key="t" :value="t">{{ t }}</option>
          </select>

          <template v-if="form.adapter_type === 'rss' || form.adapter_type === 'generic_webhook'">
            <label>{{ configHint }}</label>
            <input v-model="form.feed_url" type="url" required />
          </template>
          <template v-else-if="form.adapter_type === 'youtube'">
            <label>Channel ID</label>
            <input v-model="form.channel_id" required placeholder="UC…" />
          </template>
          <template v-else-if="form.adapter_type === 'instagram'">
            <label>Instagram user ID</label>
            <input v-model="form.ig_user_id" required />
          </template>
          <template v-else-if="form.adapter_type === 'facebook'">
            <label>Page ID</label>
            <input v-model="form.page_id" required />
          </template>
          <template v-else-if="form.adapter_type === 'linkedin'">
            <label>Author URN</label>
            <input v-model="form.author_urn" required placeholder="urn:li:organization:…" />
          </template>

          <label style="display: flex; align-items: center; gap: 0.5rem; margin-top: 1rem">
            <input v-model="form.mock" type="checkbox" />
            Mode mock (tanpa panggilan API eksternal)
          </label>

          <label>Credentials (JSON, disimpan terenkripsi)</label>
          <textarea
            v-model="form.credentials_json"
            rows="4"
            placeholder='{"access_token":"…"} atau {"api_key":"…"}'
          />
          <p v-if="error" class="error">{{ error }}</p>
          <p v-if="message" class="muted">{{ message }}</p>
          <button class="primary" type="submit" style="margin-top: 1rem">Simpan</button>
        </form>
      </div>
    </div>
  </div>
</template>
