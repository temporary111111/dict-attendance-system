from __future__ import annotations

from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "source"


def cell(root: Element, **attrs) -> Element:
    return SubElement(root, "mxCell", {key: str(value) for key, value in attrs.items()})


def geometry(parent: Element, **attrs) -> None:
    SubElement(parent, "mxGeometry", {key: str(value) for key, value in attrs.items()})


BASE_NODE = (
    "whiteSpace=wrap;html=1;strokeColor=#81B1DB;fillColor=#1f2020;"
    "fontColor=#d4d4d4;fontStyle=0;fontSize=14;spacing=8;"
)
PROCESS = "ellipse;" + BASE_NODE
EXTERNAL = "rounded=0;" + BASE_NODE
NOTE = (
    "rounded=0;whiteSpace=wrap;html=1;strokeColor=#8CA6DB;fillColor=#1f2020;"
    "fontColor=#d4d4d4;fontSize=13;spacing=8;dashed=1;"
)
STORE = (
    "shape=cylinder;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;"
    "strokeColor=#81B1DB;fillColor=#1f2020;fontColor=#d4d4d4;fontSize=14;spacing=8;"
)
EDGE = (
    "edgeStyle=orthogonalEdgeStyle;rounded=1;curved=1;html=1;endArrow=block;"
    "strokeColor=#d0d0d0;fontColor=#d4d4d4;fontSize=12;"
    "labelBackgroundColor=#1f2020;strokeWidth=2;"
)


def add_node(root: Element, node_id: str, value: str, x: int, y: int, w: int, h: int, style: str) -> None:
    node = cell(root, id=node_id, value=value, style=style, vertex="1", parent="1")
    geometry(node, x=x, y=y, width=w, height=h, **{"as": "geometry"})


def add_edge(root: Element, edge_id: str, source: str, target: str, label: str = "") -> None:
    edge = cell(root, id=edge_id, value=label, style=EDGE, edge="1", parent="1", source=source, target=target)
    geometry(edge, relative="1", **{"as": "geometry"})


def write_drawio(path: Path, name: str, width: int, height: int, nodes: list[tuple], edges: list[tuple]) -> None:
    mxfile = Element("mxfile", host="app.diagrams.net")
    diagram = SubElement(mxfile, "diagram", name=name)
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
        value=name,
        style="text;html=1;strokeColor=none;fillColor=none;fontColor=#f8fafc;fontStyle=1;fontSize=24;",
        vertex="1",
        parent="1",
    )
    geometry(title, x=0, y=20, width=width, height=40, **{"as": "geometry"})

    for node in nodes:
        add_node(root, *node)
    for index, edge in enumerate(edges, start=1):
        add_edge(root, f"e{index}", *edge)

    ElementTree(mxfile).write(path, encoding="utf-8", xml_declaration=True)


