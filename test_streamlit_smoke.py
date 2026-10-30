"""Smoke test alur UI utama; dilewati jika Streamlit belum terinstal."""

import importlib.util
import unittest
from pathlib import Path


@unittest.skipUnless(importlib.util.find_spec("streamlit"), "Streamlit belum terinstal")
class StreamlitSmokeTests(unittest.TestCase):
    def test_scenario_input_navigation_and_report_page(self):
        from streamlit.testing.v1 import AppTest

        app_path = str(Path(__file__).with_name("app.py"))
        app = AppTest.from_file(app_path, default_timeout=45).run()
        self.assertFalse(app.exception)

        app.button(key="nav_btn_2").click().run()
        app.selectbox(key="_ui_selected_modul").set_value(
            "Modul 09 - Manual Material Handling (NIOSH, Snook & L5/S1)"
        ).run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.tabs), 4)
        self.assertEqual(app.session_state["modul_09_simulasi"]["h_cm"], 25.0)

        app.number_input(key="_ui_sim_h_cm").set_value(40.0).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["modul_09_simulasi"]["h_cm"], 40.0)
        self.assertEqual(app.session_state["modul_09"]["h_cm"], 32.0)

        app.button(key="nav_btn_4").click().run()
        self.assertFalse(app.exception)


if __name__ == "__main__":
    unittest.main()
