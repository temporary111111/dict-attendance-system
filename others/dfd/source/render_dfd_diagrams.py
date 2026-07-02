from __future__ import annotations

import html
import math
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree

ROOT = Path(__file__).resolve().parents[1]


def wrap(text: str, chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if len(candidate) <= chars:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def svg_text(x: float, y: float, text: str, width: float, size: int = 14, weight: str = "400"):
    lines = wrap(text, max(10, int(width / (size * 0.55))))
    line_height = size * 1.25
    start_y = y - ((len(lines) - 1) * line_height / 2)
    parts = [
        f'<text x="{x:.1f}" y="{start_y:.1f}" text-anchor="middle" '
        f'font-family="Arial, sans-serif" font-size="{size}" font-weight="{weight}" fill="#172033">'
    ]
    for idx, line in enumerate(lines):
        dy = 0 if idx == 0 else line_height
        parts.append(f'<tspan x="{x:.1f}" dy="{dy:.1f}">{esc(line)}</tspan>')
    parts.append("</text>")
    return "".join(parts)


def draw_node(node: dict) -> str:
    x, y, w, h = node["x"], node["y"], node["w"], node["h"]
    kind = node.get("kind", "process")
    label = node["label"]
    fill = {
        "external": "#e7f0ff",
        "process": "#e9f7ef",
        "store": "#fff5d6",
        "note": "#f8fafc",
    }[kind]
    stroke = {
        "external": "#4068a8",
        "process": "#2d7d54",
        "store": "#a06b00",
        "note": "#6c4ba8",
    }[kind]
    if kind == "process":
        body = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    elif kind == "store":
        body = (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
            f'<line x1="{x + 18}" y1="{y}" x2="{x + 18}" y2="{y + h}" stroke="{stroke}" stroke-width="2"/>'
        )
    elif kind == "note":
        body = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="2" stroke-dasharray="7 5"/>'
    else:
        body = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    return body + svg_text(x + w / 2, y + h / 2, label, w - 20, size=node.get("size", 14), weight=node.get("weight", "600"))


def center(node: dict) -> tuple[float, float]:
    return node["x"] + node["w"] / 2, node["y"] + node["h"] / 2


def boundary_point(src: dict, dst: dict) -> tuple[float, float]:
    sx, sy = center(src)
    dx, dy = center(dst)
    vx, vy = dx - sx, dy - sy
    if vx == 0 and vy == 0:
        return sx, sy
    scale_x = (src["w"] / 2) / abs(vx) if vx else math.inf
    scale_y = (src["h"] / 2) / abs(vy) if vy else math.inf
    scale = min(scale_x, scale_y) * 0.96
    return sx + vx * scale, sy + vy * scale


def draw_edge(nodes: dict[str, dict], edge: tuple[str, str, str]) -> str:
    a, b, label = edge
    src, dst = nodes[a], nodes[b]
    x1, y1 = boundary_point(src, dst)
    x2, y2 = boundary_point(dst, src)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    line = (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        'stroke="#52606d" stroke-width="1.8" marker-end="url(#arrow)"/>'
    )
    if not label:
        return line
    label_lines = wrap(label, 28)
    box_h = 16 + len(label_lines) * 13
    box_w = min(250, max(90, max(len(line_text) for line_text in label_lines) * 7 + 18))
    box = (
        f'<rect x="{mx - box_w/2:.1f}" y="{my - box_h/2:.1f}" width="{box_w:.1f}" height="{box_h:.1f}" '
        'rx="4" fill="#ffffff" stroke="#d5dbe3" stroke-width="1"/>'
    )
    text = svg_text(mx, my + 4, label, box_w - 12, size=11, weight="400")
    return line + box + text


def render_svg(diagram: dict, out: Path) -> None:
    width, height = diagram["size"]
    nodes = diagram["nodes"]
    edge_svg = "\n".join(draw_edge(nodes, edge) for edge in diagram["edges"])
    node_svg = "\n".join(draw_node(node) for node in nodes.values())
    title = svg_text(width / 2, 32, diagram["title"], width - 80, size=20, weight="700")
    legend = (
        '<rect x="28" y="36" width="16" height="12" fill="#e7f0ff" stroke="#4068a8"/>'
        '<text x="50" y="47" font-family="Arial, sans-serif" font-size="11">External entity</text>'
        '<rect x="150" y="36" width="16" height="12" rx="4" fill="#e9f7ef" stroke="#2d7d54"/>'
        '<text x="172" y="47" font-family="Arial, sans-serif" font-size="11">Process</text>'
        '<rect x="230" y="36" width="16" height="12" fill="#fff5d6" stroke="#a06b00"/>'
        '<text x="252" y="47" font-family="Arial, sans-serif" font-size="11">Data store</text>'
    )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="#52606d"/>
  </marker>
</defs>
<rect width="100%" height="100%" fill="#fbfcfe"/>
{title}
{legend}
{edge_svg}
{node_svg}
</svg>
'''
    out.write_text(svg, encoding="utf-8")


def render_png(svg_path: Path, png_path: Path) -> None:
    try:
        import fitz
    except ImportError as exc:
        raise SystemExit("PNG rendering requires PyMuPDF: python -m pip install pymupdf") from exc
    doc = fitz.open(svg_path)
    page = doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    pix.save(png_path)


def node(x, y, w, h, label, kind="process", **extra):
    data = {"x": x, "y": y, "w": w, "h": h, "label": label, "kind": kind}
    data.update(extra)
    return data


DIAGRAMS = {
    "level-0": {
        "title": "DFD Level 0 - Context Diagram",
        "size": (1500, 820),
        "nodes": {
            "super": node(70, 150, 230, 90, "Super Admin", "external"),
            "program": node(70, 520, 230, 90, "Program Admin", "external"),
            "attendee": node(1190, 150, 230, 90, "External Attendee", "external"),
            "note_template": node(1065, 535, 360, 90, "Note: Generated attendance sheet follows the fixed DICT-provided format.", "note", weight="400"),
            "system": node(560, 310, 390, 150, "Program and Event Attendance Monitoring and Reporting System", "process", size=16),
        },
        "edges": [
            ("super", "system", "Admin requests and system outputs"),
            ("program", "system", "Assigned-scope requests and outputs"),
            ("attendee", "system", "Attendance submission and confirmation"),
        ],
    },
    "level-1": {
        "title": "DFD Level 1 - Main System Processes",
        "size": (1900, 1240),
        "nodes": {
            "super": node(60, 120, 210, 70, "Super Admin", "external"),
            "program": node(60, 330, 210, 70, "Program Admin", "external"),
            "attendee": node(60, 660, 210, 70, "External Attendee", "external"),
            "note_template": node(50, 900, 230, 100, "Note: Attendance Sheet Generation follows fixed DICT template layout.", "note", weight="400"),
            "p1": node(390, 90, 250, 85, "1.0 Authenticate Admin User"),
            "p2": node(390, 235, 270, 95, "2.0 Manage Users, Programs, and Assignments"),
            "p3": node(390, 395, 250, 85, "3.0 Manage Events"),
            "p4": node(390, 545, 250, 90, "4.0 Generate Attendance Link and QR Code"),
            "p5": node(390, 690, 250, 90, "5.0 Collect Attendance Submission"),
            "p6": node(760, 690, 270, 95, "6.0 Validate and Store Attendance Records"),
            "p7": node(760, 900, 305, 105, "7.0 Generate Dashboard, Reports, and Attendance Sheets"),
            "p8": node(760, 1080, 260, 85, "8.0 Manage Audit Trail"),
            "d1": node(1250, 100, 230, 60, "D1 Users", "store"),
            "d2": node(1250, 230, 270, 70, "D2 Roles and Program Assignments", "store"),
            "d3": node(1250, 380, 230, 60, "D3 Programs", "store"),
            "d4": node(1250, 535, 230, 60, "D4 Events", "store"),
            "d5": node(1250, 700, 255, 65, "D5 Attendance Records", "store"),
            "d6": node(1250, 910, 275, 70, "D6 Attendance Sheet Exports", "store"),
            "d7": node(1250, 1090, 230, 60, "D7 Audit Logs", "store"),
        },
        "edges": [
            ("super", "p1", "Login"),
            ("program", "p1", "Login"),
            ("p1", "d1", "Users"),
            ("p1", "d2", "Roles/scope"),
            ("super", "p2", ""),
            ("p2", "d1", ""),
            ("p2", "d2", ""),
            ("p2", "d3", ""),
            ("super", "p3", ""),
            ("program", "p3", ""),
            ("p3", "d3", ""),
            ("p3", "d4", ""),
            ("super", "p4", ""),
            ("program", "p4", ""),
            ("p4", "d4", ""),
            ("p4", "program", "Public link/QR"),
            ("attendee", "p5", "Open link and submit"),
            ("p5", "d4", "Event status"),
            ("p5", "p6", "Submission"),
            ("p6", "d5", "Attendance record"),
            ("p6", "attendee", "Confirmation"),
            ("super", "p7", ""),
            ("program", "p7", ""),
            ("p7", "d2", ""),
            ("p7", "d3", ""),
            ("p7", "d4", ""),
            ("p7", "d5", ""),
            ("p7", "d6", "Export record"),
            ("p7", "super", "Reports/sheets"),
            ("p7", "program", "Reports/sheets"),
            ("p1", "p8", ""),
            ("p2", "p8", ""),
            ("p3", "p8", ""),
            ("p4", "p8", ""),
            ("p6", "p8", ""),
            ("p7", "p8", ""),
            ("p8", "d7", "Audit logs"),
            ("super", "p8", "Audit log request"),
            ("p8", "super", "Audit view"),
        ],
    },
    "level-2": {
        "title": "DFD Level 2 - Attendance Submission and Sheet Generation",
        "size": (2400, 1120),
        "nodes": {
            "attendee": node(50, 220, 210, 70, "External Attendee", "external"),
            "admin": node(50, 760, 230, 75, "Super Admin / Program Admin", "external"),
            "note_template": node(45, 935, 250, 95, "Note: Formatting uses fixed DICT attendance sheet layout.", "note", weight="400"),
            "p51": node(340, 130, 235, 80, "5.1 Open Public Attendance Link"),
            "p52": node(620, 130, 235, 80, "5.2 Display Fixed Attendance Page"),
            "p53": node(900, 130, 235, 80, "5.3 Submit Attendance Details"),
            "p61": node(1180, 130, 235, 80, "6.1 Validate Event Status"),
            "p62": node(1460, 130, 235, 80, "6.2 Validate Required Fields"),
            "p63": node(1740, 130, 235, 80, "6.3 Validate Contact Information"),
            "p64": node(1460, 330, 255, 85, "6.4 Check Duplicate Within Same Event"),
            "p65": node(1740, 330, 245, 85, "6.5 Store Attendance Record"),
            "p66": node(2020, 330, 230, 80, "6.6 Show Submission Result"),
            "p71": node(340, 740, 245, 85, "7.1 Select Event for Attendance Sheet"),
            "p72": node(680, 740, 245, 85, "7.2 Retrieve Attendance Records"),
            "p73": node(1020, 740, 270, 90, "7.3 Format Records Using DICT Template"),
            "p74": node(1365, 740, 245, 85, "7.4 Generate Downloadable File"),
            "p75": node(1710, 740, 245, 85, "7.5 Record Audit Log"),
            "d2": node(680, 930, 270, 70, "D2 Roles and Program Assignments", "store"),
            "d4": node(2030, 120, 230, 60, "D4 Events", "store"),
            "d5": node(2030, 520, 250, 65, "D5 Attendance Records", "store"),
            "d6": node(2030, 735, 270, 70, "D6 Attendance Sheet Exports", "store"),
            "d7": node(2030, 900, 230, 60, "D7 Audit Logs", "store"),
        },
        "edges": [
            ("attendee", "p51", "Scan QR/open link"),
            ("p51", "p52", ""),
            ("p52", "attendee", "Fixed attendance page"),
            ("attendee", "p53", ""),
            ("p53", "p61", ""),
            ("p61", "p62", ""),
            ("p62", "p63", ""),
            ("p63", "p64", ""),
            ("p64", "p65", ""),
            ("p65", "p66", ""),
            ("p66", "attendee", "Confirmation"),
            ("p51", "d4", ""),
            ("p61", "d4", ""),
            ("p64", "d5", "Duplicate check"),
            ("p65", "d5", "Save record"),
            ("admin", "p71", ""),
            ("p71", "p72", ""),
            ("p72", "p73", ""),
            ("p73", "p74", ""),
            ("p74", "admin", "Download"),
            ("p74", "p75", ""),
            ("p71", "d2", "RBAC scope"),
            ("p72", "d4", "Event details"),
            ("p72", "d5", "Attendance records"),
            ("p74", "d6", "Export metadata"),
            ("p75", "d7", "Audit log"),
        ],
    },
}


def add_drawio_cell(root: Element, cell_id: str, value: str, style: str, x: int, y: int, w: int, h: int) -> None:
    cell = SubElement(root, "mxCell", id=cell_id, value=value, style=style, vertex="1", parent="1")
    SubElement(cell, "mxGeometry", {"x": str(x), "y": str(y), "width": str(w), "height": str(h), "as": "geometry"})


def add_drawio_edge(root: Element, edge_id: str, source: str, target: str, label: str) -> None:
    style = "endArrow=block;html=1;rounded=0;strokeColor=#52606d;fontSize=11;edgeStyle=orthogonalEdgeStyle;"
    edge = SubElement(root, "mxCell", id=edge_id, value=label, style=style, edge="1", parent="1", source=source, target=target)
    SubElement(edge, "mxGeometry", {"relative": "1", "as": "geometry"})


def render_drawio(diagram: dict, out: Path) -> None:
    mxfile = Element("mxfile", host="app.diagrams.net")
    diagram_el = SubElement(mxfile, "diagram", name=diagram["title"])
    model = SubElement(
        diagram_el,
        "mxGraphModel",
        dx="1600",
        dy="900",
        grid="1",
        gridSize="10",
        guides="1",
        tooltips="1",
        connect="1",
        arrows="1",
        fold="1",
        page="1",
        pageScale="1",
        pageWidth=str(diagram["size"][0]),
        pageHeight=str(diagram["size"][1]),
        math="0",
        shadow="0",
    )
    root = SubElement(model, "root")
    SubElement(root, "mxCell", id="0")
    SubElement(root, "mxCell", id="1", parent="0")
    styles = {
        "external": "rounded=1;whiteSpace=wrap;html=1;fillColor=#e7f0ff;strokeColor=#4068a8;fontStyle=1;",
        "process": "rounded=1;whiteSpace=wrap;html=1;fillColor=#e9f7ef;strokeColor=#2d7d54;fontStyle=1;",
        "store": "rounded=1;whiteSpace=wrap;html=1;fillColor=#fff5d6;strokeColor=#a06b00;fontStyle=1;",
        "note": "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#6c4ba8;dashed=1;",
    }
    for cell_id, data in diagram["nodes"].items():
        add_drawio_cell(root, cell_id, esc(data["label"]), styles[data.get("kind", "process")], data["x"], data["y"], data["w"], data["h"])
    for idx, (source, target, label) in enumerate(diagram["edges"], 1):
        add_drawio_edge(root, f"e{idx}", source, target, esc(label))
    ElementTree(mxfile).write(out, encoding="utf-8", xml_declaration=True)


def main() -> None:
    source_dir = ROOT / "source"
    source_dir.mkdir(exist_ok=True)
    for key, diagram in DIAGRAMS.items():
        out_dir = ROOT / key
        out_dir.mkdir(exist_ok=True)
        base = f"dfd-{key}-updated"
        svg_path = out_dir / f"{base}.svg"
        png_path = out_dir / f"{base}.png"
        drawio_path = source_dir / f"dfd-{key}.drawio"
        render_svg(diagram, svg_path)
        render_png(svg_path, png_path)
        render_drawio(diagram, drawio_path)
        print(f"Wrote {svg_path.relative_to(ROOT)}")
        print(f"Wrote {png_path.relative_to(ROOT)}")
        print(f"Wrote {drawio_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
