# IE Toolkit | Praktikum Ergonomi (Versi Perbaikan & Penyempurnaan)

Aplikasi web berbasis **Streamlit** untuk pengolahan data **Praktikum Ergonomi & Perancangan Sistem Kerja** (Program Studi Teknik Industri - Universitas Pelita Bangsa).

## Daftar Perbaikan Utama dari Versi Sebelumnya
1. **Navigasi Modern (Tanpa Radio Button):** Mengganti komponen `st.radio` horizontal di bagian atas dengan tombol navigasi berbentuk *pill bar* yang responsif.
2. **Proporsi Layar Lebar (`layout="wide"`):** Mengoptimalkan lebar kontainer (`max-width: 1420px`) sehingga kartu modul tidak sempit atau berdesakan di monitor 16:9.
3. **Konsistensi Tema Forest Green:** Mengganti kotak peringatan biru (`st.info`) yang bertabrakan warna dengan komponen `.emerald-notice` bertema hijau zambrud gelap.
4. **Integrasi Penuh RULA, OWAS, & REBA:** Menyatukan perhitungan **REBA** ke dalam **Modul 02 (Postur Kerja)** dan menautkannya langsung dengan metrik **Ringkasan Praktikum** di Beranda.
5. **Sinkronisasi Zona Waktu WIB (`Asia/Jakarta`):** Memperbaiki waktu server yang sebelumnya mengikuti UTC agar selalu akurat dengan Waktu Indonesia Barat (WIB).
6. **Ekspor Excel Multi-Sheet & Pemulihan JSON:** Dilengkapi generator laporan `.xlsx` berformat rapi (7 sheet) dan fitur *Backup/Restore* `.json` agar praktikan tidak kehilangan data saat browser ter-refresh.

## Cara Menjalankan Secara Lokal
```bash
pip install -r requirements.txt
streamlit run app.py
```
