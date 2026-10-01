<script setup>
import { computed } from 'vue'

const form = defineModel({ type: Object, required: true })
const props = defineProps({
  slugReadonly: { type: Boolean, default: false },
  adapterReadonly: { type: Boolean, default: false },
})
const slugReadonly = computed(() => props.slugReadonly)

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
  if (t === 'linkedin') return 'author_urn'
  if (t === 'tiktok') return 'Token di credentials'
  if (t === 'generic_webhook') return 'poll_url'
  return 'feed_url'
})

const credentialsPlaceholder = computed(() =>
  slugReadonly.value
    ? 'Kosongkan jika tidak mengubah credentials'
    : '{"access_token":"…"} atau {"api_key":"…"}'
)
</script>

<template>
  <label>Slug</label>
  <input v-model="form.slug" required pattern="[a-z0-9-]+" :readonly="props.slugReadonly" />

  <label>Nama tampilan</label>
  <input v-model="form.display_name" required />

  <label>Tipe adapter</label>
  <select v-model="form.adapter_type" :disabled="props.adapterReadonly">
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

  <label>Credentials (JSON, terenkripsi)</label>
  <textarea v-model="form.credentials_json" rows="4" :placeholder="credentialsPlaceholder" />
</template>
