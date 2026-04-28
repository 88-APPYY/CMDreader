"""Interactive pager for reading chapters in the terminal."""
from __future__ import annotations
import shutil
import sys
import time
import threading
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from rich import box
from reader.parser import Chapter
from reader.taskbar import TaskbarManager, format_task_for_display

console = Console()

_original_stdout = None
_taskbar_manager: TaskbarManager | None = None
_update_thread: threading.Thread | None = None
_running: bool = False


def _save_terminal_state() -> None:
    """Save original terminal state for clean exit."""
    global _original_stdout
    _original_stdout = sys.stdout


def _restore_terminal_state() -> None:
    """Restore terminal to original state."""
    global _original_stdout
    if _original_stdout is not None:
        sys.stdout = _original_stdout


def _clear_screen_completely() -> None:
    """Completely clear the terminal screen and scrollback buffer if possible."""
    console.clear()
    
    if sys.platform == "win32":
        sys.stdout.write("\x1b[2J\x1b[H")
        sys.stdout.flush()
    else:
        sys.stdout.write("\x1b[2J\x1b[3J\x1b[H")
        sys.stdout.flush()


def _start_taskbar_updater() -> None:
    """Start the background thread for updating taskbar tasks."""
    global _taskbar_manager, _update_thread, _running
    
    _taskbar_manager = TaskbarManager(max_tasks=4)
    _running = True
    
    def update_loop():
        while _running:
            if _taskbar_manager:
                _taskbar_manager.update()
            time.sleep(0.1)
    
    _update_thread = threading.Thread(target=update_loop, daemon=True)
    _update_thread.start()


def _stop_taskbar_updater() -> None:
    """Stop the background taskbar updater thread."""
    global _running, _update_thread
    _running = False
    
    if _update_thread and _update_thread.is_alive():
        _update_thread.join(timeout=1.0)


def _page_lines(lines: list[str], width: int, height: int) -> list[list[str]]:
    """Wrap and split lines into screen-sized pages."""
    import textwrap
    wrapped: list[str] = []
    for line in lines:
        if line.strip():
            wrapped.extend(textwrap.wrap(line, width) or [line])
        else:
            wrapped.append("")
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
        import tty, termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                ch2 = sys.stdin.read(1)
                ch3 = sys.stdin.read(1)
                if ch2 == "[":
                    return {"C": "l", "D": "h", "B": "n", "A": "p"}.get(ch3, "")
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except Exception:
        import msvcrt
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            ch2 = msvcrt.getwch()
            return {"M": "l", "K": "h", "P": "n", "H": "p"}.get(ch2, "")
        return ch


def _non_blocking_getch(timeout: float = 0.1) -> str | None:
    """Non-blocking keyboard input with timeout."""
    try:
        import tty, termios, select
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            rlist, _, _ = select.select([sys.stdin], [], [], timeout)
            if rlist:
                ch = sys.stdin.read(1)
                if ch == "\x1b":
                    ch2 = sys.stdin.read(1)
                    ch3 = sys.stdin.read(1)
                    if ch2 == "[":
                        return {"C": "l", "D": "h", "B": "n", "A": "p"}.get(ch3, "")
                return ch
            return None
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except Exception:
        import msvcrt
        if msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch in ("\x00", "\xe0"):
                ch2 = msvcrt.getwch()
                return {"M": "l", "K": "h", "P": "n", "H": "p"}.get(ch2, "")
            return ch
        time.sleep(timeout)
        return None


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


def _prepare_single_line_content(chapters: list[Chapter]) -> list[tuple[str, int, int]]:
    """Prepare all content as single lines with chapter info."""
    content_lines = []
    for ch_idx, chapter in enumerate(chapters):
        for line_idx, line in enumerate(chapter.lines):
            if line.strip():
                content_lines.append((line.strip(), ch_idx, line_idx))
    return content_lines


