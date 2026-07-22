"""Static regression checks para sa importanteng UI/UX safeguards."""

from pathlib import Path
import re
import unittest


FRONTEND_ROOT = Path(__file__).resolve().parents[1]


def get_css_properties(css: str, selector: str) -> dict[str, str]:
    """Kunin ang direct CSS variables ng isang simpleng selector block."""
    match = re.search(rf"{re.escape(selector)}\s*\{{([^}}]*)\}}", css, re.DOTALL)
    if not match:
        return {}

    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", match.group(1)))


def contrast_ratio(first_hex: str, second_hex: str) -> float:
    """I-compute ang WCAG contrast ratio ng dalawang hex colors."""
    def luminance(hex_color: str) -> float:
        channels = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return (0.2126 * linear[0]) + (0.7152 * linear[1]) + (0.0722 * linear[2])

    lighter, darker = sorted((luminance(first_hex), luminance(second_hex)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


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
        self.assertIn("dict-attendance-admin-theme", theme_js)

    def test_sidebar_navigation_uses_outlined_dict_style_icons(self) -> None:
        admin_html = (FRONTEND_ROOT / "admin.html").read_text(encoding="utf-8")
        admin_css = (FRONTEND_ROOT / "css" / "admin.css").read_text(encoding="utf-8")

        self.assertEqual(admin_html.count('<svg class="nav-symbol nav-symbol-bootstrap"'), 8)
        self.assertNotIn('nav-symbol material-symbols-outlined', admin_html)
        self.assertIn('viewBox="0 0 16 16"', admin_html)
        for icon_name in ("grid", "clipboard", "calendar-event", "bar-chart", "diagram-3", "person-gear", "map", "clock-history"):
            self.assertIn(f'data-icon="{icon_name}"', admin_html)
        self.assertIn('.nav-symbol {\n  width: 19px;\n  height: 19px;', admin_css)
        self.assertIn(".nav-item.active .nav-symbol", admin_css)
        self.assertIn(":root[data-theme=\"dark\"] .nav-item.active .nav-symbol", admin_css)

    def test_sidebar_brand_uses_icon_and_white_wordmark_text(self) -> None:
        admin_html = (FRONTEND_ROOT / "admin.html").read_text(encoding="utf-8")
        admin_css = (FRONTEND_ROOT / "css" / "admin.css").read_text(encoding="utf-8")

        self.assertIn('class="sidebar-brand-icon-logo" src="./assets/dict-icon.png"', admin_html)
        self.assertIn("<strong>DICT</strong><small>Attendance System</small>", admin_html)
        self.assertNotIn("sidebar-brand-header-logo", admin_html)
        self.assertIn(".sidebar-brand .sidebar-brand-icon-logo {", admin_css)
        self.assertIn('font-family: "Arial Narrow", "Aptos Narrow", Arial, sans-serif;', admin_css)
        self.assertIn("letter-spacing: 0.08em;", admin_css)
        self.assertIn(".sidebar-collapsed .sidebar-brand-icon-logo", admin_css)

    def test_admin_and_public_themes_use_separate_storage_keys(self) -> None:
        theme_js = (FRONTEND_ROOT / "js" / "theme.js").read_text(encoding="utf-8")
        admin_js = (FRONTEND_ROOT / "js" / "admin.js").read_text(encoding="utf-8")

        self.assertIn('admin: "dict-attendance-admin-theme"', theme_js)
        self.assertIn('public: "dict-attendance-public-theme"', theme_js)
        self.assertIn("initializeThemeToggle(button, storageKey)", theme_js)
        self.assertNotIn('const THEME_STORAGE_KEY = "dict-attendance-theme"', theme_js)
        self.assertIn(
            "initializeThemeToggle(themeToggle, THEME_STORAGE_KEYS.admin)",
            admin_js,
        )

    def test_login_uses_admin_theme_and_accessible_icon_controls(self) -> None:
        login_html = (FRONTEND_ROOT / "index.html").read_text(encoding="utf-8")
        login_js = (FRONTEND_ROOT / "js" / "login.js").read_text(encoding="utf-8")

        self.assertIn('<meta name="color-scheme" content="light dark" />', login_html)
        self.assertIn('id="login-theme-toggle"', login_html)
        self.assertIn('aria-label="Use dark theme"', login_html)
        self.assertIn('aria-label="Show password"', login_html)
        self.assertIn('class="material-symbols-outlined" aria-hidden="true">visibility</span>', login_html)
        self.assertIn('initializeThemeToggle(themeToggle, THEME_STORAGE_KEYS.admin)', login_js)

    def test_login_icon_controls_keep_symbol_fallbacks_inside_the_button(self) -> None:
        login_css = (FRONTEND_ROOT / "css" / "login.css").read_text(encoding="utf-8")

        self.assertIn(".login-theme-toggle,\n.password-toggle {", login_css)
        self.assertIn("  display: grid;", login_css)
        self.assertIn("  overflow: hidden;", login_css)

    def test_login_brand_restores_the_dict_header_background(self) -> None:
        login_css = (FRONTEND_ROOT / "css" / "login.css").read_text(encoding="utf-8")

        self.assertIn('background-image: url("../assets/dict-header.png");', login_css)
        self.assertIn("background-position: center;", login_css)
        self.assertIn("background-size: cover;", login_css)
        self.assertIn("background-blend-mode: multiply;", login_css)

    def test_public_attendance_has_an_isolated_accessible_theme_toggle(self) -> None:
        attendance_html = (FRONTEND_ROOT / "attendance.html").read_text(encoding="utf-8")
        attendance_js = (FRONTEND_ROOT / "js" / "attendance.js").read_text(encoding="utf-8")
        attendance_css = (FRONTEND_ROOT / "css" / "attendance.css").read_text(encoding="utf-8")

        self.assertIn('<meta name="color-scheme" content="light dark" />', attendance_html)
        self.assertIn('id="attendance-theme-toggle"', attendance_html)
        self.assertIn('aria-label="Use dark theme"', attendance_html)
        self.assertIn('initializeThemeToggle(themeToggle, THEME_STORAGE_KEYS.public)', attendance_js)
        self.assertIn(':root[data-theme="dark"] .attendance-header', attendance_css)

    def test_signature_pad_uses_the_active_theme_ink_color(self) -> None:
        attendance_js = (FRONTEND_ROOT / "js" / "attendance.js").read_text(encoding="utf-8")

        self.assertIn('getPropertyValue("--ink-900")', attendance_js)
        self.assertIn("context.strokeStyle = signatureInkColor();", attendance_js)
        self.assertIn("context.fillStyle = signatureInkColor();", attendance_js)

    def test_dark_theme_defines_shared_surface_tokens(self) -> None:
        base_css = (FRONTEND_ROOT / "css" / "base.css").read_text(encoding="utf-8")

        self.assertIn(':root[data-theme="dark"]', base_css)
        self.assertIn("--surface-raised:", base_css)
        self.assertIn("--focus-ring:", base_css)

    def test_primary_buttons_keep_accessible_contrast_in_both_themes(self) -> None:
        base_css = (FRONTEND_ROOT / "css" / "base.css").read_text(encoding="utf-8")

        for selector in (":root", ':root[data-theme="dark"]'):
            properties = get_css_properties(base_css, selector)
            self.assertIn("--primary-action", properties)
            self.assertIn("--primary-action-text", properties)
            self.assertGreaterEqual(
                contrast_ratio(
                    properties["--primary-action"].strip(),
                    properties["--primary-action-text"].strip(),
                ),
                4.5,
            )

        self.assertIn("background: var(--primary-action);", base_css)
        self.assertIn("color: var(--primary-action-text);", base_css)

    def test_admin_tables_stay_readable_inside_narrow_viewports(self) -> None:
        admin_css = (FRONTEND_ROOT / "css" / "admin.css").read_text(encoding="utf-8")

        self.assertIn(".data-table {\n  min-width: 680px;", admin_css)
        self.assertIn("#recent-events .data-table {\n  min-width: 0;", admin_css)

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
