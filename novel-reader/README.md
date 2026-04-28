# novel-reader

命令行小说阅读器，支持 `.txt` 和 `.epub` 格式，自动保存阅读进度。

## 安装

```bash
cd novel-reader
pip install -e .
```

## 使用

```bash
# 阅读小说（自动恢复上次进度）
novel read 斗破苍穹.txt

# 从第 10 章开始
novel read 斗破苍穹.txt --chapter 10

# 从头开始（忽略书签）
novel read 斗破苍穹.txt --fresh

# 查看目录
novel toc 斗破苍穹.txt

# 查看所有书籍进度
novel bookmarks
```

## 阅读快捷键

| 按键 | 功能 |
|------|------|
| `→` / `l` / `空格` | 下一页 |
| `←` / `h` | 上一页 |
| `n` | 下一章 |
| `p` | 上一章 |
| `t` | 目录跳转 |
| `q` | 退出并保存进度 |
