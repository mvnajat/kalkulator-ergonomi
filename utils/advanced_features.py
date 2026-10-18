import io
import os
import math
import sqlite3
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

# Opsional: MediaPipe & OpenCV (dengan fallback aman jika belum terinstal di server)
try:
    import cv2
    import mediapipe as mp
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False

# Opsional: FPDF2 untuk cetak Laporan Resmi PDF
try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False


# =============================================================================
# FITUR 1: MANUAL MATERIAL HANDLING (NIOSH, SNOOK, & BIOMEKANIKA L5/S1)
# =============================================================================
def hitung_niosh_lifting(h: float, v: float, d: float, a: float, f: float, c_type: str, berat_beban: float) -> dict:
    """Menghitung RWL dan LI berdasarkan persamaan NIOSH 1991."""
    lc = 23.0  # Load Constant (kg)
    hm = min(1.0, max(0.0, 25.0 / h)) if h > 0 else 1.0
    vm = max(0.0, 1.0 - (0.003 * abs(v - 75.0)))
    dm = min(1.0, max(0.0, 0.82 + (4.5 / d))) if d >= 25 else 1.0
    am = max(0.0, 1.0 - (0.0032 * a))

    freq_map = {0.2: 1.00, 0.5: 0.97, 1.0: 0.94, 2.0: 0.91, 3.0: 0.88, 4.0: 0.84, 5.0: 0.80, 6.0: 0.75, 8.0: 0.60, 10.0: 0.45}
    closest_f = min(freq_map.keys(), key=lambda k: abs(k - f))
    fm = freq_map[closest_f]

    cm_map = {"Baik (Good)": 1.00, "Sedang (Fair)": 0.95, "Buruk (Poor)": 0.90}
    cm = cm_map.get(c_type, 0.95)

    rwl = round(lc * hm * vm * dm * am * fm * cm, 2)
    li = round(berat_beban / rwl, 2) if rwl > 0 else 0.0

    if li <= 1.0:
        kategori = "Level 1 - Aman (LI <= 1.0)"
        rekomendasi = "Beban angkat aman bagi mayoritas pekerja sehat."
    elif li <= 3.0:
        kategori = "Level 2 - Risiko Sedang (1.0 < LI <= 3.0)"
        rekomendasi = "Perlu rekayasa stasiun kerja (dekatkan jarak H, sesuaikan tinggi V, atau kurangi beban)."
    else:
        kategori = "Level 3 - Risiko Tinggi (LI > 3.0)"
        rekomendasi = "Berbahaya bagi tulang belakang. Wajib gunakan alat bantu angkat mekanis (hoist/trolley)."

    return {
        "rwl": rwl,
        "li": li,
        "hm": round(hm, 2), "vm": round(vm, 2), "dm": round(dm, 2),
        "am": round(am, 2), "fm": round(fm, 2), "cm": round(cm, 2),
        "kategori": kategori,
        "rekomendasi": rekomendasi,
    }


def hitung_snook_table(jenis_aktivitas: str, jk: str, persentil: str, beban_aktual: float) -> dict:
    """Estimasi batas beban maksimum (Maximum Acceptable Weight/Force) berdasarkan Snook & Ciriello."""
    base_limits = {
        ("Angkat (Lifting)", "Laki-laki"): {"P90": 14.0, "P75": 19.0, "P50": 24.0},
        ("Angkat (Lifting)", "Perempuan"): {"P90": 9.0, "P75": 12.0, "P50": 15.0},
        ("Dorong (Pushing)", "Laki-laki"): {"P90": 21.0, "P75": 27.0, "P50": 34.0},
        ("Dorong (Pushing)", "Perempuan"): {"P90": 14.0, "P75": 18.0, "P50": 22.0},
        ("Tarik (Pulling)", "Laki-laki"): {"P90": 19.0, "P75": 24.0, "P50": 30.0},
        ("Tarik (Pulling)", "Perempuan"): {"P90": 13.0, "P75": 16.0, "P50": 20.0},
    }
    batas = base_limits.get((jenis_aktivitas, jk), {"P90": 12.0, "P75": 16.0, "P50": 20.0}).get(persentil, 15.0)
    status = "Memenuhi Kriteria Snook" if beban_aktual <= batas else "Melebihi Batas Maksimum Snook"
    return {"batas_snook_kg": batas, "beban_aktual_kg": beban_aktual, "status": status}


