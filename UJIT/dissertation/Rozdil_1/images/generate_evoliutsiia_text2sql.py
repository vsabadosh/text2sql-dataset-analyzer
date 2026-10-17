"""Generate the editable Ukrainian SVG using explicit UTF-8 serialization."""

from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).with_name("evoliutsiia_text2sql.svg")
parts = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="780" '
    'viewBox="0 0 1500 780" role="img" aria-labelledby="title description">',
    '<title id="title">Еволюція підходів до природномовного доступу до БД і Text-to-SQL</title>',
    '<desc id="description">Авторська схема за першоджерелами. Чотири умовні етапи '
    'з перекриттям; нерівномірна часова шкала. LUNAR і NaLIX не генерували SQL. '
    'Крива є концептуальною, а не кількісною оцінкою якості. '
    'Дати позначають орієнтовне становлення підходів. Джерела та пояснення: '
    '../../Related_Work/ground_truth_rozdil_1.md</desc>',
    '<defs><style>'
    'text{font-family:"Times New Roman","Liberation Serif",serif;fill:#202b24}'
    '.title{font-size:30px;font-weight:bold}'
    '.period{font-size:24px;font-weight:bold}'
    '.heading{font-size:25px;font-weight:bold}'
    '.body{font-size:22px}.axis{font-size:28px}.small{font-size:20px}'
    '.note{font-size:19px;fill:#4e5b52}'
    '.label{font-size:18px;font-weight:bold;letter-spacing:1px;fill:#46515d}'
    '.system{font-size:23px;font-weight:bold}'
    '.flow{stroke:#637382;stroke-width:2;fill:none}'
    '</style><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" '
    'refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#637382"/>'
    '</marker></defs><rect width="1500" height="780" fill="white"/>',
]


def text(x, y, lines, cls="body", step=28, center=False):
    anchor = ' text-anchor="middle"' if center else ""
    spans = "".join(
        f'<tspan x="{x}" dy="{0 if i == 0 else step}">{escape(line)}</tspan>'
        for i, line in enumerate(lines)
    )
    parts.append(f'<text x="{x}" y="{y}" class="{cls}"{anchor}>{spans}</text>')


def rect(x, y, width, height, color, radius=8):
    parts.append(
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
        f'rx="{radius}" fill="{color}" stroke="#408458" stroke-width="2"/>'
    )


def path(d, arrow=False, dashed=False):
    extra = (' marker-end="url(#arrow)"' if arrow else "") + (
        ' stroke-dasharray="6 5"' if dashed else ""
    )
    parts.append(f'<path d="{d}" class="flow"{extra}/>')


text(750, 40, ["Еволюція підходів до природномовного доступу до БД і Text-to-SQL"], "title", center=True)

# An illustrative ribbon: its height is not an empirical capability metric.
parts.append(
    '<path d="M85,573 C290,323 730,220 1370,157 '
    'L1370,115 L1470,210 L1370,315 L1370,270 '
    'C790,282 333,362 85,573 Z" '
    'fill="#b8d9b5" stroke="#526d52" stroke-width="2.5"/>'
)
path("M85,660 H1470", arrow=True)
path("M85,660 V230", arrow=True)
parts.append(
    '<text transform="translate(46 445) rotate(-90)" '
    'text-anchor="middle" class="axis">Здатність розв’язувати задачі</text>'
)

# Arrows run from the ribbon up to the box and meet both. Boxes clear the bend.
RIBBON_TOP = ((85, 573), (290, 323), (730, 220), (1370, 157))
TAG_HALF = 142
TAG_H = 70
ARROW_HEAD = 13
BOX_CLEARANCE = 16
DOT_R = 23


def ribbon_top(x):
    p0, p1, p2, p3 = RIBBON_TOP
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        u = 1 - mid
        bx = (
            u**3 * p0[0]
            + 3 * u**2 * mid * p1[0]
            + 3 * u * mid**2 * p2[0]
            + mid**3 * p3[0]
        )
        if bx < x:
            lo = mid
        else:
            hi = mid
    t = (lo + hi) / 2
    u = 1 - t
    return (
        u**3 * p0[1]
        + 3 * u**2 * t * p1[1]
        + 3 * u * t**2 * p2[1]
        + t**3 * p3[1]
    )


