# DFD Notes

The DFDs have been updated for the current MVP direction:

* No Google Forms
* No Google Sheets
* No CSV import as the main attendance flow
* Fixed public attendance page inside the system
* Template-based downloadable attendance sheet/report

## Editable Sources

Use these when modifying the diagrams visually in draw.io / diagrams.net:

* `source/dfd-level-0.drawio`
* `source/dfd-level-1.drawio`
* `source/dfd-level-2.drawio`

These `.drawio` files have been styled to look close to the Mermaid dark-theme diagrams:

* black background
* dark process circles/ellipses
* blue outlines
* light curved arrows
* cylinder-like data stores

Open them in diagrams.net / draw.io for drag-and-drop editing.

Mermaid text versions are also available:

* `source/dfd-level-0.mmd`
* `source/dfd-level-1.mmd`
* `source/dfd-level-2.mmd`

Use Mermaid if you prefer text-based editing or want easier Git diffs.

## Generated Images

Current generated image outputs:

* `level-0/dfd-level-0-updated.png`
* `level-0/dfd-level-0-updated.svg`
* `level-1/dfd-level-1-updated.png`
* `level-1/dfd-level-1-updated.svg`
* `level-2/dfd-level-2-updated.png`
* `level-2/dfd-level-2-updated.svg`

Use PNG for reports/presentations. Use SVG for sharper viewing or vector editing.

## Regeneration

The Mermaid-style images can be regenerated from:

* `source/render_mermaid_diagrams.py`

Command:

```powershell
python others\dfd\source\render_mermaid_diagrams.py
```

This renderer uses Microsoft Edge headless to render Mermaid locally, then saves PNG/SVG outputs.

Python dependencies used by the renderer:

```powershell
python -m pip install websocket-client
```

The script downloads Mermaid JS into a temp cache, but the diagram content is rendered locally in Edge.

The Mermaid-style Draw.io files can be regenerated from:

* `source/render_mermaid_style_drawio.py`

Command:

```powershell
python others\dfd\source\render_mermaid_style_drawio.py
```

There is also an older fallback custom renderer:

* `source/render_dfd_diagrams.py`

Use it only if the Mermaid-style workflows are unavailable.

## Important

Older PNG names are kept for compatibility with previous docs, but they have been replaced with the updated diagrams. The clearest current outputs are still the `*-updated.png` and `*-updated.svg` files.
