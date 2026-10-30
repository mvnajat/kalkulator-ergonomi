# IE Toolkit | Praktikum Ergonomi (Versi Perbaikan & Penyempurnaan)

Aplikasi web berbasis **Streamlit** untuk pengolahan data **Praktikum Ergonomi & Perancangan Sistem Kerja** (Program Studi Teknik Industri - Universitas Pelita Bangsa).

## Daftar Perbaikan Utama dari Versi Sebelumnya
1. **Navigasi Modern (Tanpa Radio Button):** Mengganti komponen `st.radio` horizontal di bagian atas dengan tombol navigasi berbentuk *pill bar* yang responsif.
2. **Proporsi Layar Lebar (`layout="wide"`):** Mengoptimalkan lebar kontainer (`max-width: 1420px`) sehingga kartu modul tidak sempit atau berdesakan di monitor 16:9.
3. **Konsistensi Tema Forest Green:** Mengganti kotak peringatan biru (`st.info`) yang bertabrakan warna dengan komponen `.emerald-notice` bertema hijau zambrud gelap.
4. **Integrasi Penuh RULA, OWAS, & REBA:** Menyatukan perhitungan **REBA** ke dalam **Modul 02 (Postur Kerja)** dan menautkannya langsung dengan metrik **Ringkasan Praktikum** di Beranda.
5. **Sinkronisasi Zona Waktu WIB (`Asia/Jakarta`):** Memperbaiki waktu server yang sebelumnya mengikuti UTC agar selalu akurat dengan Waktu Indonesia Barat (WIB).
6. **Ekspor Excel Multi-Sheet & Pemulihan JSON:** Dilengkapi laporan `.xlsx` berformat rapi (12 sheet dasar, plus 1 sheet simulasi bila tersedia) dan fitur *Backup/Restore* `.json` agar praktikan tidak kehilangan data saat browser ter-refresh.

## Pembaruan Terbaru

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
