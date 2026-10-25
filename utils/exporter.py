import io
import json
from collections.abc import MutableMapping
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


SESSION_BACKUP_FIELDS = (
    ("identitas", "identitas"),
    ("modul_01_fisiologi", "modul_01"),
    ("modul_02_postur", "modul_02"),
    ("modul_03_waktu_kerja", "modul_03"),
    ("modul_04_antropometri_32", "modul_04"),
    ("modul_05_antropometri_lanjutan", "modul_05"),
    ("modul_06_temperatur", "modul_06"),
    ("modul_07_kebisingan", "modul_07"),
    ("modul_08_pencahayaan", "modul_08"),
    ("modul_09_mmh", "modul_09"),
    ("analisis_modul", "analisis_modul"),
)


def export_session_to_json(state_dict: dict) -> str:
    """Mengekspor seluruh data praktikum dari session_state ke format JSON terstruktur."""
    export_data = {json_key: state_dict.get(state_key, {}) for json_key, state_key in SESSION_BACKUP_FIELDS}
    return json.dumps(export_data, indent=2, ensure_ascii=False)


def restore_session_from_json(state: MutableMapping, backup: dict) -> None:
    """Pulihkan bidang yang tersedia, termasuk backup lama tanpa Modul 09."""
    if not isinstance(backup, dict):
        raise ValueError("Format cadangan harus berupa objek JSON.")

    restored = {}
    for json_key, state_key in SESSION_BACKUP_FIELDS:
        if json_key in backup:
            if not isinstance(backup[json_key], dict):
                raise ValueError(f"Data '{json_key}' harus berupa objek JSON.")
            restored[state_key] = backup[json_key]

    for state_key, value in restored.items():
        state[state_key] = value


