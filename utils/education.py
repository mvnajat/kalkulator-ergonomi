"""Auditable calculation walkthroughs and concise practice material."""

import statistics

from utils.calculations import (
    hitung_fisiologi_cvl, hitung_waktu_kerja, hitung_antropometri_statistik,
    hitung_rula, hitung_owas, hitung_reba,
)
from utils.advanced_features import hitung_niosh_lifting


LESSONS = {
    "01": ("Fisiologi Kerja", "Denyut nadi kerja, denyut nadi maksimum, %CVL, dan estimasi energi.",
           "Bagaimana perubahan denyut kerja memengaruhi %CVL jika nadi istirahat tetap?",
           "%CVL adalah indikator latihan, bukan diagnosis medis. Periksa cara pengukuran denyut nadi."),
    "02": ("Penilaian Postur", "RULA, OWAS, dan REBA adalah metode penilaian postur dengan tabel skor.",
           "Nilai satu aktivitas sebelum dan sesudah memperbaiki posisi meja.",
           "Skor harus diverifikasi dari observasi sudut, gaya, durasi, dan aktivitas; AI hanya alat bantu."),
    "03": ("Pengukuran Waktu Kerja", "Waktu siklus, faktor Westinghouse, allowance, uji keseragaman dan kecukupan.",
           "Hitung Wn dan Wb untuk satu elemen setelah mengubah allowance dari 10% ke 15%.",
           "Pilih rumus allowance sesuai panduan dosen; aplikasi memakai Wb = Wn/(1 - a)."),
    "04": ("Antropometri 32 Dimensi", "Rata-rata, simpangan baku sampel, persentil normal dan uji Shapiro-Wilk.",
           "Bandingkan P5, P50, dan P95 untuk tinggi popliteal.",
           "Persentil parametrik mengasumsikan data mendekati distribusi normal; periksa ukuran sampel."),
    "05": ("Rancangan Stasiun Kerja", "Persentil dimensi tubuh dan kelonggaran diterapkan ke desain.",
           "Mengapa jangkauan sering memakai P5 sedangkan ruang bebas memakai P95?",
           "Pemilihan persentil dan kelonggaran tergantung fungsi rancangan dan populasi pengguna."),
    "06": ("Temperatur", "Bandingkan suhu rata-rata dua kondisi dan uji-t berpasangan.",
           "Apa bedanya suhu udara biasa dengan ISBB untuk evaluasi iklim kerja?",
           "Acuan 28 °C pada aplikasi adalah latihan, bukan ambang resmi ISBB."),
    "07": ("Kebisingan", "Ringkas pembacaan dBA dan bandingkan kondisi perlakuan.",
           "Mengapa rata-rata dBA sesaat belum dapat dinyatakan sebagai pajanan LAeq 8 jam?",
           "Rata-rata aritmetika bacaan dBA bukan pengukuran pajanan ekuivalen atau dosis kebisingan."),
    "08": ("Pencahayaan", "Hitung iluminansi (lux) rata-rata dan evaluasi kesesuaian tugas visual.",
           "Mengapa pekerjaan presisi memerlukan iluminansi berbeda dari lorong?",
           "Acuan lux harus disesuaikan dengan jenis pekerjaan dan cara pengukuran."),
    "09": ("Manual Material Handling", "NIOSH RWL/LI, simulasi Snook, dan estimasi biomekanika L5/S1.",
           "Turunkan berat beban dan jarak horizontal, lalu bandingkan LI awal dan usulan.",
           "RNLE hanya untuk tugas sesuai cakupan model; Snook dan L5/S1 di sini edukatif."),
}


