import json
import unittest

from utils.exporter import (
    SESSION_BACKUP_FIELDS,
    export_session_to_json,
    restore_session_from_json,
)


class BackupTests(unittest.TestCase):
    def test_all_modules_including_09_survive_round_trip(self):
        original = {
            state_key: {"value": f"{state_key} contoh"}
            for _, state_key in SESSION_BACKUP_FIELDS
        }
        original["modul_09"] = {
            "coupling": "Baik (Good)",
            "snook_aktivitas": "Tarik (Pulling)",
            "snook_jk": "Perempuan",
            "snook_persentil": "P50",
            "berat_beban": 20.0,
        }
        original["modul_09_simulasi"] = {
            "h_cm": 25.0, "v_cm": 75.0, "berat_beban": 12.0,
        }

        backup = json.loads(export_session_to_json(original))
        self.assertEqual(backup["modul_09_mmh"], original["modul_09"])
        self.assertEqual(backup["modul_09_simulasi"], original["modul_09_simulasi"])

        restored = {}
        restore_session_from_json(restored, backup)
        self.assertEqual(restored, original)

    def test_old_backup_without_module_09_preserves_existing_value(self):
        restored = {"modul_09": {"berat_beban": 16.0}}
        restore_session_from_json(restored, {"identitas": {"kelas": "A"}})
        self.assertEqual(restored["identitas"]["kelas"], "A")
        self.assertEqual(restored["modul_09"]["berat_beban"], 16.0)

    def test_invalid_backup_never_partially_overwrites_session(self):
        original = {"identitas": {"kelas": "lama"}, "modul_09": {"berat_beban": 16.0}}
        backup = {"identitas": {"kelas": "baru"}, "modul_09_mmh": "bukan objek"}

        with self.assertRaises(ValueError):
            restore_session_from_json(original, backup)
        self.assertEqual(original["identitas"]["kelas"], "lama")
        self.assertEqual(original["modul_09"]["berat_beban"], 16.0)


if __name__ == "__main__":
    unittest.main()