def _render_with_taskbar(
    current_line: str,
    chapter_title: str,
    line_no: int,
    total_lines: int,
    chapter_no: int,
    total_chapters: int,
) -> None:
    """Render content with dynamic taskbar at the bottom."""
    global _taskbar_manager
    
    console.clear()
    term_w, term_h = shutil.get_terminal_size()

    header = Text(f" {chapter_title} ", style="bold cyan")
    console.print(Align.center(header))
    console.print("─" * term_w, style="dim")

    import textwrap
    wrapped = textwrap.wrap(current_line, term_w - 4) or [current_line]
    console.print(Text("  " + wrapped[0] if wrapped else ""))

    console.print("─" * term_w, style="dim")
    
    if _taskbar_manager:
        tasks = _taskbar_manager.get_tasks()
        if tasks:
            console.print("[dim]═══════════════════════════════════════════════════════════════[/dim]")
            console.print("[bold][系统任务][/bold]")
            for task in tasks:
                task_line = format_task_for_display(task, term_w - 2)
                console.print(f"  {task_line}")
            
            remaining = term_h - 10 - len(tasks)
            if remaining > 0:
                for _ in range(min(remaining, 2)):
                    console.print("")
        else:
            console.print("")
            console.print("[dim][系统空闲 - 正在同步...][/dim]")
            console.print("")
    else:
        console.print("")
    
    footer = (
        f"[dim]章节 {chapter_no}/{total_chapters}  "
        f"行 {line_no}/{total_lines}[/dim]  "
        "[cyan]↑[/cyan] 上一行  [cyan]↓[/cyan] 下一行  "
        "[cyan]←/→[/cyan] 退出"
    )
    console.print(footer)


def _clean_exit_ninja() -> None:
    """Perform a completely clean, ninja-style exit without any trace."""
    global _running
    
    _running = False
    _stop_taskbar_updater()
    
    _clear_screen_completely()
    
    _restore_terminal_state()
    
    for _ in range(3):
        sys.stdout.write("\n")
        sys.stdout.flush()
        time.sleep(0.01)
    
    sys.stdout.write("\x1b[H")
    sys.stdout.flush()


def read_single_line(chapters: list[Chapter], book_path: str, start_chapter: int = 0, start_line: int = 0) -> None:
    """Read novel in single line mode with dynamic taskbar and ninja exit."""
    global _taskbar_manager, _running
    
    from reader import bookmark

    content_lines = _prepare_single_line_content(chapters)
    
    if not content_lines:
        console.clear()
        console.print("[red]小说内容为空[/red]")
        return

    line_idx = 0
    for i, (_, ch_idx, _) in enumerate(content_lines):
        if ch_idx >= start_chapter:
            line_idx = i
            break

    total_lines = len(content_lines)
    total_chapters = len(chapters)

    _save_terminal_state()
    _start_taskbar_updater()

    try:
        while 0 <= line_idx < total_lines:
            current_line, ch_idx, _ = content_lines[line_idx]
            chapter = chapters[ch_idx]
            
            _render_with_taskbar(
                current_line,
                chapter.title,
                line_idx + 1,
                total_lines,
                ch_idx + 1,
                total_chapters,
            )
            bookmark.save(book_path, ch_idx, line_idx)
            
            key = None
            for _ in range(10):
                key = _non_blocking_getch(timeout=0.05)
                if key:
                    key = key.lower()
                    break
            
            if not key:
                continue

            if key in ("n", "j"):
                if line_idx < total_lines - 1:
                    line_idx += 1
            elif key in ("p", "k"):
                if line_idx > 0:
                    line_idx -= 1
            elif key in ("h", "l"):
                _clean_exit_ninja()
                return
            elif key == "q":
                _stop_taskbar_updater()
                console.clear()
                console.print("[green]已保存阅读进度，下次继续。[/green]")
                return

        _stop_taskbar_updater()
        console.clear()
        console.print("[green]已读完全书。[/green]")
        
    except KeyboardInterrupt:
        _clean_exit_ninja()
        return
    finally:
        _stop_taskbar_updater()
        _restore_terminal_state()


def read(chapters: list[Chapter], book_path: str, start_chapter: int = 0, start_line: int = 0) -> None:
    """Main read function that uses single line mode with taskbar."""
    read_single_line(chapters, book_path, start_chapter, start_line)
