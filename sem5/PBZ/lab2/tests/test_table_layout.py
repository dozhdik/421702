import unittest
from unittest.mock import Mock, patch

from ui.app import App


class TableLayoutTests(unittest.TestCase):
    def test_row_height_tracks_font_and_scaling(self):
        app = Mock()
        app.winfo_fpixels.return_value = 8
        style = Mock()
        style.lookup.side_effect = ["TkDefaultFont", "TkHeadingFont"]
        body_font = Mock()
        body_font.metrics.return_value = 28
        heading_font = Mock()
        with patch("ui.app.ttk.Style", return_value=style), patch(
            "ui.app.tkfont.Font", side_effect=[body_font, heading_font]
        ):
            App.configure_table_style(app)
        style.configure.assert_any_call(
            "Insurance.Treeview", font=body_font, rowheight=44
        )
        body_font.configure.assert_called_once_with(size=11, weight="normal")
        heading_font.configure.assert_called_once_with(size=10, weight="bold")

    def test_column_widths_are_bounded_and_keep_short_columns_compact(self):
        app = Mock()
        app.winfo_fpixels.return_value = 12
        app.table_font.measure.side_effect = lambda text: len(text) * 10
        app.heading_font.measure.side_effect = lambda text: len(text) * 10
        tree = Mock()
        App.configure_columns(app, tree, [("id", "ID"), ("name", "Полное название")],
                              [("123", "А" * 1000)])
        id_options = tree.column.call_args_list[0].kwargs
        name_options = tree.column.call_args_list[1].kwargs
        self.assertLess(id_options["width"], name_options["width"])
        self.assertLessEqual(name_options["width"], 320)
        self.assertFalse(id_options["stretch"])
        self.assertTrue(name_options["stretch"])
        self.assertGreaterEqual(name_options["width"], name_options["minwidth"])


if __name__ == "__main__":
    unittest.main()
