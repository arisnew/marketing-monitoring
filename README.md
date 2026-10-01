# Marketing Monitoring

Open-source dashboard untuk **memantau aktivitas marketing** di beberapa platform: aturan configurable (jadwal cek, ambang status), histori, dan notifikasi email/webhook.

Cocok untuk tim kecil yang ingin satu layanan ringan di VPS/cloud (**~single container**, SQLite, ARM-friendly).

## Fitur

- **Multi-platform:** RSS, webhook, YouTube, Instagram, Facebook, LinkedIn, TikTok
- **Aturan fleksibel:** frekuensi publish, usia aktivitas terakhir, threshold metrik
- **Role:** admin (konfigurasi) dan viewer (dashboard read-only)
- **Scheduler** terintegrasi + agregat harian untuk trend sederhana
- **UI web** + REST API (OpenAPI)
- **Mock mode** untuk demo tanpa kredensial API
- **Analisa compliance**, export **CSV**, duplikat/hapus aturan, retensi histori otomatis

## Stack singkat

| Komponen | Teknologi |
|----------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy |
| Database | SQLite (WAL) |
| Frontend | Vue 3, Vite |
| Deploy | Docker Compose (amd64 / arm64) |

## Mulai cepat (Docker)

```bash
git clone <repo-url> marketing-monitoring && cd marketing-monitoring
cp .env.example .env
# Edit: SECRET_KEY, MASTER_KEY, BOOTSTRAP_ADMIN_PASSWORD
docker compose -f deploy/docker-compose.yml up --build -d
```

Buka **http://localhost:8000** → login dengan email/password bootstrap dari `.env`.

Generate `MASTER_KEY`:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Dokumentasi

| Dokumen | Untuk |
|---------|--------|
| [**Setup & deployment**](docs/setup.md) | Env, Docker, dev lokal, backup, troubleshooting |
| [**Adapter & kredensial**](docs/adapters.md) | Konfigurasi platform, cara dapat API key/token tiap provider |
| [**Index docs**](docs/README.md) | Daftar dokumentasi publik |

## Struktur repository

```text
backend/          API, scheduler, adapter platform
frontend/         Dashboard Vue
deploy/           Dockerfile & docker-compose
docs/             Dokumentasi pengguna (publik)
scripts/          Backup SQLite, utilitas
z-private-docs/   Dokumen internal tim (gitignored, tidak di-push)
```

## API (ringkas)

| Method | Path | Akses |
|--------|------|--------|
| `POST` | `/api/v1/auth/login/json` | Publik |
| `GET` | `/api/v1/monitors/dashboard` | Viewer+ |
| CRUD | `/api/v1/platforms`, `/api/v1/monitors/rules` | Admin |
| `POST` | `/api/v1/platforms/{id}/test` | Admin |
| `POST` | `/api/v1/monitors/rules/{id}/run` | Admin |
| `GET` | `/api/v1/monitors/analytics/compliance` | Viewer+ |
| `GET` | `/api/v1/monitors/rules/{id}/runs/export` | Viewer+ |
| `GET` | `/api/v1/status` | Viewer+ |

Spesifikasi lengkap: `/docs` (Swagger) saat server jalan.

## Development

```bash
# Backend
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend (DEBUG=true di .env)
cd frontend && npm install && npm run dev
```

## Kontribusi & lisensi

Issue dan pull request welcome. Jangan commit `.env`, database, atau isi `z-private-docs/`.

Lisensi: [MIT](LICENSE).

## Privasi & keamanan

Kredensial platform disimpan **terenkripsi** (Fernet). Gunakan HTTPS di produksi, rotate token provider secara berkala, dan batasi akun admin.
