import os
import json
import base64
import hashlib
from html import escape
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import streamlit as st

from utils.calculations import (
    ANTROPOMETRI_32_DIMENSI,
    hitung_fisiologi_cvl,
    hitung_pemulihan_nadi,
    hitung_perbandingan_waktu_kerja,
    hitung_rula,
    hitung_owas,
    hitung_reba,
    hitung_waktu_kerja,
    hitung_antropometri_statistik,
    hitung_lingkungan_perbandingan,
)
from utils.exporter import export_session_to_json, export_session_to_excel, restore_session_from_json
from utils.workspace import (
    create_project_file, read_project_file, normalize_project_name,
    cloud_save, cloud_list, cloud_load,
)
from utils.importer import make_excel_template, read_excel_observations
from utils.education import LESSONS, worked_example
from utils.module_report import export_module_pdf
from utils.table_editor import prepare_editor_scope, edit_table_rows
from utils.advanced_features import (
    hitung_niosh_lifting,
    bandingkan_skenario_niosh,
    hitung_snook_table,
    hitung_biomekanika_l5s1,
    buat_plot_kurva_normal,
    buat_plot_cad_stasiun_kerja,
    get_visual_angle_helper_svg,
    deteksi_postur_mediapipe,
    generate_pdf_report,
    simpan_ke_database_antropometri,
    ambil_rekap_database_populasi,
)

# -----------------------------------------------------------------------------
# 1. KONFIGURASI HALAMAN (WIDE LAYOUT & TEMA WIREFRAME LIGHT MINIMALIST)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="IE Toolkit | Praktikum Ergonomi",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    /* Paksa latar belakang aplikasi tetap terang bersih ala wireframe */
    .stApp {
        background-color: #f8fafc;
        color: #1e293b;
    }
    .block-container {
        max-width: 1260px;
        padding-top: 4.1rem !important;
        padding-bottom: 3rem;
    }
    header[data-testid="stHeader"] {
        background: rgba(248, 250, 252, 0.85);
        backdrop-filter: blur(6px);
        border-bottom: 1px solid #e2e8f0;
    }
    
    /* Header Navigasi Kiri Atas */
    .upb-top-left-fixed {
        position: fixed;
        top: 10px;
        left: 24px;
        z-index: 999999;
        display: flex;
        align-items: center;
        gap: 10px;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 6px 14px;
        height: 38px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        pointer-events: none;
    }
    .upb-top-left-fixed img {
        height: 24px;
        width: auto;
        object-fit: contain;
    }
    .upb-brand-title {
        color: #0f172a;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        white-space: nowrap;
    }

    /* Hero Banner Utama */
    .hero-card {
        background: linear-gradient(130deg, #f0fdf4, #ffffff 68%);
        border: 1px solid #bbf7d0;
        border-radius: 18px;
        padding: 28px 30px;
        margin-bottom: 16px;
        margin-top: 10px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    .hero-subtitle {
        color: #15803d;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .hero-title {
        color: #0f172a;
        font-size: clamp(1.5rem, 2.5vw, 2.3rem);
        font-weight: 700;
        margin: 0 0 6px 0;
    }
    .hero-desc {
        color: #64748b;
        font-size: 0.92rem;
        margin: 0;
    }

    /* Kartu Panel & Modul Minimalis */
    .panel-card, .module-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
        transition: all 0.2s ease;
    }
    .module-card:hover {
        border-color: #15803d;
        box-shadow: 0 4px 12px rgba(21, 128, 61, 0.08);
    }

    .badge-pill {
        display: inline-block;
        background-color: #f0fdf4;
        color: #15803d;
        border: 1px solid #bbf7d0;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 999px;
        margin-bottom: 10px;
    }
    .badge-done {
        display: inline-block;
        background-color: #f1f5f9;
        color: #475569;
        border: 1px solid #cbd5e1;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 999px;
        margin-left: 6px;
    }

    .mod-title {
        color: #0f172a;
        font-size: 1.15rem;
        font-weight: 700;
        margin: 0 0 6px 0;
    }
    .mod-desc {
        color: #64748b;
        font-size: 0.85rem;
        line-height: 1.45;
        min-height: 40px;
        margin-bottom: 12px;
    }
    .mod-footer {
        color: #94a3b8;
        font-size: 0.76rem;
        border-top: 1px solid #f1f5f9;
        padding-top: 8px;
        margin-top: 6px;
    }

    /* Kartu Informasi & Notifikasi Bersih */
    .emerald-notice {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-left: 4px solid #15803d;
        color: #166534;
        border-radius: 10px;
        padding: 13px 16px;
        font-size: 0.85rem;
        line-height: 1.45;
        margin-top: 10px;
    }

    .summary-item {
        border-bottom: 1px solid #f1f5f9;
        padding: 10px 0;
    }
    .summary-item:last-child {
        border-bottom: none;
    }
    .summary-val {
        color: #0f172a;
        font-weight: 700;
        font-size: 0.92rem;
    }
    .summary-sub {
        color: #64748b;
        font-size: 0.78rem;
    }

    /* Styling Tombol Streamlit Clean Light */
    div.stButton > button {
        background-color: #ffffff;
        color: #1e293b;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        font-weight: 600;
        height: 42px;
        width: 100%;
        transition: 0.2s;
    }
    div.stButton > button:hover {
        background-color: #f1f5f9;
        border-color: #15803d;
        color: #15803d;
    }
    div[data-testid="stButton"]:has(button[kind="primary"]) button {
        background: #166534;
        color: #ffffff;
        border-color: #166534;
    }
    div[data-testid="stButton"]:has(button[kind="primary"]) button:hover {
        background: #14532d;
        color: #ffffff;
    }
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 4px;
        gap: 2px;
        overflow-x: auto;
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        border-radius: 8px;
        font-weight: 600;
        white-space: nowrap;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        background: #dcfce7;
        color: #166534;
    }
    [data-testid="stTabs"] [data-baseweb="tab-panel"] {
        padding-top: 1rem;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:has(> [data-testid="stVerticalBlock"]) {
        border-radius: 14px;
    }
    div.stButton > button:focus-visible,
    div.stDownloadButton > button:focus-visible {
        outline: 3px solid #34d399;
        outline-offset: 3px;
    }
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 12px 16px;
    }
    [data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
    }
    @media (max-width: 850px) {
        .block-container {
            padding-top: 4rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
        }
        .upb-top-left-fixed { left: 10px; top: 10px; padding: 5px 9px; }
        .upb-brand-title { font-size: 0.67rem; }
        .hero-card { padding: 18px 16px; margin-top: 12px; }
        .hero-title { font-size: 1.3rem; line-height: 1.3; }
        .hero-desc { font-size: 0.85rem; }
        [data-testid="stTabs"] [data-baseweb="tab"] { font-size: 0.83rem; padding: 0.65rem; }
        .upb-top-left-fixed { display: none; }
        .panel-card, .module-card { padding: 15px 14px; }
        .mod-desc { min-height: 0; }
        div.stButton > button { min-height: 44px; height: auto; }
        div[data-testid="stHorizontalBlock"] { gap: 0.55rem; }
        div[data-testid="stMetric"] { padding: 0.45rem; }
        div[data-testid="stDataFrame"] { max-width: 100%; overflow-x: auto; }
        div[data-testid="stFileUploader"] { min-width: 0; }
    }
