from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Outline:
    title: str
    standfirst: str
    hook: str
    sections: List[Dict[str, Any]]  # [{ 'h2': str, 'bullets': [str]}]

def run(topic: str, research_sources: List[Dict[str, Any]]) -> Outline:
    title = 'Lightweight RAG: When a Vector DB Is Overkill'
    standfirst = 'Why simpler retrieval often beats heavy infra on small problems.'
    hook = 'Vector databases are powerful — but for small corpora and low QPS, they can add more ops cost than value.'
    sections = [
        {'h2': 'The Hidden Overhead of Vector Databases',
         'bullets': [
             'Operational complexity on small projects',
             'Index build + update costs',
             'Latency trade-offs on tiny corpora'
         ]},
        {'h2': 'When Simpler Wins: BM25, Files, and Caches',
         'bullets': [
             'BM25/BM25+ strong for lexical precision',
             'JSONL + mmap can be enough',
             'Reuse embedding caches to avoid re-indexing'
         ]},
        {'h2': 'Minimal RAG Architectures',
         'bullets': [
             'Single-process retriever',
             'Hybrid lexical+dense via one-off FAISS index',
             'No server needed at low QPS'
         ]},
        {'h2': 'Choosing the Right Tool: A Quick Heuristic',
         'bullets': [
             'N docs, QPS, update rate, team skill',
             'Cost and failure domains'
         ]}
    ]
    return Outline(title=title, standfirst=standfirst, hook=hook, sections=sections)
