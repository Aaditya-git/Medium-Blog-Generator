from pathlib import Path
from typing import Dict, Any, Tuple

def ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p

def write_text(path: Path, content: str) -> Path:
    ensure_dir(path.parent)
    path.write_text(content, encoding='utf-8')
    return path

def write_lines(path: Path, lines: list[str]) -> Path:
    return write_text(path, '\n'.join(lines))

def run_folder(root: Path, date_slug: str, topic_slug: str) -> Path:
    return ensure_dir(root / f"{date_slug}_{topic_slug}")

def finalize_folder(published_root: Path, date_slug: str, topic_slug: str) -> Path:
    return ensure_dir(published_root / f"{date_slug}_{topic_slug}")
