# IE Toolkit — Praktikum Ergonomi

Versi revisi Streamlit berdasarkan app-1.py, config-1.toml, MODUL-1-8.docx, dan screenshot Edlink yang diberikan pengguna.

## Menjalankan

Gunakan Python 3.10 atau lebih baru. Buka terminal pada folder hasil ekstraksi yang berisi app.py.

```bash
python -m venv .venv
```

Aktifkan environment:

Windows:
```bat
.venv\Scripts\activate
```

macOS / Linux:
```bash
source .venv/bin/activate
```

Instal dan jalankan:
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Pertahankan seluruh struktur folder. Jangan hanya menyalin app.py: berkas legacy.py, modules.py, core.py, styles.css, assets, dan .streamlit/config.toml juga diperlukan. Cadangkan proyek lama sebelum menggantinya. Berkas ini belum diunggah ke hosting atau repositori pengguna.

## Isi paket

- app.py: navigasi, beranda kartu modul, ekspor seluruh laporan, simpan/muat JSON.
- modules.py: formulir dan pengolahan delapan modul.
- legacy.py: komponen dan kalkulator dari aplikasi awal, disesuaikan untuk tema terang dan kunci input terpisah per konteks.
- core.py: fungsi perhitungan yang dapat diuji terpisah.
- styles.css dan .streamlit/config.toml: tema terang dengan hijau tua #123C36.
- assets/module_data.json: 252 kombinasi OWAS dan 32 dimensi antropometri, diekstrak dari dokumen modul.
- assets/ratings.json: tabel rating Westinghouse dari aplikasi awal.
- assets/MODUL-1-8.docx dan image1–3.jpg: dokumen sumber dan gambar rumus fisiologi.
- test_core.py: 11 pengujian unit fungsi perhitungan dan kelengkapan data lookup.
- originals: kode dan konfigurasi awal untuk referensi pemulihan.

## UI/UX

Header hijau tua, latar #EEF2F5, kartu putih, panel ringkasan kiri, kartu modul dua kolom kanan, pencarian modul, dan menu utama horizontal. Susunan mengikuti referensi visual Edlink; bukan integrasi dengan layanan Edlink. Logo, data kehadiran, jadwal, dan notifikasi Edlink tidak disalin. Pada layar kecil, ukuran teks/header disederhanakan dan tabel tetap dapat digulir horizontal. Tampilan browser nyata masih perlu pemeriksaan desktop dan ponsel.

## Alur penggunaan

1. Buka Identitas: kelas, kelompok, tanggal, batch, anggota, operator, usia, jenis kelamin, dan berat badan.
2. Buka setiap modul melalui Beranda atau Modul Praktikum.
3. Isi data nyata. Nilai kosong pada lembar kerja baru tidak diperlakukan sebagai nol. Kalkulator cepat lama tetap memiliki data contoh; ganti sebelum dipakai sebagai laporan.
4. Untuk RULA/OWAS, pilih operator dan aktivitas, periksa semua postur, lalu tekan Catat hasil. Perubahan pilihan tidak menimpa catatan sebelum dicatat kembali.
5. Lengkapi analisis, kesimpulan, saran, dan bukti yang diperlukan.
6. Unduh laporan modul atau seluruh tabel dalam Excel.
7. Unduh cadangan JSON untuk menyimpan seluruh sesi, termasuk gambar. JSON dapat dipulihkan melalui Laporan setelah memberi konfirmasi penggantian draft.

Data disimpan dalam st.session_state, bukan database. Perpindahan menu mempertahankan tabel dan pilihan melalui snapshot sesi. Restart server, sesi kedaluwarsa, atau refresh browser dapat menghilangkan sesi. Cadangkan JSON sebelum menutup. File Excel tidak memuat gambar; cadangan JSON memuatnya dalam bentuk base64. Belum ada login, database bersama, otorisasi per pengguna, atau sinkronisasi cloud.

## Kelengkapan modul

| Modul | Isian dan hasil |
|---|---|
| 1 Fisiologi | Dua operator, normal/setelah aktivitas, sistolik, diastolik, nadi, suhu, waktu menulis, nadi saat kerja, P1/P2/P3 pemulihan, CVL, ECPT/ECPM manual, bukti tulisan dan analisis. Berat, usia dan jenis kelamin berasal dari Identitas. |
| 2 Postur kerja | RULA dan OWAS per operator/aktivitas, lookup OWAS, foto postur, pencatatan hasil, tabel perbandingan dan rekomendasi. |
| 3 Waktu kerja | Dua operator × tujuh elemen, data pengamatan mentah, rating Schummard/Westinghouse/Obyektif, enam faktor kesulitan, lima komponen allowance, keseragaman, kecukupan, grafik kontrol dan output siklus. Kalkulator cepat lama tetap tersedia. |
| 4 Antropometri | 32 dimensi × tujuh responden, identitas responden, ukuran pintu/meja/kursi, Shapiro-Wilk, persentil P5/P10/P50/P90/P95, grafik kontrol, rancangan dan sketsa. |
| 5 Antropometri lanjutan | Tiga dimensi yang dapat dinamai × sepuluh responden, statistik, keseragaman, kecukupan, persentil dan rancangan. |
| 6 Temperatur | Dingin/panas × tiga percobaan, temperatur aktual, target, selesai, salah, durasi, ringkasan, grafik dan analisis. |
| 7 Kebisingan | Normal/bising × tiga percobaan, pengukuran dBA, target, selesai, salah, durasi, ringkasan, grafik dan analisis. |
| 8 Pencahayaan | Normal/gelap × tiga percobaan, pengukuran lux, target, selesai, salah, durasi, ringkasan, grafik dan analisis. |

