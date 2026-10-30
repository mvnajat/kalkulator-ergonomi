"""Golden tests: Phase 1 heart-rate recovery and four time-study ratings."""

import io
import math
import unittest

from openpyxl import load_workbook

from utils.calculations import (
    hitung_fisiologi_cvl, hitung_pemulihan_nadi,
    hitung_perbandingan_waktu_kerja, hitung_waktu_kerja,
)
from utils.exporter import export_session_to_excel
from utils.module_report import export_module_pdf
from test_roadmap_features import sample_state


WEST = {"skill": 0.06, "effort": 0.05, "condition": 0.02, "consistency": 0.01}


class PhaseOneFormulaTests(unittest.TestCase):
    def test_golden_operator_1_ecpt_ecpm_from_practicum(self):
        pulse = dict(zip((f"P{i}" for i in range(6)), (82, 115, 86, 85, 83, 75)))
        result = hitung_pemulihan_nadi(pulse)
        self.assertEqual(result["rata_akhir"], 81.0)
        self.assertEqual(result["ecpt"], -1.0)
        self.assertEqual(result["ecpm"], 35.0)
        self.assertEqual(result["pemulihan_persen"], 121.21)
        self.assertIn("di bawah", result["status"])

    def test_golden_operator_2_recovery(self):
        pulse = dict(zip((f"P{i}" for i in range(6)), (88, 111, 92, 92, 90, 86)))
        result = hitung_pemulihan_nadi(pulse)
        self.assertAlmostEqual(result["rata_akhir"], 89.333, places=3)
        self.assertAlmostEqual(result["ecpt"], 1.333, places=3)
        self.assertAlmostEqual(result["ecpm"], 21.667, places=3)

    def test_recovery_denominator_zero_remains_undefined(self):
        result = hitung_pemulihan_nadi({f"P{i}": 80 for i in range(6)})
        self.assertIsNone(result["pemulihan_persen"])
        self.assertEqual(result["ecpt"], 0)
        self.assertEqual(result["ecpm"], 0)

    def test_recovery_rejects_missing_nonfinite_and_out_of_range(self):
        valid = {f"P{i}": 80 for i in range(6)}
        for pulse in ({"P0": 80}, {**valid, "P2": float("nan")},
                      {**valid, "P4": float("inf")}, {**valid, "P5": -1}):
            with self.subTest(pulse=pulse), self.assertRaises(ValueError):
                hitung_pemulihan_nadi(pulse)

    def test_cvl_golden_and_boundary_threshold(self):
        result = hitung_fisiologi_cvl(80, 110, 21)
        self.assertEqual(result["dn_max"], 199)
        self.assertEqual(result["cvl_persen"], 25.21)
        self.assertEqual(hitung_fisiologi_cvl(80, 110, 100, "Perempuan")["cvl_persen"], 150)
        at_30 = hitung_fisiologi_cvl(80, 80 + 0.3 * (199 - 80), 21)
        self.assertIn("perbaikan", at_30["kategori"])

    def test_cvl_invalid_denominator_is_not_silently_forced_to_one(self):
        with self.assertRaisesRegex(ValueError, "lebih rendah"):
            hitung_fisiologi_cvl(140, 150, 70, "Perempuan")
        with self.assertRaises(ValueError):
            hitung_fisiologi_cvl(float("inf"), 100, 21)
        with self.assertRaises(ValueError):
            hitung_fisiologi_cvl(80, 100, -1)
        lower = hitung_fisiologi_cvl(90, 80, 21)
        self.assertIn("cek pengukuran", lower["kategori"])

    def study(self, *, score=60, diff=None, final=1.05, allowance=20, observations=None):
        return hitung_perbandingan_waktu_kerja(
            [10, 10, 10] if observations is None else observations,
            westinghouse=WEST, skor_schummard=score,
            skor_kesulitan={"ABT": 5, "PK": 5} if diff is None else diff,
            p_akhir=final, allowance_pct=allowance,
        )

    def test_golden_four_methods_and_allowance(self):
        result = self.study()
        self.assertEqual(result["p1"], 1)
        self.assertEqual(result["p2"], 1.1)
        self.assertAlmostEqual(result["factors"]["Westinghouse"], 1.14)
        expected_wb = {"Westinghouse": 14.25, "Schummard": 12.5,
                       "Objektif": 13.75, "Akhir (manual)": 13.125}
        for method, wb in expected_wb.items():
            with self.subTest(method=method):
                row = result["results"][method]
                self.assertAlmostEqual(row["wn"], 10 * result["factors"][method], places=3)
                self.assertAlmostEqual(row["wb"], wb, places=3)
                self.assertAlmostEqual(row["output_standar_per_jam"], round(3600 / wb, 2))
                self.assertEqual(row["n"], 3)
                self.assertEqual(row["n_prime"], 0)

    def test_schummard_72_and_objective_sum_25(self):
        result = self.study(score=72, diff={"ABT": 10, "PK": 5, "PT": 10}, allowance=0)
        self.assertEqual(result["p1"], 1.2)
        self.assertEqual(result["p2"], 1.25)
        self.assertAlmostEqual(result["factors"]["Objektif"], 1.5)
        self.assertEqual(result["results"]["Objektif"]["wb"], 15)

    def test_same_measurements_give_same_stats_every_method(self):
        result = self.study(observations=[8, 9, 10, 11, 12])
        fields = ("n", "ws", "std", "bkb", "bka", "n_prime", "seragam", "cukup")
        first = result["results"]["Westinghouse"]
        for value in result["results"].values():
            self.assertEqual([value[field] for field in fields], [first[field] for field in fields])

    def test_rejects_invalid_rating_inputs(self):
        for kwargs in ({"score": 0}, {"score": math.nan},
                       {"diff": {"ABT": -2}}, {"diff": {"BB": math.inf}},
                       {"final": 0}, {"final": 4}, {"allowance": 100}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.study(**kwargs)

    def test_legacy_westinghouse_equivalence(self):
        result = self.study(observations=[5.2, 5.4, 5.3])
        legacy = hitung_waktu_kerja([5.2, 5.4, 5.3], 0.14, 20)
        self.assertEqual(result["results"]["Westinghouse"], legacy)


class PhaseOneExportTests(unittest.TestCase):
    def test_new_sheets_are_auditable_without_breaking_old_workbooks(self):
        recovery = ["Operator 1", 82, 115, 86, 85, 83, 75, -1, 35, 121.21, "Catatan"]
        compare = ["EL-01", "Menulis", "Objektif", 10, 1.1, 1, 1.1, 10, 20,
                   11, 13.75, 261.82, 0, "Cukup", "Seragam"]
        blob = export_session_to_excel(sample_state(), {
            "m1_recovery_rows": [recovery], "m3_comparison_rows": [compare],
        })
        wb = load_workbook(io.BytesIO(blob))
        self.assertIn("01_Pemulihan_Nadi", wb.sheetnames)
        self.assertIn("03_Perbandingan_Metode", wb.sheetnames)
        self.assertEqual(wb["01_Pemulihan_Nadi"]["H5"].value, -1)
        self.assertEqual(wb["03_Perbandingan_Metode"]["K5"].value, 13.75)

    def test_module_pdfs_include_phase1_details(self):
        state = sample_state()
        result = {"m1_rows": [], "m3_rows": [],
                  "m1_recovery_rows": [["Operator", 82, 115, 86, 85, 83, 75, -1, 35, 121.21, "Catatan"]],
                  "m3_comparison_rows": [["EL-01", "Menulis", "Objektif", 10, 1.1,
                                          1, 1.1, 10, 20, 11, 13.75, 261.82, 0, "Cukup", "Seragam"]]}
        for module in ("01", "03"):
            with self.subTest(module=module):
                self.assertGreater(len(export_module_pdf(module, state, result)), 1500)


if __name__ == "__main__":
    unittest.main()
