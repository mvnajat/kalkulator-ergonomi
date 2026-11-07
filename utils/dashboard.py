"""Small, presentation-only chart datasets for the ErgoLab dashboard.

These views consume existing calculated results. They never recalculate or
reinterpret a module's original formulas.
"""

from dataclasses import dataclass
import math

import pandas as pd


CHART_MODULES = {
    "modul-01": "01 · Fisiologi (%CVL)",
    "modul-02": "02 · Postur (RULA)",
    "modul-03": "03 · Waktu baku",
    "modul-04": "04 · Persentil tubuh",
    "modul-05": "05 · Ukuran rancangan",
    "modul-06": "06 · Temperatur",
    "modul-07": "07 · Kebisingan",
    "modul-08": "08 · Pencahayaan",
    "modul-09": "09 · NIOSH Lifting Index",
}


@dataclass(frozen=True)
class ChartView:
    title: str
    unit: str
    note: str
    data: pd.DataFrame


def _number(value):
    try:
        result = float(value)
    except (ValueError, TypeError):
        return None
    return result if math.isfinite(result) else None


def _chart(title, unit, note, rows):
    data = pd.DataFrame(rows, columns=["Pengamatan", "Nilai"])
    return ChartView(title, unit, note, data)


def build_chart_view(module: str, results: dict, dimension: str = "") -> ChartView:
    """Build a comparison chart only from successfully computed values."""
    if module not in CHART_MODULES:
        raise ValueError("Modul grafik tidak dikenali.")
    if module == "modul-01":
        rows = []
        for row in results.get("m1_rows", []):
            val = _number(row[6])
            if val is not None:
                rows.append((f"{row[0]} · {row[1]}", val))
        return _chart("Beban kardiovaskular", "%CVL", "Ambang interpretasi perlu dibaca bersama konteks aktivitas dan hasil Modul 01.", rows)
    if module == "modul-02":
        rows = []
        for row in results.get("m2_rows", []):
            if row[2] == "RULA" and str(row[3]).startswith("Skor "):
                val = _number(str(row[3])[5:])
                if val is not None:
                    rows.append((f"{row[0]} · {row[1]}", val))
        return _chart("Skor RULA per aktivitas", "Skor RULA", "Skor RULA hanya dibandingkan dengan RULA; OWAS dan REBA memakai skala berbeda.", rows)
    if module == "modul-03":
        rows = [(str(r[1]), val) for r in results.get("m3_rows", []) if (val := _number(r[12])) is not None]
        return _chart("Waktu baku per elemen", "Detik", "Hasil mengikuti metode penyesuaian aktif dan allowance pada Modul 03.", rows)
    if module == "modul-04":
        records = results.get("m4_rows", [])
        row = next((r for r in records if str(r[0]) == dimension), records[0] if records else None)
        rows = [] if row is None else [(label, value) for label, raw in (("P5", row[4]), ("P50", row[6]), ("P95", row[8])) if (value := _number(raw)) is not None]
        return _chart(f"Persentil · {row[1]}" if row else "Persentil dimensi tubuh", "cm", "Persentil parametrik perlu dibaca bersama normalitas dan ukuran sampel.", rows)
    if module == "modul-05":
        rows = [(str(r[0]), value) for r in results.get("m5_rows", []) if (value := _number(r[9])) is not None]
        return _chart("Ukuran rancangan per dimensi", "cm", "Setiap dimensi dapat memakai persentil acuan berbeda; lihat tabel Modul 05.", rows)
    if module in ("modul-06", "modul-07", "modul-08"):
        index = int(module[-2:]) - 6
        records = results.get("env_rows", [])
        row = records[index] if len(records) > index else None
        labels = {
            "modul-06": ("Dingin", "Panas", "°C", "Suhu udara bukan ISBB untuk evaluasi pajanan panas."),
            "modul-07": ("Normal", "Bising", "dBA", "Bacaan sesaat bukan dosis kebisingan 8 jam."),
            "modul-08": ("Normal", "Gelap", "Lux", "Acuan lux harus disesuaikan dengan jenis pekerjaan dan titik ukur."),
        }
        first, second, unit, note = labels[module]
        rows = [] if row is None else [(label, val) for label, raw in ((first, row[2]), (second, row[3])) if (val := _number(raw)) is not None]
        return _chart(f"Perbandingan {first.lower()} & {second.lower()}", unit, note, rows)
    summary = results.get("m9_summary") or {}
    sim = results.get("m9_simulasi_summary") or {}
    rows = []
    before = _number(summary.get("li"))
    if before is not None:
        rows.append(("Kondisi awal", before))
    proposed = _number((sim.get("usulan") or {}).get("li"))
    if proposed is not None:
        rows.append(("Skenario usulan", proposed))
    return _chart("Perubahan NIOSH Lifting Index", "LI", "LI bukan probabilitas cedera; skenario usulan adalah simulasi, bukan pengukuran lapangan.", rows)