</style>
""", unsafe_allow_html=True)


def get_logo_html() -> str:
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
    st.session_state["ux_mode"] = "Pemula"
    st.session_state["ux_guide_dismissed"] = False
    st.session_state["project_name"] = "Praktikum Ergonomi - Proyek 1"
    st.session_state["module_done"] = {}
    st.session_state["_local_projects"] = {}

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
        "pemulihan": {
            "op1": {"P0": 82.0, "P1": 115.0, "P2": 86.0, "P3": 85.0, "P4": 83.0, "P5": 75.0},
            "op2": {"P0": 88.0, "P1": 111.0, "P2": 92.0, "P3": 92.0, "P4": 90.0, "P5": 86.0},
        },
    }

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
        "rating_rows": [
            {"Kode": kode, "Skor Schummard": 60.0,
             **{key: 0.0 for key in ("ABT", "PK", "PT", "KMT", "PERLT", "BB")},
             "p akhir": 1.0} for kode, _ in elemen_names
        ],
        "metode_terpilih": "Westinghouse",
    }

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

    st.session_state["modul_09"] = {
        "h_cm": 32.0,
        "v_cm": 60.0,
        "d_cm": 45.0,
        "a_deg": 15.0,
        "f_lift": 2.0,
        "durasi_angkat": "≤ 1 jam",
        "coupling": "Sedang (Fair)",
        "berat_beban": 16.0,
        "snook_aktivitas": "Angkat (Lifting)",
        "snook_jk": "Laki-laki",
        "snook_persentil": "P75",
        "bb_pekerja": 68.0,
        "sudut_punggung": 35.0,
    }

    # Skenario usulan terpisah dari data observasi, supaya simulasi tidak
    # mengubah input asli atau hasil laporan tanpa sepengetahuan pengguna.
    st.session_state["modul_09_simulasi"] = {
        "h_cm": 25.0, "v_cm": 75.0, "d_cm": 45.0, "a_deg": 0.0,
        "f_lift": 1.0, "durasi_angkat": "≤ 1 jam",
        "coupling": "Baik (Good)", "berat_beban": 12.0,
    }

    st.session_state["analisis_modul"] = {
        "Modul 01": "Tinjau hasil %CVL tiap operator dan sesuaikan rekomendasi dengan hasil perhitungan aktual.",
        "Modul 02": "Bandingkan skor RULA, OWAS, dan REBA pada tiap aktivitas; periksa kondisi postur saat observasi.",
        "Modul 03": "Periksa status keseragaman dan kecukupan tiap elemen pada tabel hasil sebelum menyimpulkan.",
        "Modul 04": "Periksa uji normalitas tiap dimensi sebelum memakai persentil parametrik untuk rancangan.",
        "Modul 05": "Bandingkan rancangan P5/P50/P95 dan kelonggaran dengan kebutuhan pengguna serta ukuran fasilitas.",
        "Modul 06": "Bandingkan suhu percobaan sebagai indikator awal; NAB panas resmi harus dinilai dengan ISBB dan beban kerja.",
        "Modul 07": "Tinjau hasil kebisingan pengukuran; kepatuhan NAB 8 jam memerlukan pengukuran pajanan ekuivalen.",
        "Modul 08": "Bandingkan iluminansi terhadap kebutuhan jenis pekerjaan yang diukur; periksa kondisi pengukuran.",
        "Modul 09": "Tinjau LI NIOSH sesuai frekuensi, durasi, dan postur angkat; Snook serta kompresi L5/S1 di sini merupakan estimasi edukatif.",
    }

    st.session_state["initialized"] = True


init_session_state()


# -----------------------------------------------------------------------------
# 3. FUNGSI KOMPILASI HASIL PERHITUNGAN UNTUK RINGKASAN, EXCEL, & PDF
# -----------------------------------------------------------------------------
def compile_all_calculations() -> dict:
    id_info = st.session_state["identitas"]
    m1 = st.session_state["modul_01"]

    m1_list = []
    configs_m1 = [
        (id_info["op1_nama"], m1["op1_akt1_nama"], id_info["op1_usia"], id_info["op1_jk"], m1["op1_akt1_dni"], m1["op1_akt1_dnk"]),
        (id_info["op1_nama"], m1["op1_akt2_nama"], id_info["op1_usia"], id_info["op1_jk"], m1["op1_akt2_dni"], m1["op1_akt2_dnk"]),
        (id_info["op2_nama"], m1["op2_akt1_nama"], id_info["op2_usia"], id_info["op2_jk"], m1["op2_akt1_dni"], m1["op2_akt1_dnk"]),
        (id_info["op2_nama"], m1["op2_akt2_nama"], id_info["op2_usia"], id_info["op2_jk"], m1["op2_akt2_dni"], m1["op2_akt2_dnk"]),
    ]
    m1_invalid = []
    for op_nama, akt_nama, usia, jk, dni, dnk in configs_m1:
        try:
            res = hitung_fisiologi_cvl(dni, dnk, int(usia), jk)
        except (ValueError, TypeError) as exc:
            m1_invalid.append(f"{op_nama} / {akt_nama}: {exc}")
            continue
        m1_list.append([
            op_nama, akt_nama, usia, dni, dnk,
            res["dn_max"], res["cvl_persen"], res["ke_bersih_kkal_menit"],
            res["kategori"], res["tindakan"]
        ])

    m1_recovery = []
    for op in ("op1", "op2"):
        points = m1.get("pemulihan", {}).get(op)
        if not points:
            continue
        try:
            recovery = hitung_pemulihan_nadi(points)
        except (ValueError, TypeError) as exc:
            m1_invalid.append(f"Pemulihan {id_info[op + '_nama']}: {exc}")
            continue
        m1_recovery.append([
            id_info[op + "_nama"], *(points[f"P{i}"] for i in range(6)),
            recovery["ecpt"], recovery["ecpm"], recovery["pemulihan_persen"], recovery["status"],
        ])

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

    m3_state = st.session_state["modul_03"]
    allow_total = m3_state["allowance_pribadi"] + m3_state["allowance_kelelahan"] + m3_state["allowance_hambatan"]
    m3_list = []
    m3_comparison = []
    m3_errors = []
    rating_map = {str(r.get("Kode")): r for r in m3_state.get("rating_rows", [])}
    selected_method = m3_state.get("metode_terpilih", "Westinghouse")
    for row in m3_state["df_siklus"]:
        obs = [row.get(f"S{i+1}", 0.0) for i in range(10)]
        profile = rating_map.get(str(row.get("Kode")), {})
        try:
            comparison = hitung_perbandingan_waktu_kerja(
                obs, westinghouse=m3_state["westinghouse"],
                skor_schummard=profile.get("Skor Schummard", 60),
                skor_kesulitan=profile, p_akhir=profile.get("p akhir", 1.0),
                allowance_pct=allow_total, k_level=m3_state["k_level"], s_level=m3_state["s_level"],
            )
        except (ValueError, TypeError) as exc:
            m3_errors.append(f"{row.get('Kode', '?')}: {exc}")
            continue
        res = comparison["results"].get(selected_method, comparison["results"]["Westinghouse"])
        if res:
            m3_list.append([
                row["Kode"], row["Elemen Kerja"], res["ws"], res["std"], res["bkb"], res["bka"],
                res["seragam"], res["n_prime"], res["cukup"], res["p_factor"], res["allowance_pct"],
                res["wn"], res["wb"], res["output_standar_per_jam"]
            ])
            for method, alternative in comparison["results"].items():
                m3_comparison.append([
                    row["Kode"], row["Elemen Kerja"], method, alternative["ws"],
                    round(comparison["factors"][method], 5), comparison["p1"],
                    comparison["p2"], comparison["total_kesulitan"],
                    alternative["allowance_pct"], alternative["wn"], alternative["wb"],
                    alternative["output_standar_per_jam"], alternative["n_prime"],
                    alternative["cukup"], alternative["seragam"],
                ])

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

    m6, m7, m8 = st.session_state["modul_06"], st.session_state["modul_07"], st.session_state["modul_08"]
    r6 = hitung_lingkungan_perbandingan(m6["dingin_suhu"], m6["panas_suhu"], "Dingin", "Panas", m6["nab_suhu"], "°C")
    r7 = hitung_lingkungan_perbandingan(m7["normal_db"], m7["bising_db"], "Normal", "Bising", m7["nab_db"], "dBA")
    r8 = hitung_lingkungan_perbandingan(m8["normal_lux"], m8["gelap_lux"], "Normal", "Gelap", m8["standar_lux"], "Lux")
    env_list = [
        ["Modul 06 - Temperatur", "Suhu Ruang (°C)", r6["Mean Dingin (°C)"], r6["Mean Panas (°C)"], r6["Selisih (°C)"], r6["Ambang Batas / Standar"], r6["p-value (Uji-t)"], r6["Kesimpulan Statistik"], st.session_state["analisis_modul"]["Modul 06"]],
        ["Modul 07 - Kebisingan", "Intensitas Suara (dBA)", r7["Mean Normal (dBA)"], r7["Mean Bising (dBA)"], r7["Selisih (dBA)"], r7["Ambang Batas / Standar"], r7["p-value (Uji-t)"], r7["Kesimpulan Statistik"], st.session_state["analisis_modul"]["Modul 07"]],
        ["Modul 08 - Pencahayaan", "Intensitas Cahaya (Lux)", r8["Mean Normal (Lux)"], r8["Mean Gelap (Lux)"], r8["Selisih (Lux)"], r8["Ambang Batas / Standar"], r8["p-value (Uji-t)"], r8["Kesimpulan Statistik"], st.session_state["analisis_modul"]["Modul 08"]],
    ]

    m9 = st.session_state["modul_09"]
    res_niosh = hitung_niosh_lifting(m9["h_cm"], m9["v_cm"], m9["d_cm"], m9["a_deg"], m9["f_lift"], m9["coupling"], m9["berat_beban"], m9.get("durasi_angkat", "≤ 1 jam"))
    res_bio = hitung_biomekanika_l5s1(m9["bb_pekerja"], m9["berat_beban"], m9["sudut_punggung"], m9["h_cm"])
    m9_summary = {
        "rwl": res_niosh["rwl"],
        "li": res_niosh["li"],
        "kategori": res_niosh["kategori"],
        "f_kompresi_n": res_bio["f_kompresi_n"],
        "status_l5s1": res_bio["kategori"],
    }
    simulasi = st.session_state.get("modul_09_simulasi")
    sim_summary = bandingkan_skenario_niosh(m9, simulasi) if simulasi else None

    return {
        "m1_rows": m1_list,
        "m1_recovery_rows": m1_recovery,
        "m1_errors": m1_invalid,
        "m2_rows": m2_list,
        "m3_rows": m3_list,
        "m3_comparison_rows": m3_comparison,
        "m3_errors": m3_errors,
        "m4_rows": m4_list,
        "m5_rows": m5_list,
        "env_rows": env_list,
        "m9_summary": m9_summary,
        "m9_simulasi_summary": sim_summary,
    }


# Setiap modul memiliki URL sendiri; navigasi antarlaman tetap menggunakan
# st.switch_page agar session_state dan data pengamatan tidak direset.
MODULE_PAGE_TITLES = {
    "modul-01": "Modul 01 - Fisiologi Kerja",
    "modul-02": "Modul 02 - Postur Kerja",
    "modul-03": "Modul 03 - Pengukuran Waktu Kerja",
    "modul-04": "Modul 04 - Antropometri 32 Dimensi",
    "modul-05": "Modul 05 - Antropometri Lanjutan",
    "modul-06": "Modul 06 - Temperatur",
    "modul-07": "Modul 07 - Kebisingan",
    "modul-08": "Modul 08 - Pencahayaan",
    "modul-09": "Modul 09 - Manual Material Handling (NIOSH, Snook & L5/S1)",
}
MODULE_ORDER = list(MODULE_PAGE_TITLES)
STATIC_PAGES = {
    "beranda": "Beranda",
    "daftar-modul": "Daftar Modul",
    "identitas": "Identitas",
    "analisis-postur": "Analisis Postur (RULA/OWAS/REBA)",
    "laporan": "Laporan & Cadangan",
    "dashboard": "Dashboard Kemajuan",
    "proyek": "Proyek Praktikum",
    "impor-excel": "Impor Excel",
    "ruang-belajar": "Ruang Belajar",
}


def activate_page(slug: str) -> None:
    st.session_state["_active_page_slug"] = slug
    if slug in MODULE_PAGE_TITLES:
        st.session_state["nav_page"] = "Modul Praktikum"
        st.session_state["selected_modul"] = MODULE_PAGE_TITLES[slug]
    else:
        st.session_state["nav_page"] = STATIC_PAGES[slug]


def page_handler(slug: str):
    return lambda: activate_page(slug)


PAGES = {
    slug: st.Page(page_handler(slug), title=title, url_path=slug,
                  default=slug == "beranda")
    for slug, title in {**STATIC_PAGES, **MODULE_PAGE_TITLES}.items()
}
st.navigation(list(PAGES.values()), position="hidden").run()


def go_to_page(slug: str) -> None:
    st.switch_page(PAGES[slug])


def render_module_navigation(place: str) -> None:
    slug = st.session_state["_active_page_slug"]
    idx = MODULE_ORDER.index(slug)
    back_col, prev_col, progress_col, next_col = st.columns([1.35, 1.25, 2.1, 1.25])
    with back_col:
        if st.button("← Daftar Modul", key=f"{place}_back_list", use_container_width=True):
            go_to_page("daftar-modul")
    with prev_col:
        if st.button("← Sebelumnya", key=f"{place}_prev", use_container_width=True, disabled=idx == 0):
            go_to_page(MODULE_ORDER[idx - 1])
    with progress_col:
        st.caption(f"Modul {idx + 1:02d} dari {len(MODULE_ORDER)} · Data tersimpan selama sesi aktif")
        st.progress((idx + 1) / len(MODULE_ORDER))
    with next_col:
        if st.button("Berikutnya →", key=f"{place}_next", use_container_width=True,
                     disabled=idx == len(MODULE_ORDER) - 1):
            go_to_page(MODULE_ORDER[idx + 1])


MODULE_GUIDANCE = {
    "01": "Ukur nadi istirahat, nadi kerja, dan P0–P5 setiap operator.",
    "02": "Periksa skor observasi postur; foto hanyalah bantuan yang harus diverifikasi.",
    "03": "Isi waktu pengamatan, tentukan penyesuaian, lalu bandingkan waktu baku.",
    "04": "Masukkan dimensi tubuh hasil pengukuran sebelum membaca persentil.",
    "05": "Masukkan dimensi kunci dan pilih persentil sebelum melihat desain CAD.",
    "06": "Catat suhu pada dua kondisi, tiga pengamatan setiap kondisi.",
    "07": "Catat dBA pada dua kondisi; bacaan sesaat bukan dosis kebisingan.",
    "08": "Catat intensitas cahaya pada dua kondisi dan cocokkan dengan tugas.",
    "09": "Pilih metode pemindahan material, masukkan parameter, lalu evaluasi hasil.",
}


def module_workspace_tabs(slug: str):
    """Alur visual konsisten pada sembilan modul, tanpa menghapus kalkulator lama."""
    number = slug.split("-")[-1]
    st.subheader(MODULE_PAGE_TITLES[slug])
    left, right = st.columns([2.5, 1], vertical_alignment="bottom")
    with left:
        st.caption(MODULE_GUIDANCE[number])
    with right:
        modes = ["Pemula", "Lanjutan"]
        selected = st.session_state.get("ux_mode", "Pemula")
        st.session_state["ux_mode"] = st.selectbox(
            "Tingkat tampilan", modes, index=modes.index(selected) if selected in modes else 0,
            key=f"ux_mode_{number}", help="Pemula menampilkan ringkasan; Lanjutan membuka detail perhitungan.",
        )
    if st.session_state["ux_mode"] == "Pemula":
        st.info("**Panduan:** Mulai dari tab Data, lanjutkan ke Hasil, lalu tulis Analisis. "
                "Buka tab Panduan & Laporan untuk melihat rumus dan menyimpan pekerjaan.", icon="💡")
    return st.tabs(["1 · Data", "2 · Hasil", "3 · Analisis", "4 · Panduan & Laporan"])


def reset_restored_widgets() -> None:
    """Loaded project/input must replace widget baselines from the old project."""
    for key in list(st.session_state):
        if key.startswith(("_ui_", "ling_", "done_", "ed_m", "op1_dn", "op2_dn", "sim_rula_")):
            st.session_state.pop(key, None)
    st.session_state.pop("_table_editor_scope", None)
    st.session_state["_cloud_last_signature"] = ""


def configured_project_db() -> str:
    try:
        return str(st.secrets.get("PROJECT_DATABASE_URL", "") or "")
    except Exception:
        return ""


def signed_in_user_id() -> str:
    try:
        user = st.user
        subject = user.get("sub") if user.is_logged_in else None
        return str(subject).strip() if subject else ""
    except (AttributeError, KeyError, TypeError):
        return ""


def render_dashboard() -> None:
    st.subheader("📊 Dashboard Kemajuan Praktikum")
    st.caption("Status selesai ditandai secara manual setelah hasil diperiksa; data contoh bukan bukti modul sudah selesai.")
    done = st.session_state["module_done"]
    count = sum(bool(done.get(slug)) for slug in MODULE_ORDER)
    a, b, c = st.columns(3)
    a.metric("Modul diperiksa", f"{count}/9")
    b.metric("Belum selesai", str(9-count))
    c.metric("Kemajuan", f"{count/9:.0%}")
    st.progress(count/9)
    st.caption(f"Proyek aktif: {st.session_state['project_name']}")
    cols = st.columns(3)
    for idx, slug in enumerate(MODULE_ORDER):
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"**{MODULE_PAGE_TITLES[slug]}**")
                st.write("✅ Sudah diperiksa" if done.get(slug) else "⏳ Belum ditandai")
                if st.button("Buka modul →", key=f"dash_{slug}", use_container_width=True):
                    go_to_page(slug)
    st.divider()
    st.markdown("#### Ringkasan angka latihan saat ini")
    res = compile_all_calculations()
    m3 = res.get("m3_rows", [])
    s = res.get("m9_summary", {})
    x, y, z = st.columns(3)
    x.metric("Pengamatan postur", len(st.session_state["modul_02"].get("records", [])))
    y.metric("Total waktu baku", f"{sum(r[12] for r in m3):.2f} detik")
    z.metric("NIOSH Lifting Index", str(s.get("li", "-")))
    st.info("Ringkasan tersebut berasal dari data yang saat ini ada di sesi, termasuk data contoh. "
            "Periksa hasil masing-masing modul sebelum membuat kesimpulan akademik.")


def render_project_manager() -> None:
    st.subheader("💾 Manajer Proyek Praktikum")
    st.caption("Beri nama proyek, simpan snapshot dalam sesi, lalu unduh file proyek. "
               "File .json dapat dibuka kembali di perangkat lain.")
    current_name = st.text_input("Nama proyek aktif", key="_project_name_edit")
    try:
        name = normalize_project_name(current_name)
        st.session_state["project_name"] = name
        serialized = create_project_file(name, st.session_state)
    except (ValueError, TypeError) as exc:
        st.warning(str(exc))
        serialized = None
    if serialized:
        st.download_button("⬇️ Simpan file proyek (.json) — bisa dibuka lagi kapan saja",
                           data=serialized.encode("utf-8"),
                           file_name="Proyek_Ergonomi.json", mime="application/json", use_container_width=True)
        if st.button("📌 Simpan snapshot di sesi ini", use_container_width=True):
            st.session_state["_local_projects"][name] = json.loads(export_session_to_json(st.session_state))
            st.success(f"Snapshot '{name}' tersimpan selama sesi ini.")
    options = list(st.session_state["_local_projects"])
    if options:
        selected = st.selectbox("Buka snapshot dalam sesi", options)
        if st.button("📂 Buka snapshot terpilih"):
            restore_session_from_json(st.session_state, st.session_state["_local_projects"][selected])
            st.session_state["project_name"] = selected
            st.session_state["_project_pending_name"] = selected
            reset_restored_widgets()
            st.rerun()
    uploaded = st.file_uploader("Impor file proyek (.json)", type=["json"], key="_project_upload")
    if uploaded is not None and st.button("📥 Buka proyek dari file"):
        try:
            imported_name, backup = read_project_file(uploaded.getvalue())
            restore_session_from_json(st.session_state, backup)
            st.session_state["project_name"] = imported_name
            st.session_state["_project_pending_name"] = imported_name
            reset_restored_widgets()
            st.session_state["_project_opened"] = True
            st.rerun()
        except ValueError as exc:
            st.error(f"Proyek tidak dibuka: {exc}")
    if st.session_state.pop("_project_opened", False):
        st.success("Proyek berhasil dibuka beserta data dan status modulnya.")

    st.divider()
    st.markdown("#### ☁️ Penyimpanan cloud pribadi (opsional)")
    db_url = configured_project_db()
    if not db_url:
        st.info("Cloud belum diaktifkan oleh pengelola. Gunakan file proyek JSON untuk "
                "penyimpanan permanen. Database server lokal tidak digunakan untuk proyek pribadi.")
        return
    owner = signed_in_user_id()
    if not owner:
        st.warning("Masuk dengan akun pribadi sebelum menyimpan ke cloud.")
        if hasattr(st, "login") and st.button("Masuk dengan akun terkonfigurasi"):
            st.login()
        return
    st.success("Akun terverifikasi. Proyek hanya ditampilkan untuk akun ini.")
    st.checkbox("Aktifkan simpan otomatis ke cloud saat data berubah", key="_cloud_autosave")
    if st.button("☁️ Simpan proyek ke cloud sekarang") and serialized:
        try:
            cloud_save(db_url, owner, name, json.loads(export_session_to_json(st.session_state)))
            st.success("Proyek berhasil tersimpan ke database cloud pribadi.")
        except Exception:
            st.error("Simpan cloud gagal. Periksa konfigurasi database bersama pengelola.")
    try:
        names = cloud_list(db_url, owner)
    except Exception:
        st.warning("Daftar proyek cloud tidak dapat dimuat. Coba lagi nanti.")
        names = []
    if names:
        selected = st.selectbox("Pilih proyek cloud", names)
        if st.button("📂 Buka proyek cloud"):
            try:
                backup = cloud_load(db_url, owner, selected)
                restore_session_from_json(st.session_state, backup)
                st.session_state["project_name"] = selected
                st.session_state["_project_pending_name"] = selected
                reset_restored_widgets()
                st.rerun()
            except Exception:
                st.error("Proyek cloud tidak dapat dibuka.")


def render_excel_import() -> None:
    st.subheader("📥 Impor Data Pengamatan dari Excel")
    st.caption("Unduh template, ubah angka contoh menjadi pengukuran sebenarnya, lalu unggah. "
               "Impor didukung untuk Modul 03–08; file diperiksa sebelum mengganti data aktif.")
    number = st.selectbox("Target modul", list(f"{i:02d}" for i in range(3, 9)),
                          format_func=lambda n: MODULE_PAGE_TITLES[f"modul-{n}"])
    current = st.session_state[f"modul_{number}"]
    st.download_button(f"⬇️ Unduh template Modul {number} (.xlsx)",
                       data=make_excel_template(number, st.session_state),
                       file_name=f"Template_Modul_{number}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    uploaded = st.file_uploader("Pilih file .xlsx sesuai template", type=["xlsx"], key=f"_import_excel_upload_{number}")
    if uploaded is not None:
        try:
            new_data = read_excel_observations(number, uploaded.getvalue(), current)
        except ValueError as exc:
            st.error(f"Validasi gagal: {exc}")
        else:
            st.success(f"Validasi berhasil untuk Modul {number}. Data lama belum diganti.")
            st.dataframe(pd.DataFrame(new_data.get({"03":"df_siklus","04":"df_32","05":"df_3dim"}.get(number), [])
                                        or [{k: new_data[k] for k in new_data if isinstance(new_data[k], list)}]),
                         use_container_width=True)
            if st.button(f"✅ Terapkan data ke Modul {number}"):
                st.session_state[f"modul_{number}"] = new_data
                st.session_state["module_done"][f"modul-{number}"] = False
                reset_restored_widgets()
                st.session_state["_import_completed"] = number
                st.rerun()
    if st.session_state.pop("_import_completed", None):
        st.success("Data Excel berhasil diterapkan. Buka modul untuk meninjau hasil perhitungan.")


def render_learning_center() -> None:
    st.subheader("📖 Ruang Belajar Ergonomi")
    st.caption("Ringkasan konsep, contoh substitusi berdasarkan data aktif, serta soal latihan.")
    number = st.selectbox("Pilih materi", list(LESSONS),
                          format_func=lambda n: f"Modul {n} — {LESSONS[n][0]}")
    title, theory, exercise, caution = LESSONS[number]
    st.markdown(f"### {title}")
    st.write(theory)
    st.markdown("#### Contoh penelusuran hasil")
    try:
        for step in worked_example(number, st.session_state):
            st.code(step, language=None)
    except (ValueError, TypeError, ZeroDivisionError) as exc:
        st.warning(f"Contoh belum dapat dihitung: {exc}")
    st.markdown("#### Latihan mandiri")
    st.info(exercise)
    st.warning(caution)
    if st.button("Buka lembar kerja modul ini →"):
        go_to_page(f"modul-{number}")


# -----------------------------------------------------------------------------
# 4. LOGO & NAMA UNIVERSITAS DI POJOK KIRI ATAS LAYAR + BAR MENU NAVIGASI
# -----------------------------------------------------------------------------
logo_tag = get_logo_html()
identitas_hero = st.session_state["identitas"]
hero_identitas = " · ".join((
    escape(str(identitas_hero["universitas"])),
    f"{escape(str(identitas_hero['prodi']))} ({escape(str(identitas_hero['kelas']))})",
))
st.markdown(f"""
<div class="upb-top-left-fixed">
    {logo_tag}
    <span class="upb-brand-title">UNIVERSITAS PELITA BANGSA</span>
