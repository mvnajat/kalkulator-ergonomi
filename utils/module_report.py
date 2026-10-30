"""Printable per-module PDF with observations, worked examples, and notes."""

import unicodedata

from utils.education import LESSONS, worked_example


RESULT_KEY = {"01": "m1_rows", "02": "m2_rows", "03": "m3_rows", "04": "m4_rows", "05": "m5_rows"}


def _safe_text(value) -> str:
    return unicodedata.normalize("NFKD", str(value)).encode("latin-1", "replace").decode("latin-1")


def export_module_pdf(module: str, state: dict, results: dict) -> bytes:
    from fpdf import FPDF

    module = str(module).zfill(2)
    if module not in LESSONS:
        raise ValueError("Nomor modul tidak tersedia.")
    lesson = LESSONS[module]
    ident = state["identitas"]
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(15, 15, 15)
    pdf.add_page()

    def line(text, bold=False):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B" if bold else "", 10 if bold else 9)
        pdf.multi_cell(0, 5.7, _safe_text(text))

    def section(text):
        pdf.ln(4)
        pdf.set_fill_color(227, 244, 232)
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(0, 7, _safe_text(text), fill=True)
        pdf.ln(2)

    line(f"LAPORAN MODUL {module} - {lesson[0].upper()}", bold=True)
    line(f"Universitas: {ident.get('universitas', '-')}")
    line(f"Kelas/Kelompok: {ident.get('kelas', '-')} / {ident.get('kelompok', '-')}")
    line(f"Tanggal: {ident.get('tanggal', '-')} | Dosen: {ident.get('dosen', '-')}")
    section("A. TUJUAN DAN BATAS METODE")
    line(lesson[1])
    line(lesson[3])
    section("B. PENELUSURAN RUMUS / METODE")
    for example in worked_example(module, state):
        line("- " + example)
    section("C. HASIL PENGOLAHAN DATA")
    if module in RESULT_KEY:
        rows = results.get(RESULT_KEY[module], [])
    elif module in ("06", "07", "08"):
        rows = [results.get("env_rows", [])[int(module) - 6]]
    else:
        rows = [[f"RWL = {results.get('m9_summary', {}).get('rwl')}",
                 f"LI = {results.get('m9_summary', {}).get('li')}",
                 f"L5/S1 = {results.get('m9_summary', {}).get('f_kompresi_n')} N"]]
    if rows:
        for i, row in enumerate(rows, 1):
            line(f"{i}. " + " | ".join(_safe_text(value) for value in row))
    else:
        line("Belum ada hasil yang valid.")
    section("D. PEMBAHASAN DAN KESIMPULAN PRAKTIKAN")
    line(state.get("analisis_modul", {}).get(f"Modul {module}", "Belum diisi."))
    section("E. LATIHAN / TINDAK LANJUT")
    line(lesson[2])
    pdf.ln(7)
    line("Dosen / Asisten: __________________     Ketua Kelompok: __________________")
    return bytes(pdf.output())
