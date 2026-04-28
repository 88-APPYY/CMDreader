"""CLI entry point."""
import click
import shutil
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

_NOVELS_DIR = Path(__file__).parent.parent / "novels"


def _ensure_novels_dir() -> None:
    """Ensure novels directory exists."""
    _NOVELS_DIR.mkdir(parents=True, exist_ok=True)


def _list_novels() -> list[Path]:
    """List all novels in the novels directory."""
    _ensure_novels_dir()
    novels = []
    for ext in ["*.txt", "*.epub"]:
        novels.extend(_NOVELS_DIR.glob(ext))
    return sorted(novels, key=lambda p: p.name.lower())


@click.group()
def main():
    """📖 命令行小说阅读器"""


@main.command("import")
@click.argument("file", type=click.Path(exists=True))
def import_novel(file: str):
    """导入小说文件到项目中（支持 .txt / .epub）"""
    _ensure_novels_dir()
    src = Path(file)
    dest = _NOVELS_DIR / src.name
    
    if dest.exists():
        console.print(f"[yellow]小说 '{src.name}' 已存在，是否覆盖？[/yellow]")
        try:
            response = input("(y/n): ").strip().lower()
            if response != "y":
                console.print("[dim]已取消导入[/dim]")
                return
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]已取消导入[/dim]")
            return
    
    try:
        shutil.copy2(src, dest)
        console.print(f"[green]成功导入: {dest}[/green]")
    except Exception as e:
        console.print(f"[red]导入失败: {e}[/red]")


@main.command()
def list():
    """列出所有已导入的小说"""
    novels = _list_novels()
    if not novels:
        console.print("[dim]暂无已导入的小说[/dim]")
        console.print(f"[dim]使用 'novel import <文件>' 导入小说[/dim]")
        return
    
    table = Table(title="已导入的小说", show_lines=True)
    table.add_column("#", justify="right", style="dim")
    table.add_column("文件名", style="cyan")
    table.add_column("大小", justify="right")
    
    for i, novel in enumerate(novels, 1):
        size = novel.stat().st_size
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size // 1024} KB"
        else:
            size_str = f"{size // (1024 * 1024)} MB"
        table.add_row(str(i), novel.name, size_str)
    
    console.print(table)
    console.print(f"\n[dim]使用 'novel read {novels[0].name}' 阅读第一本小说[/dim]")


@main.command()
@click.argument("file", type=click.Path(exists=False))
@click.option("--chapter", "-c", default=None, type=int, help="从指定章节开始（1-based）")
@click.option("--fresh", "-f", is_flag=True, help="忽略书签，从头开始")
def read(file: str, chapter: int | None, fresh: bool):
    """阅读小说（支持文件名或完整路径）"""
    from reader.parser import load_book
    from reader.bookmark import get
    from reader.display import read as do_read

    file_path = Path(file)
    
    if not file_path.exists():
        _ensure_novels_dir()
        possible_path = _NOVELS_DIR / file
        if possible_path.exists():
            file_path = possible_path
        else:
            console.print(f"[red]文件不存在: {file}[/red]")
            console.print(f"[dim]尝试使用 'novel list' 查看已导入的小说[/dim]")
            return

    console.print(f"[cyan]正在加载[/cyan] {file_path} ...")
    chapters = load_book(str(file_path))
    console.print(f"[green]共 {len(chapters)} 章[/green]")

    if chapter is not None:
        start_ch = max(0, chapter - 1)
        start_ln = 0
    elif fresh:
        start_ch, start_ln = 0, 0
    else:
        start_ch, start_ln = get(str(file_path))
        if start_ch > 0 or start_ln > 0:
            console.print(f"[dim]从上次进度继续：第 {start_ch+1} 章 第 {start_ln+1} 行[/dim]")

    do_read(chapters, str(file_path), start_ch, start_ln)


@main.command()
def bookmarks():
    """查看所有书籍的阅读进度"""
    from reader.bookmark import list_bookmarks

    data = list_bookmarks()
    if not data:
        console.print("[dim]暂无阅读记录[/dim]")
        return

    table = Table(title="阅读进度", show_lines=True)
    table.add_column("书籍路径", style="cyan", no_wrap=False)
    table.add_column("章节", justify="right")
    table.add_column("页码", justify="right")

    for path, info in data.items():
        table.add_row(path, str(info.get("chapter", 0) + 1), str(info.get("line", 0) + 1))

    console.print(table)


@main.command()
@click.argument("file", type=click.Path(exists=True))
def toc(file: str):
    """显示书籍目录"""
    from reader.parser import load_book

    chapters = load_book(file)
    table = Table(title=f"目录 — {file}", show_lines=False)
    table.add_column("#", justify="right", style="dim")
    table.add_column("章节标题", style="cyan")

    for i, ch in enumerate(chapters, 1):
        table.add_row(str(i), ch.title)

    console.print(table)
