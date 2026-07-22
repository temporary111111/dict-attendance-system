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

    def test_admin_has_persistent_theme_and_collapsible_navigation(self) -> None:
        admin_html = (FRONTEND_ROOT / "admin.html").read_text(encoding="utf-8")
        admin_css = (FRONTEND_ROOT / "css" / "admin.css").read_text(encoding="utf-8")
        admin_js = (FRONTEND_ROOT / "js" / "admin.js").read_text(encoding="utf-8")
        theme_js = (FRONTEND_ROOT / "js" / "theme.js").read_text(encoding="utf-8")

        self.assertIn('id="theme-toggle"', admin_html)
        self.assertIn('class="nav-group-label"', admin_html)
        self.assertIn("sidebar-collapsed", admin_css)
        self.assertIn("dict-attendance-sidebar-collapsed", admin_js)
        self.assertIn("prefers-color-scheme: dark", theme_js)
        self.assertIn("dict-attendance-theme", theme_js)

    def test_dark_theme_defines_shared_surface_tokens(self) -> None:
        base_css = (FRONTEND_ROOT / "css" / "base.css").read_text(encoding="utf-8")

        self.assertIn(':root[data-theme="dark"]', base_css)
        self.assertIn("--surface-raised:", base_css)
        self.assertIn("--focus-ring:", base_css)

    def test_icon_metric_layout_is_scoped_to_dashboard_cards(self) -> None:
        admin_css = (FRONTEND_ROOT / "css" / "admin.css").read_text(encoding="utf-8")
        admin_js = (FRONTEND_ROOT / "js" / "admin.js").read_text(encoding="utf-8")

        self.assertIn('class="summary-grid dashboard-summary-grid"', admin_js)
        self.assertIn(".dashboard-summary-grid .summary-card {", admin_css)
        self.assertIn("grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));", admin_css)
        self.assertIn(".summary-icon.material-symbols-outlined {", admin_css)

    def test_empty_state_message_does_not_replace_the_material_icon(self) -> None:
        admin_js = (FRONTEND_ROOT / "js" / "admin.js").read_text(encoding="utf-8")

        self.assertIn('<span class="empty-message"></span>', admin_js)
        self.assertIn('setText(".empty-message", message, container)', admin_js)


if __name__ == "__main__":
    unittest.main()
