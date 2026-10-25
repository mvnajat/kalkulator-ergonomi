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
from utils.exporter import export_session_to_json, export_session_to_excel, restore_session_from_json
from utils.table_editor import prepare_editor_scope, edit_table_rows
from utils.advanced_features import (
    hitung_niosh_lifting,
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
        max-width: 1420px;
        padding-top: 4.5rem !important;
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
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 22px 26px;
        margin-bottom: 20px;
        margin-top: 8px;
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
        font-size: 1.65rem;
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
    for op_nama, akt_nama, usia, jk, dni, dnk in configs_m1:
        res = hitung_fisiologi_cvl(dni, dnk, int(usia), jk)
        m1_list.append([
            op_nama, akt_nama, usia, dni, dnk,
            res["dn_max"], res["cvl_persen"], res["ke_bersih_kkal_menit"],
            res["kategori"], res["tindakan"]
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

    return {
        "m1_rows": m1_list,
        "m2_rows": m2_list,
        "m3_rows": m3_list,
        "m4_rows": m4_list,
        "m5_rows": m5_list,
        "env_rows": env_list,
        "m9_summary": m9_summary,
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

# A table's source must remain unchanged during cell edits. When the user
# leaves the worksheet, its next visit will use the last saved values.
if st.session_state["nav_page"] != "Modul Praktikum":
    prepare_editor_scope(st.session_state, st.session_state["nav_page"])

st.markdown(f"""
<div class="hero-card">
    <div class="hero-subtitle">{st.session_state['identitas']['universitas']} · {st.session_state['identitas']['prodi']} ({st.session_state['identitas']['kelas']})</div>
    <div class="hero-title">Ruang Praktikum Ergonomi & Perancangan Sistem Kerja</div>
    <p class="hero-desc">Dilengkapi Evaluasi Fisiologi, RULA/OWAS/REBA + AI Pose Estimation, Time Study, Antropometri + CAD 2D & Database Populasi, Lingkungan Fisik, MMH (NIOSH/Snook/L5-S1), serta Ekspor PDF & Excel.</p>
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
            <h4 style="margin:0 0 12px 0; color:#0f172a; font-size:1.05rem;">Ringkasan Praktikum</h4>
            <div class="summary-item">
                <div class="summary-val">{wib_time.strftime('%d-%m-%Y · %H:%M WIB')}</div>
                <div class="summary-sub">Waktu Server Lokal (Asia/Jakarta)</div>
            </div>
            <div class="summary-item">
                <div class="summary-val">9 Modul Praktikum Terintegrasi</div>
                <div class="summary-sub">Termasuk MMH (NIOSH, Snook, Biomekanika L5/S1) & CAD 2D</div>
            </div>
            <div class="summary-item">
                <div class="summary-val">{total_postur_records} Evaluasi Postur + AI Pose</div>
                <div class="summary-sub">RULA, OWAS, REBA & deteksi sudut foto otomatis</div>
            </div>
            <div class="summary-item">
                <div class="summary-val">Ekspor Multi-Format (PDF, XLSX, JSON, SQLite)</div>
                <div class="summary-sub">Laporan resmi siap cetak & database antropometri lintas kelompok</div>
            </div>
        </div>

        <div class="emerald-notice">
            <strong>🚀 5 Fitur Pengembangan Aktif:</strong><br>
            1. <b>MMH & Biomekanika</b> (NIOSH RWL/LI, Snook, L5/S1)<br>
            2. <b>Visualisasi CAD 2D & Kurva Normal</b><br>
            3. <b>AI Pose Estimation</b> pada foto postur kerja<br>
            4. <b>Generator Laporan PDF</b> siap cetak<br>
            5. <b>Database SQLite Sementara</b> & Indikator Lingkungan K3
        </div>
        """, unsafe_allow_html=True)

    with right_col:
        st.markdown("<h4 style='margin:0 0 10px 0; color:#0f172a;'>Modul Akademik</h4>", unsafe_allow_html=True)
        search_q = st.text_input(
            "Cari modul",
            placeholder="Cari berdasarkan nama atau nomor modul (misal: NIOSH, Antropometri, RULA, 09)...",
            label_visibility="collapsed",
        ).strip().lower()

        modules_meta = [
            ("Modul 01", "Fisiologi Kerja", "Dua operator, kondisi normal dan setelah aktivitas, nadi kerja, konsumsi energi serta perhitungan %CVL.", "Modul 01 - Fisiologi Kerja"),
            ("Modul 02", "Postur Kerja & AI Pose", "Evaluasi postur kerja terpadu (RULA, OWAS, REBA) dilengkapi deteksi sudut otomatis dari foto.", "Modul 02 - Postur Kerja"),
            ("Modul 03", "Pengukuran Waktu Kerja", "Tujuh elemen kerja, rating Westinghouse, allowance, uji keseragaman, kecukupan & waktu baku.", "Modul 03 - Pengukuran Waktu Kerja"),
            ("Modul 04", "Antropometri (32 Dimensi)", "32 dimensi tubuh, uji normalitas Shapiro-Wilk, kurva Gaussian interaktif, dan Database Populasi.", "Modul 04 - Antropometri 32 Dimensi"),
            ("Modul 05", "Antropometri Lanjutan & CAD 2D", "Uji keseragaman, kecukupan data, serta blueprint visual 2D kursi & meja stasiun kerja.", "Modul 05 - Antropometri Lanjutan"),
            ("Modul 06", "Temperatur Ruang", "Perbandingan kondisi dingin/panas beserta uji-t dan indikator awal; NAB iklim kerja memerlukan ISBB.", "Modul 06 - Lingkungan (Temperatur, Kebisingan, Pencahayaan)"),
            ("Modul 07", "Kebisingan (dBA)", "Perbandingan kondisi normal/bising (dBA) beserta evaluasi batas aman 85 dBA.", "Modul 06 - Lingkungan (Temperatur, Kebisingan, Pencahayaan)"),
            ("Modul 08", "Pencahayaan (Lux)", "Perbandingan kondisi normal/gelap (Lux) beserta evaluasi standar pencahayaan SNI.", "Modul 06 - Lingkungan (Temperatur, Kebisingan, Pencahayaan)"),
            ("Modul 09", "MMH (NIOSH, Snook & L5/S1)", "RWL & Lifting Index NIOSH, simulasi Snook, serta estimasi biomekanika L5/S1.", "Modul 09 - Manual Material Handling (NIOSH, Snook & L5/S1)"),
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
                    <div class="mod-footer">Teknik Industri · Data terintegrasi ke Laporan PDF & Excel</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Buka lembar kerja {m_code}", key=f"open_{m_code}", use_container_width=True):
                    st.session_state["selected_modul"] = target_key
                    st.session_state["_ui_selected_modul"] = target_key
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
# HALAMAN 3: MODUL PRAKTIKUM (01 s/d 09)
# -----------------------------------------------------------------------------
elif st.session_state["nav_page"] == "Modul Praktikum":
    modul_list = [
        "Modul 01 - Fisiologi Kerja",
        "Modul 02 - Postur Kerja",
        "Modul 03 - Pengukuran Waktu Kerja",
        "Modul 04 - Antropometri 32 Dimensi",
        "Modul 05 - Antropometri Lanjutan",
        "Modul 06 - Lingkungan (Temperatur, Kebisingan, Pencahayaan)",
        "Modul 09 - Manual Material Handling (NIOSH, Snook & L5/S1)",
    ]
    if st.session_state.get("_ui_selected_modul") not in modul_list:
        st.session_state["_ui_selected_modul"] = (
            st.session_state["selected_modul"] if st.session_state["selected_modul"] in modul_list else modul_list[0]
        )
    chosen = st.selectbox("Pilih Lembar Kerja Modul Praktikum:", modul_list, key="_ui_selected_modul")
    st.session_state["selected_modul"] = chosen
    prepare_editor_scope(st.session_state, f"Modul Praktikum:{chosen}")
    st.divider()

    # --- MODUL 01: FISIOLOGI ---
    if chosen == "Modul 01 - Fisiologi Kerja":
        st.subheader("🫀 Modul 01: Fisiologi Kerja & Beban Kardiovaskular (%CVL)", anchor="modul-01-fisiologi")
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

        high_cvl = [r for r in calc_all["m1_rows"] if r[6] > 30.0]
        if high_cvl:
            st.warning(f"⚠️ **Validasi Fisiologi Otomatis:** Terdapat {len(high_cvl)} aktivitas dengan nilai **%CVL > 30%** ({', '.join(r[1] for r in high_cvl)}). Diperlukan penjadwalan waktu istirahat atau rotasi operator.")
        else:
            st.success("✅ **Validasi Fisiologi Otomatis:** Seluruh aktivitas memiliki beban kardiovaskular %CVL ≤ 30% (Aman tanpa kelelahan berarti).")

        st.session_state["analisis_modul"]["Modul 01"] = st.text_area(
            "Analisis & Pembahasan Modul 01:", value=st.session_state["analisis_modul"]["Modul 01"]
        )

    # --- MODUL 02: POSTUR KERJA + AI POSE ESTIMATION ---
    elif chosen == "Modul 02 - Postur Kerja":
        st.subheader("🧍 Modul 02: Evaluasi Postur Kerja Terpadu & AI Pose Estimation", anchor="modul-02-postur")
        calc_all = compile_all_calculations()
        df_m2 = pd.DataFrame(calc_all["m2_rows"], columns=[
            "Operator", "Aktivitas", "Metode", "Skor / Kode Akhir", "Action Level", "Kategori Risiko", "Rekomendasi Perbaikan"
        ])
        st.dataframe(df_m2, use_container_width=True, hide_index=True)

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
            st.session_state["nav_page"] = "Analisis Postur (RULA/OWAS/REBA)"
            st.rerun()

        st.session_state["analisis_modul"]["Modul 02"] = st.text_area(
            "Analisis & Pembahasan Modul 02:", value=st.session_state["analisis_modul"]["Modul 02"]
        )

    # --- MODUL 03: PENGUKURAN WAKTU KERJA ---
    elif chosen == "Modul 03 - Pengukuran Waktu Kerja":
        st.subheader("⏱️ Modul 03: Pengukuran Waktu Kerja (Time Study)", anchor="modul-03-waktu-kerja")
        m3 = st.session_state["modul_03"]

        st.markdown("##### 1. Tabel Waktu Siklus Pengamatan (10 Siklus dalam Detik)")
        m3["df_siklus"] = edit_table_rows(
            st.session_state, m3["df_siklus"], "ed_m3", st.data_editor,
            use_container_width=True, num_rows="dynamic",
        )

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

        tidak_cukup = [r[0] for r in calc_all["m3_rows"] if "Tidak" in str(r[8]) or "Belum" in str(r[8])]
        tidak_seragam = [r[0] for r in calc_all["m3_rows"] if "Tidak" in str(r[6])]
        if tidak_seragam or tidak_cukup:
            st.error(f"⚠️ **Peringatan Validasi Statistik:** Elemen tidak seragam: {tidak_seragam or 'Tidak ada'} | Elemen belum cukup (N < N'): {tidak_cukup or 'Tidak ada'}. Lakukan pengambilan sampel tambahan atau revisi data ekstrem (outlier).")
        else:
            st.success("✅ **Validasi Statistik Time Study:** Seluruh elemen kerja telah **Seragam (dalam batas BKA-BKB)** dan **Cukup (N ≥ N')**.")

        total_wb = df_res_m3["Wb (dtk)"].sum() if not df_res_m3.empty else 0.0
        st.metric("Total Waktu Baku Siklus Produk (Σ Wb)", f"{total_wb:.2f} detik/unit", f"Kapasitas Produksi: {3600/total_wb:.1f} unit/jam" if total_wb > 0 else "")
        st.session_state["analisis_modul"]["Modul 03"] = st.text_area(
            "Analisis & Pembahasan Modul 03:", value=st.session_state["analisis_modul"]["Modul 03"]
        )

    # --- MODUL 04: ANTROPOMETRI 32 DIMENSI ---
    elif chosen == "Modul 04 - Antropometri 32 Dimensi":
        st.subheader("📏 Modul 04: Antropometri 32 Dimensi Tubuh, Kurva Gaussian & Database Populasi", anchor="modul-04-antropometri")
        m4 = st.session_state["modul_04"]
        m4["df_32"] = edit_table_rows(
            st.session_state, m4["df_32"], "ed_m4", st.data_editor,
            use_container_width=True, height=380,
        )

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

        st.session_state["analisis_modul"]["Modul 04"] = st.text_area(
            "Analisis & Pembahasan Modul 04:", value=st.session_state["analisis_modul"]["Modul 04"]
        )

    # --- MODUL 05: ANTROPOMETRI LANJUTAN & CAD 2D ---
    elif chosen == "Modul 05 - Antropometri Lanjutan":
        st.subheader("🪑 Modul 05: Antropometri Lanjutan & Blueprint 2D Stasiun Kerja", anchor="modul-05-antropometri-lanjutan")
        m5 = st.session_state["modul_05"]
        m5["df_3dim"] = edit_table_rows(
            st.session_state, m5["df_3dim"], "ed_m5", st.data_editor,
            use_container_width=True, num_rows="dynamic",
        )

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

        st.session_state["analisis_modul"]["Modul 05"] = st.text_area(
            "Analisis & Pembahasan Modul 05:", value=st.session_state["analisis_modul"]["Modul 05"]
        )

    # --- MODUL 06, 07, 08: LINGKUNGAN KERJA ---
    elif chosen == "Modul 06 - Lingkungan (Temperatur, Kebisingan, Pencahayaan)":
        st.subheader("🌡️🔊💡 Modul 06, 07, & 08: Lingkungan Fisik Kerja", anchor="modul-06-07-08-lingkungan")
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
            "Selisih", "Acuan Perbandingan Praktikum", "p-value (Uji-t)", "Kesimpulan Statistik", "Analisis & Rekomendasi"
        ])
        st.markdown("#### 📊 Hasil Evaluasi Lingkungan Fisik & Uji Hipotesis Komparatif")
        st.dataframe(df_env, use_container_width=True, hide_index=True)
        st.caption("Angka suhu 28°C hanya pembanding latihan, bukan NAB suhu udara berdasarkan Permenaker. "
                   "Penilaian iklim kerja memerlukan ISBB, beban kerja, dan pola kerja-istirahat; "
                   "kebisingan NAB 85 dBA mengacu pajanan ekuivalen 8 jam, bukan rerata tiga bacaan sesaat.")
        st.caption("Rujukan: [Permenaker No. 5 Tahun 2018 (JDIH Kemnaker)](https://jdih.kemnaker.go.id/peraturan/detail/1546/peraturan-menteri-nomor-5-).")

        mean_panas = np.mean(m6["panas_suhu"])
        mean_bising = np.mean(m7["bising_db"])
        mean_gelap = np.mean(m8["gelap_lux"])
        alerts = []
        if mean_panas > m6["nab_suhu"]:
            alerts.append(f"Suhu rata-rata (**{mean_panas:.1f}°C**) lebih tinggi daripada acuan latihan (**{m6['nab_suhu']}°C**); status NAB ISBB belum dapat ditentukan")
        if mean_bising > m7["nab_db"]:
            alerts.append(f"Bacaan kebisingan rata-rata (**{mean_bising:.1f} dBA**) melebihi nilai pembanding (**{m7['nab_db']} dBA**); ukur pajanan 8 jam sebelum menyimpulkan kepatuhan NAB")
        if mean_gelap < m8["standar_lux"]:
            alerts.append(f"Pencahayaan redup rata-rata (**{mean_gelap:.1f} lux**) di bawah acuan tugas (**{m8['standar_lux']} lux**); sesuaikan standar dengan jenis pekerjaan")
        if alerts:
            st.warning("⚠️ **Indikator untuk pemeriksaan K3 lebih lanjut:**\n- " + "\n- ".join(alerts))

    # --- MODUL 09: MANUAL MATERIAL HANDLING ---
    elif chosen == "Modul 09 - Manual Material Handling (NIOSH, Snook & L5/S1)":
        st.subheader("📦 Modul 09: Manual Material Handling (NIOSH Equation, Snook Tables & Biomekanika L5/S1)", anchor="modul-09-mmh")
        m9 = st.session_state["modul_09"]

        tab_n, tab_s, tab_b = st.tabs(["1️⃣ NIOSH Lifting Equation (RWL & LI)", "2️⃣ Snook & Ciriello Tables", "3️⃣ Biomekanika Segmen L5/S1"])

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

        st.session_state["analisis_modul"]["Modul 09"] = st.text_area(
            "Analisis & Pembahasan Modul 09:", value=st.session_state["analisis_modul"]["Modul 09"]
        )

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
    pdf_bytes = generate_pdf_report(st.session_state, calc_results)
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
            label="⬇️ Unduh Laporan Resmi (.pdf)",
            data=pdf_bytes,
            file_name=f"Berita_Acara_Ergonomi_{st.session_state['identitas']['kelas']}_{st.session_state['identitas']['kelompok'].replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

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
            st.session_state["_json_restore_success"] = True
            st.rerun()
        except Exception as e:
            st.error(f"Gagal membaca file JSON: {e}")
            
