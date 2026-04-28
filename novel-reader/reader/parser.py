"""Parse .txt and .epub files into a list of chapters."""
from __future__ import annotations
import re
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class Chapter:
    title: str
    lines: list[str] = field(default_factory=list)

    @property
    def content(self) -> str:
        return "\n".join(self.lines)


# Regex that matches common Chinese chapter headings
_CHAPTER_RE = re.compile(
    r"^(第[零一二三四五六七八九十百千万\d]+[章节回集卷]|Chapter\s+\d+|CHAPTER\s+\d+)",
    re.MULTILINE,
)


def parse_txt(path: Path) -> list[Chapter]:
    text = path.read_text(encoding="utf-8", errors="replace")
    parts = _CHAPTER_RE.split(text)

    # parts: [pre, heading1, body1, heading2, body2, ...]
    chapters: list[Chapter] = []
    if parts[0].strip():
        chapters.append(Chapter(title="序言", lines=parts[0].splitlines()))

    it = iter(parts[1:])
    for heading in it:
        body = next(it, "")
        chapters.append(Chapter(title=heading.strip(), lines=body.splitlines()))

    if not chapters:
        # No chapter markers — treat whole file as one chapter
        chapters.append(Chapter(title=path.stem, lines=text.splitlines()))

    return chapters


def parse_epub(path: Path) -> list[Chapter]:
    try:
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup
    except ImportError:
        raise SystemExit("请先安装 ebooklib 和 beautifulsoup4: pip install ebooklib beautifulsoup4")

    book = epub.read_epub(str(path))
    chapters: list[Chapter] = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        title_tag = soup.find(["h1", "h2", "h3", "title"])
        title = title_tag.get_text(strip=True) if title_tag else item.get_name()
        lines = [p.get_text(" ", strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
        if lines:
            chapters.append(Chapter(title=title, lines=lines))
    return chapters


def load_book(path: str) -> list[Chapter]:
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"文件不存在: {path}")
    if p.suffix.lower() == ".epub":
        return parse_epub(p)
    return parse_txt(p)
