import numpy as np
import pandas as pd
from scipy import stats

# Daftar 32 Dimensi Antropometri Standar Teknik Industri
ANTROPOMETRI_32_DIMENSI = [
    ("D01", "Tinggi Tubuh Tegak (TTT)", "cm"),
    ("D02", "Tinggi Mata Berdiri (TMB)", "cm"),
    ("D03", "Tinggi Bahu Berdiri (TBB)", "cm"),
    ("D04", "Tinggi Siku Berdiri (TSB)", "cm"),
    ("D05", "Tinggi Pinggul Berdiri (TPB)", "cm"),
    ("D06", "Tinggi Tulang Ruas Berdiri (TTR)", "cm"),
    ("D07", "Tinggi Ujung Jari Berdiri (TUJ)", "cm"),
    ("D08", "Tinggi Duduk Tegak (TDT)", "cm"),
    ("D09", "Tinggi Duduk Normal (TDN)", "cm"),
    ("D10", "Tinggi Mata Duduk (TMD)", "cm"),
    ("D11", "Tinggi Bahu Duduk (TBD)", "cm"),
    ("D12", "Tinggi Siku Duduk (TSD)", "cm"),
    ("D13", "Tebal Paha (TP)", "cm"),
    ("D14", "Panjang Lutut - Pantat (PLP)", "cm"),
    ("D15", "Panjang Popliteal - Pantat (PPP)", "cm"),
    ("D16", "Tinggi Lutut Duduk (TLD)", "cm"),
    ("D17", "Tinggi Popliteal Duduk (TPD)", "cm"),
    ("D18", "Lebar Bahu (Bidang Deltoid) (LB)", "cm"),
    ("D19", "Lebar Bahu Bagian Atas (LBA)", "cm"),
    ("D20", "Lebar Pinggul Duduk (LPD)", "cm"),
    ("D21", "Tebal Dada (TD)", "cm"),
    ("D22", "Tebal Perut (Abdominal) (TPA)", "cm"),
    ("D23", "Panjang Lengan Atas (Bahu-Siku) (PLA)", "cm"),
    ("D24", "Panjang Lengan Bawah (Siku-Ujung Jari) (PLB)", "cm"),
    ("D25", "Jangkauan Tangan ke Depan (JTD)", "cm"),
    ("D26", "Panjang Bahu - Genggaman Tangan ke Depan (PBG)", "cm"),
    ("D27", "Panjang Kepala (PK)", "cm"),
    ("D28", "Lebar Kepala (LK)", "cm"),
    ("D29", "Panjang Tangan (PT)", "cm"),
    ("D30", "Lebar Tangan (LT)", "cm"),
    ("D31", "Panjang Telapak Kaki (PTK)", "cm"),
    ("D32", "Lebar Telapak Kaki (LTK)", "cm"),
]