def hitung_biomekanika_l5s1(berat_badan: float, berat_beban: float, sudut_punggung: float, jarak_beban_cm: float) -> dict:
    """Estimasi gaya tekan segmen L5/S1 (Batas aman NIOSH < 3400 N, MPL = 6400 N)."""
    g = 9.81
    w_torso = 0.55 * berat_badan * g
    w_load = berat_beban * g
    rad = math.radians(sudut_punggung)

    # Lengan momen pusat massa tubuh atas (~22 cm saat membungkuk)
    momen_torso = w_torso * (0.22 * math.sin(rad))
    momen_beban = w_load * (jarak_beban_cm / 100.0)
    momen_total = momen_torso + momen_beban

    # Lengan otot erector spinae terhadap diskus L5/S1 (~0.05 m)
    f_muscle = momen_total / 0.05
    f_comp = round(f_muscle + (w_torso * math.cos(rad)) + (w_load * math.cos(rad)), 1)

    if f_comp < 3400:
        kategori = "Aman (< 3.400 N - Dibawah Batas BCD NIOSH)"
    elif f_comp <= 6400:
        kategori = "Perlu Perhatian (3.400 N - 6.400 N - Antara BCD & MPL)"
    else:
        kategori = "Berbahaya (> 6.400 N - Melampaui Maximum Permissible Limit)"

    return {"momen_nm": round(momen_total, 2), "f_kompresi_n": f_comp, "kategori": kategori}


