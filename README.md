# IE Toolkit | Praktikum Ergonomi (Versi Perbaikan & Penyempurnaan)

Aplikasi web berbasis **Streamlit** untuk pengolahan data **Praktikum Ergonomi & Perancangan Sistem Kerja** (Program Studi Teknik Industri - Universitas Pelita Bangsa).

## Daftar Perbaikan Utama dari Versi Sebelumnya
1. **Navigasi Modern (Tanpa Radio Button):** Mengganti komponen `st.radio` horizontal di bagian atas dengan tombol navigasi berbentuk *pill bar* yang responsif.
2. **Proporsi Layar Lebar (`layout="wide"`):** Mengoptimalkan lebar kontainer (`max-width: 1260px`) agar teks, tombol, dan kartu modul mudah diikuti di monitor maupun laptop.
3. **Konsistensi Tema Forest Green:** Mengganti kotak peringatan biru (`st.info`) yang bertabrakan warna dengan komponen `.emerald-notice` bertema hijau zambrud gelap.
4. **Integrasi Penuh RULA, OWAS, & REBA:** Menyatukan perhitungan **REBA** ke dalam **Modul 02 (Postur Kerja)** dan menautkannya langsung dengan metrik **Ringkasan Praktikum** di Beranda.
5. **Sinkronisasi Zona Waktu WIB (`Asia/Jakarta`):** Memperbaiki waktu server yang sebelumnya mengikuti UTC agar selalu akurat dengan Waktu Indonesia Barat (WIB).
6. **Ekspor Excel Multi-Sheet & Pemulihan JSON:** Dilengkapi laporan `.xlsx` berformat rapi (12 sheet dasar, plus 1 sheet simulasi bila tersedia) dan fitur *Backup/Restore* `.json` agar praktikan tidak kehilangan data saat browser ter-refresh.

## Pembaruan Terbaru

### Fase 1.5 — Penyederhanaan UI/UX dan Onboarding (Oktober 2026)

- **Beranda untuk pengguna baru:** dua aksi utama (**Mulai praktikum** dan **Coba Modul 01**), panduan tiga langkah yang bisa ditutup, progres 9 modul, serta penjelasan bahwa data bawaan adalah simulasi.
- **Navigasi utama lebih ringkas:** Beranda, Daftar Modul, Identitas, Proyek Saya, dan Laporan. Dashboard, Impor Excel, Ruang Belajar, dan Kalkulator Postur tetap tersedia dari menu pendukung atau kartu beranda.
- **Empat tahap konsisten di setiap modul:** **1 · Data**, **2 · Hasil**, **3 · Analisis**, dan **4 · Panduan & Laporan**. Input, keluaran, catatan pembahasan, penelusuran rumus, dan tanda selesai kini ditempatkan sesuai urutan belajar. Modul 02 dan 09 tetap memiliki subtab khusus metodenya.
- **Mode Pemula/Lanjutan:** mode Pemula memberi arahan singkat dan meringkas tampilan perbandingan teknis; mode Lanjutan memperluas bagian tersebut. Rumus dan hasil perhitungan **tidak berubah** karena pilihan mode.
- **Desain yang seragam:** kontainer lebih nyaman dibaca, warna tombol aksi lebih jelas, kartu beranda lebih fokus, dan tab dapat di-scroll pada layar HP. Tombol pindah modul di bagian atas/bawah dan tombol kembali browser tetap bekerja.
- **Tes regresi UI:** pengujian otomatis mencakup kesembilan modul, jumlah tab, pintasan ke laporan, panduan awal, dan keberadaan kontrol utama; tes numerik dari Fase 1 tetap dijalankan.

**Alur singkat pertama kali menggunakan:** Buka **Mulai praktikum** → isi identitas → pilih modul → masukkan data pengukuran di tab **Data** → periksa **Hasil** → tulis **Analisis** → baca **Panduan & Laporan** → unduh cadangan atau laporan. Data contoh harus diganti sebelum dipakai sebagai laporan observasi.

### Fase 1 — Audit Rumus dan Upgrade Modul 01 & 03 (Oktober 2026)

