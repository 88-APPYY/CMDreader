"""Interactive pager for reading chapters in the terminal."""
from __future__ import annotations
import shutil
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from rich import box
from reader.parser import Chapter

console = Console()


def _page_lines(lines: list[str], width: int, height: int) -> list[list[str]]:
    """Wrap and split lines into screen-sized pages."""
    import textwrap
    wrapped: list[str] = []
    for line in lines:
        if line.strip():
            wrapped.extend(textwrap.wrap(line, width) or [line])
        else:
            wrapped.append("")
    # Reserve 4 rows for header/footer
    page_size = max(height - 4, 5)
    return [wrapped[i : i + page_size] for i in range(0, max(len(wrapped), 1), page_size)]


def _render_page(
    page_lines: list[str],
    chapter_title: str,
    page_no: int,
    total_pages: int,
    chapter_no: int,
    total_chapters: int,
) -> None:
    console.clear()
    term_w, _ = shutil.get_terminal_size()

    header = Text(f" {chapter_title} ", style="bold cyan")
    console.print(Align.center(header))
    console.print("─" * term_w, style="dim")

    for line in page_lines:
        console.print(Text("  " + line) if line.strip() else "")

    console.print("─" * term_w, style="dim")
    footer = (
        f"[dim]章节 {chapter_no}/{total_chapters}  "
        f"页 {page_no}/{total_pages}[/dim]  "
        "[cyan]→/l[/cyan] 下页  [cyan]←/h[/cyan] 上页  "
        "[cyan]n[/cyan] 下章  [cyan]p[/cyan] 上章  "
        "[cyan]t[/cyan] 目录  [cyan]q[/cyan] 退出"
    )
    console.print(footer)


def _getch() -> str:
    """Read a single keypress cross-platform."""
    try:
        import tty, termios, sys
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            # Handle arrow keys (ESC sequences)
            if ch == "\x1b":
                ch2 = sys.stdin.read(1)
                ch3 = sys.stdin.read(1)
                if ch2 == "[":
                    return {"C": "l", "D": "h", "B": "n", "A": "p"}.get(ch3, "")
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except Exception:
        # Windows fallback
        import msvcrt
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            ch2 = msvcrt.getwch()
            return {"M": "l", "K": "h", "P": "n", "H": "p"}.get(ch2, "")
        return ch


def show_toc(chapters: list[Chapter], current: int) -> int | None:
    """Display table of contents, return selected chapter index or None."""
    console.clear()
    console.print(Panel("[bold]目录[/bold]", box=box.ROUNDED))
    term_h = shutil.get_terminal_size().lines
    page_size = term_h - 6
    total = len(chapters)
    page_start = max(0, current - page_size // 2)
    page_end = min(total, page_start + page_size)

    for i in range(page_start, page_end):
        marker = "[bold cyan]▶[/bold cyan] " if i == current else "  "
        console.print(f"{marker}[{i+1:>4}] {chapters[i].title}")

    console.print("\n[dim]输入章节编号跳转，直接回车返回[/dim]")
    try:
        raw = input("> ").strip()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < total:
                return idx
    except (EOFError, KeyboardInterrupt):
        pass
    return None


def read(chapters: list[Chapter], book_path: str, start_chapter: int = 0, start_line: int = 0) -> None:
    from reader import bookmark

    term_w, term_h = shutil.get_terminal_size()
    ch_idx = start_chapter
    line_offset = start_line  # which page we start on (approximation)

    while 0 <= ch_idx < len(chapters):
        chapter = chapters[ch_idx]
        pages = _page_lines(chapter.lines, term_w - 4, term_h)
        if not pages:
            pages = [[""]]

        pg = min(line_offset, len(pages) - 1)
        line_offset = 0  # reset after first chapter load

        while True:
            _render_page(
                pages[pg],
                chapter.title,
                pg + 1,
                len(pages),
                ch_idx + 1,
                len(chapters),
            )
            bookmark.save(book_path, ch_idx, pg)
            key = _getch().lower()

            if key in ("l", " ", "\r"):   # next page
                if pg < len(pages) - 1:
                    pg += 1
                elif ch_idx < len(chapters) - 1:
                    ch_idx += 1
                    break
            elif key == "h":              # prev page
                if pg > 0:
                    pg -= 1
                elif ch_idx > 0:
                    ch_idx -= 1
                    line_offset = 9999   # go to last page of prev chapter
                    break
            elif key == "n":              # next chapter
                if ch_idx < len(chapters) - 1:
                    ch_idx += 1
                    break
            elif key == "p":              # prev chapter
                if ch_idx > 0:
                    ch_idx -= 1
                    break
            elif key == "t":              # table of contents
                result = show_toc(chapters, ch_idx)
                if result is not None:
                    ch_idx = result
                    break
            elif key == "q":              # quit
                console.clear()
                console.print("[green]已保存阅读进度，下次继续。[/green]")
                return

    console.clear()
    console.print("[green]已读完全书。[/green]")
