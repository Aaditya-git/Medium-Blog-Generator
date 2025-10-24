from dataclasses import dataclass

@dataclass
class ReviewResult:
    ok: bool
    notes: str

def run(markdown: str) -> ReviewResult:
    # Minimal checks; expand as needed.
    if 'http' in markdown and 'References' not in markdown:
        return ReviewResult(ok=False, notes='Contains links but no References section.')
    if len(markdown) < 400:
        return ReviewResult(ok=False, notes='Draft is too short to be useful.')
    return ReviewResult(ok=True, notes='Ready to publish.')
