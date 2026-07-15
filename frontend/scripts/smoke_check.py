"""No-dependency checks para sa local static frontend files."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

FRONTEND_ROOT = Path(__file__).resolve().parents[1]


class LocalReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.references: list[str] = []
        self.inline_handlers: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        if attributes.get("id"):
            self.ids.append(attributes["id"])
        for attribute in ("src", "href"):
            value = attributes.get(attribute)
            if value:
                self.references.append(value)
        self.inline_handlers.extend(
            name for name, _ in attrs if name.lower().startswith("on")
        )


def local_path(source: Path, reference: str) -> Path | None:
    parsed = urlparse(reference)
    if parsed.scheme or reference.startswith(("#", "data:")):
        return None
    return (source.parent / parsed.path).resolve()


def check_html(path: Path) -> list[str]:
    parser = LocalReferenceParser()
    parser.feed(path.read_text(encoding="utf-8"))
    errors = []

    duplicate_ids = sorted({value for value in parser.ids if parser.ids.count(value) > 1})
    if duplicate_ids:
        errors.append(f"{path.name}: duplicate IDs: {', '.join(duplicate_ids)}")
    if parser.inline_handlers:
        errors.append(f"{path.name}: inline event handlers are not allowed")

    for reference in parser.references:
        target = local_path(path, reference)
        if target is not None and not target.exists():
            errors.append(f"{path.name}: missing local reference {reference}")
    return errors


def check_js_imports() -> list[str]:
    errors = []
    import_pattern = re.compile(r'from\s+["\'](.+?)["\']')
    for source in (FRONTEND_ROOT / "js").glob("*.js"):
        content = source.read_text(encoding="utf-8")
        for reference in import_pattern.findall(content):
            if not reference.startswith("."):
                continue
            target = (source.parent / reference).resolve()
            if not target.exists():
                errors.append(f"{source.name}: missing module {reference}")
    return errors


def check_config() -> list[str]:
    content = (FRONTEND_ROOT / "js" / "config.js").read_text(encoding="utf-8")
    match = re.search(r'apiBaseUrl:\s*["\'](.+?)["\']', content)
    if not match:
        return ["config.js: apiBaseUrl is missing"]
    parsed = urlparse(match.group(1))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ["config.js: apiBaseUrl must be an absolute HTTP(S) URL"]
    return []


def main() -> None:
    errors = []
    for html_path in (
        FRONTEND_ROOT / "index.html",
        FRONTEND_ROOT / "admin.html",
        FRONTEND_ROOT / "attendance.html",
    ):
        errors.extend(check_html(html_path))
    errors.extend(check_js_imports())
    errors.extend(check_config())

    if errors:
        raise SystemExit("Frontend smoke check failed:\n- " + "\n- ".join(errors))
    print("Frontend smoke check passed.")


if __name__ == "__main__":
    main()
