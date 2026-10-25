import io
import os
import math
import sqlite3
from datetime import datetime
import numpy as np
import pandas as pd

# Grafik bersifat opsional bila lingkungan tidak menyediakan cache yang bisa ditulis.
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except Exception:
    HAS_MATPLOTLIB = False

# Aman dari ModuleNotFoundError untuk Pillow (PIL)
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Opsional: MediaPipe & OpenCV (dengan fallback aman jika belum terinstal / gagal muat di server)
try:
    import cv2
    import mediapipe as mp
    HAS_MEDIAPIPE = True
except Exception:
    HAS_MEDIAPIPE = False

# Opsional: FPDF2 untuk cetak Laporan Resmi PDF
try:
    from fpdf import FPDF
    HAS_FPDF = True
except Exception:
    HAS_FPDF = False


# =============================================================================
# FITUR 1: MANUAL MATERIAL HANDLING (NIOSH, SNOOK, & BIOMEKANIKA L5/S1)
# =============================================================================
NIOSH_FREQUENCY_MULTIPLIERS = {
    # F: (<=1 jam V<75, V>=75, 1-2 jam V<75, V>=75, 2-8 jam V<75, V>=75)
    # CDC/NIOSH, Applications Manual for the Revised NIOSH Lifting Equation, Table 5.
    0.2: (1.00, 1.00, 0.95, 0.95, 0.85, 0.85),
    0.5: (0.97, 0.97, 0.92, 0.92, 0.81, 0.81),
    1.0: (0.94, 0.94, 0.88, 0.88, 0.75, 0.75),
    2.0: (0.91, 0.91, 0.84, 0.84, 0.65, 0.65),
    3.0: (0.88, 0.88, 0.79, 0.79, 0.55, 0.55),
    4.0: (0.84, 0.84, 0.72, 0.72, 0.45, 0.45),
    5.0: (0.80, 0.80, 0.60, 0.60, 0.35, 0.35),
    6.0: (0.75, 0.75, 0.50, 0.50, 0.27, 0.27),
    7.0: (0.70, 0.70, 0.42, 0.42, 0.22, 0.22),
    8.0: (0.60, 0.60, 0.35, 0.35, 0.18, 0.18),
    9.0: (0.52, 0.52, 0.30, 0.30, 0.00, 0.15),
    10.0: (0.45, 0.45, 0.26, 0.26, 0.00, 0.13),
    11.0: (0.41, 0.41, 0.00, 0.23, 0.00, 0.00),
    12.0: (0.37, 0.37, 0.00, 0.21, 0.00, 0.00),
    13.0: (0.00, 0.34, 0.00, 0.00, 0.00, 0.00),
    14.0: (0.00, 0.31, 0.00, 0.00, 0.00, 0.00),
    15.0: (0.00, 0.28, 0.00, 0.00, 0.00, 0.00),
}


def _niosh_frequency_multiplier(f: float, v: float, durasi: str) -> float:
    duration_index = {"≤ 1 jam": 0, "> 1–2 jam": 2, "> 2–8 jam": 4}
    if durasi not in duration_index:
        raise ValueError("Durasi angkat tidak dikenal.")
    col = duration_index[durasi] + (1 if v >= 75 else 0)
    frequency = max(0.2, float(f))
    points = sorted(NIOSH_FREQUENCY_MULTIPLIERS)
    if frequency > points[-1]:
        return 0.0
    for idx, upper in enumerate(points):
        if frequency <= upper:
            if idx == 0 or frequency == upper:
                return NIOSH_FREQUENCY_MULTIPLIERS[upper][col]
            lower = points[idx - 1]
            low_fm = NIOSH_FREQUENCY_MULTIPLIERS[lower][col]
            high_fm = NIOSH_FREQUENCY_MULTIPLIERS[upper][col]
            return low_fm + (high_fm - low_fm) * (frequency - lower) / (upper - lower)
    return 0.0