</div>
""", unsafe_allow_html=True)

nav_options = [
    ("Beranda", "beranda"), ("Daftar Modul", "daftar-modul"),
    ("Identitas", "identitas"), ("Proyek Saya", "proyek"),
    ("Laporan", "laporan"),
]
nav_cols = st.columns(5)

for idx, (label, slug) in enumerate(nav_options):
    with nav_cols[idx]:
        is_active = (st.session_state["_active_page_slug"] == slug or
                     (slug == "daftar-modul" and st.session_state["_active_page_slug"] in MODULE_PAGE_TITLES))
        btn_label = f"● {label}" if is_active else label
        if st.button(btn_label, key=f"nav_btn_{idx}", use_container_width=True):
            go_to_page(slug)

with st.sidebar:
    st.markdown("### Menu pendukung")
    st.caption(f"Proyek: {st.session_state['project_name']}")
    for sidebar_slug, sidebar_label in (
        ("dashboard", "📊 Progres praktikum"),
        ("impor-excel", "📥 Impor data Excel"), ("ruang-belajar", "📖 Panduan & rumus"),
        ("analisis-postur", "📐 Input skor postur"),
    ):
        if st.button(sidebar_label, key=f"side_{sidebar_slug}", use_container_width=True):
            go_to_page(sidebar_slug)

# A table's source must remain unchanged during cell edits. When the user
# leaves the worksheet, its next visit will use the last saved values.
if st.session_state["nav_page"] != "Modul Praktikum":
    prepare_editor_scope(st.session_state, st.session_state["nav_page"])

if st.session_state["nav_page"] == "Beranda":
    st.markdown(f"""
    <div class="hero-card">
        <div class="hero-subtitle">{hero_identitas} · LABORATORIUM DIGITAL</div>
        <div class="hero-title">Praktikum ergonomi, langkah demi langkah.</div>
        <p class="hero-desc">Masukkan pengamatan, pahami perhitungannya, lalu susun laporan.
        Mulai dari identitas kelompok atau coba satu modul dengan data contoh.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.caption(f"IE Toolkit / {st.session_state['nav_page']} · {st.session_state['project_name']}")