def worked_example(module: str, state: dict) -> list[str]:
    """Examples use current inputs and the *same* calculation functions as reports."""
    m = state[f"modul_{module}"]
    if module == "01":
        ident = state["identitas"]
        rest, work = float(m["op1_akt1_dni"]), float(m["op1_akt1_dnk"])
        age = int(ident["op1_usia"])
        maximum = 220 - age if ident["op1_jk"] == "Laki-laki" else 200 - age
        r = hitung_fisiologi_cvl(rest, work, age, ident["op1_jk"])
        denominator = max(maximum - rest, 1)
        return [f"DN maks = {maximum} bpm (usia {age} tahun)",
                f"%CVL = ({work:g} - {rest:g}) / {denominator:g} × 100 = {r['cvl_persen']:.2f}%",
                f"Estimasi energi bersih = {r['ke_bersih_kkal_menit']} kkal/menit"]
    if module == "02":
        records = m.get("records", [])
        if not records:
            return ["Tambahkan catatan observasi postur untuk melihat contoh."]
        r = records[0]
        p, o, b = r["rula_params"], r["owas_params"], r["reba_params"]
        ru = hitung_rula(p["ua"], p["la"], p["wr"], p["wt"], p["nk"], p["tr"], p["lg"], p["ma"], p["fa"], p["mb"], p["fb"])
        ow = hitung_owas(o["back"], o["arms"], o["legs"], o["load"])
        re = hitung_reba(b["neck"], b["trunk"], b["legs"], b["load"], b["ua"], b["la"], b["wr"], b["coup"], b["act"])
        return [f"RULA: tabel A/B → skor C={ru['score_c']}, D={ru['score_d']} → grand score {ru['grand_score']}",
                f"OWAS: punggung-lengan-kaki-beban = {ow['kode_owas']} → kategori {ow['kategori_skor']}",
                f"REBA: tabel A={re['score_a']}, B={re['score_b']}, C={re['score_c']} + aktivitas → {re['final_score']}"]
    if module == "03":
        rows = m.get("df_siklus", [])
        if not rows:
            return ["Masukkan waktu siklus untuk melihat penelusuran rumus."]
        x = [float(rows[0].get(f"S{i}") or 0) for i in range(1, 11)]
        west = sum(m["westinghouse"].values())
        allowance = sum(m[field] for field in ("allowance_pribadi", "allowance_kelelahan", "allowance_hambatan"))
        r = hitung_waktu_kerja(x, west, allowance, m["k_level"], m["s_level"])
        return [f"Ws = Σ waktu / n = {sum(x):.3f} / {len(x)} = {r['ws']:.3f} detik",
                f"p = 1 + Σ rating Westinghouse = 1 + ({west:+.3f}) = {r['p_factor']:.3f}",
                f"Wn = Ws × p ≈ {r['ws']:.3f} × {r['p_factor']:.3f} = {r['wn']:.3f} detik",
                f"Wb = Wn / (1 - {allowance:g}/100) = {r['wb']:.3f} detik",
                f"BKA/BKB = Ws ± k × SD = {r['bka']:.3f} / {r['bkb']:.3f}; N' = {r['n_prime']:.2f}",
                f"Output standar = 3600/Wb = {r['output_standar_per_jam']:.2f} unit/jam"]
    if module in ("04", "05"):
        key, prefix = ("df_32", "P") if module == "04" else ("df_3dim", "S")
        rows = m.get(key, [])
        if not rows:
            return ["Masukkan data antropometri untuk melihat contoh."]
        x = [float(rows[0].get(f"{prefix}{i}") or 0) for i in range(1, 11)]
        r = hitung_antropometri_statistik(x)
        statements = [f"Mean = Σx / n = {sum(x):.2f} / {len(x)} = {r['mean']:.2f} cm",
                      f"SD sampel = {r['std']:.2f} cm; P5 = mean - 1,645×SD = {r['p5']:.2f} cm",
                      f"P50 = mean = {r['p50']:.2f} cm; P95 = mean + 1,645×SD = {r['p95']:.2f} cm",
                      f"Keseragaman = {r['seragam']}; kecukupan = {r['cukup']}; normalitas = {r['normalitas']}"]
        if module == "05":
            field = str(rows[0].get("Persentil Acuan", "P50")).lower()
            allowance = float(rows[0].get("Kelonggaran (cm)") or 0)
            statements.append(f"Ukuran desain = {field.upper()} + kelonggaran = {r.get(field, r['p50']):.2f} + {allowance:.2f} cm")
        return statements
    if module in ("06", "07", "08"):
        from utils.importer import ENVIRONMENT
        a, b, *_ = ENVIRONMENT[module]
        av, bv = m[a], m[b]
        am, bm = statistics.mean(av), statistics.mean(bv)
        return [f"Rata-rata kondisi A = ({' + '.join(f'{v:g}' for v in av)}) / {len(av)} = {am:.2f}",
                f"Rata-rata kondisi B = ({' + '.join(f'{v:g}' for v in bv)}) / {len(bv)} = {bm:.2f}",
                f"Selisih rata-rata = {bm:.2f} - {am:.2f} = {bm-am:+.2f}",
                "Uji-t berpasangan dihitung dari selisih per pasangan percobaan; n=3 perlu interpretasi hati-hati."]
    if module == "09":
        r = hitung_niosh_lifting(m["h_cm"], m["v_cm"], m["d_cm"], m["a_deg"], m["f_lift"], m["coupling"], m["berat_beban"], m.get("durasi_angkat", "≤ 1 jam"))
        return [f"RWL = 23 × HM({r['hm']}) × VM({r['vm']}) × DM({r['dm']}) × AM({r['am']}) × FM({r['fm']}) × CM({r['cm']}) = {r['rwl']} kg",
                f"LI = beban / RWL = {m['berat_beban']} / {r['rwl']} = {r['li']}" if r["li"] is not None else "RWL=0, LI tidak terdefinisi (di luar cakupan model)."]
    raise ValueError("Modul belum tersedia.")
