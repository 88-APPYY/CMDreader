"""Dynamic taskbar effect system for simulating system tasks."""
from __future__ import annotations
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class TaskType(Enum):
    COMPILE = "compile"
    DOWNLOAD = "download"
    UPDATE = "update"
    SCAN = "scan"
    BUILD = "build"
    INSTALL = "install"
    SYNC = "sync"
    INDEX = "index"


@dataclass
class SystemTask:
    task_type: TaskType
    name: str
    progress: float = 0.0
    status: str = "正在运行"
    speed: float = 0.0
    eta: str = ""
    details: str = ""
    _start_time: float = field(default_factory=time.time)
    _duration: float = field(default_factory=lambda: random.uniform(30, 120))
    _speed_variation: float = field(default_factory=lambda: random.uniform(0.5, 2.0))

    def update(self) -> None:
        elapsed = time.time() - self._start_time
        progress_ratio = min(elapsed / self._duration, 1.0)
        
        progress_increment = random.uniform(0.1, 2.0) * self._speed_variation
        self.progress = min(self.progress + progress_increment, 100.0)
        
        if self.progress >= 100:
            self.status = "已完成"
        elif self.progress >= 90:
            self.status = "即将完成"
        elif self.progress >= 50:
            self.status = "进行中"
        elif random.random() < 0.01:
            statuses = ["正在运行", "处理中", "执行中", "工作中"]
            self.status = random.choice(statuses)


TASK_TEMPLATES = {
    TaskType.COMPILE: [
        {"name": "编译内核模块", "details": "正在处理 src/kernel/module.c"},
        {"name": "构建项目", "details": "编译 src/main.cpp -> build/main.o"},
        {"name": "编译 TypeScript", "details": "正在转换 ts/app.ts -> js/app.js"},
        {"name": "编译 Rust 代码", "details": "正在编译 src/lib.rs"},
        {"name": "打包 Java 项目", "details": "正在编译 src/com/example/Main.java"},
    ],
    TaskType.DOWNLOAD: [
        {"name": "下载更新", "details": "从 https://mirrors.example.com 获取"},
        {"name": "同步依赖包", "details": "正在下载 packages-2024.zip (156MB)"},
        {"name": "拉取 Docker 镜像", "details": "正在拉取 ubuntu:latest 镜像"},
        {"name": "克隆 Git 仓库", "details": "正在接收对象: 100% (2345/2345)"},
        {"name": "下载资源包", "details": "正在下载 assets-v2.3.tar.gz"},
    ],
    TaskType.UPDATE: [
        {"name": "系统更新", "details": "正在应用安全补丁 KB5036980"},
        {"name": "更新软件包", "details": "正在升级 python3.11 -> python3.12"},
        {"name": "同步索引", "details": "正在更新 apt 软件包列表"},
        {"name": "刷新缓存", "details": "正在更新 npm 包索引"},
        {"name": "应用更新", "details": "正在配置更新包 5/12"},
    ],
    TaskType.SCAN: [
        {"name": "病毒扫描", "details": "正在扫描 C:\\Windows\\System32"},
        {"name": "磁盘检查", "details": "正在分析文件系统结构"},
        {"name": "索引重建", "details": "正在扫描文档目录"},
        {"name": "安全审计", "details": "正在检查系统配置"},
        {"name": "漏洞扫描", "details": "正在检测已安装软件版本"},
    ],
    TaskType.BUILD: [
        {"name": "构建 Docker 镜像", "details": "Step 5/12 : RUN npm install"},
        {"name": "打包应用", "details": "正在构建 release 版本"},
        {"name": "生成文档", "details": "正在处理 docs/api.md"},
        {"name": "编译资源", "details": "正在优化 images/logo.png"},
        {"name": "链接目标文件", "details": "正在链接 build/*.o -> app.exe"},
    ],
    TaskType.INSTALL: [
        {"name": "安装 Python 包", "details": "正在安装 pandas-2.1.0-cp311-win_amd64.whl"},
        {"name": "配置服务", "details": "正在注册系统服务"},
        {"name": "解压文件", "details": "正在提取 archive.zip 到 C:\\Program Files"},
        {"name": "安装驱动", "details": "正在更新显卡驱动程序"},
        {"name": "配置环境", "details": "正在设置环境变量"},
    ],
    TaskType.SYNC: [
        {"name": "同步文件", "details": "正在上传 backup_2024.zip 到云端"},
        {"name": "同步数据库", "details": "正在复制表 users (15000/50000 行)"},
        {"name": "同步设置", "details": "正在同步配置到所有设备"},
        {"name": "同步代码", "details": "正在推送到 origin/main 分支"},
        {"name": "同步媒体", "details": "正在上传照片图库 (234/1500)"},
    ],
    TaskType.INDEX: [
        {"name": "重建索引", "details": "正在索引文件内容"},
        {"name": "更新搜索", "details": "正在处理 15,234 个文档"},
        {"name": "构建缓存", "details": "正在生成查询缓存"},
        {"name": "优化数据库", "details": "正在重建索引 idx_user_name"},
        {"name": "同步搜索", "details": "正在更新 Elasticsearch 索引"},
    ],
}


