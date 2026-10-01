# Setup & deployment

Panduan menjalankan **Marketing Monitoring** sendiri (VPS, cloud, atau laptop). Satu proses API + UI + scheduler; database SQLite.

## Prasyarat

- **Docker** 24+ (disarankan untuk produksi), atau
- **Python 3.12+** dan **Node 20+** (development)
- Port **8000** terbuka (atau sesuaikan di Compose)

## 1. Variabel environment

Salin template:

```bash
cp .env.example .env
```

| Variabel | Wajib | Keterangan |
|----------|-------|------------|
| `SECRET_KEY` | Ya | String acak panjang untuk JWT (min. ~32 karakter) |
| `MASTER_KEY` | Ya | Kunci Fernet untuk enkripsi kredensial platform di DB |
| `DATABASE_URL` | Ya | Lokal: `sqlite:///./data/app.db` — Docker: `sqlite:////data/app.db` |
| `BOOTSTRAP_ADMIN_EMAIL` | Ya* | Email admin pertama (*hanya saat DB kosong) |
| `BOOTSTRAP_ADMIN_PASSWORD` | Ya* | Password admin awal — **ganti setelah login** |
| `SCHEDULER_ENABLED` | Tidak | Default `true` |
| `SCHEDULER_TICK_SECONDS` | Tidak | Default `60` (cek antrian aturan) |
| `DEBUG` | Tidak | `true` = CORS untuk Vite dev (`localhost:5173`) |
| `SMTP_*` | Tidak | Notifikasi email |
| `DEFAULT_NOTIFY_WEBHOOK_URL` | Tidak | Webhook default saat status berubah |
| `META_APP_ID` / `META_APP_SECRET` | Tidak | Refresh token Instagram/Facebook (bisa juga di credentials per platform) |
| `CHECK_RUN_RETENTION_DAYS` | Tidak | Hapus histori cek lebih lama dari N hari (default `90`; job Minggu 03:00 UTC) |

Generate `MASTER_KEY`:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Jangan** commit file `.env` atau kredensial platform ke git.

## 2. Deploy dengan Docker (produksi)

Cocok untuk VPS kecil dan **ARM/Graviton** (image multi-arch).

```bash
docker compose -f deploy/docker-compose.yml up --build -d
```

- UI: http://localhost:8000/
- API OpenAPI: http://localhost:8000/docs
- Data SQLite: volume Docker `deploy_app_data` → `/data/app.db`

Perintah berguna:

```bash
docker compose -f deploy/docker-compose.yml logs -f api
docker compose -f deploy/docker-compose.yml down
docker compose -f deploy/docker-compose.yml up --build -d   # setelah update kode
```

## 3. Development lokal

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
mkdir -p data
export $(grep -v '^#' ../.env | xargs)   # atau set manual
export DATABASE_URL=sqlite:///./data/app.db
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend (hot reload)

```bash
cd frontend
npm install
npm run dev
```

Set `DEBUG=true` di `.env` agar API mengizinkan origin Vite. Proxy API sudah di `frontend/vite.config.js`.

### Build UI ke image API

```bash
cd frontend && npm run build
```

Output ke `backend/app/static/` (disajikan oleh FastAPI).

## 4. Login & peran

| Role | Hak akses |
|------|-----------|
| **admin** | CRUD platform & aturan, jalankan cek, buat user, test adapter |
| **viewer** | Halaman **Monitoring** & **Analisa** (read-only), detail aturan + export CSV |

1. Buka `/login`
2. Email/password = nilai bootstrap (atau user yang dibuat admin)
3. Admin dapat menambah user viewer di **User** — viewer hanya melihat aturan **aktif**, dengan refresh otomatis ~60 detik di Monitoring

## 5. Alur konfigurasi pertama

1. **Platform** — tambah sumber data (RSS, YouTube, Meta, …). Lihat [adapters.md](adapters.md).
2. **Aturan** — tentukan metrik (`publish_frequency`, `last_activity`, …), jadwal cek, ambang OK/warning/critical.
3. **Dashboard** — status per aturan; klik detail untuk histori.
4. **Test koneksi** — di daftar platform (admin), tombol *Test*, atau aktifkan **mock** untuk uji tanpa API.
5. **Analisa** — menu *Analisa* (compliance run OK vs target).
6. **Export CSV** — di detail aturan, unduh histori cek (viewer+).

Mode **mock**: centang saat buat platform → tidak memanggil API eksternal.

## 6. Backup database

```bash
./scripts/backup-sqlite.sh /path/to/app.db ./backups/
```

Di Docker:

```bash
docker compose -f deploy/docker-compose.yml exec api \
  python -c "import shutil; shutil.copy('/data/app.db','/data/app-backup.db')"
# lalu salin dari volume jika perlu
```

## 7. Troubleshooting

| Gejala | Kemungkinan |
|--------|-------------|
| Login gagal | Email/password bootstrap; DB lama di volume → user sudah ada |
| `Invalid token` / crypto error | `MASTER_KEY` berubah setelah kredensial platform disimpan |
| Adapter error 401 | Token kedaluwarsa; isi `expires_at` + refresh token atau test di UI |
| UI kosong setelah deploy | Rebuild image (frontend multi-stage di Dockerfile) |

## 8. Keamanan (checklist singkat)

- Ganti password bootstrap dan `SECRET_KEY` / `MASTER_KEY` di produksi
- HTTPS di reverse proxy (Caddy, nginx, Traefik)
- Batasi akses port admin; viewer cukup untuk stakeholder
- Rotate token platform sesuai kebijakan masing-masing provider