- **Modul 01: pemulihan nadi P0–P5.** Form pengamatan untuk dua operator, grafik nadi, perhitungan ECPT, ECPM, perubahan P1–P5, dan persentase pemulihan deskriptif. Hasil ikut ke lembar Excel `01_Pemulihan_Nadi`, PDF modul, dan PDF gabungan. Semua data contoh awal perlu diganti sesuai observasi.
- **Modul 03: empat faktor penyesuaian per elemen.** Westinghouse (`p=1+skill+effort+condition+consistency`), Schummard (`p=skor/60`), Objektif (`p=(skor/60)×(1+total kesulitan/100)`) dan faktor Akhir (manual, diputuskan praktikan). Input 6 komponen kesulitan **ABT, PK, PT, KMT, PERLT, BB** dan tabel perbandingan Ws/Wn/Wb/output; pilih metode utama untuk ringkasan produk. Lembar Excel tambahan `03_Perbandingan_Metode` dan PDF berisi jejak perbandingan.
- **Audit %CVL:** penyebut menggunakan `DN maks − DN istirahat` tanpa memaksa minimum 1; data dengan penyebut ≤0 sekarang ditolak. Batas 30% diklasifikasikan sebagai kategori perlu perbaikan, bukan rendah. Jika DN kerja lebih rendah dari DN istirahat, hasil ditandai **perlu verifikasi**.
- **Audit time study:** allowance dinyatakan sebagai `Wb = Wn / (1−A/100)` dengan `0 ≤ A < 100`, bukan menambahkan 15% ke Wn. Uji kecukupan dan keseragaman menggunakan sampel observasi yang sama pada semua metode. Kapasitas produk **3600/ΣWb** berlaku jika elemen bersama-sama membentuk satu siklus/unit, bukan dengan menjumlah output per elemen.

**Catatan istilah penting:** Nama *Extra Calorie due to Peripheral Temperature/Metabolism* (ECPT/ECPM) pada pedoman praktikum menggunakan operasi terhadap **denyut nadi P0–P5**, sehingga hasil operasi tersebut berupa indeks selisih nadi (bpm), **bukan kalori atau kkal**. Estimasi konsumsi energi di tabel %CVL berasal dari persamaan regresi terpisah; jangan menyamakan kedua jenis keluaran.

**Jejak rumus:** `assets/MODUL-1-8.docx` (panduan praktikum di repository), bagian Modul 01 “Perhitungan ECPT dan ECPM” dan Modul 03 “Penyesuaian Schummard”, “Penyesuaian Westinghouse”, dan “Penyesuaian Obyektif”. Perhitungan ini bertujuan membantu laporan praktikum; interpretasi kesehatan dan kelayakan kondisi kerja memerlukan konteks pengamatan dan penilaian ahli.

**Uji regresi:** `python -m unittest discover -v` mencakup contoh acuan P0–P5, p Schummard/Objektif/Westinghouse/akhir, allowance, data ekstrem, pembulatan ambang %CVL, dan jejak ekspor laporan.

### Workspace Praktikum — fitur yang tersedia

- **Manajer Proyek** (`/proyek`): beri nama proyek, simpan beberapa snapshot selama sesi, ekspor file proyek `.json`, kemudian impor kembali beserta status penyelesaian modul. Berkas proyek bersifat portabel, bukan terikat satu perangkat.
- **Cloud proyek pribadi (opsional)**: bila pengelola telah menyiapkan autentikasi OIDC dan PostgreSQL SSL, praktikan bisa menyimpan/membuka proyek sesuai identitas akun (`sub`) dan memilih **autosave**. Aplikasi tidak menyimpan proyek pribadi ke SQLite bersama. Tanpa pengaturan cloud, gunakan file proyek `.json`; snapshot sesi *tidak permanen* setelah refresh.
- **Dashboard kemajuan** (`/dashboard`): progres 9 modul, tanda selesai yang dikonfirmasi praktikan, dan ringkasan hitung. Data simulasi bawaan tidak otomatis diberi label selesai.
- **Impor Excel** (`/impor-excel`): template `.xlsx` dan validasi atomik untuk Modul **03–08** (waktu siklus, 32 dimensi, desain antropometri, suhu, dBA, lux). Kolom, batas nilai, rumus Excel, nilai tak hingga, dan data kosong dicek sebelum mengganti data aktif.
- **Ruang Belajar** (`/ruang-belajar`): teori ringkas, contoh hitung berdasarkan data sesi, batas metode, dan latihan untuk semua 9 modul. Tiap halaman modul juga menampilkan penelusuran hasil yang sama.
- **PDF per modul**: di halaman Laporan, unduh PDF khusus modul berisi identitas, ringkasan metode, penelusuran rumus, hasil, dan pembahasan. Laporan gabungan PDF/Excel/JSON tetap tersedia.
- **Simulasi postur RULA**: selain simulasi NIOSH pada Modul 09, Modul 02 kini mendukung perbandingan skor awal dan skor usulan tanpa menimpa observasi.
- **Peningkatan responsivitas HP** pada kartu dashboard, area impor, dan tabel.

