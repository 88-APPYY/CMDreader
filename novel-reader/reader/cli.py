"""CLI entry point."""
import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def main():
    """📖 命令行小说阅读器"""


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--chapter", "-c", default=None, type=int, help="从指定章节开始（1-based）")
@click.option("--fresh", "-f", is_flag=True, help="忽略书签，从头开始")
def read(file: str, chapter: int | None, fresh: bool):
    """阅读小说文件（支持 .txt / .epub）"""
    from reader.parser import load_book
    from reader.bookmark import get
    from reader.display import read as do_read

    console.print(f"[cyan]正在加载[/cyan] {file} ...")
    chapters = load_book(file)
    console.print(f"[green]共 {len(chapters)} 章[/green]")

    if chapter is not None:
        start_ch = max(0, chapter - 1)
        start_ln = 0
    elif fresh:
        start_ch, start_ln = 0, 0
    else:
        start_ch, start_ln = get(file)
        if start_ch > 0 or start_ln > 0:
            console.print(f"[dim]从上次进度继续：第 {start_ch+1} 章 第 {start_ln+1} 页[/dim]")

    do_read(chapters, file, start_ch, start_ln)


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
