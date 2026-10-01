export const ADAPTER_TYPES = [
  'rss',
  'generic_webhook',
  'youtube',
  'instagram',
  'linkedin',
  'tiktok',
  'facebook',
]

export function emptyPlatformForm() {
  return {
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
}

export function adapterConfigFromForm(form) {
  const t = form.adapter_type
  let cfg = {}
  if (t === 'rss') cfg = { feed_url: form.feed_url }
  else if (t === 'generic_webhook') cfg = { poll_url: form.feed_url }
  else if (t === 'youtube') cfg = { channel_id: form.channel_id }
  else if (t === 'instagram') cfg = { ig_user_id: form.ig_user_id }
  else if (t === 'facebook') cfg = { page_id: form.page_id }
  else if (t === 'linkedin') cfg = { author_urn: form.author_urn }
  if (form.mock) cfg.mock = true
  return cfg
}

export function formFromPlatform(platform) {
  const c = platform.adapter_config || {}
  return {
    slug: platform.slug,
    display_name: platform.display_name,
    adapter_type: platform.adapter_type,
    feed_url: c.feed_url || c.poll_url || '',
    channel_id: c.channel_id || '',
    ig_user_id: c.ig_user_id || '',
    page_id: c.page_id || '',
    author_urn: c.author_urn || '',
    credentials_json: '',
    mock: !!c.mock,
  }
}

export function parseCredentialsJson(raw) {
  const text = raw.trim()
  if (!text) return undefined
  return JSON.parse(text)
}