def hitung_niosh_lifting(h: float, v: float, d: float, a: float, f: float, c_type: str, berat_beban: float,
                        durasi: str = "≤ 1 jam") -> dict:
    """RWL/LI untuk satu tugas angkat dua tangan menurut NIOSH RNLE."""
    lc = 23.0  # Load Constant (kg)
    if not all(math.isfinite(float(x)) for x in (h, v, d, a, f, berat_beban)):
        raise ValueError("Seluruh parameter NIOSH harus berupa angka yang valid.")
    if min(h, f, berat_beban) <= 0 or v < 0 or d < 0 or a < 0:
        raise ValueError("Parameter NIOSH tidak boleh negatif; beban, H, dan F harus positif.")
    hm = 0.0 if h > 63 else min(1.0, 25.0 / h)
    vm = 0.0 if v > 175 else max(0.0, 1.0 - (0.003 * abs(v - 75.0)))
    dm = 0.0 if d > 175 else min(1.0, 0.82 + (4.5 / max(d, 25)))
    am = 0.0 if a > 135 else max(0.0, 1.0 - (0.0032 * a))
    fm = _niosh_frequency_multiplier(f, v, durasi)
    cm_map = {"Baik (Good)": 1.00, "Sedang (Fair)": 1.00 if v >= 75 else 0.95, "Buruk (Poor)": 0.90}
    if c_type not in cm_map:
        raise ValueError("Jenis kualitas genggaman tidak dikenal.")
    cm = cm_map[c_type]

    rwl = round(lc * hm * vm * dm * am * fm * cm, 2)
    li = round(berat_beban / rwl, 2) if rwl > 0 else None

    if li is None:
        kategori = "Di luar batas RNLE (RWL = 0)"
        rekomendasi = "Kondisi berada di luar rentang yang direkomendasikan persamaan. Redesign tugas angkat sebelum dinilai kembali."
    elif li <= 1.0:
        kategori = "LI <= 1 (lebih rendah risiko relatif)"
        rekomendasi = "Evaluasi juga kondisi nyata, pekerja, dan tugas berulang; LI <= 1 bukan jaminan bebas cedera."
    elif li <= 3.0:
        kategori = "LI > 1 (perlu perbaikan)"
        rekomendasi = "Perlu rekayasa stasiun kerja (dekatkan jarak H, sesuaikan tinggi V, atau kurangi beban)."
    else:
        kategori = "LI > 3 (prioritas perbaikan tinggi)"
        rekomendasi = "Risiko cedera punggung meningkat; prioritaskan redesign dan pertimbangkan alat bantu mekanis."

    return {
        "rwl": rwl,
        "li": li,
        "hm": round(hm, 2), "vm": round(vm, 2), "dm": round(dm, 2),
        "am": round(am, 2), "fm": round(fm, 2), "cm": round(cm, 2),
        "kategori": kategori,
        "rekomendasi": rekomendasi,
        "durasi": durasi,
    }


def hitung_snook_table(jenis_aktivitas: str, jk: str, persentil: str, beban_aktual: float) -> dict:
    """Simulasi angka pembanding kelas; bukan implementasi tabel Snook & Ciriello."""
    base_limits = {
        ("Angkat (Lifting)", "Laki-laki"): {"P90": 14.0, "P75": 19.0, "P50": 24.0},
        ("Angkat (Lifting)", "Perempuan"): {"P90": 9.0, "P75": 12.0, "P50": 15.0},
        ("Dorong (Pushing)", "Laki-laki"): {"P90": 21.0, "P75": 27.0, "P50": 34.0},
        ("Dorong (Pushing)", "Perempuan"): {"P90": 14.0, "P75": 18.0, "P50": 22.0},
        ("Tarik (Pulling)", "Laki-laki"): {"P90": 19.0, "P75": 24.0, "P50": 30.0},
        ("Tarik (Pulling)", "Perempuan"): {"P90": 13.0, "P75": 16.0, "P50": 20.0},
    }
    batas = base_limits.get((jenis_aktivitas, jk), {"P90": 12.0, "P75": 16.0, "P50": 20.0}).get(persentil, 15.0)
    status = "Di bawah contoh acuan" if beban_aktual <= batas else "Di atas contoh acuan"
    return {"batas_snook_kg": batas, "beban_aktual_kg": beban_aktual, "status": status}


