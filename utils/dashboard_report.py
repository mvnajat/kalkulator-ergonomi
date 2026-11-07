"""Compact, printable ErgoLab progress summary; separate from detailed module PDFs."""

from datetime import datetime
import math
import unicodedata
from zoneinfo import ZoneInfo

from utils.dashboard import CHART_MODULES, build_chart_view


def _latin(value):
    return unicodedata.normalize("NFKD", str(value)).encode("latin-1", "replace").decode("latin-1")


def export_dashboard_pdf(project_name: str, identity: dict, done: dict, results: dict) -> bytes:
    from fpdf import FPDF

    pdf = FPDF(format="A4")
    pdf.set_margins(16, 16, 16)
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()

    pdf.set_fill_color(18, 91, 64)
    pdf.rect(0, 0, 210, 38, "F")
    pdf.set_xy(16, 10)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 9, "ERGOLAB  /  RINGKASAN PRAKTIKUM", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(213, 241, 223)
    pdf.cell(0, 6, "Status kemajuan dan gambaran hasil perhitungan saat ini", new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(47)
    pdf.set_text_color(33, 50, 42)

    def line(value, bold=False, size=9):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B" if bold else "", size)
        pdf.multi_cell(0, 5.6, _latin(value))

    def section(value):
        pdf.ln(4)
        pdf.set_fill_color(233, 245, 237)
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(0, 7, _latin(value), fill=True)
        pdf.ln(2)

    checked = sum(bool(done.get(slug)) for slug in CHART_MODULES)
    now = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%d-%m-%Y %H:%M WIB")
    line(f"Proyek: {project_name}", True)
    line(f"Kelas / Kelompok: {identity.get('kelas', '-')} / {identity.get('kelompok', '-')}")
    line(f"Tanggal ekspor: {now}")
    line(f"Modul yang ditandai selesai: {checked} dari 9 ({checked / 9:.0%})", True)
    line("PERHATIAN: nilai awal aplikasi adalah contoh latihan. Status selesai ditandai manual oleh pengguna.", size=8)

    section("01  STATUS SEMBILAN MODUL")
    for slug, title in CHART_MODULES.items():
        line(f"{'[SUDAH DIPERIKSA]' if done.get(slug) else '[BELUM DIPERIKSA]'}  {title}")

    section("02  INDIKATOR HASIL TERPILIH")
    rows_m1 = results.get("m1_rows", [])
    cvls = [float(r[6]) for r in rows_m1 if isinstance(r[6], (float, int)) and math.isfinite(float(r[6]))]
    if cvls:
        line(f"Modul 01 - Rentang %CVL pengamatan: {min(cvls):.2f}% sampai {max(cvls):.2f}%")
    rows_m3 = results.get("m3_rows", [])
    if rows_m3:
        line(f"Modul 03 - Jumlah waktu baku elemen: {sum(float(r[12]) for r in rows_m3):.2f} detik")
    for slug in ("modul-06", "modul-07", "modul-08", "modul-09"):
        chart = build_chart_view(slug, results)
        if not chart.data.empty:
            vals = ", ".join(f"{r['Pengamatan']} {r['Nilai']:g}" for r in chart.data.to_dict("records"))
            line(f"{CHART_MODULES[slug]} - {vals} {chart.unit}")
    line("Perbandingan antar-satuan berbeda tidak dilakukan. Interpretasi tetap memerlukan observasi asli.", size=8)

    section("03  CATATAN PENGGUNAAN")
    line("Laporan ini adalah ringkasan status dan hasil sesi, bukan berita acara pengukuran atau sertifikat keselamatan kerja.")
    line("Gunakan menu Laporan untuk mengunduh penelusuran rumus, hasil rinci, dan pembahasan masing-masing modul.")
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 122, 110)
    pdf.multi_cell(0, 5, "Dihasilkan otomatis oleh ErgoLab dari data sesi yang aktif.", align="C")
    return bytes(pdf.output())