def export_session_to_excel(state_dict: dict, calc_results: dict) -> bytes:
    """Membuat file laporan Excel (.xlsx) lengkap dengan styling rapi untuk seluruh modul."""
    wb = openpyxl.Workbook()
    # Hapus sheet default
    wb.remove(wb.active)

    # Palet Styling
    header_fill = PatternFill(start_color="0F2E1E", end_color="0F2E1E", fill_type="solid")
    sub_fill = PatternFill(start_color="19452F", end_color="19452F", fill_type="solid")
    zebra_fill = PatternFill(start_color="F2F8F5", end_color="F2F8F5", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=14, bold=True, color="0F2E1E")
    bold_font = Font(name="Calibri", size=10, bold=True)
    reg_font = Font(name="Calibri", size=10)
    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1"),
    )

    def style_worksheet(ws, title_text: str):
        ws.views.sheetView[0].showGridLines = True
        ws["A1"] = title_text
        ws["A1"].font = title_font
        ws["A2"] = "UNIVERSITAS PELITA BANGSA - PROGRAM STUDI TEKNIK INDUSTRI"
        ws["A2"].font = bold_font

    def write_table(ws, start_row: int, headers: list, rows: list):
        for col_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=start_row, column=col_idx, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border
        for r_idx, row_data in enumerate(rows, start=start_row + 1):
            for col_idx, val in enumerate(row_data, start=1):
                cell = ws.cell(row=r_idx, column=col_idx, value=val)
                cell.font = reg_font
                cell.border = thin_border
                if (r_idx - start_row) % 2 == 0:
                    cell.fill = zebra_fill
        # Auto-fit lebar kolom
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or "")
                max_len = max(max_len, len(val_str))
            ws.column_dimensions[col_letter].width = min(max(max_len + 4, 14), 45)

    # 1. Sheet Identitas & Ringkasan
    ws_id = wb.create_sheet("00_Identitas")
    style_worksheet(ws_id, "IDENTITAS KELOMPOK PRAKTIKUM ERGONOMI")
    id_data = state_dict.get("identitas", {})
    rows_id = [
        ["Kelas", id_data.get("kelas", "J253B")],
        ["Kelompok", id_data.get("kelompok", "Kelompok 1")],
        ["Tanggal Praktikum", id_data.get("tanggal", "")],
        ["Asisten / Dosen Pengampu", id_data.get("dosen", "")],
        ["Operator 1 (Nama & Usia)", f"{id_data.get('op1_nama', '')} ({id_data.get('op1_usia', '')} thn)"],
        ["Operator 2 (Nama & Usia)", f"{id_data.get('op2_nama', '')} ({id_data.get('op2_usia', '')} thn)"],
        ["Daftar Anggota Kelompok", id_data.get("anggota", "")],
    ]
    write_table(ws_id, 4, ["Parameter Identitas", "Keterangan"], rows_id)

    # 2. Sheet Modul 01 Fisiologi
    ws_m1 = wb.create_sheet("01_Fisiologi")
    style_worksheet(ws_m1, "MODUL 01 - FISIOLOGI KERJA & BEBAN KARDIOVASKULAR (%CVL)")
    m1_rows = calc_results.get("m1_rows", [])
    write_table(ws_m1, 4, [
        "Operator", "Aktivitas", "Usia (th)", "DN Istirahat (bpm)", "DN Kerja (bpm)",
        "DN Maks (bpm)", "%CVL (%)", "Konsumsi Energi Bersih (kkal/mnt)", "Kategori Beban", "Rekomendasi"
    ], m1_rows)

    # 3. Sheet Modul 02 Postur (RULA, OWAS, REBA)
    ws_m2 = wb.create_sheet("02_Postur_Kerja")
    style_worksheet(ws_m2, "MODUL 02 - ANALISIS POSTUR KERJA (RULA, OWAS, & REBA)")
    m2_rows = calc_results.get("m2_rows", [])
    write_table(ws_m2, 4, [
        "Operator", "Aktivitas", "Metode", "Skor / Kode Akhir", "Action Level", "Kategori Risiko", "Rekomendasi Perbaikan"
    ], m2_rows)

    # 4. Sheet Modul 03 Waktu Kerja
    ws_m3 = wb.create_sheet("03_Waktu_Kerja")
    style_worksheet(ws_m3, "MODUL 03 - PENGUKURAN WAKTU KERJA (TIME STUDY)")
    m3_rows = calc_results.get("m3_rows", [])
    write_table(ws_m3, 4, [
        "Kode", "Elemen Kerja", "Ws Rata-rata (dtk)", "SD (dtk)", "BKB", "BKA",
        "Keseragaman", "N'", "Kecukupan", "Faktor p", "Allowance (%)", "Wn (dtk)", "Wb (dtk)", "Output Standar (unit/jam)"
    ], m3_rows)

    # 5. Sheet Modul 04 Antropometri 32 Dimensi
    ws_m4 = wb.create_sheet("04_Antropometri_32D")
    style_worksheet(ws_m4, "MODUL 04 - ANTROPOMETRI (32 DIMENSI TUBUH & PERSENTIL DESAIN)")
    m4_rows = calc_results.get("m4_rows", [])
    write_table(ws_m4, 4, [
        "Kode", "Nama Dimensi Tubuh", "Mean (cm)", "SD (cm)", "P5 (cm)", "P10 (cm)", "P50 (cm)", "P90 (cm)", "P95 (cm)", "Uji Normalitas", "Aplikasi Desain Stasiun Kerja"
    ], m4_rows)

    # 6. Sheet Modul 05 Antropometri Lanjutan
    ws_m5 = wb.create_sheet("05_Antropometri_Lanjutan")
    style_worksheet(ws_m5, "MODUL 05 - ANTROPOMETRI LANJUTAN (UJI KESERAGAMAN, KECUKUPAN & RANCANGAN)")
    m5_rows = calc_results.get("m5_rows", [])
    write_table(ws_m5, 4, [
        "Dimensi Kunci", "Mean (cm)", "SD (cm)", "BKB (cm)", "BKA (cm)",
        "Status Keseragaman", "N'", "Status Kecukupan", "Persentil Acuan", "Ukuran Rancangan (cm)"
    ], m5_rows)

    # 7. Sheet Modul 06, 07, 08 Lingkungan Fisik
    ws_env = wb.create_sheet("06_08_Lingkungan_Kerja")
    style_worksheet(ws_env, "MODUL 06, 07, & 08 - LINGKUNGAN FISIK KERJA (TEMPERATUR, KEBISINGAN, PENCAHAYAAN)")
    env_rows = calc_results.get("env_rows", [])
    write_table(ws_env, 4, [
        "Modul", "Parameter Uji", "Rata-rata Kondisi Normal/Dingin", "Rata-rata Kondisi Ekstrem/Bising/Gelap",
        "Selisih", "Standar NAB / SNI", "p-value (Uji-t)", "Kesimpulan Statistik", "Analisis & Rekomendasi"
    ], env_rows)

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()
