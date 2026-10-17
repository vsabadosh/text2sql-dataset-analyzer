"""Adapt the original diagram, retaining its icons, layout and arrows."""
from pathlib import Path
import xml.etree.ElementTree as ET

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
directory = Path(__file__).parent
root = ET.fromstring((directory / "skhema_text2sql.svg").read_text(encoding="utf-8"))


def tag(name):
    return f"{{{NS}}}{name}"


def at(parent, name, **attrs):
    matches = [
        node for node in parent.findall(tag(name))
        if all(node.get(key) == str(value) for key, value in attrs.items())
    ]
    assert len(matches) == 1, (name, attrs, len(matches))
    return matches[0]


at(root, "text", x=40, y=88).text = (
    "\u042f\u043a \u0437\u0432\u0430\u0442\u0438 \u0441\u043f\u0456\u0432\u0430\u043a\u0456\u0432, "
    "\u0441\u0442\u0430\u0440\u0448\u0438\u0445 \u0437\u0430 30 \u0440\u043e\u043a\u0456\u0432?"
)
# Remove the two background table cards, leaving a single full-size card.
for name, x, y in (("rect", 36, 158), ("text", 50, 179),
                   ("rect", 48, 180), ("text", 62, 201)):
    root.remove(at(root, name, x=x, y=y))
card = at(root, "rect", x=60, y=206)
card.set("y", "180")
card.set("height", "236")
heading = at(root, "text", x=76, y=238)
heading.set("y", "216")
heading.text = "\u0422\u0430\u0431\u043b\u0438\u0446\u044f singer"
schema = at(root, "g", **{"font-size": 16})
columns = (
    '"id" integer,', '"name" text,', '"age" integer,',
    '"country" text,', 'primary key("id")',
)
for node, value, y in zip(schema.findall(tag("text")), columns, (254, 286, 318, 350, 382)):
    node.text = value
    node.set("y", str(y))
schema.remove(schema.findall(tag("text"))[-1])

# Preserve the original result panel and colored row markers.
at(root, "text", x=898, y=187).text = "name"
results = at(root, "g", **{"font-size": 18})
names = (
    "\u041e\u043b\u0435\u043d\u0430", "\u041e\u043b\u0435\u043a\u0441\u0430\u043d\u0434\u0440",
    "\u0406\u0440\u0438\u043d\u0430", "\u041c\u0438\u043a\u043e\u043b\u0430", "\u041d\u0430\u0442\u0430\u043b\u0456\u044f",
)
for node, value in zip(results.findall(tag("text")), names):
    node.text = value

sql = at(root, "g", **{"font-size": 20})
for node, value, y in zip(
    sql.findall(tag("text")),
    ("SELECT name", "FROM singer", "WHERE age > 30;"),
    (510, 542, 574),
):
    node.text = value
    node.set("y", str(y))
for node in sql.findall(tag("text"))[3:]:
    sql.remove(node)

model = at(root, "g", transform="translate(493,300)")
at(model, "text", x=52, y=116).text = (
    "\u0421\u0438\u0441\u0442\u0435\u043c\u0430 Text-to-SQL"
)
at(root, "title").text = (
    "Text-to-SQL: \u043f\u0438\u0442\u0430\u043d\u043d\u044f, SQL, "
    "\u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442"
)
at(root, "desc").text = (
    "\u0421\u0438\u0441\u0442\u0435\u043c\u0430 Text-to-SQL: "
    "singer, SELECT name FROM singer WHERE age > 30."
)

output = ET.tostring(root, encoding="unicode")
ET.fromstring(output)
(directory / "skhema_text2sql_singer.svg").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n' + output + "\n",
    encoding="utf-8",
)
