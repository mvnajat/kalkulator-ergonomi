import unittest

from utils.table_editor import edit_table_rows, prepare_editor_scope


class FakeDataEditor:
    """Simulate Streamlit overlaying pending cell edits on its input table."""

    def __init__(self):
        self.edits = {}
        self.calls = []

    def __call__(self, source, *, key, **kwargs):
        self.calls.append((key, source.copy(deep=True)))
        result = source.copy(deep=True)
        for (row, column), value in self.edits.get(key, {}).items():
            result.at[row, column] = value
        return result


class TableEditorTests(unittest.TestCase):
    def setUp(self):
        self.state = {}
        self.render = FakeDataEditor()
        self.rows = [{"Kode": "EL-01", "S1": 4.2, "S2": 5.1}]

    def edit(self):
        self.rows = edit_table_rows(
            self.state, self.rows, "ed_m3", self.render,
            use_container_width=True, num_rows="dynamic",
        )

    def test_first_and_second_edits_persist_without_changing_editor_source(self):
        prepare_editor_scope(self.state, "Modul Praktikum:Modul 03")
        self.edit()
        key = self.render.calls[-1][0]

        # One committed cell edit is immediately reflected in module data.
        self.render.edits[key] = {(0, "S1"): 7.5}
        self.edit()
        self.assertEqual(self.rows[0]["S1"], 7.5)

        # Editing another cell does not revert the first change.
        self.render.edits[key][(0, "S2")] = 8.8
        self.edit()
        self.assertEqual(self.rows[0]["S1"], 7.5)
        self.assertEqual(self.rows[0]["S2"], 8.8)
        self.assertEqual({call[0] for call in self.render.calls}, {key})
        self.assertEqual(self.state["_table_editor_bases"]["ed_m3"].at[0, "S1"], 4.2)

    def test_revisiting_module_uses_latest_saved_values(self):
        prepare_editor_scope(self.state, "Modul Praktikum:Modul 03")
        self.edit()
        previous_key = self.render.calls[-1][0]
        self.render.edits[previous_key] = {(0, "S1"): 10.0}
        self.edit()

        prepare_editor_scope(self.state, "Beranda")
        prepare_editor_scope(self.state, "Modul Praktikum:Modul 03")
        self.edit()
        new_key, baseline = self.render.calls[-1]
        self.assertNotEqual(new_key, previous_key)
        self.assertEqual(baseline.at[0, "S1"], 10.0)
        self.assertEqual(self.rows[0]["S1"], 10.0)

    def test_dynamic_added_row_survives_module_change(self):
        prepare_editor_scope(self.state, "Modul Praktikum:Modul 05")
        self.edit()
        key = self.render.calls[-1][0]

        # Simulate a new row returned by a dynamic editor.
        def add_row(source, *, key, **kwargs):
            result = source.copy(deep=True)
            result.loc[len(result)] = ["EL-02", 3.1, 4.1]
            return result

        self.rows = edit_table_rows(self.state, self.rows, "ed_m3", add_row)
        self.assertEqual(len(self.rows), 2)
        self.assertEqual(self.state["_table_editor_bases"]["ed_m3"].shape[0], 1)

        prepare_editor_scope(self.state, "Identitas")
        prepare_editor_scope(self.state, "Modul Praktikum:Modul 05")
        self.edit()
        self.assertNotEqual(self.render.calls[-1][0], key)
        self.assertEqual(len(self.rows), 2)
        self.assertEqual(self.rows[1]["Kode"], "EL-02")


if __name__ == "__main__":
    unittest.main()