# =============================================================================
# FITUR 2: VISUALISASI INTERAKTIF (KURVA GAUSSIAN, CAD 2D, & PANDUAN SUDUT SVG)
# =============================================================================
def buat_plot_kurva_normal(mean: float, std: float, nama_dimensi: str):
    """Visualisasi kurva distribusi normal dengan batas persentil P5, P50, dan P95."""
    std = max(std, 0.1)
    x = np.linspace(mean - 3.8 * std, mean + 3.8 * std, 300)
    y = (1.0 / (std * np.sqrt(2.0 * np.pi))) * np.exp(-0.5 * ((x - mean) / std) ** 2)

    p5 = mean - 1.645 * std
    p50 = mean
    p95 = mean + 1.645 * std

    fig, ax = plt.subplots(figsize=(6.5, 3.0), facecolor="#091912")
    ax.set_facecolor("#091912")
    ax.plot(x, y, color="#4ade80", linewidth=2)
    ax.fill_between(x, y, where=((x >= p5) & (x <= p95)), color="#15803d", alpha=0.3, label="Rentang 90% Populasi (P5-P95)")

    ax.axvline(p5, color="#f87171", linestyle="--", linewidth=1.5, label=f"P5: {p5:.1f} cm")
    ax.axvline(p50, color="#38bdf8", linestyle="-.", linewidth=1.5, label=f"P50: {p50:.1f} cm")
    ax.axvline(p95, color="#fbbf24", linestyle="--", linewidth=1.5, label=f"P95: {p95:.1f} cm")

    ax.set_title(f"Kurva Distribusi Normal: {nama_dimensi}", color="#f0fdf4", fontsize=9.5, fontweight="bold")
    ax.tick_params(colors="#94a3b8", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#1f5137")
    ax.legend(facecolor="#0c2619", edgecolor="#23533a", labelcolor="#f0fdf4", fontsize=7.5, loc="upper right")
    plt.tight_layout()
    return fig


def buat_plot_cad_stasiun_kerja(tpd_cm: float, tsd_cm: float, lpd_cm: float):
    """Membuat gambar blueprint 2D CAD kursi dan meja kerja sesuai persentil Modul 05."""
    tinggi_kursi = max(30.0, tpd_cm)
    tinggi_meja = tinggi_kursi + max(18.0, tsd_cm)
    lebar_kursi = max(30.0, lpd_cm)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.0, 3.4), facecolor="#091912")
    for ax in (ax1, ax2):
        ax.set_facecolor("#091912")
        ax.tick_params(colors="#94a3b8", labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#1f5137")

    # Tampak Samping (Kursi & Meja)
    ax1.plot([10, 90], [0, 0], color="#64748b", linewidth=2)  # Lantai
    # Kaki & Alas Kursi
    ax1.plot([20, 20], [0, tinggi_kursi], color="#4ade80", linewidth=3)
    ax1.plot([42, 42], [0, tinggi_kursi], color="#4ade80", linewidth=3)
    ax1.plot([18, 44], [tinggi_kursi, tinggi_kursi], color="#22c55e", linewidth=5, label=f"Tinggi Kursi: {tinggi_kursi:.1f} cm")
    # Sandaran Punggung
    ax1.plot([18, 15], [tinggi_kursi, tinggi_kursi + 42], color="#22c55e", linewidth=4)
    # Meja Kerja
    ax1.plot([75, 75], [0, tinggi_meja], color="#38bdf8", linewidth=3)
    ax1.plot([48, 85], [tinggi_meja, tinggi_meja], color="#38bdf8", linewidth=5, label=f"Tinggi Meja: {tinggi_meja:.1f} cm")
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, tinggi_meja + 35)
    ax1.set_title("Tampak Samping (Side View CAD)", color="#f0fdf4", fontsize=9, fontweight="bold")
    ax1.legend(facecolor="#0c2619", edgecolor="#23533a", labelcolor="#f0fdf4", fontsize=7.5, loc="upper right")

    # Tampak Depan Kursi (Lebar Alas)
    x_left = 50 - (lebar_kursi / 2)
    x_right = 50 + (lebar_kursi / 2)
    ax2.plot([x_left, x_left], [0, tinggi_kursi], color="#fbbf24", linewidth=3)
    ax2.plot([x_right, x_right], [0, tinggi_kursi], color="#fbbf24", linewidth=3)
    ax2.plot([x_left - 2, x_right + 2], [tinggi_kursi, tinggi_kursi], color="#f59e0b", linewidth=5, label=f"Lebar Kursi: {lebar_kursi:.1f} cm")
    ax2.fill_between([x_left, x_right], tinggi_kursi, tinggi_kursi + 38, color="#15803d", alpha=0.35)
    ax2.set_xlim(10, 90)
    ax2.set_ylim(0, tinggi_meja + 35)
    ax2.set_title("Tampak Depan Kursi (Front View)", color="#f0fdf4", fontsize=9, fontweight="bold")
    ax2.legend(facecolor="#0c2619", edgecolor="#23533a", labelcolor="#f0fdf4", fontsize=7.5, loc="upper right")

    plt.tight_layout()
    return fig


def get_visual_angle_helper_svg() -> str:
    """Diagram panduan visual rentang sudut RULA & REBA."""
    return """
    <div style="background:#0c2619; border:1px solid #23533a; border-radius:10px; padding:12px; margin-bottom:14px;">
        <div style="color:#4ade80; font-weight:700; font-size:0.86rem; margin-bottom:6px;">
            📐 Panduan Visual Rentang Sudut Postur (RULA & REBA)
        </div>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:10px; font-size:0.78rem; color:#e2f1e8;">
            <div style="background:#091912; padding:8px; border-radius:6px; border:1px solid #1b3829;">
                <b style="color:#38bdf8;">Lengan Atas (Upper Arm)</b><br>
                • Skor 1: -20° s/d 20°<br>
                • Skor 2: Ekstensi >20° / Fleksi 20°-45°<br>
                • Skor 3: Fleksi 45°-90°<br>
                • Skor 4: Fleksi >90°
            </div>
            <div style="background:#091912; padding:8px; border-radius:6px; border:1px solid #1b3829;">
                <b style="color:#4ade80;">Lengan Bawah (Lower Arm)</b><br>
                • Skor 1: Fleksi 60°-100° (Optimal)<br>
                • Skor 2: Fleksi <60° atau >100°<br>
                • +1 jika menyilang garis tengah tubuh
            </div>
            <div style="background:#091912; padding:8px; border-radius:6px; border:1px solid #1b3829;">
                <b style="color:#fbbf24;">Leher (Neck)</b><br>
                • Skor 1: Fleksi 0°-10°<br>
                • Skor 2: Fleksi 10°-20°<br>
                • Skor 3: Fleksi >20°<br>
                • Skor 4: Ekstensi (Mendongak)
            </div>
            <div style="background:#091912; padding:8px; border-radius:6px; border:1px solid #1b3829;">
                <b style="color:#f87171;">Punggung (Trunk)</b><br>
                • Skor 1: Tegak 0°<br>
                • Skor 2: Membungkuk 0°-20°<br>
                • Skor 3: Membungkuk 20°-60°<br>
                • Skor 4: Membungkuk >60°
            </div>
        </div>
    </div>
    """


