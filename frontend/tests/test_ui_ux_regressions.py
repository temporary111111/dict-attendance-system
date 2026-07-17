"""Static regression checks para sa importanteng UI/UX safeguards."""

from pathlib import Path
import unittest


FRONTEND_ROOT = Path(__file__).resolve().parents[1]


class UiUxRegressionTests(unittest.TestCase):
    def test_forms_keep_controls_inside_narrow_viewports(self) -> None:
        base_css = (FRONTEND_ROOT / "css" / "base.css").read_text(encoding="utf-8")
        login_css = (FRONTEND_ROOT / "css" / "login.css").read_text(encoding="utf-8")

        self.assertIn(".field-group {\n  display: grid;\n  min-width: 0;", base_css)
        self.assertIn("@media (max-width: 480px)", login_css)

    def test_forms_and_loading_states_have_accessibility_safeguards(self) -> None:
        base_css = (FRONTEND_ROOT / "css" / "base.css").read_text(encoding="utf-8")
        login_html = (FRONTEND_ROOT / "index.html").read_text(encoding="utf-8")
        attendance_js = (FRONTEND_ROOT / "js" / "attendance.js").read_text(encoding="utf-8")
        admin_js = (FRONTEND_ROOT / "js" / "admin.js").read_text(encoding="utf-8")

        self.assertIn("button,\ninput,\nselect,\ntextarea", base_css)
        self.assertIn("prefers-reduced-motion: reduce", base_css)
        self.assertIn('aria-controls="password"', login_html)
        self.assertIn("focusFirstInvalidField", attendance_js)
        self.assertIn('role = "status"', admin_js)


if __name__ == "__main__":
    unittest.main()
