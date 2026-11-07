"""Dashboard views, account-private history and printable summary regression tests."""

from datetime import datetime, timezone
import sys
import types
import unittest
from unittest.mock import patch
from uuid import UUID

from utils.dashboard import CHART_MODULES, build_chart_view
from utils.dashboard_report import export_dashboard_pdf
from utils.workspace import cloud_history_list, cloud_history_load, cloud_history_save


SAMPLE_RESULTS = {
    "m1_rows": [["A", "Menulis", 20, 80, 105, 200, 20.83, 1.2, "Rendah", "Pantau"]],
    "m2_rows": [["A", "Menulis", "RULA", "Skor 4", "Level 2", "Sedang", "Evaluasi"],
                 ["A", "Menulis", "OWAS", "Kode 2121", "Level 1", "Rendah", "Pantau"]],
    "m3_rows": [["E1", "Mengukur", 20, 2, 18, 22, "Seragam", 3, "Cukup", 1, 10, 20, 22.22, 162]],
    "m4_rows": [["D01", "Tinggi badan", 160, 7, 149, 151, 160, 169, 171, "Normal", "Desain"]],
    "m5_rows": [["Tinggi meja", 70, 2, 66, 74, "Seragam", 3, "Cukup", "P50", 71]],
    "env_rows": [
        ["Modul 06", "Suhu", 24, 31, 7, 30, 0.1, "Berbeda", "Pantau"],
        ["Modul 07", "dBA", 62, 88, 26, 85, 0.1, "Berbeda", "Pantau"],
        ["Modul 08", "Lux", 300, 120, -180, 200, 0.1, "Berbeda", "Pantau"],
    ],
    "m9_summary": {"rwl": 18, "li": 1.25, "kategori": "Perlu perbaikan", "f_kompresi_n": 2700},
    "m9_simulasi_summary": {"usulan": {"li": 0.75}},
}


class DashboardDataTests(unittest.TestCase):
    def test_each_module_has_chart_from_original_results(self):
        self.assertEqual(len(CHART_MODULES), 9)
        expected = {"modul-01": 20.83, "modul-02": 4, "modul-03": 22.22,
                    "modul-04": 149, "modul-05": 71, "modul-06": 24,
                    "modul-07": 62, "modul-08": 300, "modul-09": 1.25}
        for slug, value in expected.items():
            with self.subTest(slug=slug):
                chart = build_chart_view(slug, SAMPLE_RESULTS)
                self.assertFalse(chart.data.empty)
                self.assertAlmostEqual(chart.data.iloc[0]["Nilai"], value)
                self.assertTrue(chart.note)

    def test_rula_chart_never_mixes_owas_or_reba(self):
        chart = build_chart_view("modul-02", SAMPLE_RESULTS)
        self.assertEqual(chart.data["Nilai"].tolist(), [4.0])

    def test_missing_and_invalid_results_are_safe(self):
        for slug in CHART_MODULES:
            with self.subTest(slug=slug):
                self.assertTrue(build_chart_view(slug, {}).data.empty)
        bad = {"m1_rows": [["A", "Menulis", 20, 80, 105, 200, float("inf")]]}
        self.assertTrue(build_chart_view("modul-01", bad).data.empty)
        with self.assertRaises(ValueError):
            build_chart_view("modul-10", {})

    def test_dashboard_summary_pdf_exports_without_login(self):
        pdf = export_dashboard_pdf("Latihan 01", {"kelas": "J253B", "kelompok": "020"},
                                   {"modul-01": True, "modul-09": False}, SAMPLE_RESULTS)
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 1600)


class CloudHistoryTests(unittest.TestCase):
    def setUp(self):
        self.queries = []
        owner = self

        class Cursor:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def execute(self, query, params=None):
                owner.queries.append((query, params))

            def fetchall(self):
                return [("640dbd49-9774-4c2a-beb0-77d2faf5a143", "Proyek A", "modul-01",
                         "Beban kardiovaskular", datetime(2026, 11, 7, tzinfo=timezone.utc))]

            def fetchone(self):
                return ({"identitas": {"kelas": "J253B"}},)

        class Connection:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def cursor(self):
                return Cursor()

        self.fake_psycopg = types.ModuleType("psycopg")
        self.fake_psycopg.connect = lambda *_a, **_kw: Connection()
        fake_types = types.ModuleType("psycopg.types")
        fake_json = types.ModuleType("psycopg.types.json")
        fake_json.Jsonb = lambda val: val
        self.modules_patch = patch.dict(sys.modules, {"psycopg": self.fake_psycopg,
                                                      "psycopg.types": fake_types,
                                                      "psycopg.types.json": fake_json})
        self.modules_patch.start()

    def tearDown(self):
        self.modules_patch.stop()

    def test_history_saves_append_only_and_scopes_owner(self):
        uid = cloud_history_save("postgresql://example", "sub-A", "Proyek A", "modul-01", {"identitas": {}}, "Uji")
        self.assertIsInstance(UUID(uid), UUID)
        query, args = self.queries[-1]
        self.assertIn("INSERT INTO ie_toolkit_history", query)
        self.assertEqual(args[1:4], ("sub-A", "Proyek A", "modul-01"))
        self.assertNotIn("ON CONFLICT", query)

    def test_history_list_is_owner_scoped(self):
        rows = cloud_history_list("postgresql://example", "sub-A")
        self.assertEqual(rows[0]["name"], "Proyek A")
        query, params = self.queries[-1]
        self.assertIn("WHERE owner_sub = %s", query)
        self.assertEqual(params, ("sub-A", 30))

    def test_history_load_is_owner_scoped_and_validated(self):
        with patch("utils.workspace.restore_session_from_json") as restore:
            item = cloud_history_load("postgresql://example", "sub-B",
                                      "640dbd49-9774-4c2a-beb0-77d2faf5a143")
            restore.assert_called_once_with({}, item)
        query, params = self.queries[-1]
        self.assertIn("WHERE owner_sub = %s AND id = %s", query)
        self.assertEqual(params[0], "sub-B")

    def test_history_rejects_anonymous_and_bad_inputs(self):
        with self.assertRaises(ValueError):
            cloud_history_save("postgresql://example", "", "A", "all", {}, "x")
        with self.assertRaises(ValueError):
            cloud_history_save("postgresql://example", "sub-A", "A", "modul-99", {}, "x")
        with self.assertRaises(ValueError):
            cloud_history_list("postgresql://example", "sub-A", limit=1000)
        with self.assertRaises(ValueError):
            cloud_history_load("postgresql://example", "sub-A", "not-a-uuid")


if __name__ == "__main__":
    unittest.main()