#### Cara mengaktifkan penyimpanan cloud (khusus pengelola aplikasi)

Penyimpanan **tidak** menjadi permanen hanya karena aplikasi terhubung ke Streamlit Community Cloud. Siapkan PostgreSQL privat dan konfigurasi OIDC sesuai [panduan resmi Streamlit](https://docs.streamlit.io/develop/concepts/connections/authentication). Simpan nilai rahasia di Streamlit Cloud Secrets (jangan commit ke GitHub):

```toml
PROJECT_DATABASE_URL = "postgresql://USER:PASSWORD@DB_HOST:5432/DB_NAME"

[auth]
redirect_uri = "https://kalkulator-ergonomi.streamlit.app/oauth2callback"
cookie_secret = "PAKAI_NILAI_ACAK_RAHASIA"
client_id = "CLIENT_ID_DARI_PENYEDIA_OIDC"
client_secret = "CLIENT_SECRET_DARI_PENYEDIA_OIDC"
server_metadata_url = "URL_METADATA_OIDC_DARI_PENYEDIA"
```

Kolom `[auth]` hanya contoh bentuk konfigurasi: URI pengalihan dan metadata harus mengikuti penyedia OIDC yang benar-benar didaftarkan oleh pengelola. Jangan memakai nilai contoh di atas. Database harus membatasi akses melalui kredensial rahasia, mengaktifkan SSL, dan disertai kebijakan backup. Setelah itu masuk melalui `/proyek` dan aktifkan autosave secara sadar. Tidak ada login ataupun database eksternal yang otomatis dibuat oleh repository ini.

File `.json` cadangan maupun `.xlsx` bisa memuat identitas anggota kelompok; simpan dan bagikan dengan hati-hati. Template Excel memuat data contoh yang **wajib diganti** sebelum membuat analisis atas observasi nyata. Perhitungan RULA, uji-t, ISBB, dan dosis kebisingan memerlukan validasi konteks lapangan, bukan sekadar hasil numerik aplikasi.

- **Navigasi multipage:** 9 modul kini memiliki halaman dan URL sendiri (`/modul-01` sampai `/modul-09`). Tombol **Daftar Modul**, **Sebelumnya**, dan **Berikutnya** serta tombol Back/Forward browser memudahkan berpindah halaman.
- **Modul lingkungan dipisahkan:** Modul 06 (Temperatur), 07 (Kebisingan), dan 08 (Pencahayaan) kini memiliki input, hasil, peringatan, dan analisis masing-masing. Semua nilai tetap ikut di ekspor PDF/Excel/JSON.
- **Simulasi perbaikan Manual Material Handling (Modul 09):** bandingkan kondisi awal dengan usulan jarak horizontal, tinggi tangan, perpindahan vertikal, sudut, frekuensi, durasi, genggaman, dan berat beban. RWL serta Lifting Index dihitung untuk kedua skenario tanpa mengganti data observasi utama.
- **Ekspor skenario:** unduh perbandingan `.csv`; skenario juga disertakan dalam cadangan `.json`, ringkasan PDF, dan sheet `09_Simulasi` pada Excel.
- **Perhitungan dan validasi:** Lifting Index memakai RWL tanpa pembulatan antara; input faktor penyesuaian, allowance, dan parameter statistik diuji terhadap nilai yang tidak valid.
- **Antarmuka:** kartu metrik, fokus keyboard, dan tata letak layar sempit diperjelas. Identitas yang tampil dalam HTML di-escape dengan aman.
- **Uji regresi:** skenario RNLE, kondisi di luar cakupan, ekspor, dan backup mendapat tes tambahan.

**Batas pemakaian:** NIOSH RNLE digunakan untuk pengangkatan dua tangan sesuai cakupan model. Perubahan persentase LI bukan perubahan persentase risiko cedera. Modul Snook adalah simulasi edukatif, sedangkan L5/S1 memakai pendekatan biomekanika sederhana. Kedua hasil tersebut tidak boleh dianggap pengganti penilaian K3 lapangan.

**Catatan penyimpanan:** Navigasi antarmodul melalui tombol aplikasi mempertahankan data selama sesi aktif. Membuka URL modul secara langsung di tab baru atau memuat ulang halaman dapat membuat sesi baru; unduh **Cadangan JSON** untuk menyimpan pekerjaan secara permanen.

## Cara Menjalankan Secara Lokal
```bash
pip install -r requirements.txt
streamlit run app.py
```

Untuk menjalankan tes otomatis:

```bash
python -m unittest discover -v
```
