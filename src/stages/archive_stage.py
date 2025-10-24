from pathlib import Path
from dataclasses import dataclass
from ..utils.io import write_text, write_lines

@dataclass
class ArchiveResult:
    folder: Path

def run(output_folder: Path, markdown: str, references_lines: list[str]) -> ArchiveResult:
    write_text(output_folder / 'draft.md', markdown)
    write_lines(output_folder / 'references.txt', references_lines)
    return ArchiveResult(folder=output_folder)