def crest_under_box(x):
    return min(ribbon_top(x - TAG_HALF + i) for i in range(0, TAG_HALF * 2 + 1, 2))


def stage_layout(x, dot_y):
    """Tip meets the box outline and the base meets the dot or ribbon outline."""
    ribbon = ribbon_top(x)
    dot_top = dot_y - DOT_R
    box_bottom = round(crest_under_box(x) - BOX_CLEARANCE)
    # A dot that rises above the band is the surface; otherwise use the outer stroke.
    base = round(dot_top) if dot_top < ribbon else round(ribbon) - 1
    tip = box_bottom + 1
    return box_bottom - TAG_H, tip, base


# Each stage has a short method tag above and a category below the ribbon.
stages = [
    {
        "x": 265, "y": 436, "box_y": 555,
        "tag": ["Дерева розбору", "Граматичні правила"],
        "name": ["Методи", "на основі правил"],
        "date": ["Від 1970-х"],
        "examples": ["LUNAR · NaLIX · NaLIR"],
        "color": "#75b86b",
    },
    {
        "x": 570, "y": 321, "box_y": 410,
        "tag": ["LSTM-кодування", "Складові й шаблони SQL"],
        "name": ["Глибокі", "нейронні мережі"],
        "date": ["Від 2016 р."],
        "examples": ["Seq2SQL · SQLNet"],
        "color": "#4e9b50",
    },
    {
        "x": 890, "y": 253, "box_y": 344,
        "tag": ["BERT і T5", "Схема й обмежене декодування"],
        "name": ["Попередньо навчені", "мовні моделі (PLM)"],
        "date": ["Від 2019–2020 рр."],
        "examples": ["RAT-SQL · TaBERT · PICARD"],
        "color": "#2e773c",
    },
    {
        "x": 1210, "y": 223, "box_y": 305,
        "tag": ["Навчання в контексті (ICL)", "Донавчання"],
        "name": ["Великі", "мовні моделі (LLM)"],
        "date": ["Від 2022 р."],
        "examples": ["Codex · DIN-SQL · DAIL-SQL · OmniSQL"],
        "examples_x": 1250,
        "color": "#18552d",
    },
]
for stage in stages:
    x, y = stage["x"], stage["y"]
    tag_y, tip, base = stage_layout(x, y)
    box_y = stage["box_y"]
    shoulder = tip + ARROW_HEAD
    rect(x - TAG_HALF, tag_y, TAG_HALF * 2, TAG_H, "#d9e8d5")
    text(x, tag_y + 28, stage["tag"], "small", step=25, center=True)
    parts.append(f'<circle cx="{x}" cy="{y}" r="23" fill="{stage["color"]}"/>')
    # Drawn last so the point stays whole and only meets the outline.
    parts.append(
        f'<path d="M{x-10},{base} V{shoulder} H{x-23} '
        f'L{x},{tip} L{x+23},{shoulder} H{x+10} V{base} Z" '
        'fill="#408458"/>'
    )
    # Draw guides first so their endpoints sit behind the category boxes.
    path(f"M{x},{box_y+74} V660", dashed=True)
    rect(x - 143, box_y, 286, 74, "white")
    text(x, box_y + 30, stage["name"], "heading", step=28, center=True)
    text(x, 698, stage["date"], "axis", center=True)
    text(stage.get("examples_x", x), 736, stage["examples"], "small", center=True)

# A break explicitly separates the multi-decade prehistory from recent work.
parts.append('<path d="M401,651 l9,18 m3,-18 l9,18" stroke="white" stroke-width="7"/>')
path("M401,651 l9,18 m3,-18 l9,18")
parts.append("</svg>")

if __name__ == "__main__":
    OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(OUT)