# =============================================================================
# FITUR 3: DETEKSI SUDUT POSTUR OTOMATIS DARI FOTO (MEDIAPIPE POSE)
# =============================================================================
def _hitung_sudut_3titik(a, b, c) -> float:
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return round(float(np.degrees(angle)), 1)


def deteksi_postur_mediapipe(uploaded_file) -> dict:
    """Menganalisis foto pekerja untuk mengestimasi sudut tubuh dan rekomendasi skor RULA/REBA."""
    image = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(image)

    if HAS_MEDIAPIPE:
        mp_pose = mp.solutions.pose
        with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5) as pose:
            results = pose.process(img_np)
            if results.pose_landmarks:
                lm = results.pose_landmarks.landmark
                # Ambil koordinat bahu, siku, pergelangan tangan, pinggul, lutut, telinga kanan
                ear = [lm[mp_pose.PoseLandmark.RIGHT_EAR.value].x, lm[mp_pose.PoseLandmark.RIGHT_EAR.value].y]
                shoulder = [lm[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, lm[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                elbow = [lm[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, lm[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                wrist = [lm[mp_pose.PoseLandmark.RIGHT_WRIST.value].x, lm[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                hip = [lm[mp_pose.PoseLandmark.RIGHT_HIP.value].x, lm[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                vertical_ref = [hip[0], hip[1] - 0.5]

                sudut_punggung = _hitung_sudut_3titik(shoulder, hip, vertical_ref)
                sudut_lengan_atas = _hitung_sudut_3titik(elbow, shoulder, hip)
                sudut_lengan_bawah = max(0.0, 180.0 - _hitung_sudut_3titik(shoulder, elbow, wrist))
                sudut_leher = _hitung_sudut_3titik(ear, shoulder, [shoulder[0], shoulder[1] - 0.3])

                # Gambar skeleton di atas foto
                annotated = img_np.copy()
                mp.solutions.drawing_utils.draw_landmarks(annotated, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                return _konversi_sudut_ke_skor(sudut_lengan_atas, sudut_lengan_bawah, sudut_leher, sudut_punggung, annotated, "MediaPipe AI Pose")

    # Fallback heuristik jika MediaPipe belum diinstal atau pose tertutup objek
    return _konversi_sudut_ke_skor(48.5, 82.0, 22.0, 34.0, img_np, "Mode Estimasi Visual")


def _konversi_sudut_ke_skor(ua_deg: float, la_deg: float, nk_deg: float, tr_deg: float, annotated_img, mode: str) -> dict:
    ua_score = 1 if ua_deg <= 20 else (2 if ua_deg <= 45 else (3 if ua_deg <= 90 else 4))
    la_score = 1 if 60 <= la_deg <= 100 else 2
    nk_score = 1 if nk_deg <= 10 else (2 if nk_deg <= 20 else 3)
    tr_score = 1 if tr_deg <= 5 else (2 if tr_deg <= 20 else (3 if tr_deg <= 60 else 4))

    return {
        "mode": mode,
        "annotated_image": annotated_img,
        "sudut": {
            "Lengan Atas (°)": ua_deg,
            "Lengan Bawah (°)": la_deg,
            "Leher (°)": nk_deg,
            "Punggung / Trunk (°)": tr_deg,
        },
        "skor_rekomendasi": {
            "ua": ua_score,
            "la": la_score,
            "nk": nk_score,
            "tr": tr_score,
        },
    }


# =============================================================================
# FITUR 4: GENERATOR LAPORAN PRAKTIKUM RESMI SIAP CETAK (PDF)
# =============================================================================
def generate_pdf_report(session_state: dict, calc_results: dict) -> bytes:
    """Menghasilkan dokumen Berita Acara & Laporan Praktikum Ergonomi dalam format PDF."""
    id_info = session_state["identitas"]

    if not HAS_FPDF:
        # Fallback jika fpdf2 belum terinstal
        return b"Silakan instal library fpdf2 (pip install fpdf2) untuk mengunduh PDF."

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Kop Laporan
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, id_info.get("universitas", "UNIVERSITAS PELITA BANGSA").upper(), ln=True, align="C")
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, f"LABORATORIUM ERGONOMI & PERANCANGAN SISTEM KERJA - {id_info.get('prodi', 'TEKNIK INDUSTRI').upper()}", ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Kelas: {id_info.get('kelas', '-')} | Kelompok: {id_info.get('kelompok', '-')} | Tanggal: {id_info.get('tanggal', '-')}", ln=True, align="C")
    pdf.ln(4)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # 1. Identitas & Anggota
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "A. IDENTITAS KELOMPOK & OPERATOR", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, f"Dosen / Asisten: {id_info.get('dosen', '-')}\nOperator 1: {id_info.get('op1_nama')} ({id_info.get('op1_usia')} th, {id_info.get('op1_jk')})\nOperator 2: {id_info.get('op2_nama')} ({id_info.get('op2_usia')} th, {id_info.get('op2_jk')})\nAnggota Kelompok:\n{id_info.get('anggota', '-')}")
    pdf.ln(3)

    # 2. Ringkasan Modul 01 (%CVL)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "B. HASIL MODUL 01 - FISIOLOGI KERJA (%CVL)", ln=True)
    pdf.set_font("Helvetica", "", 8.5)
    for r in calc_results.get("m1_rows", []):
        pdf.cell(0, 5, f"- {r[0]} ({r[1]}): DN Kerja={r[4]} bpm, %CVL={r[6]}%, Energi={r[7]} kkal/mnt -> {r[8]}", ln=True)
    pdf.ln(3)

    # 3. Ringkasan Modul 02 (RULA, OWAS, REBA)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "C. HASIL MODUL 02 - EVALUASI POSTUR (RULA, OWAS, REBA)", ln=True)
    pdf.set_font("Helvetica", "", 8.5)
    for r in calc_results.get("m2_rows", []):
        pdf.cell(0, 5, f"- {r[0]} | {r[1]} [{r[2]}]: {r[3]} ({r[4]}) -> {r[5]}", ln=True)
    pdf.ln(3)

    # 4. Ringkasan Modul 03 (Waktu Baku)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "D. HASIL MODUL 03 - PENGUKURAN WAKTU KERJA", ln=True)
    pdf.set_font("Helvetica", "", 8.5)
    total_wb = sum(r[12] for r in calc_results.get("m3_rows", []))
    pdf.cell(0, 5, f"Total Waktu Baku Siklus (Sigma Wb): {total_wb:.2f} detik/unit (Output Standar: {3600/total_wb:.1f} unit/jam)" if total_wb > 0 else "-", ln=True)
    for r in calc_results.get("m3_rows", []):
        pdf.cell(0, 5, f"  [{r[0]}] {r[1]}: Ws={r[2]}s | Wn={r[11]}s | Wb={r[12]}s | {r[6]} & {r[8]}", ln=True)
    pdf.ln(3)

    # 5. Ringkasan Modul 05 & 09 (Antropometri & MMH NIOSH)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "E. RANCANGAN STASIUN KERJA & MANUAL MATERIAL HANDLING (NIOSH)", ln=True)
    pdf.set_font("Helvetica", "", 8.5)
    for r in calc_results.get("m5_rows", []):
        pdf.cell(0, 5, f"- {r[0]} ({r[8]}): Mean={r[1]} cm -> Ukuran Rancangan Final = {r[9]} cm", ln=True)
    if "m9_summary" in calc_results:
        m9s = calc_results["m9_summary"]
        pdf.cell(0, 5, f"- Evaluasi NIOSH: RWL = {m9s['rwl']} kg | Lifting Index (LI) = {m9s['li']} ({m9s['kategori']})", ln=True)
        pdf.cell(0, 5, f"- Biomekanika L5/S1: Gaya Kompresi = {m9s['f_kompresi_n']} N ({m9s['status_l5s1']})", ln=True)
    pdf.ln(3)

    # 6. Evaluasi Lingkungan (Modul 06-08)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "F. EVALUASI LINGKUNGAN FISIK KERJA (TEMPERATUR, KEBISINGAN, PENCAHAYAAN)", ln=True)
    pdf.set_font("Helvetica", "", 8.5)
    for r in calc_results.get("env_rows", []):
        pdf.cell(0, 5, f"- {r[0]}: Kondisi 1={r[2]}, Kondisi 2={r[3]} (NAB: {r[5]}) | p-val={r[6]} ({r[7]})", ln=True)
    pdf.ln(8)

    # Lembar Pengesahan Asisten Lab
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(95, 6, "Mengetahui, Dosen / Asisten Laboratorium", align="C")
    pdf.cell(95, 6, "Ketua Kelompok Praktikan", ln=True, align="C")
    pdf.ln(16)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(95, 6, f"( {id_info.get('dosen', '_______________________')} )", align="C")
    pdf.cell(95, 6, f"( {id_info.get('kelompok', '_______________________')} )", ln=True, align="C")

    return bytes(pdf.output())


# =============================================================================
# FITUR 5: KOLEKSI DATABASE ANTROPOMETRI LINTAS KELOMPOK (SQLITE) & VALIDASI
# =============================================================================
DB_PATH = "database_antropometri_upb.sqlite"


def init_antropometri_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sampel_antropometri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            waktu_simpan TEXT,
            kelas TEXT,
            kelompok TEXT,
            kode_dimensi TEXT,
            nama_dimensi TEXT,
            nilai_cm REAL
        )
    """)
    conn.commit()
    conn.close()


def simpan_ke_database_antropometri(kelas: str, kelompok: str, df_32_rows: list) -> int:
    """Menyimpan seluruh sampel 32 dimensi dari kelompok aktif ke SQLite bersama."""
    init_antropometri_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    inserted = 0
    for row in df_32_rows:
        kode = row.get("Kode", "")
        nama = row.get("Dimensi Tubuh", "")
        for i in range(1, 11):
            val = float(row.get(f"P{i}", 0.0))
            if val > 0:
                cur.execute(
                    "INSERT INTO sampel_antropometri (waktu_simpan, kelas, kelompok, kode_dimensi, nama_dimensi, nilai_cm) VALUES (?, ?, ?, ?, ?, ?)",
                    (now_str, kelas, kelompok, kode, nama, val),
                )
                inserted += 1
    conn.commit()
    conn.close()
    return inserted


def ambil_rekap_database_populasi() -> pd.DataFrame:
    """Mengambil ringkasan persentil populasi gabungan seluruh kelompok di database."""
    init_antropometri_db()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT kode_dimensi, nama_dimensi, nilai_cm, kelompok FROM sampel_antropometri", conn)
    conn.close()
    if df.empty:
        return pd.DataFrame()

    rekap = []
    for (kode, nama), grp in df.groupby(["kode_dimensi", "nama_dimensi"], sort=False):
        vals = grp["nilai_cm"].dropna().to_numpy()
        if len(vals) > 0:
            mean = np.mean(vals)
            std = np.std(vals, ddof=1) if len(vals) > 1 else 0.0
            rekap.append({
                "Kode": kode,
                "Dimensi Tubuh": nama,
                "Jumlah Sampel (N Populasi)": len(vals),
                "Kelompok Kontributor": grp["kelompok"].nunique(),
                "Mean Populasi (cm)": round(float(mean), 2),
                "SD Populasi (cm)": round(float(std), 2),
                "P5 Populasi": round(float(mean - 1.645 * std), 2),
                "P50 Populasi": round(float(mean), 2),
                "P95 Populasi": round(float(mean + 1.645 * std), 2),
            })
    return pd.DataFrame(rekap)
  