def main() -> None:
    SOURCE_DIR.mkdir(exist_ok=True)

    write_drawio(
        SOURCE_DIR / "dfd-level-0.drawio",
        "DFD Level 0 - Context Diagram",
        1900,
        760,
        [
            ("super_admin", "Super Admin", 110, 365, 130, 40, EXTERNAL),
            ("system", "Program and Event Attendance Monitoring and Reporting System", 760, 115, 510, 510, PROCESS),
            ("program_admin", "Program Admin", 1710, 325, 150, 45, EXTERNAL),
            ("attendee", "External Attendee", 1710, 455, 160, 45, EXTERNAL),
            ("note_template", "Note: Generated attendance sheet follows the fixed DICT-provided format.", 720, 650, 590, 55, NOTE),
        ],
        [
            ("super_admin", "system", "Login credentials; program/user/event/report requests"),
            ("system", "super_admin", "Dashboard; records; QR/link; attendance sheets; audit logs"),
            ("program_admin", "system", "Login credentials; event/status/report requests for assigned program"),
            ("system", "program_admin", "Assigned program dashboard; event tools; QR/link; records; sheets/reports"),
            ("attendee", "system", "Fixed attendance details and consent responses"),
            ("system", "attendee", "Public attendance page; validation; confirmation"),
            ("system", "program_admin", "Attendance sheet for assigned program events, if permitted"),
            ("system", "super_admin", "Generated attendance sheet"),
        ],
    )

    write_drawio(
        SOURCE_DIR / "dfd-level-1.drawio",
        "DFD Level 1 - Main System Processes",
        2300,
        1500,
        [
            ("super_admin", "Super Admin", 40, 600, 125, 40, EXTERNAL),
            ("program_admin", "Program Admin", 1030, 710, 130, 40, EXTERNAL),
            ("attendee", "External Attendee", 430, 1220, 160, 40, EXTERNAL),
            ("note_template", "Note: Attendance Sheet Generation follows fixed DICT template layout.", 965, 900, 380, 60, NOTE),
            ("p1", "1.0 Authenticate Admin User", 1660, 70, 185, 185, PROCESS),
            ("p2", "2.0 Manage Users, Programs, and Assignments", 1600, 315, 280, 280, PROCESS),
            ("p3", "3.0 Manage Events", 1680, 720, 170, 170, PROCESS),
            ("p4", "4.0 Generate Attendance Link and QR Code", 390, 685, 285, 285, PROCESS),
            ("p5", "5.0 Collect Attendance Submission", 1025, 1240, 220, 220, PROCESS),
            ("p6", "6.0 Validate and Store Attendance Records", 1665, 1165, 260, 260, PROCESS),
            ("p7", "7.0 Generate Dashboard, Reports, and Attendance Sheets", 1660, 920, 330, 330, PROCESS),
            ("p8", "8.0 Manage Audit Trail", 450, 510, 180, 180, PROCESS),
            ("d1", "D1 Users", 2100, 70, 145, 65, STORE),
            ("d2", "D2 Roles and Program Assignments", 2030, 240, 245, 80, STORE),
            ("d3", "D3 Programs", 2110, 880, 145, 65, STORE),
            ("d4", "D4 Events", 2110, 1260, 145, 65, STORE),
            ("d5", "D5 Attendance Records", 2070, 1355, 220, 75, STORE),
            ("d6", "D6 Attendance Sheet Exports", 2060, 1450, 235, 75, STORE),
            ("d7", "D7 Audit Logs", 2095, 450, 165, 70, STORE),
        ],
        [
            ("super_admin", "p1", "Login credentials"),
            ("program_admin", "p1", "Login credentials"),
            ("p1", "d1", ""),
            ("p1", "d2", ""),
            ("super_admin", "p2", "User, program, assignment requests"),
            ("p2", "d1", ""),
            ("p2", "d2", ""),
            ("p2", "d3", ""),
            ("super_admin", "p3", "Event details/status changes"),
            ("program_admin", "p3", "Create/update events under assigned program"),
            ("p3", "d2", ""),
            ("p3", "d3", ""),
            ("p3", "d4", ""),
            ("super_admin", "p4", "QR/link request"),
            ("program_admin", "p4", "QR/link request for program event"),
            ("p4", "d4", ""),
            ("p4", "super_admin", "Public attendance link and QR code"),
            ("p4", "program_admin", "Public attendance link and QR code for created event"),
            ("attendee", "p5", "Open link and submit attendance"),
            ("p5", "d4", ""),
            ("p5", "p6", "Submitted attendance data"),
            ("p6", "d4", ""),
            ("p6", "d5", ""),
            ("p6", "attendee", "Validation result and confirmation"),
            ("super_admin", "p7", "Dashboard/report/sheet request"),
            ("program_admin", "p7", "Report/sheet request for assigned program"),
            ("p7", "d2", ""),
            ("p7", "d3", ""),
            ("p7", "d4", ""),
            ("p7", "d5", ""),
            ("p7", "d6", ""),
            ("p7", "super_admin", "Dashboard, reports, attendance sheets"),
            ("p7", "program_admin", "Reports and sheets for assigned program, if permitted"),
            ("super_admin", "p8", "Audit log request"),
            ("p8", "d7", ""),
            ("p8", "super_admin", "Audit logs"),
            ("p1", "d7", ""),
            ("p2", "d7", ""),
            ("p3", "d7", ""),
            ("p4", "d7", ""),
            ("p6", "d7", ""),
            ("p7", "d7", ""),
        ],
    )

    write_drawio(
        SOURCE_DIR / "dfd-level-2.drawio",
        "DFD Level 2 - Attendance Submission and Sheet Generation",
        2500,
        1120,
        [
            ("note_template", "Note: Formatting uses fixed DICT attendance sheet layout.", 760, 40, 390, 60, NOTE),
            ("admin", "Super Admin / Program Admin", 30, 250, 170, 40, EXTERNAL),
            ("attendee", "External Attendee", 30, 750, 150, 40, EXTERNAL),
            ("p71", "7.1 Select Event for Attendance Sheet", 430, 245, 230, 230, PROCESS),
            ("p72", "7.2 Retrieve Attendance Records", 825, 185, 215, 215, PROCESS),
            ("p73", "7.3 Format Records Using DICT Template", 1220, 110, 250, 250, PROCESS),
            ("p74", "7.4 Generate Downloadable File", 1670, 70, 230, 230, PROCESS),
            ("p75", "7.5 Record Audit Log", 1960, 65, 160, 160, PROCESS),
            ("p51", "5.1 Open Public Attendance Link", 425, 870, 205, 205, PROCESS),
            ("p52", "5.2 Display Fixed Attendance Page", 785, 730, 230, 230, PROCESS),
            ("p53", "5.3 Submit Attendance Details", 425, 610, 200, 200, PROCESS),
            ("p61", "6.1 Validate Event Status", 790, 600, 170, 170, PROCESS),
            ("p62", "6.2 Validate Required Fields", 1220, 760, 180, 180, PROCESS),
            ("p63", "6.3 Validate Contact Information", 1630, 795, 205, 205, PROCESS),
            ("p64", "6.4 Check Duplicate Within Same Event", 1900, 785, 235, 235, PROCESS),
            ("p65", "6.5 Store Attendance Record", 2190, 635, 190, 190, PROCESS),
            ("p66", "6.6 Show Submission Result", 2310, 390, 220, 220, PROCESS),
            ("d2", "D2 Roles and Program Assignments", 770, 450, 240, 80, STORE),
            ("d4", "D4 Events", 1290, 640, 110, 60, STORE),
            ("d5", "D5 Attendance Records", 2310, 780, 180, 70, STORE),
            ("d6", "D6 Attendance Sheet Exports", 2140, 210, 240, 75, STORE),
            ("d7", "D7 Audit Logs", 2190, 60, 160, 70, STORE),
        ],
        [
            ("attendee", "p51", "Scans QR or opens public link"),
            ("p51", "p52", "Valid open event"),
            ("p52", "attendee", "Fixed attendance page"),
            ("attendee", "p53", "Submitted fixed attendance details"),
            ("p53", "p61", ""),
            ("p61", "d4", ""),
            ("p61", "p62", ""),
            ("p62", "p63", ""),
            ("p63", "p64", ""),
            ("p64", "p65", ""),
            ("p64", "d5", ""),
            ("p65", "d5", ""),
            ("p65", "p66", ""),
            ("p66", "attendee", "Confirmation or validation message"),
            ("admin", "p71", "Select event and request attendance sheet"),
            ("p71", "d2", ""),
            ("p71", "d4", ""),
            ("p71", "p72", ""),
            ("p72", "d4", ""),
            ("p72", "d5", ""),
            ("p72", "p73", ""),
            ("p73", "p74", ""),
            ("p74", "admin", "Downloadable attendance sheet"),
            ("p74", "d6", ""),
            ("p74", "p75", ""),
            ("p75", "d7", ""),
        ],
    )

    print("Wrote Mermaid-style Draw.io files:")
    print(SOURCE_DIR / "dfd-level-0.drawio")
    print(SOURCE_DIR / "dfd-level-1.drawio")
    print(SOURCE_DIR / "dfd-level-2.drawio")


if __name__ == "__main__":
    main()
