from dataclasses import dataclass
from typing import List, Dict, Any
from ..clients.claude_client import ClaudeClient
from ..utils.timestamps import today_slug

@dataclass
class Research:
    queries: List[str]
    sources: List[Dict[str, Any]]  # allow empty; outline/draft do not depend on specific titles

def _expand_queries(topic: str) -> List[str]:
    t = topic.strip()
    base = [
        f"{t} overview",
        f"{t} tutorial 2025",
        f"{t} best practices",
        f"{t} pitfalls",
        f"{t} pros and cons",
        f"{t} benchmarks",
        f"{t} examples",
    ]
    # Heuristics based on topic pattern
    low = t.lower()
    if " vs " in low or " versus " in low:
        base += [f"{t} comparison", f"{t} trade-offs", f"{t} decision guide"]
    if any(k in low for k in ["how to", "guide", "quickstart", "setup", "install"]):
        base += [f"{t} step by step", f"{t} quickstart 2025"]
    if any(k in low for k in ["interview", "questions", "prep"]):
        base += [f"{t} common questions", f"{t} interview checklist"]
    if any(k in low for k in ["rag", "retrieval"]):
        base += [f"{t} bm25", f"{t} hybrid retrieval", f"{t} vector db alternatives"]
    return sorted(set(base), key=str.lower)

def _seed_sources(topic: str) -> List[Dict[str, Any]]:
    # Keep generic, topic-labeled placeholders so nothing is hardcoded to RAG.
    # If you wire web search later, replace this with real results.
    today = today_slug()
    return [
        {
            "n": 1,
            "title": f"Overview: {topic}",
            "url": "about:offline-overview",
            "published": "n/a",
            "notes": ["High-level concepts", "Common components", "Where it fits"],
            "accessed": today,
        },
        {
            "n": 2,
            "title": f"Best Practices for {topic}",
            "url": "about:offline-best-practices",
            "published": "n/a",
            "notes": ["Design tips", "Operational concerns", "Quality & metrics"],
            "accessed": today,
        },
    ]

def run(topic: str) -> Research:
    client = ClaudeClient()
    # If you later implement client.research(topic) it can return real sources.
    queries = _expand_queries(topic)
    sources = _seed_sources(topic)
    return Research(queries=queries, sources=sources)