REBA dipertahankan sebagai fitur tambahan, bukan pengganti OWAS pada Modul 2.

## Dasar rumus dan batasan

### Fisiologi

CVL = 100 × (nadi kerja − nadi istirahat) / (nadi maksimum − nadi istirahat).
Estimasi maksimum: 220−usia untuk laki-laki dan 200−usia untuk perempuan; tersedia override manual. Nadi sesudah aktivitas tidak otomatis dianggap nadi saat kerja.
Acuan tambahan: https://ejournal.akprind.ac.id/index.php/rekavasi/article/download/4182/3025/7040

ECPT/ECPM disediakan sebagai isian manual beserta satuannya. Gambar rumus sumber dapat dibuka pada modul 1, tetapi rumus tersebut belum ditranskripsi/diverifikasi untuk otomatisasi. CVL di sini adalah perhitungan praktikum, bukan diagnosis.

### Postur

OWAS menyalin 252 sel lookup dari tabel dokumen modul, termasuk sel yang mungkin memerlukan koreksi pengampu. Salinan ini tidak berarti tabel telah divalidasi terhadap publikasi OWAS asli. RULA/REBA mempertahankan matriks dan interpretasi dari kode awal; belum ada audit ilmiah independen seluruh sel.

Dokumen modul mencampur penyebutan treadmill dan naik-turun tangga. Aplikasi menyediakan aktivitas terpisah agar pengguna memilih sesuai pengamatan.

### Waktu kerja

Schummard p=score/60; Westinghouse p=1+empat faktor; Obyektif p=(score/60)×(1+jumlah faktor kesulitan/100), mengikuti rumus teks modul.

Allowance per elemen adalah jumlah lima komponennya. Persentase antar-elemen tidak dijumlahkan untuk diterapkan pada satu siklus; angka contoh 108.50% di modul tidak dijadikan allowance siklus. Pilih basis allowance:
- Waktu normal: Wb=Wn×(1+a).
- Waktu kerja total: Wb=Wn/(1−a).

Total Wb siklus adalah jumlah Wb ketujuh elemen; kapasitas siklus dihitung 3600/total Wb, bukan menjumlahkan output tiap elemen. Hasil statistik tetap harus diperiksa; jumlah elemen lengkap tidak menjamin data sudah seragam/cukup. Kalkulator cepat mempertahankan eliminasi outlier satu putaran dari kode lama; lembar tiga metode tidak membuang outlier otomatis.

### Antropometri

SD sampel; BKA/BKB=rata-rata±k×SD. N' memakai rumus kecukupan yang sudah ada dalam kode awal. Shapiro-Wilk dijalankan untuk 3–5000 nilai yang tidak konstan. p≥0.05 bukan jaminan distribusi normal. Mode otomatis memakai persentil parametrik ketika p≥0.05; selain itu memakai persentil empiris interpolasi linear. Pengguna dapat memilih metode secara eksplisit. Tidak ada eliminasi outlier otomatis.

### Modul lingkungan 6–8

Rumus gambar untuk efisiensi resmi modul belum diverifikasi. Aplikasi memberikan definisi operasional yang ditampilkan jelas:
- Selesai% = selesai/target ×100.
- Kesalahan% = salah/selesai ×100 (0 jika tidak ada unit selesai).
- Baik terhadap target% = (selesai−salah)/target ×100.
- Output baik per jam = 3600×(selesai−salah)/durasi detik.

Nilai baik terhadap target tidak disamakan dengan efisiensi resmi modul. Disediakan kolom manual efisiensi serta rumus/acuan dari pengampu. Ringkasan adalah rata-rata aritmetika persentase percobaan, bukan rasio gabungan. Periksa jumlah percobaan dan kesetaraan target.

## Pengujian

```bash
python -m unittest test_core.py -v
```

Hasil pemeriksaan saat pembuatan:
- 11 pengujian unit lulus: parsing, input invalid, SD, outlier, persentil, CVL, tiga metode waktu, allowance invalid, metrik lingkungan, dan dimensi lookup.
- Seluruh berkas Python lolos pemeriksaan sintaks.
- Smoke test fungsi halaman dengan tiruan API Streamlit/Altair melewati formulir kosong, RULA, REBA, OWAS, dan kalkulator cepat tanpa exception.
- Uji input terisi menghasilkan dua hasil CVL, 42 baris metode waktu, 32+3 dimensi antropometri, dan 18 baris percobaan lingkungan.
- Putaran ekspor/impor JSON serta pembuatan workbook Excel diuji secara programatis.

Streamlit dan Altair tidak terpasang di lingkungan pembuatan. Belum ada pengujian browser/end-to-end dengan Streamlit asli, verifikasi responsivitas visual, atau deploy ke website aktif. Lakukan uji jalankan dengan requirements.txt sebelum mengganti aplikasi produksi. Hasil smoke test tiruan tidak menjamin kompatibilitas semua versi browser/Streamlit.