class TaskbarManager:
    def __init__(self, max_tasks: int = 4):
        self.max_tasks = max_tasks
        self.tasks: list[SystemTask] = []
        self._last_update: float = 0
        self._task_change_counter: int = 0
        
    def _create_random_task(self) -> SystemTask:
        task_type = random.choice(list(TaskType))
        templates = TASK_TEMPLATES[task_type]
        template = random.choice(templates)
        
        return SystemTask(
            task_type=task_type,
            name=template["name"],
            progress=random.uniform(0, 30),
            details=template["details"],
        )
    
    def _update_task_details(self, task: SystemTask) -> None:
        if random.random() < 0.05:
            templates = TASK_TEMPLATES[task.task_type]
            template = random.choice(templates)
            task.details = template["details"]
    
    def update(self) -> None:
        current_time = time.time()
        
        for task in self.tasks:
            task.update()
            self._update_task_details(task)
        
        self.tasks = [t for t in self.tasks if t.progress < 100 or random.random() < 0.3]
        
        self._task_change_counter += 1
        if (len(self.tasks) < self.max_tasks and 
            (self._task_change_counter > 50 or len(self.tasks) == 0)):
            self._task_change_counter = 0
            if random.random() < 0.3 or len(self.tasks) == 0:
                new_task = self._create_random_task()
                self.tasks.append(new_task)
        
        while len(self.tasks) > self.max_tasks:
            self.tasks.pop(random.randint(0, len(self.tasks) - 1))
    
    def get_tasks(self) -> list[SystemTask]:
        return self.tasks
    
    def get_task_count(self) -> int:
        return len(self.tasks)


def generate_progress_bar(progress: float, width: int = 20) -> str:
    filled = int(width * progress / 100)
    bar = "█" * filled + "░" * (width - filled)
    return bar


def format_task_for_display(task: SystemTask, width: int) -> str:
    icon_map = {
        TaskType.COMPILE: "🔨",
        TaskType.DOWNLOAD: "⬇️",
        TaskType.UPDATE: "🔄",
        TaskType.SCAN: "🔍",
        TaskType.BUILD: "📦",
        TaskType.INSTALL: "💾",
        TaskType.SYNC: "🔗",
        TaskType.INDEX: "📋",
    }
    
    icon = icon_map.get(task.task_type, "⚙️")
    progress_bar = generate_progress_bar(task.progress, 10)
    
    status_color = {
        "已完成": "[green]",
        "即将完成": "[yellow]",
        "进行中": "[cyan]",
    }.get(task.status, "[dim]")
    
    name_width = width - 35
    short_name = task.name[:name_width]
    if len(task.name) > name_width:
        short_name = task.name[:name_width-3] + "..."
    
    return (
        f"{icon} {short_name:<{name_width}} "
        f"[{progress_bar}] "
        f"{task.progress:>5.1f}% "
        f"{status_color}{task.status}[/]"
    )
