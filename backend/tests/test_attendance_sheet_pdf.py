from dataclasses import replace
from datetime import date
from io import BytesIO
from pathlib import Path

from PIL import Image
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.units import mm

from app.services.attendance_sheet_pdf import (
    AttendanceSheetEvent,
    AttendanceSheetRow,
    _attendance_table,
    _logos_cell,
    _styles,
    render_attendance_sheet_pdf,
)


LOGO_PATH = Path("app/assets/dict-logo.png")


def make_event() -> AttendanceSheetEvent:
    return AttendanceSheetEvent(
        office_name="DICT Regional Office No. V - Bicol",
        event_title="Digital Inclusion Orientation",
        venue="DICT Regional Office",
        event_date=date(2026, 8, 15),
    )


def make_row(number: int = 1) -> AttendanceSheetRow:
    return AttendanceSheetRow(
        row_number=number,
        attendee_name="Maria Santos Reyes",
        affiliation="Municipality of San Fernando",
        designation_category="Government Official",
        sex="F",
        email="maria.reyes@example.com",
        consent_documentation_publication=False,
        consent_database_processing=True,
        signature_text="Maria Santos Reyes",
        signature_image_path=None,
    )


def render(rows: list[AttendanceSheetRow]) -> bytes:
    return render_attendance_sheet_pdf(
        make_event(),
        rows,
        logo_path=LOGO_PATH,
    )


def extract_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def count_page_images(page) -> int:
    resources = page["/Resources"].get_object()
    xobjects = resources.get("/XObject", {}).get_object()
    return sum(
        1
        for reference in xobjects.values()
        if reference.get_object().get("/Subtype") == "/Image"
    )


def test_renderer_generates_landscape_pdf_with_event_and_attendee_text():
    pdf_bytes = render_attendance_sheet_pdf(
        make_event(),
        [make_row()],
        logo_path=LOGO_PATH,
    )

    reader = PdfReader(BytesIO(pdf_bytes))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    assert pdf_bytes.startswith(b"%PDF-")
    assert len(reader.pages) == 1
    assert float(reader.pages[0].mediabox.width) > float(
        reader.pages[0].mediabox.height
    )
    assert "Digital Inclusion Orientation" in text
    assert "Maria Santos Reyes" in text
    assert "Municipality of San Fernando" in text


def test_renderer_generates_one_page_for_zero_valid_records():
    pdf_bytes = render_attendance_sheet_pdf(
        make_event(),
        [],
        logo_path=LOGO_PATH,
    )

    reader = PdfReader(BytesIO(pdf_bytes))
    text = reader.pages[0].extract_text() or ""

    assert pdf_bytes.startswith(b"%PDF-")
    assert len(reader.pages) == 1
    assert [line.strip() for line in text.splitlines()].count("X") == 0


def test_renderer_keeps_the_attendance_table_close_to_its_title():
    page = PdfReader(BytesIO(render([make_row()]))).pages[0]
    text_positions: dict[str, float] = {}

    def capture_position(text, canvas_matrix, _text_matrix, _font, _size):
        normalized = text.strip()
        if normalized in {"ATTENDANCE SHEET", "NAME"}:
            text_positions[normalized] = canvas_matrix[5]

    page.extract_text(visitor_text=capture_position)

    vertical_distance = text_positions["ATTENDANCE SHEET"] - text_positions["NAME"]
    assert vertical_distance < 12 * 2.83465


def test_renderer_uses_compact_logo_and_table_visuals(tmp_path):
    program_logo_path = tmp_path / "program-logo.png"
    Image.new("RGB", (400, 200), "blue").save(program_logo_path)

    logos = _logos_cell(LOGO_PATH, program_logo_path, _styles())
    table = _attendance_table([make_row()], _styles(), 800)
    table_header_color = table._bkgrndcmds[0][-1]
    grid_command = table._linecmds[0]

    assert logos._argW == [37 * mm, 33 * mm]
    assert table_header_color == colors.HexColor("#E9F2F8")
    assert grid_command[3] == 0.35
    assert grid_command[4] == colors.HexColor("#4B5563")


def test_renderer_paginates_27_standard_rows_and_repeats_complete_header():
    rows = [make_row(number=index) for index in range(1, 28)]

    reader = PdfReader(BytesIO(render(rows)))
    second_page_text = reader.pages[1].extract_text() or ""

    assert len(reader.pages) == 2
    assert "Digital Inclusion Orientation" in second_page_text
    assert "Privacy Notice" in second_page_text
    assert "27" in second_page_text


def test_renderer_wraps_long_values_without_losing_text():
    row = replace(
        make_row(),
        affiliation="A very long government agency and local office name",
    )

    text = extract_text(render([row]))
    normalized_text = " ".join(text.split())

    assert (
        "A very long government agency and local office name"
        in normalized_text
    )


def test_renderer_leaves_missing_optional_values_blank():
    row = replace(
        make_row(),
        affiliation=None,
        designation_category=None,
        sex=None,
        signature_text=None,
    )

    text = extract_text(render([row]))
    normalized_lines = [line.strip() for line in text.splitlines()]

    assert "None" not in text
    # Vector check mark ang gamit; wala nang ambiguous na X text.
    assert normalized_lines.count("X") == 0


def test_renderer_embeds_valid_png_signature(tmp_path):
    signature_path = tmp_path / "signature.png"
    Image.new("RGBA", (240, 80), "white").save(signature_path)
    row = replace(make_row(), signature_image_path=signature_path)

    reader = PdfReader(BytesIO(render([row])))

    # Isang image ang DICT logo; pangalawa ang attendee signature.
    assert count_page_images(reader.pages[0]) >= 2


def test_renderer_flattens_signature_alpha_channel(tmp_path):
    signature_path = tmp_path / "transparent-signature.png"
    Image.new("RGBA", (240, 80), (255, 255, 255, 255)).save(signature_path)
    row = replace(make_row(), signature_image_path=signature_path)

    page = PdfReader(BytesIO(render([row]))).pages[0]
    xobjects = page["/Resources"]["/XObject"].get_object()
    image_objects = [
        reference.get_object()
        for reference in xobjects.values()
        if reference.get_object().get("/Subtype") == "/Image"
    ]

    assert all(image.get("/SMask") is None for image in image_objects)


def test_renderer_uses_typed_signature_when_image_is_missing(tmp_path):
    row = replace(
        make_row(),
        signature_image_path=tmp_path / "missing.png",
        signature_text="Typed Signature Fallback",
    )

    assert "Typed Signature Fallback" in extract_text(render([row]))
