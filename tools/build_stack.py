#!/usr/bin/env python3
"""Generate stack-light.svg and stack-dark.svg.

One SVG per theme with every logo embedded, so the profile never depends on an
external badge service at render time. Edit ROWS and re-run.

    python3 tools/build_stack.py

Logos come from devicon (MIT). Re-download them with tools/fetch_logos.sh.
"""

from __future__ import annotations

import base64
import hashlib
import pathlib
import re
import xml.dom.minidom

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOGOS = ROOT / "tools" / "logos"

# (row label, [(logo stem, chip label or None for a wordmark, ["tint"])])
#
# "tint" is for single-colour marks whose SVG carries no fill of its own — they
# default to black and vanish on the dark theme, so the root fill is set to the
# theme's foreground instead.
ROWS = [
    ("Backend", [
        ("dotnetcore-original", ".NET"),
        ("nodejs-original", "Node.js"),
        ("typescript-original", "TypeScript"),
    ]),
    ("Mobile", [
        ("react-original", "React Native"),
        ("expo-original", "Expo", "tint"),
    ]),
    ("Data", [
        ("microsoftsqlserver-plain", "SQL Server"),
        ("postgresql-original", "PostgreSQL"),
        ("mongodb-original", "MongoDB"),
        ("firebase-plain", "Firebase"),
        ("supabase-original", "Supabase"),
        ("redis-original", "Redis"),
        ("elasticsearch-original", "Elasticsearch"),
    ]),
    ("Cloud", [
        ("azure-original", "Azure"),
        ("amazonwebservices-plain-wordmark", None),
        ("cloudflare-original", "Cloudflare"),
        ("docker-original", "Docker"),
    ]),
]

LOGO_H, CHIP_H, PAD, GAP, ROW_GAP = 18, 32, 11, 8, 12
LABEL_X, CHIPS_X, CHAR_W, WIDTH = 96, 112, 6.55, 1200

THEMES = {
    "light": dict(bg="#ffffff", border="#d1d9e0", label="#59636e",
                  text="#1f2328", chip="#f6f8fa", chip_border="#d1d9e0"),
    "dark": dict(bg="#0d1117", border="#30363d", label="#9198a1",
                 text="#e6edf3", chip="#151b23", chip_border="#30363d"),
}

_cache: dict[str, tuple[str, float]] = {}


def logo(stem: str, tint: str | None = None) -> tuple[str, float]:
    """Base64 of the SVG, and its width/height aspect ratio."""
    key = f"{stem}|{tint or ''}"
    if key not in _cache:
        raw = (LOGOS / f"{stem}.svg").read_text()

        box = re.search(r'viewBox="([-\d.\s]+)"', raw)
        aspect = 1.0
        if box:
            parts = [float(v) for v in box.group(1).split()]
            aspect = parts[2] / parts[3]

        # fill is inherited, so setting it on the root recolours every path that
        # does not declare one of its own.
        if tint:
            raw = raw.replace("<svg ", f'<svg fill="{tint}" ', 1)

        _cache[key] = (base64.b64encode(raw.encode()).decode(), aspect)
    return _cache[key]


def chip_width(aspect: float, label: str | None) -> float:
    width = PAD + LOGO_H * aspect
    if label:
        width += 8 + len(label) * CHAR_W
    return width + PAD


def build(theme: dict[str, str]) -> str:
    height = len(ROWS) * CHIP_H + (len(ROWS) - 1) * ROW_GAP + 44
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height:.0f}" '
        f'viewBox="0 0 {WIDTH} {height:.0f}" role="img" aria-label="Technology stack">',
        f'<rect x="0.5" y="0.5" width="{WIDTH-1}" height="{height-1:.0f}" rx="12" '
        f'fill="{theme["bg"]}" stroke="{theme["border"]}"/>',
        '<g font-family="ui-sans-serif,-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
    ]

    y = 22
    for name, items in ROWS:
        centre = y + CHIP_H / 2
        out.append(
            f'<text x="{LABEL_X}" y="{centre+4:.1f}" text-anchor="end" font-size="12.5" '
            f'font-weight="600" fill="{theme["label"]}">{name}</text>')

        x = CHIPS_X
        for item in items:
            stem, label = item[0], item[1]
            tint = theme["text"] if len(item) > 2 and item[2] == "tint" else None
            b64, aspect = logo(stem, tint)
            logo_w = LOGO_H * aspect
            width = chip_width(aspect, label)

            out.append(
                f'<rect x="{x:.1f}" y="{y}" width="{width:.1f}" height="{CHIP_H}" rx="7" '
                f'fill="{theme["chip"]}" stroke="{theme["chip_border"]}"/>')
            out.append(
                f'<image x="{x+PAD:.1f}" y="{centre-LOGO_H/2:.1f}" width="{logo_w:.1f}" '
                f'height="{LOGO_H}" preserveAspectRatio="xMidYMid meet" '
                f'href="data:image/svg+xml;base64,{b64}"/>')
            if label:
                out.append(
                    f'<text x="{x+PAD+logo_w+8:.1f}" y="{centre+4:.1f}" font-size="12" '
                    f'fill="{theme["text"]}">{label}</text>')
            x += width + GAP

        y += CHIP_H + ROW_GAP

    return "\n".join(out + ["</g>", "</svg>", ""])


def stamp_readme() -> None:
    """Append a content hash to every local SVG the README references.

    GitHub and the browser both cache these by URL, so regenerating an image
    without changing its URL leaves visitors looking at the old one. The hash
    changes only when the file does.
    """
    readme = ROOT / "README.md"
    text = readme.read_text()

    for svg in sorted(ROOT.glob("*.svg")):
        digest = hashlib.md5(svg.read_bytes()).hexdigest()[:8]
        text = re.sub(
            rf'{re.escape(svg.name)}(\?v=[0-9a-f]+)?',
            f"{svg.name}?v={digest}",
            text,
        )

    readme.write_text(text)
    print("README.md stamped")


def main() -> int:
    for name, theme in THEMES.items():
        path = ROOT / f"stack-{name}.svg"
        path.write_text(build(theme))
        xml.dom.minidom.parse(str(path))
        print(f"{path.name}  {path.stat().st_size // 1024} KB")

    stamp_readme()

    for name, items in ROWS:
        end = CHIPS_X + sum(chip_width(logo(i[0])[1], i[1]) + GAP for i in items)
        flag = "ok" if end < WIDTH - 20 else "OVERFLOW"
        print(f"  {name:9} {end:5.0f}px / {WIDTH}  {flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
