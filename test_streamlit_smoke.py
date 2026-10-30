"""Smoke test alur UI utama; dilewati jika Streamlit belum terinstal."""

import importlib.util
import unittest
from pathlib import Path


@unittest.skipUnless(importlib.util.find_spec("streamlit"), "Streamlit belum terinstal")
class StreamlitSmokeTests(unittest.TestCase):
    def test_new_workspace_pages_render_without_exception(self):
        from streamlit.testing.v1 import AppTest

        pages = {
            "dashboard": "Dashboard Kemajuan",
            "proyek": "Proyek Praktikum",
            "impor-excel": "Impor Excel",
            "ruang-belajar": "Ruang Belajar",
        }
        for slug, page_title in pages.items():
            with self.subTest(page=slug):
                app = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=45).run()
                app.button(key=f"home_tool_{slug}").click().run()
                self.assertFalse(app.exception)
                self.assertEqual(app.session_state["_active_page_slug"], slug)
                self.assertEqual(app.session_state["nav_page"], page_title)

    def test_every_module_page_opens_without_exception(self):
        from streamlit.testing.v1 import AppTest

        for nomor in ("01", "02", "03", "04", "05", "06", "07", "08", "09"):
            with self.subTest(modul=nomor):
                app = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=45).run()
                app.button(key=f"open_Modul {nomor}").click().run()
                self.assertFalse(app.exception)
                self.assertEqual(app.session_state["_active_page_slug"], f"modul-{nomor}")
                self.assertEqual(app.selectbox(key=f"ux_mode_{nomor}").value, "Pemula")
                self.assertEqual(len(app.tabs), 8 if nomor == "09" else 6 if nomor == "02" else 4)
                self.assertTrue(any(b.key == f"module_report_modul-{nomor}" for b in app.button))
                self.assertTrue(any(c.key == f"done_modul-{nomor}" for c in app.checkbox))

    def test_beginner_home_guides_first_time_visitors(self):
        from streamlit.testing.v1 import AppTest

        app_path = str(Path(__file__).with_name("app.py"))
        app = AppTest.from_file(app_path, default_timeout=45).run()
        self.assertFalse(app.exception)
        self.assertTrue(any(b.key == "home_start" for b in app.button))
        self.assertTrue(any(b.key == "home_demo" for b in app.button))
        self.assertTrue(any(b.key == "home_dismiss_guide" for b in app.button))
        self.assertEqual(app.session_state["ux_mode"], "Pemula")
        app.button(key="home_dismiss_guide").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(app.session_state["ux_guide_dismissed"])
        # AppTest 1.40 mengekspos elemen sebelum st.rerun diproses;
        # render sekali lagi agar pohon elemen sesuai state akhir.
        app.run()
        self.assertFalse(any(b.key == "home_dismiss_guide" for b in app.button))

    def test_report_page_opens_from_home(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=45).run()
        app.button(key="nav_btn_4").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["_active_page_slug"], "laporan")

    def test_home_opens_separate_module_directory(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=45).run()
        app.button(key="home_all_modules").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["_active_page_slug"], "daftar-modul")
        self.assertEqual(len([x for x in app.button if x.key and x.key.startswith("open_Modul")]), 9)

    def test_scenario_input_navigation_and_report_page(self):
        from streamlit.testing.v1 import AppTest

        app_path = str(Path(__file__).with_name("app.py"))
        app = AppTest.from_file(app_path, default_timeout=45).run()
        self.assertFalse(app.exception)

        app.button(key="open_Modul 09").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["_active_page_slug"], "modul-09")
        self.assertEqual(len(app.tabs), 8)
        self.assertEqual(app.session_state["modul_09_simulasi"]["h_cm"], 25.0)
        self.assertEqual(app.session_state["modul_09"]["h_cm"], 32.0)
        self.assertTrue(any(button.key == "atas_back_list" for button in app.button))
        self.assertTrue(any(button.key == "bawah_prev" for button in app.button))

        # AppTest Streamlit 1.40 menyimpan widget lama dari beranda sesudah
        # switch_page; pengujian lintas halaman lanjutan dilakukan di browser.

    def test_modules_06_to_08_have_separate_pages_and_keep_observations(self):
        from streamlit.testing.v1 import AppTest

        for nomor in ("06", "07", "08"):
            with self.subTest(modul=nomor):
                app = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=45).run()
                if nomor == "06":
                    app.session_state["modul_06"]["dingin_suhu"][0] = 24.5
                app.button(key=f"open_Modul {nomor}").click().run()
                self.assertFalse(app.exception)
                self.assertEqual(app.session_state["_active_page_slug"], f"modul-{nomor}")
                controls = [x for x in app.number_input if x.key and x.key.startswith("ling_")]
                self.assertEqual(len(controls), 6)
                self.assertTrue(all(x.key.startswith(f"ling_{nomor}_") for x in controls))
                if nomor == "06":
                    self.assertEqual(app.session_state["modul_06"]["dingin_suhu"][0], 24.5)

    def test_phase1_pulse_inputs_and_method_selector_render(self):
        from streamlit.testing.v1 import AppTest

        app_path = str(Path(__file__).with_name("app.py"))
        app = AppTest.from_file(app_path, default_timeout=45).run()
        app.button(key="open_Modul 01").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len([w for w in app.number_input
                              if w.key and w.key.startswith("pulse_")]), 12)
        self.assertEqual(app.number_input(key="pulse_op1_P5").value, 75.0)

        fresh = AppTest.from_file(app_path, default_timeout=45).run()
        fresh.button(key="open_Modul 03").click().run()
        self.assertFalse(fresh.exception)
        methods = [item for item in fresh.selectbox if "Metode yang digunakan" in item.label]
        self.assertEqual(len(methods), 1)
        self.assertEqual(methods[0].value, "Westinghouse")
        self.assertIn("Objektif", methods[0].options)
        self.assertIn("Akhir (manual)", methods[0].options)
        # Streamlit AppTest 1.40 kembali ke beranda setelah navigasi
        # st.switch_page di rerun ke-2; interaksi pascanavigasi harus
        # diperiksa pada browser sesungguhnya, bukan dinilai gagal di sini.


if __name__ == "__main__":
    unittest.main()
