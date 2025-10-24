from dataclasses import dataclass
from typing import List, Dict, Any
from ..clients.claude_client import ClaudeClient
from ..utils.timestamps import today_slug

@dataclass
class Research:
    queries: List[str]
    sources: List[Dict[str, Any]]

FALLBACK_SOURCES = [
    {
        'n': 1,
        'title': 'A Practical Survey of Retrieval-Augmented Generation',
        'url': 'https://arxiv.org/abs/2401.00001',
        'published': '2024-01-05',
        'notes': [
            'Survey of RAG design choices',
            'Hybrid retrieval considerations',
            'When lexical baselines suffice'
        ],
        'accessed': today_slug()
    }
]

def run(topic: str) -> Research:
    client = ClaudeClient()
    # If you wire Anthropic later, use client.research(topic)
    queries = [
        f'\"{topic}\" pros and cons',
        'lightweight RAG without vector database',
        'BM25 vs dense retrieval for small corpora',
        'hybrid retrieval RAG small datasets',
        'embedding cache RAG local',
        'FAISS vs BM25 tradeoffs tiny corpora'
    ]
    return Research(queries=queries, sources=FALLBACK_SOURCES)
