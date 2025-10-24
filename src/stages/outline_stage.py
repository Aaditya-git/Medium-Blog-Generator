from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Outline:
    title: str
    standfirst: str
    hook: str
    sections: List[Dict[str, Any]]  # [{ 'h2': str, 'bullets': [str]}]

def _title_from_topic(topic: str) -> str:
    t = topic.strip()
    # Title case lightly
    return t[0].upper() + t[1:] if t else "Untitled"

def _standfirst(topic: str) -> str:
    return f"A practical guide to {topic.lower()}, focused on clarity, trade-offs, and quick wins."

def _hook(topic: str) -> str:
    return (
        f"{topic} sounds straightforward until you hit real constraints—data quality, latency, "
        "and maintenance. This post shows you how to approach it pragmatically, starting simple and "
        "adding complexity only when measurement demands it."
    )

def _intent_sections(topic: str) -> List[Dict[str, Any]]:
    low = topic.lower()

    # Baseline sections that work for most technical topics
    sections: List[Dict[str, Any]] = [
        {
            "h2": "What & Why",
            "bullets": [
                f"Define {topic} in one paragraph and explain where it fits.",
                "List the core building blocks and typical inputs/outputs.",
                "Call out adjacent concepts people confuse it with.",
            ],
        },
        {
            "h2": "Core Mechanics",
            "bullets": [
                "Walk through the end-to-end flow at a high level.",
                "Detail the key knobs: size, latency, quality, cost.",
                "Show a minimal example or pseudo-code.",
            ],
        },
        {
            "h2": "Trade-offs & When Not to Use It",
            "bullets": [
                "List failure modes, edge cases, and common misconceptions.",
                "Explain when a leaner alternative is sufficient.",
                "Provide a measurement-first heuristic to decide.",
            ],
        },
        {
            "h2": "Practical Steps & Next Actions",
            "bullets": [
                "Step-by-step path from zero to a working baseline.",
                "Instrumentation to track accuracy and latency.",
                "Safe next upgrades if/when the baseline is not enough.",
            ],
        },
    ]

    # Intent-specific tweaks
    if " vs " in low or " versus " in low:
        sections[0]["h2"] = "What Are We Comparing?"
        sections.insert(1, {
            "h2": "Dimensions to Compare",
            "bullets": ["Accuracy/quality", "Latency/throughput", "Cost/ops", "Complexity/risk"],
        })

    if any(k in low for k in ["how to", "guide", "quickstart", "setup", "install"]):
        sections[0]["h2"] = "What You’ll Build"
        sections[1]["h2"] = "Step-by-Step Quickstart"

    if any(k in low for k in ["interview", "questions", "prep"]):
        sections[0]["h2"] = "Role Expectations & Scope"
        sections[1]["h2"] = "Core Topics to Master"
        sections[2]["h2"] = "Common Pitfalls in Interviews"
        sections[3]["h2"] = "Practice Plan & Resources"

    if any(k in low for k in ["rag", "retrieval"]):
        sections[1]["bullets"] += [
            "Explain lexical vs. dense retrieval in plain terms.",
            "Discuss hybrid strategies and when they help."
        ]

    return sections

def run(topic: str, research_sources: List[Dict[str, Any]]) -> Outline:
    return Outline(
        title=_title_from_topic(topic),
        standfirst=_standfirst(topic),
        hook=_hook(topic),
        sections=_intent_sections(topic),
    )