def hitung_biomekanika_l5s1(berat_badan: float, berat_beban: float, sudut_punggung: float, jarak_beban_cm: float) -> dict:
    """Estimasi model statis sederhana; perbandingan 3400/6400 N bukan kepastian aman."""
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
        kategori = "Estimasi di bawah 3.400 N (bukan jaminan aman)"
    elif f_comp <= 6400:
        kategori = "Estimasi 3.400-6.400 N (perlu penilaian lanjut)"
    else:
        kategori = "Estimasi > 6.400 N (prioritas perbaikan tinggi)"

    return {"momen_nm": round(momen_total, 2), "f_kompresi_n": f_comp, "kategori": kategori}


# =============================================================================
# FITUR 2: VISUALISASI INTERAKTIF (KURVA GAUSSIAN, CAD 2D, & PANDUAN SUDUT SVG)
# =============================================================================
def buat_plot_kurva_normal(mean: float, std: float, nama_dimensi: str):
    """Visualisasi kurva distribusi normal dengan batas persentil P5, P50, dan P95."""
    if not HAS_MATPLOTLIB:
        return None

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
    if not HAS_MATPLOTLIB:
        return None

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
    ax1.plot([20, 20], [0, tinggi_kursi], color="#4ade80", linewidth=3)
    ax1.plot([42, 42], [0, tinggi_kursi], color="#4ade80", linewidth=3)
    ax1.plot([18, 44], [tinggi_kursi, tinggi_kursi], color="#22c55e", linewidth=5, label=f"Tinggi Kursi: {tinggi_kursi:.1f} cm")
    ax1.plot([18, 15], [tinggi_kursi, tinggi_kursi + 42], color="#22c55e", linewidth=4)
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
# FITUR 3: DETEKSI SUDUT POSTUR OTOMATIS DARI FOTO (MEDIAPIPE POSE - ANTI CRASH)
# =============================================================================
def _hitung_sudut_3titik(a, b, c) -> float:
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return round(float(np.degrees(angle)), 1)


