"""Pure PDF renderer para sa fixed DICT attendance-sheet layout."""

from dataclasses import dataclass
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Literal
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as ReportLabImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PRIVACY_NOTICE = (
    "The DICT collects your personal data in these physical forms to provide "
    "verifiable evidence and documentation that you participated in this "
    "event, as well as for monitoring and evaluation purposes. Your "
    "information will be stored in our database (or other repositories such "
    "as secured records locker for physical forms, among others) for 3 years "
    "before being permanently erased from our records.<br/><br/>"
    "We will also be taking photos as well as video and audio recordings "
    "throughout the event for documentation and may be used in official DICT "
    "publications if needed. Should you wish to withdraw your consent, please "
    "contact the respective organizers."
)


class AttendanceSheetPDFError(Exception):
    """Raised kapag hindi mabuo ang attendance-sheet PDF."""


@dataclass(frozen=True)
class AttendanceSheetEvent:
    office_name: str
    event_title: str
    venue: str
    event_date: date
    root_office_name: str | None = None


@dataclass(frozen=True)
class AttendanceSheetRow:
    row_number: int
    attendee_name: str
    affiliation: str | None
    designation_category: str | None
    sex: Literal["F", "M"] | None
    email: str
    consent_documentation_publication: bool
    consent_database_processing: bool
    signature_text: str | None
    signature_image_path: Path | None


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()["Normal"]
    return {
        "small": ParagraphStyle(
            "AttendanceSmall",
            parent=base,
            fontName="Helvetica",
            fontSize=5.5,
            leading=6.5,
            alignment=TA_LEFT,
        ),
        "small_center": ParagraphStyle(
            "AttendanceSmallCenter",
            parent=base,
            fontName="Helvetica",
            fontSize=5.5,
            leading=6.5,
            alignment=TA_CENTER,
        ),
        "header": ParagraphStyle(
            "AttendanceHeader",
            parent=base,
            fontName="Helvetica-Bold",
            fontSize=6,
            leading=7,
            alignment=TA_CENTER,
        ),
        "event": ParagraphStyle(
            "AttendanceEvent",
            parent=base,
            fontName="Helvetica",
            fontSize=8,
            leading=9,
            alignment=TA_CENTER,
        ),
        "notice": ParagraphStyle(
            "AttendanceNotice",
            parent=base,
            fontName="Helvetica",
            fontSize=5.5,
            leading=7,
            alignment=TA_LEFT,
        ),
    }


def _text(value: object, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape("" if value is None else str(value)), style)


def _event_date(value: date) -> str:
    return f"{value.strftime('%B')} {value.day}, {value.year}"


def _logos_cell(
    dict_logo_path: Path,
    program_logo_path: Path | None,
    styles: dict[str, ParagraphStyle],
) -> object:
    """Dalawang logo side-by-side kung may program logo; DICT logo lang kung wala."""
    if program_logo_path is None or not program_logo_path.is_file():
        return ReportLabImage(str(dict_logo_path), width=42 * mm, height=21.42 * mm)

    # Each logo gets roughly half the column (column is ~0.35 of total width).
    # Target height: 18mm to fit comfortably in the 26mm row span.
    dict_img = ReportLabImage(str(dict_logo_path), width=40 * mm, height=20.4 * mm)

    try:
        with PILImage.open(program_logo_path) as src:
            pw, ph = src.size
        # Scale program logo to fit max 40mm wide × 20mm tall.
        scale = min((40 * mm) / pw, (20 * mm) / ph)
        prog_img = ReportLabImage(
            str(program_logo_path),
            width=pw * scale,
            height=ph * scale,
        )
    except (OSError, ValueError):
        # Fallback: mostra lang ang DICT logo kung may issue sa program logo file.
        return ReportLabImage(str(dict_logo_path), width=42 * mm, height=21.42 * mm)

    logos_table = Table(
        [[dict_img, prog_img]],
        colWidths=[42 * mm, 42 * mm],
    )
    logos_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )
    return logos_table


def _header_story(
    event: AttendanceSheetEvent,
    logo_path: Path,
    styles: dict[str, ParagraphStyle],
    width: float,
    *,
    program_logo_path: Path | None = None,
) -> list[object]:
    logos_cell = _logos_cell(logo_path, program_logo_path, styles)
    office_lines = ""
    if event.root_office_name:
        office_lines = f"{escape(event.root_office_name)}<br/>{escape(event.office_name)}"
    else:
        office_lines = escape(event.office_name)
    event_value = Paragraph(
        f"{office_lines}<br/>"
        f"<b>{escape(event.event_title)}</b>",
        styles["event"],
    )
    # Kapag may program logo, dagdag ang column width para magkasya ang dalawang logo.
    logo_col_width = (0.40 if program_logo_path else 0.35) * width
    event_col_width = width - logo_col_width - 0.11 * width - 0.07 * width
    header = Table(
        [
            [
                logos_cell,
                _text("TITLE OF EVENT/SEMINAR/MEETING:", styles["header"]),
                _text("VENUE:", styles["header"]),
                _text("DATE:", styles["header"]),
            ],
            [
                "",
                event_value,
                _text(event.venue, styles["small_center"]),
                _text(_event_date(event.event_date), styles["small_center"]),
            ],
        ],
        colWidths=[logo_col_width, event_col_width, 0.11 * width, 0.07 * width],
        rowHeights=[8 * mm, 18 * mm],
    )
    header.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (0, 1)),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#333333")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )
    notice = Table(
        [
            [_text("Privacy Notice", styles["header"])],
            [Paragraph(PRIVACY_NOTICE, styles["notice"])],
        ],
        colWidths=[width],
    )
    notice.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#333333")),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return [
        header,
        notice,
        _text("ATTENDANCE SHEET", styles["header"]),
        Spacer(1, 1),
    ]


