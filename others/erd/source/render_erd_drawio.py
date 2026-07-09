from __future__ import annotations

from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree, SubElement

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "source"

TABLE_STYLE = (
    "rounded=0;whiteSpace=wrap;html=1;strokeColor=#81B1DB;fillColor=#1f2020;"
    "fontColor=#d4d4d4;fontSize=12;spacing=8;align=left;verticalAlign=top;"
)
EDGE_STYLE = (
    "edgeStyle=orthogonalEdgeStyle;rounded=1;curved=1;html=1;endArrow=block;"
    "strokeColor=#d0d0d0;fontColor=#d4d4d4;fontSize=11;"
    "labelBackgroundColor=#1f2020;strokeWidth=2;"
)


def cell(root: Element, **attrs) -> Element:
    return SubElement(root, "mxCell", {key: str(value) for key, value in attrs.items()})


def geometry(parent: Element, **attrs) -> None:
    SubElement(parent, "mxGeometry", {key: str(value) for key, value in attrs.items()})


def html_table(name: str, fields: list[str]) -> str:
    lines = [f"<b>{name}</b>", "<hr>"]
    lines.extend(fields)
    return "<br>".join(lines)


def add_table(root: Element, table_id: str, name: str, fields: list[str], x: int, y: int, w: int, h: int) -> None:
    node = cell(root, id=table_id, value=html_table(name, fields), style=TABLE_STYLE, vertex="1", parent="1")
    geometry(node, x=x, y=y, width=w, height=h, **{"as": "geometry"})


def add_edge(root: Element, edge_id: str, source: str, target: str, label: str) -> None:
    edge = cell(root, id=edge_id, value=label, style=EDGE_STYLE, edge="1", parent="1", source=source, target=target)
    geometry(edge, relative="1", **{"as": "geometry"})


