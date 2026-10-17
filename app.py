import os
import json
import base64
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import streamlit as st

from utils.calculations import (
    ANTROPOMETRI_32_DIMENSI,
    hitung_fisiologi_cvl,
    hitung_rula,
    hitung_owas,
    hitung_reba,
    hitung_waktu_kerja,
    hitung_antropometri_statistik,
    hitung_lingkungan_perbandingan,
)
from utils.exporter import export_session_to_json, export_session_to_excel

# -----------------------------------------------------------------------------
# 1. KONFIGURASI HALAMAN (WIDE LAYOUT & TEMA FOREST GREEN)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="IE Toolkit | Praktikum Ergonomi",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS untuk menyempurnakan tampilan Forest Dark Green & memperbaiki kontras UI
st.markdown("""
<style>
    .stApp {
        background-color: #06110b;
        color: #e2f1e8;
    }
    /* Padding atas dinaikkan ke 4.5rem agar header & tombol tidak terpotong */
    .block-container {
        max-width: 1420px;
        padding-top: 4.5rem !important;
        padding-bottom: 3rem;
    }
    header[data-testid="stHeader"] {
        background: rgba(6, 17, 11, 0.75);
        backdrop-filter: blur(6px);
    }
    /* POSISI FIXED DI POJOK KIRI ATAS LAYAR (Sejajar tombol Share di kanan atas) */
    .upb-top-left-fixed {
        position: fixed;
        top: 10px;
        left: 24px;
        z-index: 999999;
        display: flex;
        align-items: center;
        gap: 10px;
        background: linear-gradient(135deg, #0c2619 0%, #081a11 100%);
        border: 1px solid #23533a;
        border-radius: 10px;
        padding: 6px 14px;
        height: 38px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.35);
        pointer-events: none;
    }
    .upb-top-left-fixed img {
        height: 24px;
        width: auto;
        object-fit: contain;
    }
    .upb-brand-title {
        color: #f0fdf4;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        white-space: nowrap;
    }
    /* Banner Header */
    .hero-card {
        background: linear-gradient(135deg, #0b2217 0%, #07170f 100%);
        border: 1px solid #1c3d2b;
        border-radius: 14px;
        padding: 22px 26px;
        margin-bottom: 20px;
        margin-top: 8px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
    }
    .hero-subtitle {
        color: #34d399;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .hero-title {
        color: #f0fdf4;
        font-size: 1.65rem;
        font-weight: 700;
        margin: 0 0 6px 0;
    }
    .hero-desc {
        color: #9ca3af;
        font-size: 0.92rem;
        margin: 0;
    }
    /* Kartu Panel Samping & Modul */
    .panel-card {
        background-color: #091912;
        border: 1px solid #1b3829;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 16px;
    }
    .module-card {
        background-color: #091912;
        border: 1px solid #1b3829;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 10px;
        transition: all 0.2s ease;
    }
    .module-card:hover {
        border-color: #22c55e;
        box-shadow: 0 4px 14px rgba(34, 197, 94, 0.12);
    }
    .badge-pill {
        display: inline-block;
        background-color: #112e1f;
        color: #4ade80;
        border: 1px solid #1f5137;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 999px;
        margin-bottom: 10px;
    }
    .badge-done {
        display: inline-block;
        background-color: #064e3b;
        color: #6ee7b7;
        border: 1px solid #10b981;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 999px;
        margin-left: 6px;
    }
    .mod-title {
        color: #f0fdf4;
        font-size: 1.15rem;
        font-weight: 700;
        margin: 0 0 6px 0;
    }
    .mod-desc {
        color: #94a3b8;
        font-size: 0.85rem;
        line-height: 1.45;
        min-height: 40px;
        margin-bottom: 12px;
    }
    .mod-footer {
        color: #64748b;
        font-size: 0.76rem;
        border-top: 1px solid #142a1e;
        padding-top: 8px;
        margin-top: 6px;
    }
    /* Custom Emerald Alert */
    .emerald-notice {
        background-color: #0b291c;
        border: 1px solid #10b981;
        border-left: 4px solid #22c55e;
        color: #a7f3d0;
        border-radius: 10px;
        padding: 13px 16px;
        font-size: 0.85rem;
        line-height: 1.45;
        margin-top: 10px;
    }
    .summary-item {
        border-bottom: 1px solid #142a1e;
        padding: 10px 0;
    }
    .summary-item:last-child {
        border-bottom: none;
    }
    .summary-val {
        color: #f0fdf4;
        font-weight: 700;
        font-size: 0.92rem;
    }
    .summary-sub {
        color: #86efac;
        font-size: 0.78rem;
        opacity: 0.8;
    }
    /* Styling Tombol Streamlit */
    div.stButton > button {
        background-color: #0c2318;
        color: #e2f1e8;
        border: 1px solid #234d37;
        border-radius: 8px;
        font-weight: 600;
        height: 42px;
        width: 100%;
        transition: 0.2s;
    }
    div.stButton > button:hover {
        background-color: #153c28;
        border-color: #4ade80;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)


def get_logo_html() -> str:
    """Memuat logo_upb.png jika ada di folder proyek, atau menampilkan SVG emblem UPB."""
    for filename in ["logo_upb.png", "logo_upb.jpg", "assets/logo_upb.png"]:
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            ext = "png" if filename.endswith(".png") else "jpeg"
            return f'<img src="data:image/{ext};base64,{b64}" alt="Logo UPB">'
    return """
    <svg width="24" height="24" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M18 2L4 8V17C4 25.5 9.9 33.3 18 35C26.1 33.3 32 25.5 32 17V8L18 2Z" fill="#15803d" stroke="#4ade80" stroke-width="2"/>
        <text x="18" y="22" text-anchor="middle" fill="#ffffff" font-size="10" font-weight="bold" font-family="sans-serif">UPB</text>
    </svg>
    """


# -----------------------------------------------------------------------------
# 2. INISIALISASI SESSION STATE DENGAN DATA CONTOH REALISTIS (SIAP UJI)
# -----------------------------------------------------------------------------
def init_session_state():
    if "initialized" in st.session_state:
        return

    wib_now = datetime.now(ZoneInfo("Asia/Jakarta"))
    st.session_state["nav_page"] = "Beranda"
    st.session_state["selected_modul"] = "Modul 01 - Fisiologi Kerja"

    # Identitas Praktikum
    st.session_state["identitas"] = {
        "universitas": "Universitas Pelita Bangsa",
        "prodi": "Teknik Industri",
        "kelas": "J253B",
        "kelompok": "Kelompok 01",
        "tanggal": wib_now.strftime("%d-%m-%Y"),
        "dosen": "Tim Laboratorium Ergonomi & Perancangan Sistem Kerja",
        "op1_nama": "Operator A (Praktikan 1)",
        "op1_usia": 21,
        "op1_jk": "Laki-laki",
        "op2_nama": "Operator B (Praktikan 2)",
        "op2_usia": 20,
        "op2_jk": "Perempuan",
        "anggota": "\n".join([
            "1. Anggota 1 (NIM)",
            "2. Anggota 2 (NIM)",
            "3. Anggota 3 (NIM)",
            "4. Anggota 4 (NIM)",
        ]),
    }

    # Modul 01: Fisiologi (2 Operator x 2 Aktivitas)
    st.session_state["modul_01"] = {
        "op1_akt1_nama": "Pengangkatan Beban Manual (15 kg)",
        "op1_akt1_dni": 74.0,
        "op1_akt1_dnk": 118.0,
        "op1_akt2_nama": "Perakitan Komponen Berdiri",
        "op1_akt2_dni": 75.0,
        "op1_akt2_dnk": 102.0,
        "op2_akt1_nama": "Pengangkatan Beban Manual (10 kg)",
        "op2_akt1_dni": 78.0,
        "op2_akt1_dnk": 124.0,
        "op2_akt2_nama": "Inspeksi & Pengemasan Duduk",
        "op2_akt2_dni": 76.0,
        "op2_akt2_dnk": 95.0,
    }

    # Modul 02: Postur Kerja (RULA, OWAS, & REBA Terintegrasi)
    st.session_state["modul_02"] = {
        "records": [
            {
                "id": "POST-01",
                "operator": "Operator 1",
                "aktivitas": "Merakit Komponen di Meja Rendah",
                "rula_params": {"ua": 3, "la": 2, "wr": 2, "wt": 1, "nk": 3, "tr": 3, "lg": 1, "ma": 1, "fa": 1, "mb": 1, "fb": 1},
                "owas_params": {"back": 2, "arms": 1, "legs": 2, "load": 1},
                "reba_params": {"neck": 2, "trunk": 3, "legs": 1, "load": 1, "ua": 3, "la": 2, "wr": 2, "coup": 1, "act": 1},
            },
            {
                "id": "POST-02",
                "operator": "Operator 2",
                "aktivitas": "Mengangkat Kotak dari Lantai",
                "rula_params": {"ua": 4, "la": 2, "wr": 3, "wt": 2, "nk": 4, "tr": 4, "lg": 2, "ma": 1, "fa": 2, "mb": 1, "fb": 2},
                "owas_params": {"back": 4, "arms": 1, "legs": 4, "load": 2},
                "reba_params": {"neck": 2, "trunk": 4, "legs": 2, "load": 2, "ua": 4, "la": 2, "wr": 2, "coup": 2, "act": 1},
            },
        ],
        "bukti_gambar_count": 0,
        "bukti_files": [],
    }

    # Modul 03: Pengukuran Waktu Kerja (7 Elemen Kerja x 10 Siklus Pengamatan)
    elemen_names = [
        ("EL-01", "Mengambil bahan baku dari wadah"),
        ("EL-02", "Memposisikan benda kerja pada jig"),
        ("EL-03", "Melakukan perakitan komponen utama"),
        ("EL-04", "Mengencangkan baut pengunci"),
        ("EL-05", "Melakukan pemeriksaan dimensi (QC)"),
        ("EL-06", "Memberi label identitas produk"),
        ("EL-07", "Meletakkan produk jadi ke boks selesai"),
    ]
    np.random.seed(42)
    m3_rows = []
    base_times = [4.2, 5.5, 12.4, 8.1, 6.0, 3.8, 4.5]
    for (kode, nama), bt in zip(elemen_names, base_times):
        siklus = np.round(np.random.normal(loc=bt, scale=0.25, size=10), 2)
        row = {"Kode": kode, "Elemen Kerja": nama}
        for i in range(10):
            row[f"S{i+1}"] = float(siklus[i])
        m3_rows.append(row)

    st.session_state["modul_03"] = {
        "df_siklus": m3_rows,
        "westinghouse": {"skill": 0.06, "effort": 0.05, "condition": 0.02, "consistency": 0.01},
        "allowance_pribadi": 5.0,
        "allowance_kelelahan": 7.0,
        "allowance_hambatan": 3.0,
        "k_level": 2.0,
        "s_level": 0.05,
    }

    # Modul 04: Antropometri 32 Dimensi Tubuh (10 Sampel Praktikan)
    default_means = [
        167.5, 156.2, 138.4, 104.5, 92.0, 74.3, 64.1, 86.5, 83.2, 75.0,
        58.4, 24.5, 14.8, 56.2, 46.5, 51.0, 42.5, 44.2, 38.0, 35.4,
        22.5, 21.8, 33.5, 44.0, 76.5, 65.2, 19.2, 15.6, 18.4, 8.5, 25.2, 9.6
    ]
    aplikasi_desain = [
        "Tinggi langit-langit ruang / pintu (P95)",
        "Tinggi layar display visual berdiri (P50)",
        "Batas jangkauan rak bagian atas (P5)",
        "Tinggi meja kerja berdiri presisi (P50)",
        "Tinggi sabuk pengaman / pagar pelindung (P50)",
        "Batas kontrol panel rendah berdiri (P5)",
        "Tinggi objek paling bawah tanpa membungkuk (P5)",
        "Ruang bebas vertikal kabin duduk (P95)",
        "Tinggi sandaran kepala kursi (P50)",
        "Tinggi pusat layar monitor duduk (P50)",
        "Tinggi sandaran punggung kursi atas (P50)",
        "Tinggi sandaran tangan kursi / armrest (P50)",
        "Ruang bebas kolong meja (tebal paha) (P95)",
        "Jarak bebas depan lutut di bawah meja (P95)",
        "Kedalaman alas duduk kursi kerja (P5)",
        "Tinggi minimal ruang bawah meja (P95)",
        "Tinggi alas kursi kerja dari lantai (P5)",
        "Lebar ruang duduk antar sandaran lengan (P95)",
        "Lebar sandaran punggung kursi (P95)",
        "Lebar alas duduk kursi kerja (P95)",
        "Jarak bebas akses lorong sempit dada (P95)",
        "Jarak bebas kursi ke tepi meja (P95)",
        "Jarak penempatan komponen vertikal (P50)",
        "Radius jangkauan area kerja meja normal (P5)",
        "Jarak jangkauan maksimum ke depan (P5)",
        "Jarak penempatan tombol darurat / tuas (P5)",
        "Ukuran panjang helm pelindung APD (P95)",
        "Lebar dalam helm keselamatan (P95)",
        "Ukuran panjang sarung tangan kerja (P95)",
        "Lebar gagang perkakas tangan / handtool (P5)",
        "Panjang pedal kaki mesin / sepatu safety (P95)",
        "Lebar pijakan pedal kaki (P95)",
    ]
    m4_rows = []
    for idx, (kode, nama, satuan) in enumerate(ANTROPOMETRI_32_DIMENSI):
        samples = np.round(np.random.normal(loc=default_means[idx], scale=2.1, size=10), 1)
        r = {"Kode": kode, "Dimensi Tubuh": nama, "Aplikasi Desain": aplikasi_desain[idx]}
        for s_i in range(10):
            r[f"P{s_i+1}"] = float(samples[s_i])
        m4_rows.append(r)
    st.session_state["modul_04"] = {"df_32": m4_rows}

    # Modul 05: Antropometri Lanjutan (3 Dimensi Kunci x 10 Sampel + Spesifikasi Stasiun Kerja)
    st.session_state["modul_05"] = {
        "df_3dim": [
            {"Dimensi": "Tinggi Popliteal Duduk (TPD)", "Persentil Acuan": "P5", "Kelonggaran (cm)": 2.5,
             "S1": 41.5, "S2": 42.0, "S3": 43.2, "S4": 40.8, "S5": 42.5, "S6": 41.9, "S7": 43.0, "S8": 42.2, "S9": 41.4, "S10": 42.8},
            {"Dimensi": "Tinggi Siku Duduk (TSD)", "Persentil Acuan": "P50", "Kelonggaran (cm)": 0.0,
             "S1": 24.0, "S2": 24.5, "S3": 25.1, "S4": 23.8, "S5": 24.6, "S6": 24.2, "S7": 25.0, "S8": 24.4, "S9": 23.9, "S10": 24.7},
            {"Dimensi": "Lebar Pinggul Duduk (LPD)", "Persentil Acuan": "P95", "Kelonggaran (cm)": 3.0,
             "S1": 34.5, "S2": 35.2, "S3": 36.0, "S4": 33.8, "S5": 35.5, "S6": 34.9, "S7": 36.2, "S8": 35.1, "S9": 34.4, "S10": 35.8},
        ]
    }

    # Modul 06, 07, 08: Lingkungan Kerja (3 Percobaan per Kondisi)
    st.session_state["modul_06"] = {
        "dingin_suhu": [21.4, 21.8, 21.5],
        "panas_suhu": [32.6, 33.1, 32.8],
        "dingin_waktu": [48.2, 46.5, 47.0],
        "panas_waktu": [56.4, 58.1, 57.2],
        "nab_suhu": 28.0,
    }
    st.session_state["modul_07"] = {
        "normal_db": [62.5, 64.0, 63.2],
        "bising_db": [88.4, 89.2, 88.7],
        "normal_waktu": [45.0, 44.2, 46.1],
        "bising_waktu": [54.8, 56.0, 55.3],
        "nab_db": 85.0,
    }
    st.session_state["modul_08"] = {
        "normal_lux": [340.0, 355.0, 348.0],
        "gelap_lux": [85.0, 92.0, 88.0],
        "normal_waktu": [42.5, 43.1, 41.8],
        "gelap_waktu": [59.2, 61.5, 60.4],
        "standar_lux": 300.0,
    }

    # Catatan Analisis Praktikan per Modul
    st.session_state["analisis_modul"] = {
        "Modul 01": "Berdasarkan perhitungan %CVL, aktivitas pengangkatan beban manual menghasilkan beban kardiovaskular di atas 30% sehingga diperlukan pengaturan waktu istirahat berkala.",
        "Modul 02": "Postur pengangkatan dari lantai memiliki skor RULA, OWAS, dan REBA tertinggi. Disarankan penambahan meja angkat (scissor lift) agar operator tidak membungkuk ekstrem.",
        "Modul 03": "Seluruh 7 elemen kerja berada dalam batas kontrol BKA dan BKB (data seragam) serta jumlah pengamatan N >= N' (data cukup).",
        "Modul 04": "Data 32 dimensi tubuh berdistribusi normal (Shapiro-Wilk p > 0.05) dan dapat digunakan sebagai acuan perancangan fasilitas kerja berbasis persentil P5, P50, dan P95.",
        "Modul 05": "Dimensi rancangan kursi dan meja perakitan ditentukan dari Tinggi Popliteal Duduk (P5), Tinggi Siku Duduk (P50), dan Lebar Pinggul (P95) ditambah kelonggaran pakaian/sepatu.",
        "Modul 06": "Suhu ruang panas (> 32°C) melebihi NAB Permenaker No. 5 Tahun 2018 (28°C) dan meningkatkan waktu penyelesaian kerja secara signifikan.",
        "Modul 07": "Paparan kebisingan (> 88 dBA) melebihi NAB 85 dBA untuk 8 jam kerja, mengganggu konsentrasi dan menurunkan kecepatan kerja operator.",
        "Modul 08": "Kondisi pencahayaan redup (< 100 Lux) berada di bawah standar SNI (min. 300 Lux untuk perakitan halus), meningkatkan ketegangan mata dan waktu siklus.",
    }

    st.session_state["initialized"] = True


init_session_state()

# -----------------------------------------------------------------------------
# 3. FUNGSI KOMPILASI HASIL PERHITUNGAN UNTUK RINGKASAN & LAPORAN EXCEL
# -----------------------------------------------------------------------------
def compile_all_calculations() -> dict:
    id_info = st.session_state["identitas"]
    m1 = st.session_state["modul_01"]

    # Modul 01
    m1_list = []
    configs_m1 = [
        (id_info["op1_nama"], m1["op1_akt1_nama"], id_info["op1_usia"], id_info["op1_jk"], m1["op1_akt1_dni"], m1["op1_akt1_dnk"]),
        (id_info["op1_nama"], m1["op1_akt2_nama"], id_info["op1_usia"], id_info["op1_jk"], m1["op1_akt2_dni"], m1["op1_akt2_dnk"]),
        (id_info["op2_nama"], m1["op2_akt1_nama"], id_info["op2_usia"], id_info["op2_jk"], m1["op2_akt1_dni"], m1["op2_akt1_dnk"]),
        (id_info["op2_nama"], m1["op2_akt2_nama"], id_info["op2_usia"], id_info["op2_jk"], m1["op2_akt2_dni"], m1["op2_akt2_dnk"]),
    ]
    for op_nama, akt_nama, usia, jk, dni, dnk in configs_m1:
        res = hitung_fisiologi_cvl(dni, dnk, int(usia), jk)
        m1_list.append([
            op_nama, akt_nama, usia, dni, dnk,
            res["dn_max"], res["cvl_persen"], res["ke_bersih_kkal_menit"],
            res["kategori"], res["tindakan"]
        ])

    # Modul 02 (RULA, OWAS, REBA)
    m2_list = []
    for rec in st.session_state["modul_02"]["records"]:
        rp = rec["rula_params"]
        rula_res = hitung_rula(rp["ua"], rp["la"], rp["wr"], rp["wt"], rp["nk"], rp["tr"], rp["lg"], rp["ma"], rp["fa"], rp["mb"], rp["fb"])
        m2_list.append([rec["operator"], rec["aktivitas"], "RULA", f"Skor {rula_res['grand_score']}", f"Level {rula_res['action_level']}", rula_res["kategori"], rula_res["rekomendasi"]])

        op = rec["owas_params"]
        owas_res = hitung_owas(op["back"], op["arms"], op["legs"], op["load"])
        m2_list.append([rec["operator"], rec["aktivitas"], "OWAS", f"Kode {owas_res['kode_owas']} (Kat {owas_res['kategori_skor']})", f"Kategori {owas_res['kategori_skor']}", owas_res["kategori"], owas_res["rekomendasi"]])

        rbp = rec["reba_params"]
        reba_res = hitung_reba(rbp["neck"], rbp["trunk"], rbp["legs"], rbp["load"], rbp["ua"], rbp["la"], rbp["wr"], rbp["coup"], rbp["act"])
        m2_list.append([rec["operator"], rec["aktivitas"], "REBA", f"Skor {reba_res['final_score']}", f"Level {reba_res['action_level']}", reba_res["kategori"], reba_res["rekomendasi"]])

    # Modul 03
    m3_state = st.session_state["modul_03"]
    p_west = sum(m3_state["westinghouse"].values())
    allow_total = m3_state["allowance_pribadi"] + m3_state["allowance_kelelahan"] + m3_state["allowance_hambatan"]
    m3_list = []
    for row in m3_state["df_siklus"]:
        obs = [row.get(f"S{i+1}", 0.0) for i in range(10)]
        res = hitung_waktu_kerja(obs, p_west, allow_total, m3_state["k_level"], m3_state["s_level"])
        if res:
            m3_list.append([
                row["Kode"], row["Elemen Kerja"], res["ws"], res["std"], res["bkb"], res["bka"],
                res["seragam"], res["n_prime"], res["cukup"], res["p_factor"], res["allowance_pct"],
                res["wn"], res["wb"], res["output_standar_per_jam"]
            ])

    # Modul 04
    m4_list = []
    for row in st.session_state["modul_04"]["df_32"]:
        vals = [row.get(f"P{i+1}", 0.0) for i in range(10)]
        res = hitung_antropometri_statistik(vals)
        if res:
            m4_list.append([
                row["Kode"], row["Dimensi Tubuh"], res["mean"], res["std"],
                res["p5"], res["p10"], res["p50"], res["p90"], res["p95"],
                res["normalitas"], row.get("Aplikasi Desain", "")
            ])

    # Modul 05
    m5_list = []
    for row in st.session_state["modul_05"]["df_3dim"]:
        vals = [row.get(f"S{i+1}", 0.0) for i in range(10)]
        res = hitung_antropometri_statistik(vals)
        if res:
            acuan = str(row.get("Persentil Acuan", "P50")).lower()
            base_p = res.get(acuan, res["p50"])
            ukuran_desain = round(base_p + float(row.get("Kelonggaran (cm)", 0.0)), 2)
            m5_list.append([
                row["Dimensi"], res["mean"], res["std"], res["bkb"], res["bka"],
                res["seragam"], res["n_prime"], res["cukup"], row.get("Persentil Acuan", "P50"), ukuran_desain
            ])

    # Modul 06, 07, 08
    m6 = st.session_state["modul_06"]
    m7 = st.session_state["modul_07"]
    m8 = st.session_state["modul_08"]
    r6 = hitung_lingkungan_perbandingan(m6["dingin_suhu"], m6["panas_suhu"], "Dingin", "Panas", m6["nab_suhu"], "°C")
    r7 = hitung_lingkungan_perbandingan(m7["normal_db"], m7["bising_db"], "Normal", "Bising", m7["nab_db"], "dBA")
    r8 = hitung_lingkungan_perbandingan(m8["normal_lux"], m8["gelap_lux"], "Normal", "Gelap", m8["standar_lux"], "Lux")
    env_list = [
        ["Modul 06 - Temperatur", "Suhu Ruang (°C)", r6["Mean Dingin (°C)"], r6["Mean Panas (°C)"], r6["Selisih (°C)"], r6["Ambang Batas / Standar"], r6["p-value (Uji-t)"], r6["Kesimpulan Statistik"], st.session_state["analisis_modul"]["Modul 06"]],
        ["Modul 07 - Kebisingan", "Intensitas Suara (dBA)", r7["Mean Normal (dBA)"], r7["Mean Bising (dBA)"], r7["Selisih (dBA)"], r7["Ambang Batas / Standar"], r7["p-value (Uji-t)"], r7["Kesimpulan Statistik"], st.session_state["analisis_modul"]["Modul 07"]],
        ["Modul 08 - Pencahayaan", "Intensitas Cahaya (Lux)", r8["Mean Normal (Lux)"], r8["Mean Gelap (Lux)"], r8["Selisih (Lux)"], r8["Ambang Batas / Standar"], r8["p-value (Uji-t)"], r8["Kesimpulan Statistik"], st.session_state["analisis_modul"]["Modul 08"]],
    ]

    return {
        "m1_rows": m1_list,
        "m2_rows": m2_list,
        "m3_rows": m3_list,
        "m4_rows": m4_list,
        "m5_rows": m5_list,
        "env_rows": env_list,
    }


# -----------------------------------------------------------------------------
# 4. LOGO & NAMA UNIVERSITAS DI POJOK KIRI ATAS LAYAR + BAR MENU NAVIGASI
# -----------------------------------------------------------------------------
logo_tag = get_logo_html()
st.markdown(f"""
<div class="upb-top-left-fixed">
    {logo_tag}
    <span class="upb-brand-title">UNIVERSITAS PELITA BANGSA</span>
</div>
""", unsafe_allow_html=True)

nav_options = ["Beranda", "Identitas", "Modul Praktikum", "Analisis Postur (RULA/OWAS/REBA)", "Laporan & Cadangan"]
nav_cols = st.columns([1.15, 1.15, 1.45, 2.25, 1.6])

for idx, label in enumerate(nav_options):
    with nav_cols[idx]:
        is_active = (st.session_state["nav_page"] == label)
        btn_label = f"🟢 {label}" if is_active else label
        if st.button(btn_label, key=f"nav_btn_{idx}", use_container_width=True):
            st.session_state["nav_page"] = label
            st.rerun()

# Banner Utama
st.markdown(f"""
<div class="hero-card">
    <div class="hero-subtitle">{st.session_state['identitas']['universitas']} · {st.session_state['identitas']['prodi']} ({st.session_state['identitas']['kelas']})</div>
    <div class="hero-title">Ruang Praktikum Ergonomi & Perancangan Sistem Kerja</div>
    <p class="hero-desc">Isi lembar pengamatan, periksa hasil perhitungan otomatis (Fisiologi, RULA/OWAS/REBA, Waktu Baku, Antropometri, & Lingkungan), lalu unduh laporan Excel & cadangan JSON.</p>
</div>
""", unsafe_allow_html=True)

wib_time = datetime.now(ZoneInfo("Asia/Jakarta"))
total_postur_records = len(st.session_state["modul_02"]["records"]) * 3
total_bukti_gambar = st.session_state["modul_02"]["bukti_gambar_count"]

# -----------------------------------------------------------------------------
# HALAMAN 1: BERANDA (DASHBOARD MODUL & RINGKASAN)
# -----------------------------------------------------------------------------
if st.session_state["nav_page"] == "Beranda":
    left_col, right_col = st.columns([1.05, 2.35], gap="large")

    with left_col:
        st.markdown(f"""
        <div class="panel-card">
            <h4 style="margin:0 0 12px 0; color:#f0fdf4; font-size:1.05rem;">Ringkasan Praktikum</h4>
            <div class="summary-item">
                <div class="summary-val">{wib_time.strftime('%d-%m-%Y · %H:%M WIB')}</div>
                <div class="summary-sub">Waktu Server Lokal (Asia/Jakarta)</div>
            </div>
            <div class="summary-item">
                <div class="summary-val">8 Modul Praktikum Terintegrasi</div>
                <div class="summary-sub">Fisiologi, postur (RULA/OWAS/REBA), waktu kerja, antropometri & lingkungan</div>
            </div>
            <div class="summary-item">
                <div class="summary-val">{total_postur_records} Evaluasi Postur Dicatat</div>
                <div class="summary-sub">RULA, OWAS, dan REBA terhitung otomatis per aktivitas</div>
            </div>
            <div class="summary-item">
                <div class="summary-val">{total_bukti_gambar} Bukti Gambar Diunggah</div>
                <div class="summary-sub">Dokumentasi postur kerja & sketsa stasiun kerja</div>
            </div>
        </div>

        <div class="panel-card">
            <h4 style="margin:0 0 12px 0; color:#f0fdf4; font-size:1.05rem;">Urutan Pengisian</h4>
            <div class="summary-item">
                <div class="summary-val">01 - Lengkapi Identitas</div>
                <div class="summary-sub">Kelas ({st.session_state['identitas']['kelas']}), kelompok, anggota, dan data 2 operator</div>
            </div>
            <div class="summary-item">
                <div class="summary-val">02 - Isi Lembar Pengamatan</div>
                <div class="summary-sub">Gunakan data pengamatan asli atau modifikasi sampel terisi</div>
            </div>
            <div class="summary-item">
                <div class="summary-val">03 - Periksa Hasil & Analisis</div>
                <div class="summary-sub">Verifikasi uji statistik dan lengkapi kesimpulan tiap modul</div>
            </div>
            <div class="summary-item">
                <div class="summary-val">04 - Unduh Laporan & Cadangan</div>
                <div class="summary-sub">Ekspor ke Excel (.xlsx) multi-sheet atau simpan sesi JSON</div>
            </div>
        </div>

        <div class="emerald-notice">
            <strong>💾 Penyimpanan Sesi & Pemulihan Instan:</strong><br>
            Data disimpan di memori sesi aktif. Gunakan fitur <b>Ekspor / Impor JSON</b> pada tab <i>Laporan & Cadangan</i> agar data aman saat menutup browser.
        </div>
        """, unsafe_allow_html=True)

    with right_col:
        st.markdown("<h4 style='margin:0 0 10px 0; color:#f0fdf4;'>Modul Akademik</h4>", unsafe_allow_html=True)
        search_q = st.text_input(
            "Cari modul",
            placeholder="Cari berdasarkan nama atau nomor modul (misal: Antropometri, RULA, 03)...",
            label_visibility="collapsed",
        ).strip().lower()

        modules_meta = [
            ("Modul 01", "Fisiologi", "Dua operator, kondisi normal dan setelah aktivitas, nadi kerja, konsumsi energi serta perhitungan %CVL.", "Modul 01 - Fisiologi Kerja"),
            ("Modul 02", "Postur Kerja (RULA, OWAS & REBA)", "Evaluasi postur kerja terpadu menggunakan metode RULA, OWAS, dan REBA per operator beserta rekomendasi.", "Modul 02 - Postur Kerja"),
            ("Modul 03", "Pengukuran Waktu Kerja", "Tujuh elemen kerja, metode rating Westinghouse, rincian allowance, uji keseragaman, kecukupan & waktu baku.", "Modul 03 - Pengukuran Waktu Kerja"),
            ("Modul 04", "Antropometri (32 Dimensi)", "32 dimensi tubuh, uji normalitas Shapiro-Wilk, perhitungan persentil (P5, P50, P95) dan acuan desain.", "Modul 04 - Antropometri 32 Dimensi"),
            ("Modul 05", "Antropometri Lanjutan", "Uji keseragaman (BKA/BKB), kecukupan data (N'), dan spesifikasi rancangan kursi/meja stasiun kerja.", "Modul 05 - Antropometri Lanjutan"),
            ("Modul 06", "Temperatur", "Perbandingan kondisi dingin/panas dalam tiga percobaan per kondisi beserta uji-t dan evaluasi NAB.", "Modul 06 - Lingkungan (Temperatur, Kebisingan, Pencahayaan)"),
            ("Modul 07", "Kebisingan", "Perbandingan kondisi normal/bising (dBA) dalam tiga percobaan per kondisi beserta evaluasi NAB 85 dBA.", "Modul 06 - Lingkungan (Temperatur, Kebisingan, Pencahayaan)"),
            ("Modul 08", "Pencahayaan", "Perbandingan kondisi normal/gelap (Lux) dalam tiga percobaan per kondisi beserta evaluasi standar SNI.", "Modul 06 - Lingkungan (Temperatur, Kebisingan, Pencahayaan)"),
        ]

        filtered_mods = [
            m for m in modules_meta
            if search_q == "" or search_q in m[0].lower() or search_q in m[1].lower() or search_q in m[2].lower()
        ]

        mod_cols = st.columns(2, gap="medium")
        for idx, (m_code, m_title, m_desc, target_key) in enumerate(filtered_mods):
            with mod_cols[idx % 2]:
                st.markdown(f"""
                <div class="module-card">
                    <span class="badge-pill">{m_code}</span>
                    <span class="badge-done">Siap Olah</span>
                    <div class="mod-title">{m_title}</div>
                    <div class="mod-desc">{m_desc}</div>
                    <div class="mod-footer">Teknik Industri · Data terintegrasi ke Laporan Excel</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Buka lembar kerja {m_code}", key=f"open_{m_code}", use_container_width=True):
                    st.session_state["selected_modul"] = target_key
                    st.session_state["nav_page"] = "Modul Praktikum"
                    st.rerun()

# -----------------------------------------------------------------------------
# HALAMAN 2: IDENTITAS KELOMPOK & OPERATOR
# -----------------------------------------------------------------------------
elif st.session_state["nav_page"] == "Identitas":
    st.subheader("📋 Identitas Kelompok & Operator Praktikum")
    id_state = st.session_state["identitas"]

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("##### Informasi Akademik Kelompok")
        id_state["universitas"] = st.text_input("Perguruan Tinggi", value=id_state["universitas"])
        id_state["prodi"] = st.text_input("Program Studi", value=id_state["prodi"])
        id_state["kelas"] = st.text_input("Kelas", value=id_state["kelas"])
        id_state["kelompok"] = st.text_input("Nama / Nomor Kelompok", value=id_state["kelompok"])
        id_state["tanggal"] = st.text_input("Tanggal Praktikum", value=id_state["tanggal"])
        id_state["dosen"] = st.text_input("Dosen Pengampu / Asisten Lab", value=id_state["dosen"])
        id_state["anggota"] = st.text_area("Daftar Nama & NIM Anggota Kelompok", value=id_state["anggota"], height=130)

    with c2:
        st.markdown("##### Profil Operator 1 & Operator 2")
        st.caption("Usia dan jenis kelamin operator digunakan secara otomatis untuk menghitung Denyut Nadi Maksimum pada Modul 01.")
        id_state["op1_nama"] = st.text_input("Nama Operator 1", value=id_state["op1_nama"])
        oc1, oc2 = st.columns(2)
        with oc1:
            id_state["op1_usia"] = st.number_input("Usia Operator 1 (Tahun)", min_value=15, max_value=70, value=int(id_state["op1_usia"]))
        with oc2:
            id_state["op1_jk"] = st.selectbox("Jenis Kelamin Operator 1", ["Laki-laki", "Perempuan"], index=0 if id_state["op1_jk"] == "Laki-laki" else 1)

        st.divider()
        id_state["op2_nama"] = st.text_input("Nama Operator 2", value=id_state["op2_nama"])
        oc3, oc4 = st.columns(2)
        with oc3:
            id_state["op2_usia"] = st.number_input("Usia Operator 2 (Tahun)", min_value=15, max_value=70, value=int(id_state["op2_usia"]))
        with oc4:
            id_state["op2_jk"] = st.selectbox("Jenis Kelamin Operator 2", ["Laki-laki", "Perempuan"], index=0 if id_state["op2_jk"] == "Laki-laki" else 1)

    st.success("Perubahan identitas tersimpan otomatis ke dalam sesi praktikum.")

# -----------------------------------------------------------------------------
# HALAMAN 3: MODUL PRAKTIKUM (01 s/d 08)
# -----------------------------------------------------------------------------
elif st.session_state["nav_page"] == "Modul Praktikum":
    modul_list = [
        "Modul 01 - Fisiologi Kerja",
        "Modul 02 - Postur Kerja",
        "Modul 03 - Pengukuran Waktu Kerja",
        "Modul 04 - Antropometri 32 Dimensi",
        "Modul 05 - Antropometri Lanjutan",
        "Modul 06 - Lingkungan (Temperatur, Kebisingan, Pencahayaan)",
    ]
    default_idx = modul_list.index(st.session_state["selected_modul"]) if st.session_state["selected_modul"] in modul_list else 0
    chosen = st.selectbox("Pilih Lembar Kerja Modul Praktikum:", modul_list, index=default_idx)
    st.session_state["selected_modul"] = chosen
    st.divider()

    # --- MODUL 01: FISIOLOGI ---
    if chosen == "Modul 01 - Fisiologi Kerja":
        st.subheader("🫀 Modul 01: Fisiologi Kerja & Beban Kardiovaskular (%CVL)")
        m1 = st.session_state["modul_01"]
        id_info = st.session_state["identitas"]

        col_op1, col_op2 = st.columns(2, gap="large")
        with col_op1:
            st.markdown(f"#### 👤 {id_info['op1_nama']} ({id_info['op1_usia']} thn, {id_info['op1_jk']})")
            m1["op1_akt1_nama"] = st.text_input("Nama Aktivitas 1 (Op 1)", value=m1["op1_akt1_nama"])
            a1, a2 = st.columns(2)
            m1["op1_akt1_dni"] = a1.number_input("DN Istirahat Akt 1 (bpm)", 40.0, 150.0, float(m1["op1_akt1_dni"]), key="op1_dni1")
            m1["op1_akt1_dnk"] = a2.number_input("DN Kerja Akt 1 (bpm)", 50.0, 210.0, float(m1["op1_akt1_dnk"]), key="op1_dnk1")

            m1["op1_akt2_nama"] = st.text_input("Nama Aktivitas 2 (Op 1)", value=m1["op1_akt2_nama"])
            b1, b2 = st.columns(2)
            m1["op1_akt2_dni"] = b1.number_input("DN Istirahat Akt 2 (bpm)", 40.0, 150.0, float(m1["op1_akt2_dni"]), key="op1_dni2")
            m1["op1_akt2_dnk"] = b2.number_input("DN Kerja Akt 2 (bpm)", 50.0, 210.0, float(m1["op1_akt2_dnk"]), key="op1_dnk2")

        with col_op2:
            st.markdown(f"#### 👤 {id_info['op2_nama']} ({id_info['op2_usia']} thn, {id_info['op2_jk']})")
            m1["op2_akt1_nama"] = st.text_input("Nama Aktivitas 1 (Op 2)", value=m1["op2_akt1_nama"])
            c1, c2 = st.columns(2)
            m1["op2_akt1_dni"] = c1.number_input("DN Istirahat Akt 1 (bpm)", 40.0, 150.0, float(m1["op2_akt1_dni"]), key="op2_dni1")
            m1["op2_akt1_dnk"] = c2.number_input("DN Kerja Akt 1 (bpm)", 50.0, 210.0, float(m1["op2_akt1_dnk"]), key="op2_dnk1")

            m1["op2_akt2_nama"] = st.text_input("Nama Aktivitas 2 (Op 2)", value=m1["op2_akt2_nama"])
            d1, d2 = st.columns(2)
            m1["op2_akt2_dni"] = d1.number_input("DN Istirahat Akt 2 (bpm)", 40.0, 150.0, float(m1["op2_akt2_dni"]), key="op2_dni2")
            m1["op2_akt2_dnk"] = d2.number_input("DN Kerja Akt 2 (bpm)", 50.0, 210.0, float(m1["op2_akt2_dnk"]), key="op2_dnk2")

        calc_all = compile_all_calculations()
        df_m1 = pd.DataFrame(calc_all["m1_rows"], columns=[
            "Operator", "Aktivitas", "Usia (th)", "DN Istirahat", "DN Kerja",
            "DN Maks", "%CVL (%)", "Konsumsi Energi Bersih (kkal/mnt)", "Kategori Beban", "Rekomendasi"
        ])
        st.markdown("#### 📊 Hasil Perhitungan Fisiologi Kerja (%CVL & Konsumsi Energi)")
        st.dataframe(df_m1, use_container_width=True, hide_index=True)
        st.session_state["analisis_modul"]["Modul 01"] = st.text_area(
            "Analisis & Pembahasan Modul 01:", value=st.session_state["analisis_modul"]["Modul 01"]
        )

    # --- MODUL 02: POSTUR KERJA ---
    elif chosen == "Modul 02 - Postur Kerja":
        st.subheader("🧍 Modul 02: Evaluasi Postur Kerja Terpadu (RULA, OWAS, & REBA)")
        st.info("Metode REBA telah diintegrasikan langsung bersama RULA & OWAS agar seluruh evaluasi postur tercatat di Ringkasan Praktikum. Anda juga bisa mengakses kalkulator detailnya di tab 'Analisis Postur (RULA/OWAS/REBA)'.")
        calc_all = compile_all_calculations()
        df_m2 = pd.DataFrame(calc_all["m2_rows"], columns=[
            "Operator", "Aktivitas", "Metode", "Skor / Kode Akhir", "Action Level", "Kategori Risiko", "Rekomendasi Perbaikan"
        ])
        st.dataframe(df_m2, use_container_width=True, hide_index=True)

        uploaded_imgs = st.file_uploader("Unggah Bukti Foto Postur / Sketsa Kerja (JPG/PNG)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        if uploaded_imgs:
            st.session_state["modul_02"]["bukti_gambar_count"] = len(uploaded_imgs)
            img_cols = st.columns(min(len(uploaded_imgs), 4))
            for i, img_f in enumerate(uploaded_imgs):
                img_cols[i % 4].image(img_f, caption=img_f.name, use_container_width=True)

        if st.button("🔧 Buka Kalkulator Input Skor RULA / OWAS / REBA Detail"):
            st.session_state["nav_page"] = "Analisis Postur (RULA/OWAS/REBA)"
            st.rerun()

        st.session_state["analisis_modul"]["Modul 02"] = st.text_area(
            "Analisis & Pembahasan Modul 02:", value=st.session_state["analisis_modul"]["Modul 02"]
        )

    # --- MODUL 03: PENGUKURAN WAKTU KERJA ---
    elif chosen == "Modul 03 - Pengukuran Waktu Kerja":
        st.subheader("⏱️ Modul 03: Pengukuran Waktu Kerja (Time Study)")
        m3 = st.session_state["modul_03"]

        st.markdown("##### 1. Tabel Waktu Siklus Pengamatan (10 Siklus dalam Detik)")
        edited_m3 = st.data_editor(pd.DataFrame(m3["df_siklus"]), use_container_width=True, num_rows="dynamic", key="ed_m3")
        m3["df_siklus"] = edited_m3.to_dict("records")

        st.markdown("##### 2. Penyesuaian (Westinghouse Rating) & Kelonggaran (Allowance)")
        w1, w2, w3, w4 = st.columns(4)
        m3["westinghouse"]["skill"] = w1.number_input("Skill (Keterampilan)", -0.22, 0.15, float(m3["westinghouse"]["skill"]), step=0.01)
        m3["westinghouse"]["effort"] = w2.number_input("Effort (Usaha)", -0.17, 0.13, float(m3["westinghouse"]["effort"]), step=0.01)
        m3["westinghouse"]["condition"] = w3.number_input("Condition (Kondisi)", -0.07, 0.06, float(m3["westinghouse"]["condition"]), step=0.01)
        m3["westinghouse"]["consistency"] = w4.number_input("Consistency (Konsistensi)", -0.04, 0.04, float(m3["westinghouse"]["consistency"]), step=0.01)

        al1, al2, al3 = st.columns(3)
        m3["allowance_pribadi"] = al1.number_input("Kelonggaran Kebutuhan Pribadi (%)", 0.0, 20.0, float(m3["allowance_pribadi"]), step=0.5)
        m3["allowance_kelelahan"] = al2.number_input("Kelonggaran Menghilangkan Kelelahan (%)", 0.0, 30.0, float(m3["allowance_kelelahan"]), step=0.5)
        m3["allowance_hambatan"] = al3.number_input("Kelonggaran Hambatan Tak Terhindarkan (%)", 0.0, 20.0, float(m3["allowance_hambatan"]), step=0.5)

        calc_all = compile_all_calculations()
        df_res_m3 = pd.DataFrame(calc_all["m3_rows"], columns=[
            "Kode", "Elemen Kerja", "Ws (dtk)", "SD", "BKB", "BKA",
            "Uji Keseragaman", "N'", "Uji Kecukupan", "Faktor p", "Allowance (%)", "Wn (dtk)", "Wb (dtk)", "Output Standar (unit/jam)"
        ])
        st.markdown("##### 3. Hasil Perhitungan Waktu Siklus, Waktu Normal, Waktu Baku, & Uji Data")
        st.dataframe(df_res_m3, use_container_width=True, hide_index=True)

        total_wb = df_res_m3["Wb (dtk)"].sum() if not df_res_m3.empty else 0.0
        st.metric("Total Waktu Baku Siklus Produk (Σ Wb)", f"{total_wb:.2f} detik/unit", f"Kapasitas Produksi: {3600/total_wb:.1f} unit/jam" if total_wb > 0 else "")
        st.session_state["analisis_modul"]["Modul 03"] = st.text_area(
            "Analisis & Pembahasan Modul 03:", value=st.session_state["analisis_modul"]["Modul 03"]
        )

    # --- MODUL 04: ANTROPOMETRI 32 DIMENSI ---
    elif chosen == "Modul 04 - Antropometri 32 Dimensi":
        st.subheader("📏 Modul 04: Antropometri 32 Dimensi Tubuh, Uji Normalitas & Persentil")
        m4 = st.session_state["modul_04"]
        edited_m4 = st.data_editor(pd.DataFrame(m4["df_32"]), use_container_width=True, height=420, key="ed_m4")
        m4["df_32"] = edited_m4.to_dict("records")

        calc_all = compile_all_calculations()
        df_res_m4 = pd.DataFrame(calc_all["m4_rows"], columns=[
            "Kode", "Nama Dimensi Tubuh", "Mean (cm)", "SD (cm)",
            "P5 (cm)", "P10 (cm)", "P50 (cm)", "P90 (cm)", "P95 (cm)", "Uji Normalitas (Shapiro-Wilk)", "Aplikasi Desain Stasiun Kerja"
        ])
        st.markdown("##### Hasil Rekapitulasi Persentil & Uji Normalitas 32 Dimensi")
        st.dataframe(df_res_m4, use_container_width=True, hide_index=True, height=400)
        st.session_state["analisis_modul"]["Modul 04"] = st.text_area(
            "Analisis & Pembahasan Modul 04:", value=st.session_state["analisis_modul"]["Modul 04"]
        )

    # --- MODUL 05: ANTROPOMETRI LANJUTAN ---
    elif chosen == "Modul 05 - Antropometri Lanjutan":
        st.subheader("🪑 Modul 05: Antropometri Lanjutan & Spesifikasi Rancangan Stasiun Kerja")
        m5 = st.session_state["modul_05"]
        st.caption("Fokus pada 3 dimensi kunci penentu rancangan stasiun kerja (Uji Keseragaman BKA/BKB, Kecukupan N', dan Penambahan Kelonggaran/Allowance).")
        edited_m5 = st.data_editor(pd.DataFrame(m5["df_3dim"]), use_container_width=True, num_rows="dynamic", key="ed_m5")
        m5["df_3dim"] = edited_m5.to_dict("records")

        calc_all = compile_all_calculations()
        df_res_m5 = pd.DataFrame(calc_all["m5_rows"], columns=[
            "Dimensi Kunci", "Mean (cm)", "SD (cm)", "BKB (cm)", "BKA (cm)",
            "Status Keseragaman", "N'", "Status Kecukupan", "Persentil Acuan", "Ukuran Rancangan Final (cm)"
        ])
        st.dataframe(df_res_m5, use_container_width=True, hide_index=True)
        st.session_state["analisis_modul"]["Modul 05"] = st.text_area(
            "Analisis & Pembahasan Modul 05:", value=st.session_state["analisis_modul"]["Modul 05"]
        )

    # --- MODUL 06, 07, 08: LINGKUNGAN KERJA ---
    elif chosen == "Modul 06 - Lingkungan (Temperatur, Kebisingan, Pencahayaan)":
        st.subheader("🌡️🔊💡 Modul 06, 07, & 08: Lingkungan Fisik Kerja")
        m6, m7, m8 = st.session_state["modul_06"], st.session_state["modul_07"], st.session_state["modul_08"]

        t_col1, t_col2, t_col3 = st.columns(3, gap="medium")
        with t_col1:
            st.markdown("#### 🌡️ Modul 06: Temperatur (°C)")
            for i in range(3):
                m6["dingin_suhu"][i] = st.number_input(f"Suhu Kondisi Dingin - Percobaan {i+1} (°C)", 10.0, 45.0, float(m6["dingin_suhu"][i]), key=f"t_d_{i}")
            for i in range(3):
                m6["panas_suhu"][i] = st.number_input(f"Suhu Kondisi Panas - Percobaan {i+1} (°C)", 10.0, 50.0, float(m6["panas_suhu"][i]), key=f"t_p_{i}")

        with t_col2:
            st.markdown("#### 🔊 Modul 07: Kebisingan (dBA)")
            for i in range(3):
                m7["normal_db"][i] = st.number_input(f"Kebisingan Normal - Percobaan {i+1} (dBA)", 30.0, 120.0, float(m7["normal_db"][i]), key=f"b_n_{i}")
            for i in range(3):
                m7["bising_db"][i] = st.number_input(f"Kebisingan Bising - Percobaan {i+1} (dBA)", 30.0, 120.0, float(m7["bising_db"][i]), key=f"b_b_{i}")

        with t_col3:
            st.markdown("#### 💡 Modul 08: Pencahayaan (Lux)")
            for i in range(3):
                m8["normal_lux"][i] = st.number_input(f"Cahaya Normal - Percobaan {i+1} (Lux)", 1.0, 2000.0, float(m8["normal_lux"][i]), key=f"l_n_{i}")
            for i in range(3):
                m8["gelap_lux"][i] = st.number_input(f"Cahaya Gelap - Percobaan {i+1} (Lux)", 1.0, 2000.0, float(m8["gelap_lux"][i]), key=f"l_g_{i}")

        calc_all = compile_all_calculations()
        df_env = pd.DataFrame(calc_all["env_rows"], columns=[
            "Modul", "Parameter Uji", "Mean Kondisi 1", "Mean Kondisi 2",
            "Selisih", "Standar NAB / SNI", "p-value (Uji-t)", "Kesimpulan Statistik", "Analisis & Rekomendasi"
        ])
        st.markdown("#### 📊 Hasil Evaluasi Lingkungan Fisik & Uji Hipotesis Komparatif")
        st.dataframe(df_env, use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# HALAMAN 4: KALKULATOR POSTUR KERJA LENGKAP (RULA, OWAS, & REBA TERPADU)
# -----------------------------------------------------------------------------
elif st.session_state["nav_page"] == "Analisis Postur (RULA/OWAS/REBA)":
    st.subheader("📐 Kalkulator Evaluasi Postur Kerja Terintegrasi (RULA, OWAS, & REBA)")
    st.caption("Semua perubahan skor pada halaman ini otomatis memperbarui metrik Ringkasan Praktikum dan Tabel Modul 02.")

    records = st.session_state["modul_02"]["records"]
    rec_labels = [f"{r['id']} · {r['operator']} - {r['aktivitas']}" for r in records]
    selected_idx = st.selectbox("Pilih Aktivitas Postur untuk Diedit:", range(len(records)), format_func=lambda x: rec_labels[x])
    active_rec = records[selected_idx]

    c_meta1, c_meta2 = st.columns(2)
    active_rec["operator"] = c_meta1.text_input("Nama / Kode Operator", value=active_rec["operator"])
    active_rec["aktivitas"] = c_meta2.text_input("Deskripsi Aktivitas Kerja", value=active_rec["aktivitas"])

    tab_rula, tab_owas, tab_reba = st.tabs(["1️⃣ Metode RULA", "2️⃣ Metode OWAS", "3️⃣ Metode REBA"])

    with tab_rula:
        rp = active_rec["rula_params"]
        rc1, rc2 = st.columns(2)
        with rc1:
            st.markdown("**Grup A (Lengan Atas, Lengan Bawah, Pergelangan Tangan)**")
            rp["ua"] = st.slider("Skor Lengan Atas (Upper Arm 1-6)", 1, 6, int(rp["ua"]))
            rp["la"] = st.slider("Skor Lengan Bawah (Lower Arm 1-3)", 1, 3, int(rp["la"]))
            rp["wr"] = st.slider("Skor Pergelangan Tangan (Wrist 1-4)", 1, 4, int(rp["wr"]))
            rp["wt"] = st.slider("Putaran Pergelangan (Wrist Twist 1-2)", 1, 2, int(rp["wt"]))
            rp["ma"] = st.selectbox("Penggunaan Otot Grup A (0 atau 1)", [0, 1], index=int(rp["ma"]))
            rp["fa"] = st.slider("Skor Beban / Gaya Grup A (0-3)", 0, 3, int(rp["fa"]))
        with rc2:
            st.markdown("**Grup B (Leher, Punggung/Trunk, Kaki)**")
            rp["nk"] = st.slider("Skor Leher (Neck 1-6)", 1, 6, int(rp["nk"]))
            rp["tr"] = st.slider("Skor Punggung (Trunk 1-6)", 1, 6, int(rp["tr"]))
            rp["lg"] = st.slider("Skor Kaki (Legs 1=Seimbang, 2=Tidak Seimbang)", 1, 2, int(rp["lg"]))
            rp["mb"] = st.selectbox("Penggunaan Otot Grup B (0 atau 1)", [0, 1], index=int(rp["mb"]))
            rp["fb"] = st.slider("Skor Beban / Gaya Grup B (0-3)", 0, 3, int(rp["fb"]))

        rula_out = hitung_rula(rp["ua"], rp["la"], rp["wr"], rp["wt"], rp["nk"], rp["tr"], rp["lg"], rp["ma"], rp["fa"], rp["mb"], rp["fb"])
        st.success(f"**Grand Score RULA: {rula_out['grand_score']}** (Skor C={rula_out['score_c']}, Skor D={rula_out['score_d']}) → **{rula_out['kategori']}** | {rula_out['rekomendasi']}")

    with tab_owas:
        op = active_rec["owas_params"]
        oc1, oc2 = st.columns(2)
        with oc1:
            op["back"] = st.selectbox("1. Sikap Punggung (Back 1-4)", [1, 2, 3, 4], index=int(op["back"]) - 1,
                                      format_func=lambda x: {1: "1 - Lurus", 2: "2 - Membungkuk", 3: "3 - Memutar/Miring", 4: "4 - Membungkuk & Memutar"}[x])
            op["arms"] = st.selectbox("2. Sikap Lengan (Arms 1-3)", [1, 2, 3], index=int(op["arms"]) - 1,
                                      format_func=lambda x: {1: "1 - Kedua lengan di bawah bahu", 2: "2 - Satu lengan di atas bahu", 3: "3 - Kedua lengan di atas bahu"}[x])
        with oc2:
            op["legs"] = st.selectbox("3. Sikap Kaki (Legs 1-7)", [1, 2, 3, 4, 5, 6, 7], index=int(op["legs"]) - 1,
                                      format_func=lambda x: {1: "1 - Duduk", 2: "2 - Berdiri 2 kaki lurus", 3: "3 - Berdiri 1 kaki lurus", 4: "4 - Berdiri 2 lutut ditekuk", 5: "5 - Berdiri 1 lutut ditekuk", 6: "6 - Berlutut", 7: "7 - Berjalan/Bergerak"}[x])
            op["load"] = st.selectbox("4. Beban Kerja (Load 1-3)", [1, 2, 3], index=int(op["load"]) - 1,
                                      format_func=lambda x: {1: "1 - Beban < 10 kg", 2: "2 - Beban 10 kg - 20 kg", 3: "3 - Beban > 20 kg"}[x])

        owas_out = hitung_owas(op["back"], op["arms"], op["legs"], op["load"])
        st.success(f"**Kode OWAS: {owas_out['kode_owas']}** → **{owas_out['kategori']}** | {owas_out['rekomendasi']}")

    with tab_reba:
        rbp = active_rec["reba_params"]
        rbc1, rbc2 = st.columns(2)
        with rbc1:
            st.markdown("**Grup A (Leher, Punggung, Kaki + Beban)**")
            rbp["neck"] = st.slider("Skor Leher REBA (1-3)", 1, 3, int(rbp["neck"]))
            rbp["trunk"] = st.slider("Skor Punggung / Trunk REBA (1-5)", 1, 5, int(rbp["trunk"]))
            rbp["legs"] = st.slider("Skor Kaki REBA (1-4)", 1, 4, int(rbp["legs"]))
            rbp["load"] = st.slider("Skor Beban / Force REBA (0-3)", 0, 3, int(rbp["load"]))
        with rbc2:
            st.markdown("**Grup B (Lengan Atas, Lengan Bawah, Pergelangan + Coupling + Aktivitas)**")
            rbp["ua"] = st.slider("Skor Lengan Atas REBA (1-6)", 1, 6, int(rbp["ua"]))
            rbp["la"] = st.slider("Skor Lengan Bawah REBA (1-2)", 1, 2, int(rbp["la"]))
            rbp["wr"] = st.slider("Skor Pergelangan Tangan REBA (1-3)", 1, 3, int(rbp["wr"]))
            rbp["coup"] = st.slider("Skor Coupling / Genggaman (0-3)", 0, 3, int(rbp["coup"]))
            rbp["act"] = st.slider("Skor Aktivitas (0-3)", 0, 3, int(rbp["act"]))

        reba_out = hitung_reba(rbp["neck"], rbp["trunk"], rbp["legs"], rbp["load"], rbp["ua"], rbp["la"], rbp["wr"], rbp["coup"], rbp["act"])
        st.success(f"**Skor Akhir REBA: {reba_out['final_score']}** (Skor A={reba_out['score_a']}, Skor B={reba_out['score_b']}, Skor C={reba_out['score_c']}) → **{reba_out['kategori']}** | {reba_out['rekomendasi']}")

    if st.button("➕ Tambah Baris Evaluasi Postur Baru"):
        new_id = f"POST-0{len(records)+1}"
        records.append({
            "id": new_id,
            "operator": f"Operator {(len(records) % 2) + 1}",
            "aktivitas": f"Aktivitas Kerja Tambahan {len(records)+1}",
            "rula_params": {"ua": 2, "la": 2, "wr": 2, "wt": 1, "nk": 2, "tr": 2, "lg": 1, "ma": 0, "fa": 0, "mb": 0, "fb": 0},
            "owas_params": {"back": 1, "arms": 1, "legs": 2, "load": 1},
            "reba_params": {"neck": 1, "trunk": 2, "legs": 1, "load": 0, "ua": 2, "la": 1, "wr": 1, "coup": 0, "act": 1},
        })
        st.rerun()

# -----------------------------------------------------------------------------
# HALAMAN 5: LAPORAN EXCEL & CADANGAN SESI JSON
# -----------------------------------------------------------------------------
elif st.session_state["nav_page"] == "Laporan & Cadangan":
    st.subheader("📥 Unduh Laporan Praktikum Lengkap (.xlsx) & Cadangan Sesi (.json)")

    calc_results = compile_all_calculations()
    excel_bytes = export_session_to_excel(st.session_state, calc_results)
    json_str = export_session_to_json(st.session_state)

    col_dl1, col_dl2 = st.columns(2, gap="large")
    with col_dl1:
        st.markdown("""
        <div class="panel-card">
            <h4 style="margin-top:0; color:#4ade80;">📊 Laporan Praktikum Excel (.xlsx)</h4>
            <p style="font-size:0.88rem; color:#cbd5e1;">
                Berisi 7 Worksheet rapi (Identitas, Fisiologi %CVL, Postur RULA/OWAS/REBA, Pengukuran Waktu Kerja, Antropometri 32 Dimensi, Antropometri Lanjutan, serta Evaluasi Lingkungan Fisik).
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.download_button(
            label="⬇️ Unduh Laporan Excel Lengkap (.xlsx)",
            data=excel_bytes,
            file_name=f"Laporan_Ergonomi_{st.session_state['identitas']['kelas']}_{st.session_state['identitas']['kelompok'].replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col_dl2:
        st.markdown("""
        <div class="panel-card">
            <h4 style="margin-top:0; color:#4ade80;">💾 Cadangan Data Sesi (.json)</h4>
            <p style="font-size:0.88rem; color:#cbd5e1;">
                Simpan seluruh input data pengamatan ke file JSON lokal. Anda dapat mengunggah kembali file ini kapan saja untuk melanjutkan pengerjaan tanpa takut kehilangan data saat browser tertutup.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.download_button(
            label="⬇️ Unduh Cadangan Data (.json)",
            data=json_str.encode("utf-8"),
            file_name=f"Cadangan_Ergonomi_{st.session_state['identitas']['kelas']}.json",
            mime="application/json",
            use_container_width=True,
        )

    st.divider()
    st.markdown("#### 🔄 Pulihkan Data dari File Cadangan JSON")
    uploaded_json = st.file_uploader("Unggah file .json hasil cadangan sebelumnya:", type=["json"])
    if uploaded_json is not None:
        try:
            loaded = json.loads(uploaded_json.read().decode("utf-8"))
            if "identitas" in loaded:
                st.session_state["identitas"] = loaded["identitas"]
            if "modul_01_fisiologi" in loaded:
                st.session_state["modul_01"] = loaded["modul_01_fisiologi"]
            if "modul_02_postur" in loaded:
                st.session_state["modul_02"] = loaded["modul_02_postur"]
            if "modul_03_waktu_kerja" in loaded:
                st.session_state["modul_03"] = loaded["modul_03_waktu_kerja"]
            if "modul_04_antropometri_32" in loaded:
                st.session_state["modul_04"] = loaded["modul_04_antropometri_32"]
            if "modul_05_antropometri_lanjutan" in loaded:
                st.session_state["modul_05"] = loaded["modul_05_antropometri_lanjutan"]
            if "modul_06_temperatur" in loaded:
                st.session_state["modul_06"] = loaded["modul_06_temperatur"]
            if "modul_07_kebisingan" in loaded:
                st.session_state["modul_07"] = loaded["modul_07_kebisingan"]
            if "modul_08_pencahayaan" in loaded:
                st.session_state["modul_08"] = loaded["modul_08_pencahayaan"]
            if "analisis_modul" in loaded:
                st.session_state["analisis_modul"] = loaded["analisis_modul"]
            st.success("✅ Data sesi berhasil dipulihkan dari file JSON!")
        except Exception as e:
            st.error(f"Gagal membaca file JSON: {e}")
