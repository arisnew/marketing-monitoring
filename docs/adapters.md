# Adapter platform & kredensial

Setiap **platform** = satu sumber data (adapter). **Aturan monitor** membaca metrik dari platform tersebut.

## Ringkasan adapter

| Adapter | Autentikasi | Monitor yang didukung |
|---------|-------------|------------------------|
| `rss` | Tidak perlu | `publish_frequency`, `last_activity` |
| `generic_webhook` | Opsional header | `publish_frequency`, `custom_webhook`, `metric_threshold` |
| `youtube` | API key atau OAuth | `publish_frequency`, `last_activity`, `metric_threshold`* |
| `instagram` | Meta access token | `publish_frequency`, `last_activity`, `metric_threshold`* |
| `facebook` | Meta Page token | `publish_frequency`, `last_activity` |
| `linkedin` | OAuth access token | `publish_frequency`, `last_activity` |
| `tiktok` | Display API token | `publish_frequency`, `last_activity` |

\* `metric_threshold`: tentukan field numerik di `thresholds`, mis. `{"field": "subscriber_count", "min": 1000}` (YouTube) atau `followers_count` dengan `params.include_profile_metrics: true` (Instagram).

Parameter umum aturan: `params.window_days` (default `7`) — rentang hitung publish.

---

## Mock & uji koneksi

- **`adapter_config.mock`: true** — data contoh, tanpa internet (ideal untuk demo).
- **Test koneksi** (admin UI atau `POST /api/v1/platforms/{id}/test`).

### Refresh token otomatis

- **Instagram / Facebook:** Meta `fb_exchange_token` (butuh `app_id` + `app_secret` di credentials atau env `META_APP_ID`, `META_APP_SECRET`).
- **LinkedIn:** `refresh_token` + client id/secret.
- Dipicu jika `expires_at` ≤ 7 hari, respons HTTP 401/403, atau job harian **02:00 UTC**.

Contoh credentials dengan expiry:

```json
{
  "access_token": "…",
  "expires_at": "2026-12-01T00:00:00+00:00",
  "app_id": "…",
  "app_secret": "…"
}
```

---

## RSS

Tanpa API key. Cocok untuk blog, podcast, atau **feed video YouTube**.

### Konfigurasi

```json
{ "feed_url": "https://example.com/feed.xml" }
```

Feed YouTube (ganti `UC…`):

```text
https://www.youtube.com/feeds/videos.xml?channel_id=UCxxxxxxxx
```

### Cara mendapatkan

1. Buka situs / channel → cari link RSS, atau gunakan URL feed YouTube di atas.
2. Di UI: adapter **rss**, isi URL feed.

---

## Generic webhook

Endpoint **Anda sendiri** yang mengembalikan JSON metrik.

### Konfigurasi

```json
{ "poll_url": "https://your-service.example/metrics/brand-a" }
```

Credentials (opsional):

```json
{ "headers": { "Authorization": "Bearer YOUR_SECRET" } }
```

### Respons yang didukung

```json
{
  "metrics": {
    "publish_count_in_window": 5,
    "followers_count": 1200
  }
}
```

---

## YouTube

Menggunakan **YouTube Data API v3** (quota harian — jadwalkan cek ≥ 6 jam).

### Konfigurasi

```json
{ "channel_id": "UCxxxxxxxxxxxxxxxx" }
```

Credentials (**salah satu**):

```json
{ "api_key": "AIzaSy…" }
```

```json
{ "access_token": "ya29…" }
```

### Cara mendapatkan Channel ID

1. Buka channel YouTube → URL `youtube.com/channel/UC…`.
2. ID selalu diawali `UC`.

### Cara mendapatkan API key

1. [Google Cloud Console](https://console.cloud.google.com/) → buat/pilih proyek.
2. Aktifkan **YouTube Data API v3**.
3. **Credentials** → **API key**; restrict ke YouTube Data API + IP server (opsional).
4. Simpan sebagai `api_key` di credentials platform.

Alternatif tanpa API key: adapter **rss** + feed channel YouTube.

---

## Instagram (Meta Graph API)

Akun **Instagram Business/Creator** terhubung ke **Facebook Page**.

### Konfigurasi

```json
{ "ig_user_id": "17841400000000000" }
```

Credentials:

```json
{ "access_token": "EAA…" }
```

### Cara mendapatkan ID & token

1. [Meta for Developers](https://developers.facebook.com/) → App Business → **Instagram Graph API**.
2. Hubungkan Page ke akun IG Business.
3. Graph API Explorer: permission `instagram_basic`, `pages_read_engagement`, `pages_show_list`.
4. `GET /me/accounts` → `GET /{page-id}?fields=instagram_business_account` → ambil `ig_user_id`.
5. Gunakan **Page access token** long-lived.

Dokumentasi: [IG User Media](https://developers.facebook.com/docs/instagram-api/reference/ig-user/media)

---

## Facebook Page

### Konfigurasi

```json
{ "page_id": "123456789012345" }
```

Credentials:

```json
{ "access_token": "EAA…" }
```

### Cara mendapatkan

1. Meta Developer App → `GET /me/accounts` → `page_id` + page access token.
2. Permission: `pages_read_engagement`, `pages_show_list`.

---

## LinkedIn

### Konfigurasi

```json
{
  "author_urn": "urn:li:organization:12345678",
  "linkedin_version": "202401"
}
```

Credentials:

```json
{
  "access_token": "AQV…",
  "refresh_token": "…",
  "client_id": "…",
  "client_secret": "…",
  "expires_at": "2026-12-01T00:00:00+00:00"
}
```

### Cara mendapatkan

1. [LinkedIn Developers](https://www.linkedin.com/developers/apps) → buat app, associate Company Page.
2. Request produk API posting organisasi; OAuth scope `r_organization_social`.
3. Author URN: `urn:li:organization:{id}`.

---

## TikTok

### Credentials

```json
{ "access_token": "act.example…" }
```

### Cara mendapatkan

1. [TikTok for Developers](https://developers.tiktok.com/) → buat app, Display API.
2. OAuth user dengan scope **`video.list`**.
3. Simpan `access_token`.

---

## Contoh aturan

```json
{
  "monitor_type": "publish_frequency",
  "params": { "window_days": 7 },
  "thresholds": { "min_count": 3, "warning_below": 4 },
  "schedule": { "kind": "interval", "every": "12h" }
}
```

```json
{
  "monitor_type": "last_activity",
  "params": { "window_days": 7 },
  "thresholds": { "max_age_hours": 48, "warning_hours": 24 }
}
```
