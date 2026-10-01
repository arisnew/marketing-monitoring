<script setup>
import AdminPageHeader from '../components/AdminPageHeader.vue'
</script>

<template>
  <div class="admin-page admin-guide">
    <AdminPageHeader
      title="Petunjuk penggunaan"
      subtitle="Cara mengatur monitoring lewat menu web — tanpa perlu akses server atau kode."
    />

    <div class="guide-grid">
      <section class="card guide-section guide-intro">
        <h2>Urutan yang disarankan</h2>
        <ol class="guide-steps">
          <li>Login sebagai <strong>admin</strong> → menu <router-link to="/admin/platforms">Platform</router-link>.</li>
          <li>Tambah platform (sumber data) → tombol <strong>Test</strong> untuk cek koneksi.</li>
          <li>Menu <router-link to="/admin/rules">Aturan</router-link> → buat aturan per platform, aktifkan jika siap dipantau.</li>
          <li>Menu <router-link to="/">Monitoring</router-link> → lihat status; klik nama aturan untuk detail dan cek manual.</li>
          <li>Menu <router-link to="/analytics">Analisa</router-link> → ringkasan kepatuhan target.</li>
          <li>Untuk stakeholder: menu <router-link to="/admin/users">User</router-link> → buat akun <strong>viewer</strong>.</li>
        </ol>
      </section>

      <section class="card guide-section">
        <h2>Menu Platform</h2>
        <ul class="guide-list">
          <li><strong>+ Tambah platform</strong> — isi slug (unik), nama tampilan, jenis adapter, dan konfigurasi di form.</li>
          <li><strong>Mock</strong> — centang jika ingin uji alur tanpa memanggil API eksternal (data contoh).</li>
          <li><strong>Credentials</strong> — JSON token/kunci sesuai adapter; saat edit, kosongkan field jika tidak ingin mengubah kredensial.</li>
          <li><strong>Edit</strong> — ubah nama atau konfigurasi; slug dan jenis adapter tidak bisa diubah setelah dibuat.</li>
          <li><strong>Test</strong> — hasil muncul di jendela; gunakan untuk validasi sebelum membuat aturan.</li>
          <li><strong>Hapus</strong> — menghapus platform sekaligus semua aturan terkait.</li>
        </ul>
      </section>

      <section class="card guide-section">
        <h2>Menu Aturan</h2>
        <ul class="guide-list">
          <li><strong>publish_frequency</strong> — pantau jumlah publikasi dalam window (hari) vs minimum yang diharapkan.</li>
          <li><strong>last_activity</strong> — pantau seberapa lama sejak aktivitas terakhir (batas jam).</li>
          <li><strong>Interval cek</strong> — seberapa sering sistem mengecek, mis. <code>6h</code> (6 jam) atau <code>30m</code>.</li>
          <li><strong>Aktif</strong> — hanya aturan aktif yang muncul di Monitoring untuk user <strong>viewer</strong>.</li>
          <li><strong>Duplikat</strong> — salin aturan (salinan nonaktif) untuk variasi cepat.</li>
          <li>Klik <strong>nama aturan</strong> di tabel → histori cek, jalankan cek sekarang, unduh CSV.</li>
        </ul>
      </section>

      <section class="card guide-section">
        <h2>Menu User</h2>
        <ul class="guide-list">
          <li><strong>admin</strong> — akses Platform, Aturan, User, Petunjuk, plus Monitoring & Analisa.</li>
          <li><strong>viewer</strong> — hanya Monitoring & Analisa (read-only).</li>
          <li><strong>Edit</strong> — ubah role, aktif/nonaktif, atau reset password.</li>
          <li><strong>Hapus</strong> — hapus akun (tidak bisa menghapus diri sendiri atau admin aktif terakhir).</li>
        </ul>
      </section>

      <section class="card guide-section">
        <h2>Monitoring (dashboard)</h2>
        <ul class="guide-list">
          <li>Chip di atas — filter cepat menurut status (OK, warning, critical, unknown).</li>
          <li>Filter platform / tampilan kartu atau tabel — sesuaikan kebutuhan tim.</li>
          <li>Refresh otomatis ~60 detik; tombol refresh manual di kanan atas.</li>
          <li>Admin melihat semua aturan; viewer hanya aturan yang <strong>aktif</strong>.</li>
        </ul>
      </section>

      <section class="card guide-section">
        <h2>Analisa</h2>
        <p class="muted" style="margin-top: 0">
          Ringkasan run cek yang memenuhi target dalam periode window. Berguna untuk laporan rutin ke manajemen.
        </p>
      </section>

      <section class="card guide-section">
        <h2>Masalah umum (di UI)</h2>
        <table class="admin-table compact">
          <thead>
            <tr>
              <th>Situasi</th>
              <th>Apa yang dilakukan</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Viewer tidak melihat aturan</td>
              <td>Buka Aturan → pastikan status <strong>aktif</strong> dan centang saat edit jika perlu.</td>
            </tr>
            <tr>
              <td>Status unknown / error</td>
              <td>Platform → <strong>Test</strong>; periksa kredensial; untuk uji awal gunakan mode mock.</td>
            </tr>
            <tr>
              <td>Ingin cek segera tanpa menunggu jadwal</td>
              <td>Monitoring → klik aturan → <strong>Jalankan cek</strong>.</td>
            </tr>
            <tr>
              <td>Salin aturan mirip</td>
              <td>Aturan → <strong>Duplikat</strong> → edit salinan → aktifkan.</td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  </div>
</template>