def _attendance_table(
    rows: list[AttendanceSheetRow],
    styles: dict[str, ParagraphStyle],
    width: float,
) -> Table:
    header = [
        "#",
        "NAME",
        "AFFILIATION",
        "DESIGNATION/CATEGORY",
        "F",
        "M",
        "EMAIL ADDRESS",
        "CONSENT: DOCUMENTATION/PUBLICATION",
        "CONSENT: DATABASE PROCESSING",
        "SIGNATURE",
    ]
    data: list[list[object]] = [
        [_text(value, styles["header"]) for value in header]
    ]
    if not rows:
        data.append([_text(1, styles["small_center"])] + [""] * 9)

    for row in rows:
        data.append(
            [
                _text(row.row_number, styles["small_center"]),
                _text(row.attendee_name, styles["small"]),
                _text(row.affiliation, styles["small"]),
                _text(row.designation_category, styles["small"]),
                _check_mark(row.sex == "F", styles["small_center"]),
                _check_mark(row.sex == "M", styles["small_center"]),
                _text(row.email, styles["small"]),
                _check_mark(
                    row.consent_documentation_publication,
                    styles["small_center"],
                ),
                _check_mark(
                    row.consent_database_processing,
                    styles["small_center"],
                ),
                _signature_cell(row, styles),
            ]
        )
    table = Table(
        data,
        colWidths=[
            0.025 * width,
            0.145 * width,
            0.15 * width,
            0.14 * width,
            0.025 * width,
            0.025 * width,
            0.145 * width,
            0.13 * width,
            0.12 * width,
            0.095 * width,
        ],
        repeatRows=1,
    )
    table_commands = [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#333333")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 1.5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1.5),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]
    table.setStyle(TableStyle(table_commands))
    return table


def _check_mark(selected: bool, style: ParagraphStyle) -> object:
    return _text("✓" if selected else "", style)


def _signature_cell(
    row: AttendanceSheetRow,
    styles: dict[str, ParagraphStyle],
) -> object:
    path = row.signature_image_path
    if path is not None and path.is_file():
        try:
            with PILImage.open(path) as source_image:
                source_image.load()
                rgba_image = source_image.convert("RGBA")
                normalized_image = PILImage.new("RGB", rgba_image.size, "white")
                normalized_image.paste(rgba_image, mask=rgba_image.getchannel("A"))
                width, height = normalized_image.size
                image_buffer = BytesIO()
                normalized_image.save(image_buffer, format="PNG")
                image_buffer.seek(0)
            scale = min((22 * mm) / width, (6 * mm) / height)
            return ReportLabImage(
                image_buffer,
                width=width * scale,
                height=height * scale,
            )
        except (OSError, ValueError):
            pass
    return _text(row.signature_text or "", styles["small_center"])


def _draw_page_header(
    canvas,
    document,
    event: AttendanceSheetEvent,
    logo_path: Path,
    styles: dict[str, ParagraphStyle],
    *,
    program_logo_path: Path | None = None,
) -> None:
    """Inuulit ang event context sa bawat printed page."""
    canvas.saveState()
    y_position = landscape(A4)[1] - 7 * mm
    for flowable in _header_story(
        event,
        logo_path,
        styles,
        document.width,
        program_logo_path=program_logo_path,
    ):
        _, height = flowable.wrap(document.width, document.topMargin)
        y_position -= height
        flowable.drawOn(canvas, document.leftMargin, y_position)
    canvas.restoreState()


def render_attendance_sheet_pdf(
    event: AttendanceSheetEvent,
    rows: list[AttendanceSheetRow],
    *,
    logo_path: Path,
    program_logo_path: Path | None = None,
) -> bytes:
    """Gumagawa ng in-memory PDF; walang database o file write dito."""
    try:
        output = BytesIO()
        document = SimpleDocTemplate(
            output,
            pagesize=landscape(A4),
            leftMargin=8 * mm,
            rightMargin=8 * mm,
            topMargin=54 * mm,
            bottomMargin=7 * mm,
            title=f"Attendance Sheet - {event.event_title}",
            author="Department of Information and Communications Technology",
        )
        styles = _styles()
        chunks = [rows[index : index + 26] for index in range(0, len(rows), 26)]
        if not chunks:
            chunks = [[]]
        story: list[object] = []
        for index, chunk in enumerate(chunks):
            story.append(_attendance_table(chunk, styles, document.width))
            if index < len(chunks) - 1:
                story.append(PageBreak())

        def draw_header(canvas, current_document) -> None:
            _draw_page_header(
                canvas,
                current_document,
                event,
                logo_path,
                styles,
                program_logo_path=program_logo_path,
            )

        document.build(
            story,
            onFirstPage=draw_header,
            onLaterPages=draw_header,
        )
        return output.getvalue()
    except Exception as exc:
        raise AttendanceSheetPDFError from exc
