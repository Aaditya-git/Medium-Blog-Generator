from pathlib import Path
from dataclasses import dataclass
from shutil import copy2

@dataclass
class FinalizeResult:
    published_folder: Path

def run(src_folder: Path, dst_folder: Path, medium_url: str | None = None) -> FinalizeResult:
    dst_folder.mkdir(parents=True, exist_ok=True)
    # copy the two main files if present
    for name in ('draft.md','references.txt'):
        p = src_folder / name
        if p.exists():
            copy2(p, dst_folder / name)
    if medium_url:
        (dst_folder / 'published_url.txt').write_text(medium_url, encoding='utf-8')
    return FinalizeResult(published_folder=dst_folder)
