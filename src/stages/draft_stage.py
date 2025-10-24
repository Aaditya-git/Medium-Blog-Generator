from dataclasses import dataclass
from typing import List, Dict
from ..utils.timestamps import today_slug

TEMPLATE = """# {title}
*{standfirst}*

{hook}

{body}

## Key Takeaways
{takeaways}

## What’s Next
{whats_next}

## References
{references}
"""

@dataclass
class Draft:
    markdown: str
    citations: List[Dict]

def _bullets_to_paragraph(bullets: List[str]) -> str:
    # Convert list of notes into 2–4 natural sentences
    if not bullets:
        return ""
    sentences = []
    for raw in bullets:
        s = raw.strip().rstrip(".")
        if not s:
            continue
        # Capitalize first letter and end with a period.
        sentences.append(s[0].upper() + s[1:] + ".")
    # Merge into a paragraph
    para = " ".join(sentences)
    # Ensure reasonable line breaks for Medium readability
    return para

def _sections_to_body(sections: List[Dict]) -> str:
    blocks = []
    for sec in sections:
        h2 = sec.get("h2", "Section")
        bullets = sec.get("bullets", [])
        para = _bullets_to_paragraph(bullets)
        blocks.append(f"## {h2}\n{para}\n")
    return "\n".join(blocks).strip()

def _generic_takeaways(topic: str) -> str:
    lines = [
        f"- Start simple for {topic.lower()}; add complexity only when metrics demand it.",
        "- Measure quality and latency with small, representative tests.",
        "- Prefer changes that reduce operational risk and cognitive load.",
    ]
    return "\n".join(lines)

def _generic_next(topic: str) -> str:
    lines = [
        "- Instrument your baseline (quality, latency, cost).",
        f"- Identify one upgrade for {topic.lower()} that could yield a clear lift; test it behind a flag.",
        "- Keep a rollback path and write down what you learned.",
    ]
    return "\n".join(lines)

def run(title: str, standfirst: str, hook: str, sections: List[Dict], sources: List[Dict], tone: str | None = None) -> Draft:
    body = _sections_to_body(sections)

    refs_lines, citations = [], []
    for i, s in enumerate(sources, start=1):
        refs_lines.append(f"[{i}] {s['title']} — {s['url']} (accessed: {today_slug()})")
        citations.append({"n": i, "title": s["title"], "url": s["url"], "accessed_at": today_slug()})

    md = TEMPLATE.format(
        title=title,
        standfirst=standfirst,
        hook=hook,
        body=body,
        takeaways=_generic_takeaways(title),
        whats_next=_generic_next(title),
        references="\n".join(refs_lines) if refs_lines else "—",
    )
    return Draft(markdown=md, citations=citations)
