"""Smoke test alur UI utama; dilewati jika Streamlit belum terinstal."""

import importlib.util
import unittest
from pathlib import Path


@unittest.skipUnless(importlib.util.find_spec("streamlit"), "Streamlit belum terinstal")
class StreamlitSmokeTests(unittest.TestCase):
    def test_every_module_page_opens_without_exception(self):
        from streamlit.testing.v1 import AppTest

        for nomor in ("01", "02", "03", "04", "05", "09"):
            with self.subTest(modul=nomor):
                app = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=45).run()
                app.button(key=f"open_Modul {nomor}").click().run()
                self.assertFalse(app.exception)
                self.assertEqual(app.session_state["_active_page_slug"], f"modul-{nomor}")

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
        self.assertEqual(len(app.tabs), 4)
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


if __name__ == "__main__":
    unittest.main()