wib_time = datetime.now(ZoneInfo("Asia/Jakarta"))
total_postur_records = len(st.session_state["modul_02"]["records"]) * 3
total_bukti_gambar = st.session_state["modul_02"]["bukti_gambar_count"]

# -----------------------------------------------------------------------------
# HALAMAN 1: BERANDA (DASHBOARD MODUL & RINGKASAN)
# -----------------------------------------------------------------------------
if st.session_state["nav_page"] in ("Beranda", "Daftar Modul"):
    if st.session_state["nav_page"] == "Beranda":
        start_col, demo_col = st.columns([1, 1], gap="medium")
        with start_col:
            if st.button("Mulai praktikum →", key="home_start", type="primary", use_container_width=True):
                go_to_page("identitas")
        with demo_col:
            if st.button("Coba Modul 01 dengan data contoh", key="home_demo", use_container_width=True):
                go_to_page("modul-01")

        done_count = sum(bool(st.session_state["module_done"].get(s)) for s in MODULE_ORDER)
        st.caption(f"Proyek: {st.session_state['project_name']} · {done_count} dari 9 modul ditandai selesai · "
                   "Data contoh belum dianggap hasil praktikum nyata.")
        st.progress(done_count / len(MODULE_ORDER))
        if not st.session_state.get("ux_guide_dismissed", False):
            with st.container(border=True):
                st.markdown("#### 👋 Baru pertama kali? Mulai dari sini")
                a, b, c = st.columns(3)
                a.markdown("**01 · Isi identitas**  \nNama kelompok dan operator.")
                b.markdown("**02 · Kerjakan modul**  \nGanti data contoh dengan pengamatan.")
                c.markdown("**03 · Unduh laporan**  \nPeriksa hasil lalu ekspor PDF/Excel.")
                st.caption("Semua data tersimpan selama sesi aktif; gunakan Proyek Saya atau ekspor JSON "
                           "sebelum menutup tab. Website ini alat bantu praktikum, bukan diagnosis atau sertifikasi K3.")
                if st.button("Saya mengerti, tutup panduan", key="home_dismiss_guide"):
                    st.session_state["ux_guide_dismissed"] = True
                    st.rerun()

        with st.expander("Akses cepat & alat pendukung", expanded=False):
            tools_cols = st.columns(4)
            for col, (label, slug) in zip(tools_cols, (
                ("📊 Dashboard", "dashboard"), ("💾 Proyek", "proyek"),
                ("📥 Impor Excel", "impor-excel"), ("📖 Belajar", "ruang-belajar"),
            )):
                with col:
                    if st.button(label, key=f"home_tool_{slug}", use_container_width=True):
                        go_to_page(slug)
    if st.session_state["nav_page"] == "Daftar Modul":
        st.subheader("📚 Daftar 9 Modul Praktikum")
        st.caption("Klik kartu untuk masuk ke halaman khusus modul. Tombol Back browser dan navigasi antarmodul dapat digunakan.")
    left_col, right_col = st.columns([0.85, 2.8], gap="large")

    with left_col:
        st.markdown(f"""
        <div class="panel-card">
            <h4 style="margin:0 0 12px 0; color:#0f172a; font-size:1.05rem;">Sekilas aplikasi</h4>
            <div class="summary-item">
                <div class="summary-val">{wib_time.strftime('%d-%m-%Y · %H:%M WIB')}</div>
                <div class="summary-sub">Waktu Server Lokal (Asia/Jakarta)</div>
            </div>
            <div class="summary-item"><div class="summary-val">9 modul terintegrasi</div>
                <div class="summary-sub">Dari fisiologi hingga pemindahan material</div></div>
            <div class="summary-item"><div class="summary-val">Laporan PDF & Excel</div>
                <div class="summary-sub">Hasil dan rumus bisa ditelusuri kembali</div></div>
        </div>
        """, unsafe_allow_html=True)
        if st.session_state["nav_page"] == "Beranda":
            if st.button("Lihat daftar semua modul →", key="home_all_modules", use_container_width=True):
                go_to_page("daftar-modul")

    with right_col:
        st.markdown("#### Pilih modul yang ingin dikerjakan")
        search_q = st.text_input(
            "Cari modul",
            placeholder="Cari berdasarkan nama atau nomor modul (misal: NIOSH, Antropometri, RULA, 09)...",
            label_visibility="collapsed",
        ).strip().lower()

        modules_meta = [
            ("Modul 01", "Fisiologi Kerja", "Dua operator, kondisi normal dan setelah aktivitas, nadi kerja, konsumsi energi serta perhitungan %CVL.", "modul-01"),
            ("Modul 02", "Postur Kerja & AI Pose", "Evaluasi postur kerja terpadu (RULA, OWAS, REBA) dilengkapi deteksi sudut otomatis dari foto.", "modul-02"),
            ("Modul 03", "Pengukuran Waktu Kerja", "Tujuh elemen kerja, rating Westinghouse, allowance, uji keseragaman, kecukupan & waktu baku.", "modul-03"),
            ("Modul 04", "Antropometri (32 Dimensi)", "32 dimensi tubuh, uji normalitas Shapiro-Wilk, kurva Gaussian interaktif, dan Database Populasi.", "modul-04"),
            ("Modul 05", "Antropometri Lanjutan & CAD 2D", "Uji keseragaman, kecukupan data, serta blueprint visual 2D kursi & meja stasiun kerja.", "modul-05"),
            ("Modul 06", "Temperatur Ruang", "Perbandingan kondisi dingin/panas beserta uji-t dan indikator awal; NAB iklim kerja memerlukan ISBB.", "modul-06"),
            ("Modul 07", "Kebisingan (dBA)", "Perbandingan kondisi normal/bising (dBA) beserta evaluasi pajanan suara.", "modul-07"),
            ("Modul 08", "Pencahayaan (Lux)", "Perbandingan kondisi normal/gelap (Lux) beserta evaluasi standar pencahayaan.", "modul-08"),
            ("Modul 09", "MMH (NIOSH, Snook & L5/S1)", "RWL & Lifting Index NIOSH, simulasi Snook, serta estimasi biomekanika L5/S1.", "modul-09"),
        ]

        filtered_mods = [
            m for m in modules_meta
            if search_q == "" or search_q in m[0].lower() or search_q in m[1].lower() or search_q in m[2].lower()
        ]

        mod_cols = st.columns(2, gap="medium")
        for idx, (m_code, m_title, m_desc, page_slug) in enumerate(filtered_mods):
            with mod_cols[idx % 2]:
                st.markdown(f"""
                <div class="module-card">
                    <span class="badge-pill">{m_code}</span>
                    <span class="badge-done">{'Sudah diperiksa' if st.session_state['module_done'].get(page_slug) else 'Belum diperiksa'}</span>
                    <div class="mod-title">{m_title}</div>
                    <div class="mod-desc">{m_desc}</div>
                    <div class="mod-footer">Teknik Industri · Data terintegrasi ke Laporan PDF & Excel</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Buka lembar kerja {m_code}", key=f"open_{m_code}", use_container_width=True):
                    go_to_page(page_slug)

# -----------------------------------------------------------------------------
# ALAT BARU: DASHBOARD, PROYEK, IMPOR EXCEL, DAN RUANG BELAJAR
# -----------------------------------------------------------------------------
elif st.session_state["nav_page"] == "Dashboard Kemajuan":
    render_dashboard()

elif st.session_state["nav_page"] == "Proyek Praktikum":
    if "_project_pending_name" in st.session_state:
        st.session_state["_project_name_edit"] = st.session_state.pop("_project_pending_name")
    st.session_state.setdefault("_project_name_edit", st.session_state["project_name"])
    render_project_manager()

elif st.session_state["nav_page"] == "Impor Excel":
    render_excel_import()

elif st.session_state["nav_page"] == "Ruang Belajar":
    render_learning_center()

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
# HALAMAN 3: MODUL PRAKTIKUM (01 s/d 09)
# -----------------------------------------------------------------------------
elif st.session_state["nav_page"] == "Modul Praktikum":
    chosen = MODULE_PAGE_TITLES[st.session_state["_active_page_slug"]]
    render_module_navigation("atas")
    prepare_editor_scope(st.session_state, f"Modul Praktikum:{chosen}")
    step_tabs = module_workspace_tabs(st.session_state["_active_page_slug"])

    # --- MODUL 01: FISIOLOGI ---
    if chosen == "Modul 01 - Fisiologi Kerja":
        m1 = st.session_state["modul_01"]
        id_info = st.session_state["identitas"]


        with step_tabs[0]:
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

            st.markdown("#### 💓 Pemulihan Denyut Nadi (P0–P5), ECPT & ECPM")
            st.caption("Masukkan nadi terukur dalam bpm. P0 = sebelum kerja; P1–P5 = pengamatan saat/setelah aktivitas sesuai protokol praktikum. "
                       "Contoh isian awal hanya ilustrasi dan harus diganti dengan hasil pengamatan.")
            m1.setdefault("pemulihan", {})
            pulse_defaults = {"op1": (82, 115, 86, 85, 83, 75), "op2": (88, 111, 92, 92, 90, 86)}
            recovery_cols = st.columns(2, gap="large")
            for idx, op in enumerate(("op1", "op2")):
                with recovery_cols[idx]:
                    st.markdown(f"**{id_info[op + '_nama']}**")
                    points = m1["pemulihan"].setdefault(op, {f"P{i}": float(p) for i, p in enumerate(pulse_defaults[op])})
                    for group in (("P0", "P1", "P2"), ("P3", "P4", "P5")):
                        cols = st.columns(3)
                        for col, label in zip(cols, group):
                            points[label] = col.number_input(
                                f"{label} (bpm) · {op.upper()}", min_value=30.0, max_value=250.0,
                                value=float(points.get(label, pulse_defaults[op][int(label[1])])), step=1.0,
                                key=f"pulse_{op}_{label}",
                            )

        with step_tabs[1]:
            calc_all = compile_all_calculations()
            df_m1 = pd.DataFrame(calc_all["m1_rows"], columns=[
                "Operator", "Aktivitas", "Usia (th)", "DN Istirahat", "DN Kerja",
                "DN Maks", "%CVL (%)", "Konsumsi Energi Bersih (kkal/mnt)", "Kategori Beban", "Rekomendasi"
            ])
            st.markdown("#### 📊 Hasil Perhitungan Fisiologi Kerja (%CVL & Konsumsi Energi)")
            st.dataframe(df_m1, use_container_width=True, hide_index=True)

            for message in calc_all.get("m1_errors", []):
                st.error(f"Periksa data: {message}")

            calc_all = compile_all_calculations()
            recovery_rows = calc_all.get("m1_recovery_rows", [])
            if recovery_rows:
                st.dataframe(pd.DataFrame(recovery_rows, columns=[
                    "Operator", "P0", "P1", "P2", "P3", "P4", "P5", "ECPT (bpm)",
                    "ECPM (bpm)", "Pemulihan P1→P5 (%)", "Catatan",
                ]), use_container_width=True, hide_index=True)
                chart = pd.DataFrame({r[0]: r[1:7] for r in recovery_rows}, index=[f"P{i}" for i in range(6)])
                st.line_chart(chart, x_label="Titik pengamatan", y_label="Denyut nadi (bpm)")
            with st.expander("🔎 Rumus dan interpretasi ECPT/ECPM", expanded=False):
                st.latex(r"ECPT = \frac{P3+P4+P5}{3}-P0")
                st.latex(r"ECPM = (P1+P2-P3)-\frac{P3+P4+P5}{3}")
                st.caption("Sesuai rumus di pedoman praktikum Modul 01 (MODUL-1-8.docx). "
                           "Meski nama historisnya *Extra Calorie*, operasi ini menggunakan nadi: satuan selisihnya bpm, "
                           "**bukan energi kkal**. Nilai negatif dipertahankan untuk analisis, bukan dipaksa nol.")

            high_cvl = [r for r in calc_all["m1_rows"] if r[6] > 30.0]
            if high_cvl:
                st.warning(f"⚠️ **Validasi Fisiologi Otomatis:** Terdapat {len(high_cvl)} aktivitas dengan nilai **%CVL > 30%** ({', '.join(r[1] for r in high_cvl)}). Diperlukan penjadwalan waktu istirahat atau rotasi operator.")
            elif not calc_all.get("m1_errors"):
                st.success("✅ **Validasi Fisiologi Otomatis:** Seluruh aktivitas memiliki beban kardiovaskular %CVL ≤ 30% (Aman tanpa kelelahan berarti).")

        with step_tabs[2]:
            st.session_state["analisis_modul"]["Modul 01"] = st.text_area(
                "Analisis & Pembahasan Modul 01:", value=st.session_state["analisis_modul"]["Modul 01"]
            )

    # --- MODUL 02: POSTUR KERJA + AI POSE ESTIMATION ---
    elif chosen == "Modul 02 - Postur Kerja":
        with step_tabs[0]:
            st.markdown("##### 🤖 Deteksi Sudut Postur Otomatis (Unggah Foto atau Potret dari Kamera)")
            tab_upload, tab_kamera = st.tabs(["📁 Unggah File Foto (JPG/PNG)", "📸 Potret Langsung dari Kamera"])

            semua_gambar = []

            with tab_upload:
                uploaded_imgs = st.file_uploader(
                    "Pilih satu atau beberapa foto postur kerja:",
                    type=["png", "jpg", "jpeg"],
                    accept_multiple_files=True,
                    key="upload_m2"
                )
                if uploaded_imgs:
                    semua_gambar.extend(uploaded_imgs)

            with tab_kamera:
                st.caption("Gunakan kamera laptop (Webcam) atau kamera belakang HP saat praktikum berlangsung.")
                aktifkan_kamera = st.checkbox("🟢 Aktifkan Kamera Perangkat", value=False)
                if aktifkan_kamera:
                    cam_img = st.camera_input("Arahkan kamera ke samping tubuh operator lalu klik 'Take Photo'")
                    if cam_img is not None:
                        cam_img.name = f"Kamera_Postur_{datetime.now().strftime('%H%M%S')}.jpg"
                        semua_gambar.append(cam_img)

            if semua_gambar:
                st.session_state["modul_02"]["bukti_gambar_count"] = len(semua_gambar)
                records = st.session_state["modul_02"]["records"]
                opsi_target = [f"{r['id']} · {r['operator']} ({r['aktivitas']})" for r in records]

                for i, img_f in enumerate(semua_gambar):
                    st.divider()
                    pose_res = deteksi_postur_mediapipe(img_f)
                    p_col1, p_col2 = st.columns([1.1, 1.9], gap="medium")
                    with p_col1:
                        st.image(pose_res["annotated_image"], caption=f"{img_f.name} ({pose_res['mode']})", use_container_width=True)
                    with p_col2:
                        st.markdown(f"**Hasil Ekstraksi Sudut Tubuh (`{img_f.name}`):**")
                        st.json(pose_res["sudut"])
                        rek = pose_res.get("skor_rekomendasi")
                        if not pose_res.get("valid_detection") or not rek:
                            st.warning("Pose manusia belum terdeteksi dengan andal. Skor otomatis tidak tersedia; "
                                       "unggah foto yang memperlihatkan seluruh tubuh atau masukkan skor secara manual.")
                        else:
                            st.info(
                                f"💡 **Saran skor sementara (verifikasi manual):** Lengan Atas = **{rek['ua']}**, "
                                f"Lengan Bawah = **{rek['la']}**, Leher = **{rek['nk']}**, Punggung = **{rek['tr']}**"
                            )
                            target_idx = st.selectbox(
                                "Pilih Aktivitas Tujuan:", range(len(records)),
                                format_func=lambda x: opsi_target[x], key=f"target_rec_{i}"
                            )
                            if st.button(f"⚡ Terapkan Skor ke {records[target_idx]['id']}", key=f"apply_pose_{i}"):
                                rec_target = st.session_state["modul_02"]["records"][target_idx]
                                rec_target["rula_params"].update(rek)
                                rec_target["reba_params"].update({
                                    "ua": rek["ua"], "la": min(2, rek["la"]),
                                    "neck": min(3, rek["nk"]), "trunk": rek["tr"]
                                })
                                st.success(f"Skor RULA & REBA pada {rec_target['id']} berhasil diperbarui dari foto!")
                                st.rerun()

            st.divider()
            if st.button("🔧 Buka Kalkulator Input Skor RULA / OWAS / REBA Detail"):
                go_to_page("analisis-postur")

            with st.expander("🔄 Simulasi perbaikan postur RULA (tanpa mengubah observasi)"):
                st.caption("Gunakan skor contoh usulan untuk memahami perubahan grand score; "
                           "nilai resmi harus diperoleh dari observasi setelah perbaikan.")
                rec = st.session_state["modul_02"]["records"][0]
                original = rec["rula_params"]
                rula_before = hitung_rula(original["ua"], original["la"], original["wr"], original["wt"],
                                         original["nk"], original["tr"], original["lg"], original["ma"],
                                         original["fa"], original["mb"], original["fb"])
                r1, r2, r3 = st.columns(3)
                proposed_ua = r1.slider("Usulan skor lengan atas", 1, 6, int(original["ua"]), key="sim_rula_ua")
                proposed_nk = r2.slider("Usulan skor leher", 1, 6, int(original["nk"]), key="sim_rula_nk")
                proposed_tr = r3.slider("Usulan skor punggung", 1, 6, int(original["tr"]), key="sim_rula_tr")
                rula_after = hitung_rula(proposed_ua, original["la"], original["wr"], original["wt"],
                                        proposed_nk, proposed_tr, original["lg"], original["ma"],
                                        original["fa"], original["mb"], original["fb"])
                before, after = rula_before["grand_score"], rula_after["grand_score"]
                r1.metric("RULA sebelum", before)
                r2.metric("RULA usulan", after)
                r3.metric("Perubahan skor", f"{after-before:+d}")
                st.caption("Simulasi hanya mengganti tiga komponen postur; parameter lain tetap. "
                           "Penurunan skor tidak sama dengan persentase penurunan risiko cedera.")

        with step_tabs[1]:
            calc_all = compile_all_calculations()
            df_m2 = pd.DataFrame(calc_all["m2_rows"], columns=[
                "Operator", "Aktivitas", "Metode", "Skor / Kode Akhir", "Action Level", "Kategori Risiko", "Rekomendasi Perbaikan"
            ])
            st.dataframe(df_m2, use_container_width=True, hide_index=True)

        with step_tabs[2]:
            st.session_state["analisis_modul"]["Modul 02"] = st.text_area(
                "Analisis & Pembahasan Modul 02:", value=st.session_state["analisis_modul"]["Modul 02"]
            )

    # --- MODUL 03: PENGUKURAN WAKTU KERJA ---
    elif chosen == "Modul 03 - Pengukuran Waktu Kerja":
        m3 = st.session_state["modul_03"]

        with step_tabs[0]:
            st.markdown("##### 1. Tabel Waktu Siklus Pengamatan (10 Siklus dalam Detik)")
            m3["df_siklus"] = edit_table_rows(
                st.session_state, m3["df_siklus"], "ed_m3", st.data_editor,
                use_container_width=True, num_rows="dynamic",
            )

            st.markdown("##### 2. Penyesuaian Westinghouse & Kelonggaran (Allowance)")
            w1, w2, w3, w4 = st.columns(4)
            m3["westinghouse"]["skill"] = w1.number_input("Skill (Keterampilan)", -0.22, 0.15, float(m3["westinghouse"]["skill"]), step=0.01)
            m3["westinghouse"]["effort"] = w2.number_input("Effort (Usaha)", -0.17, 0.13, float(m3["westinghouse"]["effort"]), step=0.01)
            m3["westinghouse"]["condition"] = w3.number_input("Condition (Kondisi)", -0.07, 0.06, float(m3["westinghouse"]["condition"]), step=0.01)
            m3["westinghouse"]["consistency"] = w4.number_input("Consistency (Konsistensi)", -0.04, 0.04, float(m3["westinghouse"]["consistency"]), step=0.01)

            al1, al2, al3 = st.columns(3)
            m3["allowance_pribadi"] = al1.number_input("Kelonggaran Kebutuhan Pribadi (%)", 0.0, 20.0, float(m3["allowance_pribadi"]), step=0.5)
            m3["allowance_kelelahan"] = al2.number_input("Kelonggaran Menghilangkan Kelelahan (%)", 0.0, 30.0, float(m3["allowance_kelelahan"]), step=0.5)
            m3["allowance_hambatan"] = al3.number_input("Kelonggaran Hambatan Tak Terhindarkan (%)", 0.0, 20.0, float(m3["allowance_hambatan"]), step=0.5)

            st.markdown("##### 3. Schummard, Tingkat Kesulitan Objektif, dan Penyesuaian Akhir")
            st.caption("Setiap elemen memiliki skor Schummard (p1 = skor/60), enam skor kesulitan (p2 = 1 + Σ skor/100), "
                       "dan p akhir manual. Westinghouse berlaku sama untuk seluruh elemen; sesuaikan skor dengan pengamatan.")
            profile_map = {str(item.get("Kode")): item for item in m3.get("rating_rows", [])}
            rating_rows = []
            for item in m3["df_siklus"]:
                code = str(item.get("Kode", "")).strip()
                if not code:
                    continue
                profile = profile_map.get(code, {})
                rating_rows.append({
                    "Kode": code,
                    "Skor Schummard": float(profile.get("Skor Schummard", 60)),
                    **{key: float(profile.get(key, 0)) for key in ("ABT", "PK", "PT", "KMT", "PERLT", "BB")},
                    "p akhir": float(profile.get("p akhir", 1)),
                })
            # Pergantian kode/jumlah elemen harus membangun ulang basis editor.
            rating_scope = hashlib.sha256("|".join(r["Kode"] for r in rating_rows).encode()).hexdigest()[:10]
            m3["rating_rows"] = edit_table_rows(
                st.session_state, rating_rows, f"ed_m3_rating_{rating_scope}", st.data_editor,
                use_container_width=True, num_rows="fixed", hide_index=True, disabled=["Kode"],
            ) if rating_rows else []
            st.caption("ABT: anggota badan terpakai, PK: pedal kaki, PT: penggunaan tangan, "
                       "KMT: koordinasi mata-tangan, PERLT: peralatan, BB: berat beban. "
                       "p akhir adalah keputusan praktikan, **bukan rata-rata otomatis** ketiga metode.")
            method_options = ["Westinghouse", "Schummard", "Objektif", "Akhir (manual)"]
            current_method = m3.get("metode_terpilih", "Westinghouse")
            m3["metode_terpilih"] = st.selectbox(
                "Metode yang digunakan untuk hasil utama, total waktu baku, dan kapasitas:",
                method_options, index=method_options.index(current_method) if current_method in method_options else 0,
            )

        with step_tabs[1]:
            calc_all = compile_all_calculations()
            for message in calc_all.get("m3_errors", []):
                st.error(f"Elemen belum dapat dihitung: {message}")
            df_res_m3 = pd.DataFrame(calc_all["m3_rows"], columns=[
                "Kode", "Elemen Kerja", "Ws (dtk)", "SD", "BKB", "BKA",
                "Uji Keseragaman", "N'", "Uji Kecukupan", "Faktor p", "Allowance (%)", "Wn (dtk)", "Wb (dtk)", "Output Standar (unit/jam)"
            ])
            st.markdown("##### 4. Hasil Perhitungan Utama, Waktu Normal, Waktu Baku & Uji Data")
            st.dataframe(df_res_m3, use_container_width=True, hide_index=True)
            with st.expander("Bandingkan empat metode & lihat rumus", expanded=st.session_state["ux_mode"] == "Lanjutan"):
                st.markdown("##### 5. Perbandingan Empat Metode per Elemen")
                df_compare = pd.DataFrame(calc_all.get("m3_comparison_rows", []), columns=[
                    "Kode", "Elemen Kerja", "Metode", "Ws (dtk)", "Faktor p", "Schummard p1",
                    "Objektif p2", "Total kesulitan", "Allowance (%)", "Wn (dtk)", "Wb (dtk)",
                    "Output (unit/jam)", "N'", "Uji Kecukupan", "Uji Keseragaman",
                ])
                st.dataframe(df_compare, use_container_width=True, hide_index=True)
                if not df_compare.empty:
                    recap = df_compare.groupby("Metode", sort=False).agg(
                        **{"Total Wb (detik)": ("Wb (dtk)", "sum"), "Jumlah elemen": ("Kode", "count")}
                    ).reset_index()
                    recap["Kapasitas (unit/jam)"] = 3600 / recap["Total Wb (detik)"].replace(0, np.nan)
                    st.dataframe(recap, use_container_width=True, hide_index=True)
                    st.caption("Kapasitas gabungan = 3600 / Σ Wb hanya untuk urutan elemen yang membentuk satu unit produk. "
                               "Output per elemen tidak boleh dijumlahkan sebagai output produk.")
                with st.container(border=True):
                    st.markdown("**🧮 Cara memperoleh faktor penyesuaian**")
                    st.latex(r"p_{Schummard}=\frac{skor}{60}")
                    st.latex(r"p_{Objektif}=p_{Schummard}\left(1+\frac{ABT+PK+PT+KMT+PERLT+BB}{100}\right)")
                    st.latex(r"p_{Westinghouse}=1+skill+effort+condition+consistency")
                    st.latex(r"W_n=W_s\cdot p; \quad W_b=\frac{W_n}{1-a/100}; \quad Output=\frac{3600}{W_b}")
                    st.caption("Acuan metode Schummard/Objektif: panduan praktikum Modul 03 (MODUL-1-8.docx). "
                               "Uji keseragaman memakai batas rata-rata ± k·SD; kecukupan memakai N'.")
            tidak_cukup = [r[0] for r in calc_all["m3_rows"] if "Tidak" in str(r[8]) or "Belum" in str(r[8])]
            tidak_seragam = [r[0] for r in calc_all["m3_rows"] if "Tidak" in str(r[6])]
            if tidak_seragam or tidak_cukup or calc_all.get("m3_errors"):
                st.error(f"⚠️ **Peringatan Validasi Statistik:** Elemen tidak seragam: {tidak_seragam or 'Tidak ada'} | Elemen belum cukup (N < N'): {tidak_cukup or 'Tidak ada'}. Lakukan pengambilan sampel tambahan atau revisi data ekstrem (outlier).")
            else:
                st.success("✅ **Validasi Statistik Time Study:** Seluruh elemen kerja telah **Seragam (dalam batas BKA-BKB)** dan **Cukup (N ≥ N')**.")

            total_wb = df_res_m3["Wb (dtk)"].sum() if not df_res_m3.empty else 0.0
            if len(df_res_m3) == len(m3["df_siklus"]) and total_wb > 0:
                st.metric(f"Total Waktu Baku — {m3['metode_terpilih']} (Σ Wb)",
                          f"{total_wb:.2f} detik/unit", f"Kapasitas: {3600/total_wb:.1f} unit/jam")
            else:
                st.warning("Total waktu baku produk belum ditampilkan karena ada elemen tanpa hasil valid.")

        with step_tabs[2]:
            st.session_state["analisis_modul"]["Modul 03"] = st.text_area(
                "Analisis & Pembahasan Modul 03:", value=st.session_state["analisis_modul"]["Modul 03"]
            )

    # --- MODUL 04: ANTROPOMETRI 32 DIMENSI ---
    elif chosen == "Modul 04 - Antropometri 32 Dimensi":
        with step_tabs[0]:
            m4 = st.session_state["modul_04"]
            m4["df_32"] = edit_table_rows(
                st.session_state, m4["df_32"], "ed_m4", st.data_editor,
                use_container_width=True, height=380,
            )

        with step_tabs[1]:
            calc_all = compile_all_calculations()
            df_res_m4 = pd.DataFrame(calc_all["m4_rows"], columns=[
                "Kode", "Nama Dimensi Tubuh", "Mean (cm)", "SD (cm)",
                "P5 (cm)", "P10 (cm)", "P50 (cm)", "P90 (cm)", "P95 (cm)", "Uji Normalitas (Shapiro-Wilk)", "Aplikasi Desain Stasiun Kerja"
            ])
            st.markdown("##### 📊 Hasil Rekapitulasi Persentil & Uji Normalitas 32 Dimensi")
            st.dataframe(df_res_m4, use_container_width=True, hide_index=True, height=340)
            st.caption("Data awal merupakan simulasi untuk latihan. Ganti dengan hasil pengukuran sebenarnya sebelum menarik kesimpulan populasi.")

            st.divider()
            col_g1, col_g2 = st.columns([1.2, 1.8], gap="large")
            with col_g1:
                st.markdown("##### 📈 Visualisasi Kurva Normal (P5, P50, P95)")
                sel_row = None
                if calc_all["m4_rows"]:
                    pilihan_dim = st.selectbox("Pilih Dimensi Tubuh:", [f"{r[0]} - {r[1]}" for r in calc_all["m4_rows"]])
                    idx_d = [f"{r[0]} - {r[1]}" for r in calc_all["m4_rows"]].index(pilihan_dim)
                    sel_row = calc_all["m4_rows"][idx_d]
                    st.caption(f"**Acuan Desain:** {sel_row[10]}")
                    st.write(f"- **P5:** `{sel_row[4]} cm` | **P50:** `{sel_row[6]} cm` | **P95:** `{sel_row[8]} cm`")
                else:
                    st.info("Belum ada dimensi dengan data positif. Isi sampel pengukuran agar grafik dapat ditampilkan.")
            with col_g2:
                if sel_row:
                    fig_norm = buat_plot_kurva_normal(sel_row[2], sel_row[3], f"{sel_row[0]} ({sel_row[1]})")
                    if fig_norm:
                        st.pyplot(fig_norm)

            st.divider()

        with step_tabs[2]:
            st.session_state["analisis_modul"]["Modul 04"] = st.text_area(
                "Analisis & Pembahasan Modul 04:", value=st.session_state["analisis_modul"]["Modul 04"]
            )
            with st.expander("Penyimpanan populasi SQLite (opsional)", expanded=st.session_state["ux_mode"] == "Lanjutan"):
                st.markdown("##### 🗄️ Database Antropometri Lokal (SQLite)")
                st.warning("Database SQLite berada di server aplikasi dan **tidak permanen** pada Streamlit Community Cloud. "
                           "Data dapat hilang saat server dimulai ulang; gunakan cadangan JSON/Excel. "
                           "Jangan simpan data pribadi sensitif atau gunakan untuk kesimpulan populasi resmi.")
                db_col1, db_col2 = st.columns([1, 2])
                with db_col1:
                    data_sah = st.checkbox("Saya sudah mengganti data simulasi dengan pengukuran nyata dan memahami penyimpanan lokal bersifat sementara.")
                    if st.button("📥 Simpan Data Kelompok ke SQLite Lokal", use_container_width=True, disabled=not data_sah):
                        try:
                            jml = simpan_ke_database_antropometri(
                                st.session_state["identitas"]["kelas"],
                                st.session_state["identitas"]["kelompok"],
                                m4["df_32"],
                            )
                        except (ValueError, OSError) as exc:
                            st.error(f"Data belum disimpan: {exc}")
                        else:
                            st.success(f"Tersimpan {jml} titik pengukuran pada SQLite lokal. Data lama kelas/kelompok yang sama diganti.")
                with db_col2:
                    df_pop = ambil_rekap_database_populasi()
                    if not df_pop.empty:
                        st.dataframe(df_pop, use_container_width=True, hide_index=True, height=220)
                    else:
                        st.info("Database lokal masih kosong. Gunakan data pengukuran nyata dan simpan cadangan sebelum keluar.")

    # --- MODUL 05: ANTROPOMETRI LANJUTAN & CAD 2D ---
    elif chosen == "Modul 05 - Antropometri Lanjutan":
        with step_tabs[0]:
            m5 = st.session_state["modul_05"]
            m5["df_3dim"] = edit_table_rows(
                st.session_state, m5["df_3dim"], "ed_m5", st.data_editor,
                use_container_width=True, num_rows="dynamic",
            )

        with step_tabs[1]:
            calc_all = compile_all_calculations()
            df_res_m5 = pd.DataFrame(calc_all["m5_rows"], columns=[
                "Dimensi Kunci", "Mean (cm)", "SD (cm)", "BKB (cm)", "BKA (cm)",
                "Status Keseragaman", "N'", "Status Kecukupan", "Persentil Acuan", "Ukuran Rancangan Final (cm)"
            ])
            st.dataframe(df_res_m5, use_container_width=True, hide_index=True)

            if len(calc_all["m5_rows"]) >= 3:
                st.markdown("##### 📐 Visualisasi Blueprint 2D CAD Stasiun Kerja (Otomatis Mengikuti Ukuran Rancangan Final)")
                tpd_val = float(calc_all["m5_rows"][0][9])
                tsd_val = float(calc_all["m5_rows"][1][9])
                lpd_val = float(calc_all["m5_rows"][2][9])
                fig_cad = buat_plot_cad_stasiun_kerja(tpd_val, tsd_val, lpd_val)
                if fig_cad:
                    st.pyplot(fig_cad)

        with step_tabs[2]:
            st.session_state["analisis_modul"]["Modul 05"] = st.text_area(
                "Analisis & Pembahasan Modul 05:", value=st.session_state["analisis_modul"]["Modul 05"]
            )

    # --- MODUL 06, 07, 08: TIAP LINGKUNGAN MEMILIKI HALAMAN SENDIRI ---
    elif chosen in ("Modul 06 - Temperatur", "Modul 07 - Kebisingan", "Modul 08 - Pencahayaan"):
        with step_tabs[0]:
            nomor = chosen.split()[1]
            konfigurasi = {
                "06": ("🌡️ Modul 06: Temperatur (°C)", "modul_06", [
                    ("dingin_suhu", "Suhu kondisi dingin (°C)", 10.0, 45.0),
                    ("panas_suhu", "Suhu kondisi panas (°C)", 10.0, 50.0),
                ]),
                "07": ("🔊 Modul 07: Kebisingan (dBA)", "modul_07", [
                    ("normal_db", "Kebisingan normal (dBA)", 30.0, 120.0),
                    ("bising_db", "Kebisingan saat bising (dBA)", 30.0, 120.0),
                ]),
                "08": ("💡 Modul 08: Pencahayaan (lux)", "modul_08", [
                    ("normal_lux", "Cahaya normal (lux)", 1.0, 2000.0),
                    ("gelap_lux", "Cahaya saat redup (lux)", 1.0, 2000.0),
                ]),
            }
            judul, state_key, input_specs = konfigurasi[nomor]
            data_lingkungan = st.session_state[state_key]
            st.caption("Tiga percobaan per kondisi. Input dan analisis hanya untuk modul yang sedang dibuka.")
            cols = st.columns(2, gap="large")
            for col, (field, label, minimum, maksimum) in zip(cols, input_specs):
                with col:
                    st.markdown(f"#### {label}")
                    for i in range(3):
                        data_lingkungan[field][i] = st.number_input(
                            f"{label} — Percobaan {i + 1}", minimum, maksimum,
                            float(data_lingkungan[field][i]), key=f"ling_{nomor}_{field}_{i}",
                        )

        with step_tabs[1]:
            hasil = compile_all_calculations()["env_rows"][int(nomor) - 6]
            df_env = pd.DataFrame([hasil], columns=[
                "Modul", "Parameter Uji", "Mean Kondisi 1", "Mean Kondisi 2",
                "Selisih", "Acuan Perbandingan Praktikum", "p-value (Uji-t)",
                "Kesimpulan Statistik", "Analisis & Rekomendasi",
            ])
            st.markdown("#### 📊 Hasil Perhitungan dan Perbandingan Kondisi")
            st.dataframe(df_env, use_container_width=True, hide_index=True)
            if nomor == "06":
                st.caption("Suhu 28°C hanyalah pembanding latihan; penilaian iklim kerja resmi memerlukan ISBB, beban kerja, serta waktu kerja-istirahat.")
                mean_value = float(np.mean(data_lingkungan["panas_suhu"]))
                batas = data_lingkungan["nab_suhu"]
                if mean_value > batas:
                    st.warning(f"Suhu rata-rata {mean_value:.1f}°C melampaui acuan latihan {batas}°C; belum berarti melampaui NAB ISBB.")
            elif nomor == "07":
                st.caption("Acuan 85 dBA terkait pajanan ekuivalen 8 jam, bukan hanya tiga pembacaan sesaat.")
                mean_value = float(np.mean(data_lingkungan["bising_db"]))
                batas = data_lingkungan["nab_db"]
                if mean_value > batas:
                    st.warning(f"Rerata bacaan {mean_value:.1f} dBA di atas acuan {batas} dBA; ukur pajanan ekuivalen sebelum menyimpulkan kepatuhan.")
            else:
                st.caption("Standar pencahayaan perlu disesuaikan dengan jenis pekerjaan dan area pengukuran.")
                mean_value = float(np.mean(data_lingkungan["gelap_lux"]))
                batas = data_lingkungan["standar_lux"]
                if mean_value < batas:
                    st.warning(f"Rerata pencahayaan redup {mean_value:.1f} lux di bawah acuan tugas {batas} lux.")
            st.caption("Rujukan umum: [Permenaker No. 5 Tahun 2018](https://jdih.kemnaker.go.id/peraturan/detail/1546/peraturan-menteri-nomor-5-).")

        with step_tabs[2]:
            kunci_analisis = f"Modul {nomor}"
            st.session_state["analisis_modul"][kunci_analisis] = st.text_area(
                f"Analisis & Pembahasan Modul {nomor}:",
                value=st.session_state["analisis_modul"][kunci_analisis],
            )

    # --- MODUL 09: MANUAL MATERIAL HANDLING ---
    elif chosen == "Modul 09 - Manual Material Handling (NIOSH, Snook & L5/S1)":
        m9 = st.session_state["modul_09"]

        with step_tabs[0]:
            tab_n, tab_s, tab_b, tab_sim = st.tabs([
                "1️⃣ NIOSH (RWL & LI)", "2️⃣ Snook & Ciriello", "3️⃣ Biomekanika L5/S1",
                "4️⃣ Simulasi Perbaikan",
            ])

            with tab_n:
                c1, c2, c3 = st.columns(3)
                with c1:
                    m9["h_cm"] = st.number_input("Jarak Horizontal H (cm)", 15.0, 80.0, float(m9["h_cm"]))
                    m9["v_cm"] = st.number_input("Tinggi Vertikal Awal V (cm)", 0.0, 175.0, float(m9["v_cm"]))
                with c2:
                    m9["d_cm"] = st.number_input("Jarak Angkat Vertikal D (cm)", 25.0, 175.0, float(m9["d_cm"]))
                    m9["a_deg"] = st.number_input("Sudut Asimetri A (°)", 0.0, 135.0, float(m9["a_deg"]))
                with c3:
                    m9["f_lift"] = st.number_input("Frekuensi Angkat F (kali/menit)", 0.2, 12.0, float(m9["f_lift"]))
                    durasi_options = ["≤ 1 jam", "> 1–2 jam", "> 2–8 jam"]
                    if st.session_state.get("_ui_m9_durasi") not in durasi_options:
                        saved_duration = m9.get("durasi_angkat", "≤ 1 jam")
                        st.session_state["_ui_m9_durasi"] = saved_duration if saved_duration in durasi_options else durasi_options[0]
                    m9["durasi_angkat"] = st.selectbox(
                        "Durasi Total Aktivitas Angkat",
                        durasi_options,
                        key="_ui_m9_durasi",
                    )
                    coupling_options = ["Baik (Good)", "Sedang (Fair)", "Buruk (Poor)"]
                    if st.session_state.get("_ui_m9_coupling") not in coupling_options:
                        saved_coupling = m9.get("coupling", "Sedang (Fair)")
                        st.session_state["_ui_m9_coupling"] = saved_coupling if saved_coupling in coupling_options else coupling_options[1]
                    m9["coupling"] = st.selectbox("Kualitas Genggaman (Coupling)", coupling_options, key="_ui_m9_coupling")
                    m9["berat_beban"] = st.number_input("Berat Beban Aktual L (kg)", 1.0, 60.0, float(m9["berat_beban"]))

                res_n = hitung_niosh_lifting(m9["h_cm"], m9["v_cm"], m9["d_cm"], m9["a_deg"], m9["f_lift"], m9["coupling"], m9["berat_beban"], m9["durasi_angkat"])
                k1, k2, k3 = st.columns(3)
                k1.metric("Recommended Weight Limit (RWL)", f"{res_n['rwl']} kg")
                k2.metric("Lifting Index (LI)", str(res_n["li"]) if res_n["li"] is not None else "Tidak terdefinisi")
                k3.metric("Kategori Risiko NIOSH", res_n["kategori"])
                if res_n["li"] is None:
                    st.error("RWL = 0 pada kombinasi parameter ini; persamaan NIOSH tidak menghasilkan nilai LI yang valid.")
                st.caption("Model RNLE untuk satu tugas mengangkat dengan dua tangan; bukan untuk dorong/tarik, "
                           "mengangkat satu tangan, atau lingkungan dan kondisi kerja di luar batas model. "
                           "FM mengikuti tabel frekuensi × durasi × tinggi tangan (NIOSH).")
                st.caption("Rujukan: [CDC/NIOSH Revised Lifting Equation](https://www.cdc.gov/niosh/ergonomics/about/rnle.html).")
                st.caption(f"Faktor Pengali: HM={res_n['hm']} | VM={res_n['vm']} | DM={res_n['dm']} | AM={res_n['am']} | FM={res_n['fm']} | CM={res_n['cm']}")
                st.info(f"**Rekomendasi Perbaikan:** {res_n['rekomendasi']}")

                # Keterunutan Rumus (Traceability) yang diperbaiki
                with st.expander("🔍 Lihat Penelusuran Rumus & Substitusi NIOSH"):
                    formula_teks = (
                        "Rumus Dasar: RWL = LC x HM x VM x DM x AM x FM x CM\n"
                        f"Substitusi Angka: 23 x {res_n['hm']} x {res_n['vm']} x {res_n['dm']} x {res_n['am']} x {res_n['fm']} x {res_n['cm']}\n"
                        f"Hasil Akhir RWL: {res_n['rwl']} kg\n"
                        f"Lifting Index (LI): Beban Aktual ({m9['berat_beban']}) / RWL ({res_n['rwl']}) = {res_n['li']}"
                    )
                    st.text(formula_teks)

            with tab_s:
                sc1, sc2, sc3 = st.columns(3)
                aktivitas_options = ["Angkat (Lifting)", "Dorong (Pushing)", "Tarik (Pulling)"]
                jk_options = ["Laki-laki", "Perempuan"]
                persentil_options = ["P90", "P75", "P50"]
                for field, options, fallback in (("snook_aktivitas", aktivitas_options, "Angkat (Lifting)"),
                                                 ("snook_jk", jk_options, "Laki-laki"),
                                                 ("snook_persentil", persentil_options, "P75")):
                    widget_key = f"_ui_{field}"
                    if st.session_state.get(widget_key) not in options:
                        saved = m9.get(field, fallback)
                        st.session_state[widget_key] = saved if saved in options else fallback
                m9["snook_aktivitas"] = sc1.selectbox("Jenis Aktivitas MMH", aktivitas_options, key="_ui_snook_aktivitas")
                m9["snook_jk"] = sc2.selectbox("Populasi Pekerja", jk_options, key="_ui_snook_jk")
                m9["snook_persentil"] = sc3.selectbox("Target Persentil Populasi", persentil_options, key="_ui_snook_persentil")
                res_s = hitung_snook_table(m9["snook_aktivitas"], m9["snook_jk"], m9["snook_persentil"], m9["berat_beban"])
                st.metric("Contoh Batas Ilustratif (bukan tabel Snook resmi)", f"{res_s['batas_snook_kg']} kg", res_s["status"])
                st.warning("Angka ini hanya **simulasi edukatif**, bukan hasil tabel Liberty Mutual/Snook & Ciriello yang tervalidasi. "
                           "Penilaian riil memerlukan tinggi tangan, frekuensi, jarak perpindahan, dan gaya dorong/tarik (N), "
                           "serta tabel sesuai aktivitas. Jangan gunakan angka simulasi sebagai keputusan K3.")

            with tab_b:
                bc1, bc2 = st.columns(2)
                m9["bb_pekerja"] = bc1.number_input("Berat Badan Operator (kg)", 40.0, 120.0, float(m9["bb_pekerja"]))
                m9["sudut_punggung"] = bc2.slider("Sudut Membungkuk / Fleksi Punggung (°)", 0.0, 90.0, float(m9["sudut_punggung"]))
                res_b = hitung_biomekanika_l5s1(m9["bb_pekerja"], m9["berat_beban"], m9["sudut_punggung"], m9["h_cm"])
                bm1, bm2 = st.columns(2)
                bm1.metric("Momen Gaya pada L5/S1", f"{res_b['momen_nm']} Nm")
                bm2.metric("Estimasi Kompresi L5/S1", f"{res_b['f_kompresi_n']} N", res_b["kategori"])
                st.caption("Model biomekanika dua dimensi yang disederhanakan; tidak menggantikan analisis dinamis atau pemeriksaan K3 profesional.")

            with tab_sim:
                st.markdown("#### Bandingkan kondisi angkat saat ini dengan usulan perbaikan")
                st.caption(
                    "Ubah jarak beban, tinggi tangan, frekuensi, atau berat beban untuk melihat "
                    "bagaimana RWL dan LI berubah. Skenario ini tidak mengubah data pengamatan utama."
                )
                sim = st.session_state.setdefault("modul_09_simulasi", {
                    "h_cm": 25.0, "v_cm": 75.0, "d_cm": 45.0, "a_deg": 0.0,
                    "f_lift": 1.0, "durasi_angkat": "≤ 1 jam",
                    "coupling": "Baik (Good)", "berat_beban": 12.0,
                })
                for field, saved in sim.items():
                    st.session_state.setdefault(f"_ui_sim_{field}", saved)

                with st.container(border=True):
                    st.markdown("**Parameter usulan (skenario latihan)**")
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        sim["h_cm"] = st.number_input("Usulan H — jarak horizontal (cm)", min_value=15.0,
                            max_value=80.0, step=1.0, key="_ui_sim_h_cm")
                        sim["v_cm"] = st.number_input("Usulan V — tinggi awal (cm)", min_value=0.0,
                            max_value=175.0, step=1.0, key="_ui_sim_v_cm")
                        sim["d_cm"] = st.number_input("Usulan D — perpindahan vertikal (cm)", min_value=25.0,
                            max_value=175.0, step=1.0, key="_ui_sim_d_cm")
                        sim["a_deg"] = st.number_input("Usulan A — sudut asimetri (°)", min_value=0.0,
                            max_value=135.0, step=5.0, key="_ui_sim_a_deg")
                    with sc2:
                        sim["f_lift"] = st.number_input("Usulan F — angkatan/menit", min_value=0.2,
                            max_value=12.0, step=0.2, key="_ui_sim_f_lift")
                        sim["berat_beban"] = st.number_input("Usulan berat beban (kg)", min_value=1.0,
                            max_value=60.0, step=1.0, key="_ui_sim_berat_beban")
                        sim["durasi_angkat"] = st.selectbox("Usulan durasi angkat", durasi_options,
                            key="_ui_sim_durasi_angkat")
                        sim["coupling"] = st.selectbox("Usulan kualitas genggaman", coupling_options,
                            key="_ui_sim_coupling")

                komparasi = bandingkan_skenario_niosh(m9, sim)
                awal, usulan = komparasi["awal"], komparasi["usulan"]
                km1, km2, km3 = st.columns(3)
                km1.metric("LI kondisi awal", f"{awal['li']:.3f}" if awal["li"] is not None else "Tidak valid")
                km2.metric("LI usulan", f"{usulan['li']:.3f}" if usulan["li"] is not None else "Tidak valid")
                km3.metric("Perubahan indikator LI", (
                    f"Turun {komparasi['perubahan_li_pct']:.1f}%" if komparasi["perubahan_li_pct"] is not None
                    and komparasi["perubahan_li_pct"] >= 0 else
                    f"Naik {-komparasi['perubahan_li_pct']:.1f}%" if komparasi["perubahan_li_pct"] is not None
                    else "Tidak dapat dihitung"
                ))
                if awal["li"] is None or usulan["li"] is None:
                    st.error(komparasi["status"])
                elif komparasi["perubahan_li_pct"] > 0:
                    st.success(komparasi["status"])
                else:
                    st.warning(komparasi["status"])
                st.caption(
                    "Target LI ≤ 1 adalah acuan evaluasi NIOSH, bukan jaminan bebas cedera. "
                    "Persentase di atas adalah perubahan angka LI, bukan persentase penurunan risiko cedera."
                )

                labels_sim = [
                    ("h_cm", "H (cm)"), ("v_cm", "V (cm)"), ("d_cm", "D (cm)"),
                    ("a_deg", "A (°)"), ("f_lift", "F (kali/menit)"),
                    ("berat_beban", "Beban (kg)"), ("durasi_angkat", "Durasi"),
                    ("coupling", "Genggaman"),
                ]
                rows_sim = [
                    {"Parameter": label, "Kondisi awal": m9[field], "Usulan": sim[field]}
                    for field, label in labels_sim
                ]
                rows_sim.extend([
                    {"Parameter": "RWL (kg)", "Kondisi awal": awal["rwl"], "Usulan": usulan["rwl"]},
                    {"Parameter": "LI", "Kondisi awal": awal["li"], "Usulan": usulan["li"]},
                    {"Parameter": "Kategori", "Kondisi awal": awal["kategori"], "Usulan": usulan["kategori"]},
                ])
                df_sim = pd.DataFrame(rows_sim)
                for col in ("Kondisi awal", "Usulan"):
                    df_sim[col] = df_sim[col].map(lambda value: "—" if value is None else str(value))
                st.dataframe(df_sim, use_container_width=True, hide_index=True)
                st.download_button(
                    "⬇️ Unduh perbandingan skenario (.csv)",
                    data=df_sim.to_csv(index=False).encode("utf-8-sig"),
                    file_name="Simulasi_Perbaikan_NIOSH.csv",
                    mime="text/csv", use_container_width=True,
                )

        with step_tabs[1]:
            st.markdown("#### Ringkasan hasil tiga pendekatan")
            a, b, c = st.columns(3)
            a.metric("NIOSH · RWL", f"{res_n['rwl']} kg")
            b.metric("NIOSH · LI", f"{res_n['li']}" if res_n["li"] is not None else "Tidak terdefinisi")
            c.metric("Biomekanika · L5/S1", f"{res_b['f_kompresi_n']} N")
            st.info(f"**Evaluasi NIOSH:** {res_n['kategori']}. {res_n['rekomendasi']}")
            st.warning("Perhitungan Snook di sini hanya ilustrasi untuk belajar; bukan tabel ergonomi resmi dan tidak boleh dipakai sebagai keputusan K3.")

        with step_tabs[2]:
            st.session_state["analisis_modul"]["Modul 09"] = st.text_area(
                "Analisis & Pembahasan Modul 09:", value=st.session_state["analisis_modul"]["Modul 09"]
            )

    with step_tabs[3]:
        st.markdown("#### Selesaikan praktikum dan simpan hasil")
        st.caption("Pahami langkah perhitungan, periksa hasil, lalu tandai progres modul."
                   " Gunakan menu Laporan untuk ekspor dan cadangan proyek.")
        with st.expander("🧮 Penelusuran rumus, contoh hitung & bahan belajar", expanded=st.session_state["ux_mode"] == "Pemula"):
            module_number = st.session_state["_active_page_slug"].split("-")[-1]
            lesson = LESSONS[module_number]
            st.write(lesson[1])
            try:
                for step in worked_example(module_number, st.session_state):
                    st.code(step, language=None)
            except (ValueError, TypeError, ZeroDivisionError) as exc:
                st.warning(f"Penelusuran belum dapat dihitung: {exc}")
            st.info("Latihan: " + lesson[2])
            st.caption(lesson[3])

        slug = st.session_state["_active_page_slug"]
        checked = st.checkbox("✅ Tandai modul ini selesai setelah data dan hasil diperiksa",
                              value=bool(st.session_state["module_done"].get(slug, False)), key=f"done_{slug}")
        st.session_state["module_done"][slug] = checked
        if st.button("Buka Laporan & Ekspor →", key=f"module_report_{slug}", type="primary"):
            go_to_page("laporan")
    st.divider()
    render_module_navigation("bawah")

# -----------------------------------------------------------------------------
# HALAMAN 4: KALKULATOR POSTUR KERJA LENGKAP
# -----------------------------------------------------------------------------
elif st.session_state["nav_page"] == "Analisis Postur (RULA/OWAS/REBA)":
    st.subheader("📐 Kalkulator Evaluasi Postur Kerja Terintegrasi (RULA, OWAS, & REBA)")
    st.markdown(get_visual_angle_helper_svg(), unsafe_allow_html=True)

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
# HALAMAN 5: LAPORAN PDF, EXCEL & CADANGAN SESI JSON
# -----------------------------------------------------------------------------
elif st.session_state["nav_page"] == "Laporan & Cadangan":
    st.subheader("📥 Unduh Laporan Praktikum Resmi (.pdf / .xlsx) & Cadangan Sesi (.json)")

    calc_results = compile_all_calculations()
    excel_bytes = export_session_to_excel(st.session_state, calc_results)
    try:
        pdf_bytes = generate_pdf_report(st.session_state, calc_results)
        pdf_error = None
    except (RuntimeError, ValueError, OSError) as exc:
        pdf_bytes = None
        pdf_error = str(exc)
    json_str = export_session_to_json(st.session_state)

    col_dl1, col_dl2, col_dl3 = st.columns(3, gap="medium")
    with col_dl1:
        st.markdown("""
        <div class="panel-card">
            <h4 style="margin-top:0; color:#15803d;">📄 Laporan Resmi PDF (.pdf)</h4>
            <p style="font-size:0.85rem; color:#64748b;">
                Berita acara & ringkasan hasil seluruh modul praktikum lengkap dengan kolom pengesahan Dosen / Asisten Lab.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.download_button(
            label="⬇️ Unduh Laporan Resmi (.pdf)" if pdf_bytes is not None else "PDF belum tersedia",
            data=pdf_bytes if pdf_bytes is not None else b"",
            file_name=f"Berita_Acara_Ergonomi_{st.session_state['identitas']['kelas']}_{st.session_state['identitas']['kelompok'].replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            disabled=pdf_bytes is None,
        )
        if pdf_error:
            st.warning(f"Ekspor PDF sementara tidak tersedia: {pdf_error}. Ekspor Excel dan JSON tetap dapat digunakan.")

    with col_dl2:
        st.markdown("""
        <div class="panel-card">
            <h4 style="margin-top:0; color:#15803d;">📊 Kertas Kerja Excel (.xlsx)</h4>
            <p style="font-size:0.85rem; color:#64748b;">
                Memuat ringkasan Modul 01–09 serta data pengamatan mentah yang dapat ditelusuri dalam worksheet tambahan.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.download_button(
            label="⬇️ Unduh Laporan Excel (.xlsx)",
            data=excel_bytes,
            file_name=f"Laporan_Ergonomi_{st.session_state['identitas']['kelas']}_{st.session_state['identitas']['kelompok'].replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col_dl3:
        st.markdown("""
        <div class="panel-card">
            <h4 style="margin-top:0; color:#15803d;">💾 Cadangan Data Sesi (.json)</h4>
            <p style="font-size:0.85rem; color:#64748b;">
                Simpan seluruh input sesi ke file JSON lokal agar dapat dilanjutkan kembali kapan saja tanpa kehilangan data.
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
    st.markdown("#### 📄 Buat Laporan PDF untuk Satu Modul")
    pdf_mod = st.selectbox("Pilih modul untuk laporan terpisah", list(LESSONS),
                           format_func=lambda n: f"Modul {n} - {LESSONS[n][0]}")
    st.caption("Berisi identitas, ringkasan hasil, substitusi rumus/metode, pembahasan, "
               "dan kolom pengesahan. Hasil mengikuti data aktif saat ini.")
    try:
        module_pdf = export_module_pdf(pdf_mod, st.session_state, calc_results)
    except (RuntimeError, ValueError, OSError) as exc:
        st.warning(f"PDF modul belum tersedia: {exc}")
    else:
        st.download_button("⬇️ Unduh Laporan Modul Terpilih (.pdf)", data=module_pdf,
                           file_name=f"Laporan_Ergonomi_Modul_{pdf_mod}.pdf", mime="application/pdf")

    st.divider()
    st.markdown("#### 🔄 Pulihkan Data dari File Cadangan JSON")
    if st.session_state.pop("_json_restore_success", False):
        st.success("✅ Data sesi berhasil dipulihkan dari file JSON!")
    uploaded_json = st.file_uploader("Unggah file .json hasil cadangan sebelumnya:", type=["json"])
    if uploaded_json is not None and st.button("🔄 Pulihkan Data dari File Ini"):
        try:
            loaded = json.loads(uploaded_json.getvalue().decode("utf-8"))
            restore_session_from_json(st.session_state, loaded)
            for widget_key in ("_ui_m9_durasi", "_ui_m9_coupling", "_ui_snook_aktivitas",
                               "_ui_snook_jk", "_ui_snook_persentil"):
                st.session_state.pop(widget_key, None)
            for widget_key in list(st.session_state):
                if widget_key.startswith("_ui_sim_"):
                    st.session_state.pop(widget_key, None)
            st.session_state["_json_restore_success"] = True
            st.rerun()
        except Exception as e:
            st.error(f"Gagal membaca file JSON: {e}")


# Cloud autosave is strictly opt-in and only runs for a signed-in OIDC account.
# Without private DB configuration the app never uploads project content.
if st.session_state.get("_cloud_autosave"):
    project_db = configured_project_db()
    owner_sub = signed_in_user_id() if project_db else ""
    if project_db and owner_sub:
        payload = export_session_to_json(st.session_state)
        signature = hashlib.sha256((owner_sub + st.session_state["project_name"] + payload).encode("utf-8")).hexdigest()
        if signature != st.session_state.get("_cloud_last_signature"):
            try:
                cloud_save(project_db, owner_sub, st.session_state["project_name"], json.loads(payload))
            except Exception:
                st.warning("Simpan otomatis cloud tertunda. Unduh file proyek sebagai cadangan.")
            else:
                st.session_state["_cloud_last_signature"] = signature
            