def _positive_measurements(values: list) -> np.ndarray:
    """Kosong/0 adalah sampel belum diisi; tolak nilai tak hingga dan bukan angka."""
    numbers = []
    for raw in values:
        if raw is None or str(raw).strip() == "":
            continue
        try:
            val = float(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Data pengukuran bukan angka: {raw!r}") from exc
        if not np.isfinite(val) or val < 0:
            raise ValueError("Data pengukuran harus angka positif atau kosong.")
        if val > 0:
            numbers.append(val)
    return np.asarray(numbers, dtype=float)

def hitung_fisiologi_cvl(dn_istirahat: float, dn_kerja: float, usia: int, jk: str = "Laki-laki") -> dict:
    """Menghitung %CVL (Cardiovascular Load), Denyut Nadi Maksimum, dan Konsumsi Energi."""
    dn_max = (220 - usia) if jk == "Laki-laki" else (200 - usia)
    denom = max(dn_max - dn_istirahat, 1)
    cvl = ((dn_kerja - dn_istirahat) / denom) * 100.0
    
    if cvl <= 30:
        kategori = "Tidak terjadi kelelahan (< 30%)"
        tindakan = "Kondisi kerja aman, tidak diperlukan perbaikan segera."
        level_risiko = "Rendah"
    elif cvl <= 60:
        kategori = "Diperlukan perbaikan (30% - 60%)"
        tindakan = "Perlu penyesuaian beban kerja atau pengaturan waktu istirahat."
        level_risiko = "Sedang"
    elif cvl <= 80:
        kategori = "Kerja dalam waktu singkat (60% - 80%)"
        tindakan = "Batasi durasi kerja kontinu dan jadwalkan istirahat berkala."
        level_risiko = "Tinggi"
    elif cvl <= 100:
        kategori = "Diperlukan tindakan segera (80% - 100%)"
        tindakan = "Beban fisik terlalu berat! Segera redesain metode kerja/alat."
        level_risiko = "Sangat Tinggi"
    else:
        kategori = "Tidak diperbolehkan beraktivitas (> 100%)"
        tindakan = "Hentikan aktivitas kerja segera!"
        level_risiko = "Kritis"

    # Estimasi Konsumsi Energi (persamaan regresi kuadratik: Y = 1.80411 - 0.0229038 X + 4.71733E-4 X^2)
    ke_istirahat = 1.80411 - 0.0229038 * dn_istirahat + 0.000471733 * (dn_istirahat ** 2)
    ke_kerja = 1.80411 - 0.0229038 * dn_kerja + 0.000471733 * (dn_kerja ** 2)
    ke_bersih = max(0.0, ke_kerja - ke_istirahat)

    return {
        "dn_max": round(dn_max, 2),
        "nadi_kerja_pulse": round(dn_kerja - dn_istirahat, 2),
        "cvl_persen": round(cvl, 2),
        "kategori": kategori,
        "tindakan": tindakan,
        "level_risiko": level_risiko,
        "ke_istirahat_kkal_menit": round(ke_istirahat, 3),
        "ke_kerja_kkal_menit": round(ke_kerja, 3),
        "ke_bersih_kkal_menit": round(ke_bersih, 3),
    }


def hitung_rula(upper_arm: int, lower_arm: int, wrist: int, wrist_twist: int,
                neck: int, trunk: int, legs: int,
                muscle_a: int, force_a: int, muscle_b: int, force_b: int) -> dict:
    """Perhitungan Skor RULA (Rapid Upper Limb Assessment) dengan Tabel A, B, dan C resmi."""
    # Tabel A: [upper_arm 1..6][lower_arm 1..3][wrist 1..4][wrist_twist 1..2]
    table_a = {
        (1,1,1): (1,2), (1,1,2): (2,2), (1,1,3): (2,3), (1,1,4): (3,3),
        (1,2,1): (2,2), (1,2,2): (2,2), (1,2,3): (3,3), (1,2,4): (3,3),
        (1,3,1): (2,3), (1,3,2): (3,3), (1,3,3): (3,3), (1,3,4): (4,4),
        (2,1,1): (2,3), (2,1,2): (3,3), (2,1,3): (3,4), (2,1,4): (4,4),
        (2,2,1): (3,3), (2,2,2): (3,3), (2,2,3): (3,4), (2,2,4): (4,4),
        (2,3,1): (3,4), (2,3,2): (4,4), (2,3,3): (4,4), (2,3,4): (5,5),
        (3,1,1): (3,3), (3,1,2): (4,4), (3,1,3): (4,4), (3,1,4): (5,5),
        (3,2,1): (3,4), (3,2,2): (4,4), (3,2,3): (4,4), (3,2,4): (5,5),
        (3,3,1): (4,4), (3,3,2): (4,4), (3,3,3): (4,5), (3,3,4): (5,5),
        (4,1,1): (4,4), (4,1,2): (4,4), (4,1,3): (4,5), (4,1,4): (5,5),
        (4,2,1): (4,4), (4,2,2): (4,4), (4,2,3): (4,5), (4,2,4): (5,5),
        (4,3,1): (4,4), (4,3,2): (4,5), (4,3,3): (5,5), (4,3,4): (6,6),
        (5,1,1): (5,5), (5,1,2): (5,5), (5,1,3): (5,6), (5,1,4): (6,7),
        (5,2,1): (5,6), (5,2,2): (6,6), (5,2,3): (6,7), (5,2,4): (7,7),
        (5,3,1): (6,6), (5,3,2): (6,7), (5,3,3): (7,7), (5,3,4): (7,8),
        (6,1,1): (7,7), (6,1,2): (7,7), (6,1,3): (7,8), (6,1,4): (8,9),
        (6,2,1): (8,8), (6,2,2): (8,8), (6,2,3): (8,9), (6,2,4): (9,9),
        (6,3,1): (9,9), (6,3,2): (9,9), (6,3,3): (9,9), (6,3,4): (9,9),
    }
    ua = min(max(upper_arm, 1), 6)
    la = min(max(lower_arm, 1), 3)
    wr = min(max(wrist, 1), 4)
    wt = min(max(wrist_twist, 1), 2)
    posture_a = table_a[(ua, la, wr)][wt - 1]
    score_c = posture_a + muscle_a + force_a

    # Tabel B: [neck 1..6][trunk 1..6][legs 1..2]
    table_b = {
        1: [(1,3), (2,3), (3,4), (5,5), (6,6), (7,7)],
        2: [(2,3), (2,3), (4,5), (5,5), (6,7), (7,7)],
        3: [(3,3), (3,4), (4,5), (5,6), (6,7), (7,7)],
        4: [(5,5), (5,6), (6,7), (7,7), (7,7), (8,8)],
        5: [(7,7), (7,7), (7,8), (8,8), (8,8), (8,8)],
        6: [(8,8), (8,8), (8,8), (8,9), (9,9), (9,9)],
    }
    nk = min(max(neck, 1), 6)
    tr = min(max(trunk, 1), 6)
    lg = min(max(legs, 1), 2)
    posture_b = table_b[nk][tr - 1][lg - 1]
    score_d = posture_b + muscle_b + force_b

    # Tabel C (Grand Score 1..7)
    table_c = [
        [1, 2, 3, 3, 4, 5, 5],
        [2, 2, 3, 4, 4, 5, 5],
        [3, 3, 3, 4, 4, 5, 6],
        [3, 3, 3, 4, 5, 6, 6],
        [4, 4, 4, 5, 6, 7, 7],
        [4, 4, 5, 6, 6, 7, 7],
        [5, 5, 6, 6, 7, 7, 7],
        [5, 5, 6, 7, 7, 7, 7],
    ]
    r_idx = min(max(score_c, 1), 8) - 1
    c_idx = min(max(score_d, 1), 7) - 1
    grand_score = table_c[r_idx][c_idx]

    if grand_score in [1, 2]:
        action_level = 1
        kategori = "Level 1 (Skor 1-2): Risiko Dapat Diterima"
        rekomendasi = "Postur dapat diterima jika tidak dipertahankan dalam periode sangat lama."
    elif grand_score in [3, 4]:
        action_level = 2
        kategori = "Level 2 (Skor 3-4): Diperlukan Investigasi Lanjutan"
        rekomendasi = "Diperlukan pemeriksaan lebih lanjut dan mungkin diperlukan perubahan postur/stasiun kerja."
    elif grand_score in [5, 6]:
        action_level = 3
        kategori = "Level 3 (Skor 5-6): Investigasi & Perubahan Segera"
        rekomendasi = "Perlu dilakukan penelitian lebih lanjut dan perubahan dalam waktu dekat."
    else:
        action_level = 4
        kategori = "Level 4 (Skor 7): Perubahan Saat Ini Juga!"
        rekomendasi = "Kondisi berbahaya! Investigasi dan ubah postur/stasiun kerja saat ini juga."

    return {
        "posture_a": posture_a,
        "score_c": score_c,
        "posture_b": posture_b,
        "score_d": score_d,
        "grand_score": grand_score,
        "action_level": action_level,
        "kategori": kategori,
        "rekomendasi": rekomendasi,
    }


def hitung_owas(back: int, arms: int, legs: int, load: int) -> dict:
    """Perhitungan Kategori Tindakan OWAS (Ovako Working Posture Analysis System)."""
    # Matriks Lookup OWAS (Back 1..4, Arms 1..3, Legs 1..7, Load 1..3)
    owas_matrix = {
        1: { # Back = 1
            1: [(1,1,1),(1,1,1),(1,1,1),(2,2,2),(2,2,2),(1,1,1),(1,1,1)],
            2: [(1,1,1),(1,1,1),(1,1,1),(2,2,2),(2,2,2),(1,1,1),(1,1,1)],
            3: [(1,1,1),(1,1,1),(1,1,1),(2,2,3),(2,2,3),(1,1,1),(1,1,2)],
        },
        2: { # Back = 2
            1: [(2,2,3),(2,2,3),(2,2,3),(3,3,3),(3,3,3),(2,2,2),(2,3,3)],
            2: [(2,2,3),(2,2,3),(2,3,3),(3,4,4),(3,4,4),(3,3,4),(2,3,4)],
            3: [(3,3,4),(2,2,3),(3,3,3),(3,4,4),(4,4,4),(4,4,4),(2,3,4)],
        },
        3: { # Back = 3
            1: [(1,1,1),(1,1,1),(1,1,2),(3,3,3),(4,4,4),(1,1,1),(1,1,1)],
            2: [(2,2,3),(1,1,1),(1,1,2),(4,4,4),(4,4,4),(3,3,3),(1,1,1)],
            3: [(2,2,3),(1,1,2),(2,3,3),(4,4,4),(4,4,4),(4,4,4),(1,1,1)],
        },
        4: { # Back = 4
            1: [(2,3,3),(2,2,3),(2,2,3),(4,4,4),(4,4,4),(4,4,4),(2,3,4)],
            2: [(3,3,4),(2,3,4),(3,3,4),(4,4,4),(4,4,4),(4,4,4),(2,3,4)],
            3: [(4,4,4),(2,3,4),(3,3,4),(4,4,4),(4,4,4),(4,4,4),(2,3,4)],
        }
    }
    b = min(max(back, 1), 4)
    a = min(max(arms, 1), 3)
    l = min(max(legs, 1), 7)
    ld = min(max(load, 1), 3)
    kategori_skor = owas_matrix[b][a][l - 1][ld - 1]

    info = {
        1: ("Kategori 1: Aman / Normal", "Tidak ada masalah pada sistem muskuloskeletal. Tidak perlu perbaikan."),
        2: ("Kategori 2: Perlu Perbaikan di Masa Mendatang", "Postur berbahaya ringan pada sistem muskuloskeletal. Perlu perbaikan di masa yang akan datang."),
        3: ("Kategori 3: Perlu Perbaikan Segera", "Postur berbahaya pada sistem muskuloskeletal. Perbaikan harus dilakukan sesegera mungkin."),
        4: ("Kategori 4: Perlu Perbaikan Saat Ini Juga!", "Postur sangat berbahaya! Perbaikan harus dilakukan secara langsung / saat ini juga."),
    }
    kat_label, rekom = info[kategori_skor]
    return {
        "kode_owas": f"{b}{a}{l}{ld}",
        "kategori_skor": kategori_skor,
        "kategori": kat_label,
        "rekomendasi": rekom,
    }


def hitung_reba(neck: int, trunk: int, legs: int, load_force: int,
                upper_arm: int, lower_arm: int, wrist: int, coupling: int,
                activity: int) -> dict:
    """Perhitungan Skor REBA (Rapid Entire Body Assessment) Lengkap."""
    # Tabel A: [neck 1..3][trunk 1..5][legs 1..4]
    table_a = {
        1: [[1,2,3,4],[2,3,4,5],[2,4,5,6],[3,5,6,7],[4,6,7,8]],
        2: [[1,2,3,4],[3,4,5,6],[4,5,6,7],[5,6,7,8],[6,7,8,9]],
        3: [[3,3,5,6],[4,5,6,7],[5,6,7,8],[6,7,8,9],[7,8,9,9]],
    }
    n = min(max(neck, 1), 3)
    t = min(max(trunk, 1), 5)
    lg = min(max(legs, 1), 4)
    posture_a = table_a[n][t - 1][lg - 1]
    score_a = posture_a + load_force

    # Tabel B: [upper_arm 1..6][lower_arm 1..2][wrist 1..3]
    table_b = {
        1: [[1,2,2],[1,2,3]],
        2: [[1,2,3],[2,3,4]],
        3: [[3,4,5],[4,5,5]],
        4: [[4,5,5],[5,6,7]],
        5: [[6,7,8],[7,8,8]],
        6: [[7,8,8],[8,9,9]],
    }
    ua = min(max(upper_arm, 1), 6)
    la = min(max(lower_arm, 1), 2)
    wr = min(max(wrist, 1), 3)
    posture_b = table_b[ua][la - 1][wr - 1]
    score_b = posture_b + coupling

    # Tabel C: [score_a 1..12][score_b 1..12]
    table_c = [
        [1, 1, 1, 2, 3, 3, 4, 5, 6, 7, 7, 7],
        [1, 2, 2, 3, 4, 4, 5, 6, 6, 7, 7, 8],
        [2, 3, 3, 3, 4, 5, 6, 7, 7, 8, 8, 8],
        [3, 4, 4, 4, 5, 6, 7, 8, 8, 9, 9, 9],
        [4, 4, 4, 5, 6, 7, 8, 8, 9, 9, 9, 9],
        [6, 6, 6, 7, 8, 8, 9, 9, 10, 10, 10, 10],
        [7, 7, 7, 8, 9, 9, 9, 10, 10, 11, 11, 11],
        [8, 8, 8, 9, 10, 10, 10, 10, 10, 11, 11, 11],
        [9, 9, 9, 10, 10, 10, 11, 11, 11, 12, 12, 12],
        [10, 10, 10, 11, 11, 11, 11, 12, 12, 12, 12, 12],
        [11, 11, 11, 11, 12, 12, 12, 12, 12, 12, 12, 12],
        [12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12],
    ]
    ra = min(max(score_a, 1), 12) - 1
    rb = min(max(score_b, 1), 12) - 1
    score_c = table_c[ra][rb]
    final_reba = score_c + activity

    if final_reba == 1:
        action_level = 0
        kategori = "Level 0 (Skor 1): Risiko Dapat Diabaikan"
        rekomendasi = "Tidak diperlukan tindakan perbaikan."
    elif final_reba in [2, 3]:
        action_level = 1
        kategori = "Level 1 (Skor 2-3): Risiko Rendah"
        rekomendasi = "Mungkin diperlukan tindakan perbaikan postur."
    elif final_reba in [4, 5, 6, 7]:
        action_level = 2
        kategori = "Level 2 (Skor 4-7): Risiko Sedang"
        rekomendasi = "Diperlukan tindakan perbaikan postur dan stasiun kerja."
    elif final_reba in [8, 9, 10]:
        action_level = 3
        kategori = "Level 3 (Skor 8-10): Risiko Tinggi"
        rekomendasi = "Diperlukan tindakan perbaikan segera!"
    else:
        action_level = 4
        kategori = "Level 4 (Skor 11-15): Risiko Sangat Tinggi"
        rekomendasi = "Diperlukan tindakan perbaikan saat ini juga (darurat)!"

    return {
        "posture_a": posture_a,
        "score_a": score_a,
        "posture_b": posture_b,
        "score_b": score_b,
        "score_c": score_c,
        "final_score": final_reba,
        "action_level": action_level,
        "kategori": kategori,
        "rekomendasi": rekomendasi,
    }


def hitung_waktu_kerja(observations: list, p_westinghouse: float, allowance_pct: float,
                       k_level: float = 2.0, s_level: float = 0.05) -> dict:
    """
    Menghitung Waktu Siklus (Ws), Waktu Normal (Wn), Waktu Baku (Wb),
    serta Uji Keseragaman (BKA/BKB) dan Uji Kecukupan Data (N').
    """
    params = (p_westinghouse, allowance_pct, k_level, s_level)
    if not all(np.isfinite(float(value)) for value in params):
        raise ValueError("Parameter time study harus berupa angka hingga.")
    if 1.0 + p_westinghouse <= 0 or not 0 <= allowance_pct < 100 or k_level <= 0 or s_level <= 0:
        raise ValueError("Faktor penyesuaian, kelonggaran (0–<100%), k, dan tingkat ketelitian tidak valid.")
    arr = _positive_measurements(observations)
    n = len(arr)
    if n == 0:
        return {}
    mean_ws = float(np.mean(arr))
    std_s = float(np.std(arr, ddof=1)) if n > 1 else 0.0

    bka = mean_ws + k_level * std_s
    bkb = max(0.0, mean_ws - k_level * std_s)
    seragam = bool(np.all((arr >= bkb) & (arr <= bka)))

    sum_x = float(np.sum(arr))
    sum_x2 = float(np.sum(arr ** 2))
    numerator = (k_level / s_level) * np.sqrt(max(0.0, n * sum_x2 - (sum_x ** 2)))
    n_prime = (numerator / sum_x) ** 2 if sum_x > 0 else 0.0
    cukup = bool(n >= 2 and n >= n_prime)

    # Faktor Penyesuaian (p = 1 + rating Westinghouse)
    p_factor = 1.0 + p_westinghouse
    wn = mean_ws * p_factor
    # Waktu Baku dengan rumus Wb = Wn * (100 / (100 - Allowance%))
    wb = wn * (100.0 / (100.0 - allowance_pct))

    return {
        "n": n,
        "ws": round(mean_ws, 3),
        "std": round(std_s, 3),
        "bka": round(bka, 3),
        "bkb": round(bkb, 3),
        "seragam": "Seragam" if seragam else "Tidak Seragam (Ada Outlier)",
        "n_prime": round(n_prime, 2),
        "cukup": "Cukup (N >= N')" if cukup else "Belum Cukup (N < N')",
        "p_factor": round(p_factor, 3),
        "allowance_pct": round(allowance_pct, 2),
        "wn": round(wn, 3),
        "wb": round(wb, 3),
        "output_standar_per_jam": round(3600.0 / wb, 2) if wb > 0 else 0.0,
    }


def hitung_antropometri_statistik(values: list, k_level: float = 2.0, s_level: float = 0.05) -> dict:
    """Menghitung Rata-rata, SD, BKA, BKB, N', Persentil (P5, P10, P50, P90, P95), dan Uji Normalitas Shapiro-Wilk."""
    if not all(np.isfinite(float(v)) and v > 0 for v in (k_level, s_level)):
        raise ValueError("Nilai k dan tingkat ketelitian harus positif dan hingga.")
    arr = _positive_measurements(values)
    n = len(arr)
    if n == 0:
        return {}
    mean_val = float(np.mean(arr))
    std_val = float(np.std(arr, ddof=1)) if n > 1 else 0.0

    bka = mean_val + k_level * std_val
    bkb = max(0.0, mean_val - k_level * std_val)
    seragam = bool(np.all((arr >= bkb) & (arr <= bka)))

    sum_x = float(np.sum(arr))
    sum_x2 = float(np.sum(arr ** 2))
    numerator = (k_level / s_level) * np.sqrt(max(0.0, n * sum_x2 - (sum_x ** 2)))
    n_prime = (numerator / sum_x) ** 2 if sum_x > 0 else 0.0
    cukup = bool(n >= 3 and n >= n_prime)

    # Persentil Normal (Parametrik)
    p5 = mean_val - 1.645 * std_val
    p10 = mean_val - 1.280 * std_val
    p50 = mean_val
    p90 = mean_val + 1.280 * std_val
    p95 = mean_val + 1.645 * std_val

    # Uji Normalitas Shapiro-Wilk
    if n >= 3 and std_val > 0:
        stat_sw, p_val = stats.shapiro(arr)
        normal_status = "Normal (p > 0.05)" if p_val > 0.05 else "Tidak Normal (p <= 0.05)"
    else:
        stat_sw, p_val = None, None
        normal_status = "Sampel < 3 / Konstan"

    return {
        "n": n,
        "mean": round(mean_val, 2),
        "std": round(std_val, 2),
        "bka": round(bka, 2),
        "bkb": round(bkb, 2),
        "seragam": "Seragam" if seragam else "Ada Outlier",
        "n_prime": round(n_prime, 2),
        "cukup": "Cukup" if cukup else "Belum Cukup",
        "p5": round(p5, 2),
        "p10": round(p10, 2),
        "p50": round(p50, 2),
        "p90": round(p90, 2),
        "p95": round(p95, 2),
        "shapiro_p": round(float(p_val), 4) if p_val is not None else None,
        "normalitas": normal_status,
    }


def hitung_lingkungan_perbandingan(kondisi_a: list, kondisi_b: list, nama_a: str, nama_b: str,
                                   ambang_nab: float, satuan: str) -> dict:
    """Analisis statistik komparatif 2 kondisi lingkungan kerja (paired / independent t-test)."""
    a = np.array([float(x) for x in kondisi_a])
    b = np.array([float(x) for x in kondisi_b])
    mean_a, std_a = float(np.mean(a)), float(np.std(a, ddof=1)) if len(a) > 1 else 0.0
    mean_b, std_b = float(np.mean(b)), float(np.std(b, ddof=1)) if len(b) > 1 else 0.0
    selisih = mean_b - mean_a

    if len(a) == len(b) and len(a) >= 2 and (std_a > 0 or std_b > 0):
        t_stat, p_val = stats.ttest_rel(a, b)
        if np.isnan(p_val):
            t_stat, p_val = 0.0, 1.0
    else:
        t_stat, p_val = 0.0, 1.0

    signifikan = "Berbeda Signifikan (p < 0.05)" if p_val < 0.05 else "Tidak Berbeda Signifikan (p >= 0.05)"

    return {
        f"Mean {nama_a} ({satuan})": round(mean_a, 2),
        f"SD {nama_a}": round(std_a, 2),
        f"Mean {nama_b} ({satuan})": round(mean_b, 2),
        f"SD {nama_b}": round(std_b, 2),
        f"Selisih ({satuan})": round(selisih, 2),
        "Ambang Batas / Standar": f"{ambang_nab} {satuan}",
        "p-value (Uji-t)": round(float(p_val), 4),
        "Kesimpulan Statistik": signifikan,
    }
