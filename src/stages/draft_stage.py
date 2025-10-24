from dataclasses import dataclass
from typing import List, Dict
from ..utils.timestamps import today_slug

TEMPLATE = """# {title}
*{standfirst}*

{hook}

{body}

## Key Takeaways
- Start simple; add complexity only when bottlenecks are measured.

## What’s Next
- Measure retrieval quality and latency before adding infra.

## References
{references}
"""

@dataclass
class Draft:
    markdown: str
    citations: List[Dict]

def run(title: str, standfirst: str, hook: str, sections: List[Dict], sources: List[Dict]) -> Draft:
    # Build body from sections
    parts = []
    for sec in sections:
        parts.append(f"## {sec['h2']}")
        for b in sec.get('bullets', []):
            parts.append(f"- {b}")
        parts.append('')  # blank line
    body = '\n'.join(parts)

    refs_lines, citations = [], []
    for i, s in enumerate(sources, start=1):
        refs_lines.append(f"[{i}] {s['title']} — {s['url']} (accessed: {today_slug()})")
        citations.append({'n': i, 'title': s['title'], 'url': s['url'], 'accessed_at': today_slug()})

    md = TEMPLATE.format(title=title, standfirst=standfirst, hook=hook, body=body, references='\n'.join(refs_lines))
    return Draft(markdown=md, citations=citations)