def deteksi_postur_mediapipe(uploaded_file) -> dict:
    """Hanya sarankan skor jika landmark pose manusia benar-benar terdeteksi."""
    if not HAS_PIL:
        raise RuntimeError("Pillow tidak tersedia untuk membaca gambar.")
    try:
        uploaded_file.seek(0)
    except Exception:
        pass

    image = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(image)

    if HAS_MEDIAPIPE:
        try:
            try:
                mp_pose = mp.solutions.pose
                mp_drawing = mp.solutions.drawing_utils
            except AttributeError:
                from mediapipe.python.solutions import pose as mp_pose
                from mediapipe.python.solutions import drawing_utils as mp_drawing

            with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.4) as pose:
                results = pose.process(img_np)
                if results.pose_landmarks:
                    lm = results.pose_landmarks.landmark
                    required = (mp_pose.PoseLandmark.RIGHT_EAR, mp_pose.PoseLandmark.RIGHT_SHOULDER,
                                mp_pose.PoseLandmark.RIGHT_ELBOW, mp_pose.PoseLandmark.RIGHT_WRIST,
                                mp_pose.PoseLandmark.RIGHT_HIP)
                    if any(lm[j.value].visibility < 0.5 for j in required):
                        return _pose_not_available(img_np, "Sendi tubuh tidak terlihat jelas")
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

                    annotated = img_np.copy()
                    mp_drawing.draw_landmarks(annotated, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                    return _konversi_sudut_ke_skor(
                        sudut_lengan_atas, sudut_lengan_bawah, sudut_leher, sudut_punggung,
                        annotated, "MediaPipe AI Pose (Sendi Terdeteksi)"
                    )
                else:
                    return _pose_not_available(img_np, "Manusia tidak terdeteksi")
        except Exception:
            return _pose_not_available(img_np, "Analisis pose gagal pada server")

    return _pose_not_available(img_np, "MediaPipe tidak tersedia di server")


def _pose_not_available(img_np, reason: str) -> dict:
    return {"mode": reason, "annotated_image": img_np, "sudut": {},
            "skor_rekomendasi": None, "valid_detection": False}


def _konversi_sudut_ke_skor(ua_deg: float, la_deg: float, nk_deg: float, tr_deg: float, annotated_img, mode: str) -> dict:
    ua_score = 1 if ua_deg <= 20 else (2 if ua_deg <= 45 else (3 if ua_deg <= 90 else 4))
    la_score = 1 if 60 <= la_deg <= 100 else 2
    nk_score = 1 if nk_deg <= 10 else (2 if nk_deg <= 20 else 3)
    tr_score = 1 if tr_deg <= 5 else (2 if tr_deg <= 20 else (3 if tr_deg <= 60 else 4))

    return {
        "mode": mode,
        "valid_detection": True,
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
def _clean_pdf_text(text: str) -> str:
    """Membersihkan karakter non-Latin-1 agar FPDF tidak error."""
    replacements = {"≥": ">=", "≤": "<=", "±": "+/-", "Σ": "Sigma", "°": " deg", "·": "-"}
    res = str(text)
    for k, v in replacements.items():
        res = res.replace(k, v)
    return res.encode("latin-1", "ignore").decode("latin-1")


def generate_pdf_report(session_state: dict, calc_results: dict) -> bytes:
    """Laporan PDF ringkas tetapi mencakup Modul 01-09 tanpa teks terpotong."""
    if not HAS_FPDF:
        raise RuntimeError("Paket fpdf2 tidak tersedia untuk membuat laporan PDF.")

    identitas = session_state.get("identitas", {})
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=17)
    pdf.set_margins(13, 14, 13)
    pdf.add_page()

    def line(value):
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5, _clean_pdf_text(value))

    def section(title):
        if pdf.get_y() > 266:
            pdf.add_page()
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(231, 243, 234)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 7, _clean_pdf_text(title), fill=True)
        pdf.ln(1)

    pdf.set_font("Helvetica", "B", 13)
    pdf.multi_cell(0, 7, _clean_pdf_text(identitas.get("universitas", "UNIVERSITAS PELITA BANGSA")).upper(), align="C")
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 10)
    pdf.multi_cell(0, 6, "LAPORAN PRAKTIKUM ERGONOMI - TEKNIK INDUSTRI", align="C")
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, _clean_pdf_text(
        f"Kelas: {identitas.get('kelas', '-')} | Kelompok: {identitas.get('kelompok', '-')} | "
        f"Tanggal: {identitas.get('tanggal', '-')}"), align="C")

    section("A. IDENTITAS KELOMPOK DAN OPERATOR")
    for field, label in (("dosen", "Dosen/Asisten"), ("op1_nama", "Operator 1"),
                         ("op2_nama", "Operator 2"), ("anggota", "Anggota kelompok")):
        line(f"{label}: {identitas.get(field, '-')}")

    section("B. MODUL 01 - FISIOLOGI KERJA")
    for r in calc_results.get("m1_rows", []):
        line(f"- {r[0]} ({r[1]}): DN kerja {r[4]} bpm, %CVL {r[6]}%, "
             f"energi {r[7]} kkal/menit. {r[8]}")

    section("C. MODUL 02 - PENILAIAN POSTUR")
    for r in calc_results.get("m2_rows", []):
        line(f"- {r[0]} / {r[1]} [{r[2]}]: {r[3]}; {r[4]}; {r[5]}")

    section("D. MODUL 03 - PENGUKURAN WAKTU KERJA")
    m3_rows = calc_results.get("m3_rows", [])
    total_wb = sum(r[12] for r in m3_rows)
    line(f"Total waktu baku: {total_wb:.2f} detik/unit" +
         (f"; output standar {3600 / total_wb:.1f} unit/jam" if total_wb > 0 else "; belum ada data valid"))
    for r in m3_rows:
        line(f"- {r[0]} {r[1]}: Ws={r[2]} dtk, Wn={r[11]} dtk, Wb={r[12]} dtk; "
             f"keseragaman={r[6]}; kecukupan={r[8]}")

    section("E. MODUL 04 - ANTROPOMETRI 32 DIMENSI")
    for r in calc_results.get("m4_rows", []):
        line(f"- {r[0]} {r[1]}: mean {r[2]} cm, SD {r[3]} cm, "
             f"P5 {r[4]} cm, P50 {r[6]} cm, P95 {r[8]} cm. {r[9]}")

    section("F. MODUL 05 - RANCANGAN STASIUN KERJA")
    for r in calc_results.get("m5_rows", []):
        line(f"- {r[0]}: mean {r[1]} cm, acuan {r[8]}, rancangan {r[9]} cm; "
             f"keseragaman={r[5]}, kecukupan={r[7]}")

    section("G. MODUL 06-08 - LINGKUNGAN KERJA")
    for r in calc_results.get("env_rows", []):
        line(f"- {r[0]} ({r[1]}): kondisi 1={r[2]}, kondisi 2={r[3]}, "
             f"acuan praktikum={r[5]}, p={r[6]}; {r[7]}")
    line("Catatan: suhu udara biasa bukan indeks ISBB; pembacaan dBA sesaat bukan dosis pajanan 8 jam.")

    section("H. MODUL 09 - MANUAL MATERIAL HANDLING")
    summary = calc_results.get("m9_summary", {})
    if summary:
        line(f"NIOSH: RWL={summary.get('rwl')} kg; LI={summary.get('li') if summary.get('li') is not None else 'tidak terdefinisi'}; "
             f"{summary.get('kategori', '-')}.")
        line(f"Estimasi biomekanika L5/S1: {summary.get('f_kompresi_n')} N; "
             f"{summary.get('status_l5s1', '-')}.")
        line("Perhitungan Snook pada aplikasi hanya simulasi edukatif dan bukan batas resmi Liberty Mutual.")

    # Pastikan tanda tangan tidak terpotong atau terpisah pada pergantian halaman.
    if pdf.get_y() > 251:
        pdf.add_page()
    pdf.ln(7)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(90, 6, "Dosen / Asisten Laboratorium", align="C")
    pdf.cell(90, 6, "Ketua Kelompok", ln=True, align="C")
    pdf.ln(13)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 5, _clean_pdf_text(
        f"Dosen/Asisten: {identitas.get('dosen', '-')}    |    "
        f"Kelompok: {identitas.get('kelompok', '-')}"), align="C")
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
    """Ganti data kelompok yang sama secara atomik agar klik berulang tidak menggandakan populasi."""
    kelas, kelompok = str(kelas).strip(), str(kelompok).strip()
    if not kelas or not kelompok:
        raise ValueError("Kelas dan kelompok wajib diisi sebelum menyimpan.")
    if not isinstance(df_32_rows, list):
        raise ValueError("Data antropometri harus berupa daftar baris.")

    records = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for row in df_32_rows:
        kode = str(row.get("Kode", "")).strip()
        nama = str(row.get("Dimensi Tubuh", "")).strip()
        if not kode or not nama:
            continue
        for i in range(1, 11):
            raw = row.get(f"P{i}", None)
            if raw is None or str(raw).strip() == "":
                continue
            try:
                val = float(raw)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Nilai {kode} P{i} bukan angka.") from exc
            if not math.isfinite(val) or val < 0:
                raise ValueError(f"Nilai {kode} P{i} tidak valid.")
            if val > 0:
                records.append((now_str, kelas, kelompok, kode, nama, val))
    if not records:
        raise ValueError("Tidak ada sampel pengukuran positif yang dapat disimpan.")

    init_antropometri_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        with conn:
            conn.execute("DELETE FROM sampel_antropometri WHERE kelas=? AND kelompok=?", (kelas, kelompok))
            conn.executemany(
                "INSERT INTO sampel_antropometri (waktu_simpan, kelas, kelompok, kode_dimensi, nama_dimensi, nilai_cm) "
                "VALUES (?, ?, ?, ?, ?, ?)", records
            )
    finally:
        conn.close()
    return len(records)


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
    
