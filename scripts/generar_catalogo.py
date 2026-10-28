
from pathlib import Path
from html.parser import HTMLParser
from datetime import date
from urllib.parse import quote
import json
import re

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "catalogo.json"


class MetadataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.metadata = {}
        self.in_title = False
        self.title_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag.lower() == "meta":
            name = attrs.get("name", "").lower()
            if name in ("blog-title", "blog-date", "blog-keywords"):
                self.metadata[name] = attrs.get("content", "")

        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_text.append(data)


def clean_title(filename):
    name = Path(filename).stem
    name = re.sub(r"[-_]+", " ", name)
    return name[:1].upper() + name[1:]


def encoded_path(path):
    return quote(path.as_posix(), safe="/")


def read_html(path):
    parser = MetadataParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))

    title = (
        parser.metadata.get("blog-title")
        or "".join(parser.title_text).strip()
        or clean_title(path.name)
    )

    published = parser.metadata.get("blog-date", "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", published):
        published = date.today().isoformat()

    keywords = [
        item.strip().lower()
        for item in parser.metadata.get("blog-keywords", "").split(",")
        if item.strip()
    ]

    return {
        "title": title,
        "date": published,
        "keywords": keywords,
        "url": encoded_path(path.relative_to(ROOT)),
        "type": "HTML",
    }


# Publicaciones HTML antiguas.
legacy_html = [
    {
        "file": "cabalgando-la-nota.html",
        "title": "Cabalgando la nota",
        "date": "2026-01-01",
        "keywords": ["literatura", "archivo"],
    },
    {
        "file": "pensamientos-libidinosos-tralfamadore.html",
        "title": "Pensamientos Libidinosos: Un estudio científico desde el paradigma de Tralfamadore",
        "date": "2026-01-01",
        "keywords": ["literatura", "pensamiento", "archivo"],
    },
]

items = []

for entry in legacy_html:
    path = ROOT / entry["file"]
    if path.is_file():
        items.append({
            "title": entry["title"],
            "date": entry["date"],
            "keywords": entry["keywords"],
            "url": encoded_path(path.relative_to(ROOT)),
            "type": "HTML",
        })


# PDF antiguos conocidos.
known_pdfs = {
    "dos-hombres-y-el-olor-a-tierra.pdf": {
        "title": "Dos hombres y el olor a tierra",
        "keywords": ["literatura", "encuentros", "memoria"],
    },
    "archivo-de-continentes-encuentros-con-hombres-africanos-de-distintos-países-africa.pdf": {
        "title": "Archivo de continentes: encuentros con hombres africanos de distintos países de África",
        "keywords": ["literatura", "encuentros", "continentes"],
    },
    "Inventarios-de-40-expresiones-masculinas-que-me-han-dicho-mientras-han-eyaculado-en-mi-boca.pdf": {
        "title": "Inventarios de 40 expresiones masculinas que me han dicho mientras han eyaculado en mi boca",
        "keywords": ["literatura", "inventario", "lenguaje"],
    },
    "Todo-empieza-en-el-chat.pdf": {
        "title": "Todo empieza en el chat",
        "keywords": ["literatura", "chat", "encuentros"],
    },
}

duplicate_pdf_names = {
    "cabalgando-la-nota.pdf",
    "pensamientos-libidinosos-tralfamadore.pdf",
}

pdf_dir = ROOT / "pdf"

if pdf_dir.is_dir():
    for path in pdf_dir.iterdir():
        if not path.is_file() or path.suffix.lower() != ".pdf":
            continue

        if path.name.lower() in duplicate_pdf_names:
            continue

        known = known_pdfs.get(path.name, {})

        items.append({
            "title": known.get("title", clean_title(path.name)),
            "date": "2026-01-01",
            "keywords": known.get("keywords", ["literatura"]),
            "url": encoded_path(path.relative_to(ROOT)),
            "type": "PDF",
        })


# HTML nuevos: cada archivo lleva título, fecha y palabras clave.
posts_dir = ROOT / "publicaciones"

if posts_dir.is_dir():
    for path in sorted(posts_dir.rglob("*.html")):
        items.append(read_html(path))


# Primero las publicaciones más recientes.
items.sort(
    key=lambda item: (item["date"], item["title"].casefold()),
    reverse=True,
)

OUTPUT.write_text(
    json.dumps(items, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(f"Catálogo actualizado: {len(items)} publicaciones.")