def main() -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    out = SOURCE_DIR / "attendance-system-erd.drawio"
    width, height = 2350, 1300

    mxfile = Element("mxfile", host="app.diagrams.net")
    diagram = SubElement(mxfile, "diagram", name="Normalized MySQL ERD - Attendance System")
    model = SubElement(
        diagram,
        "mxGraphModel",
        dx=str(width),
        dy=str(height),
        grid="1",
        gridSize="10",
        guides="1",
        tooltips="1",
        connect="1",
        arrows="1",
        fold="1",
        page="1",
        pageScale="1",
        pageWidth=str(width),
        pageHeight=str(height),
        background="#000000",
        math="0",
        shadow="0",
    )
    root = SubElement(model, "root")
    cell(root, id="0")
    cell(root, id="1", parent="0")

    bg = cell(
        root,
        id="background",
        value="",
        style="rounded=0;whiteSpace=wrap;html=1;fillColor=#000000;strokeColor=none;locked=1;",
        vertex="1",
        parent="1",
    )
    geometry(bg, x=0, y=0, width=width, height=height, **{"as": "geometry"})

    title = cell(
        root,
        id="title",
        value="Normalized MySQL ERD - Attendance System",
        style="text;html=1;strokeColor=none;fillColor=none;fontColor=#f8fafc;fontStyle=1;fontSize=24;",
        vertex="1",
        parent="1",
    )
    geometry(title, x=0, y=20, width=width, height=40, **{"as": "geometry"})

    tables = [
        (
            "roles",
            "roles",
            ["role_id PK", "role_name UK", "description", "is_active", "created_at", "updated_at"],
            40,
            245,
            225,
            165,
        ),
        (
            "users",
            "users",
            ["user_id PK", "role_id FK", "org_unit_id FK nullable", "full_name", "email UK", "password_hash", "account_status", "created_at", "updated_at"],
            330,
            220,
            250,
            235,
        ),
        (
            "org_units",
            "organizational_units",
            ["org_unit_id PK", "parent_unit_id FK nullable", "unit_name", "unit_type", "unit_code UK nullable", "is_active", "created_at", "updated_at"],
            40,
            475,
            255,
            225,
        ),
        (
            "assignments",
            "program_admin_assignments",
            ["assignment_id PK", "program_id FK", "user_id FK", "assigned_by_user_id FK", "assignment_status", "assigned_at", "revoked_at"],
            645,
            70,
            285,
            205,
        ),
        (
            "programs",
            "programs",
            ["program_id PK", "owning_unit_id FK", "created_by_user_id FK", "program_name", "description", "program_status", "created_at", "updated_at"],
            645,
            355,
            285,
            225,
        ),
        (
            "events",
            "events",
            ["event_id PK", "program_id FK", "created_by_user_id FK", "event_title", "venue", "event_date", "event_code UK", "public_attendance_url", "qr_code_path", "event_status"],
            1000,
            300,
            285,
            265,
        ),
        (
            "attendance",
            "attendance_records",
            ["attendance_id PK", "event_id FK", "first/middle/last/suffix", "school_university", "designation_category", "sex", "email", "consent fields", "signature fields", "attendance_status"],
            1345,
            60,
            270,
            265,
        ),
        (
            "address",
            "attendance_record_addresses",
            ["address_id PK", "attendance_id FK", "region_code FK", "province_code FK nullable", "city_municipality_code FK", "barangay_code FK", "street_address", "postal_code"],
            1660,
            80,
            300,
            245,
        ),
        (
            "exports",
            "attendance_sheet_exports",
            ["export_id PK", "event_id FK", "exported_by_user_id FK", "export_format", "file_path", "total_records", "exported_at"],
            1345,
            465,
            270,
            200,
        ),
        (
            "audit",
            "audit_logs",
            ["audit_log_id PK", "user_id FK nullable", "action", "entity_type", "entity_id", "description", "old_values_json", "new_values_json", "created_at"],
            1000,
            690,
            285,
            235,
        ),
        (
            "psgc_regions",
            "psgc_regions",
            ["region_code PK", "region_name", "is_active", "created_at", "updated_at"],
            2020,
            65,
            270,
            150,
        ),
        (
            "psgc_provinces",
            "psgc_provinces",
            ["province_code PK", "region_code FK", "province_name", "is_active", "created_at", "updated_at"],
            2020,
            275,
            270,
            170,
        ),
        (
            "psgc_cities",
            "psgc_cities_municipalities",
            ["city_municipality_code PK", "region_code FK", "province_code FK nullable", "city_municipality_name", "city_municipality_type", "is_active"],
            2020,
            505,
            270,
            190,
        ),
        (
            "psgc_barangays",
            "psgc_barangays",
            ["barangay_code PK", "city_municipality_code FK", "barangay_name", "is_active", "created_at", "updated_at"],
            2020,
            755,
            270,
            170,
        ),
    ]

    for table in tables:
        add_table(root, *table)

    edges = [
        ("roles", "users", "1:M"),
        ("org_units", "org_units", "parent"),
        ("org_units", "users", "assigned"),
        ("org_units", "programs", "owns"),
        ("users", "programs", "creates"),
        ("users", "assignments", "assigned/admin/by"),
        ("programs", "assignments", "1:M"),
        ("programs", "events", "1:M"),
        ("users", "events", "creates"),
        ("events", "attendance", "1:M"),
        ("attendance", "address", "0..1"),
        ("events", "exports", "1:M"),
        ("users", "exports", "generates"),
        ("users", "audit", "performs"),
        ("psgc_regions", "psgc_provinces", "1:M"),
        ("psgc_regions", "psgc_cities", "1:M"),
        ("psgc_provinces", "psgc_cities", "1:M"),
        ("psgc_cities", "psgc_barangays", "1:M"),
        ("psgc_regions", "address", "region"),
        ("psgc_provinces", "address", "province"),
        ("psgc_cities", "address", "city/municipality"),
        ("psgc_barangays", "address", "barangay"),
    ]
    for index, edge in enumerate(edges, start=1):
        add_edge(root, f"e{index}", *edge)

    ElementTree(mxfile).write(out, encoding="utf-8", xml_declaration=True)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
