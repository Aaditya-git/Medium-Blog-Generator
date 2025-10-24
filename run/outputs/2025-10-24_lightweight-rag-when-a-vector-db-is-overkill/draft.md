# Lightweight RAG: When a Vector DB Is Overkill
*Why simpler retrieval often beats heavy infra on small problems.*

Vector databases are powerful — but for small corpora and low QPS, they can add more ops cost than value.

## The Hidden Overhead of Vector Databases
- Operational complexity on small projects
- Index build + update costs
- Latency trade-offs on tiny corpora

## When Simpler Wins: BM25, Files, and Caches
- BM25/BM25+ strong for lexical precision
- JSONL + mmap can be enough
- Reuse embedding caches to avoid re-indexing

## Minimal RAG Architectures
- Single-process retriever
- Hybrid lexical+dense via one-off FAISS index
- No server needed at low QPS

## Choosing the Right Tool: A Quick Heuristic
- N docs, QPS, update rate, team skill
- Cost and failure domains


## Key Takeaways
- Start simple; add complexity only when bottlenecks are measured.

## What’s Next
- Measure retrieval quality and latency before adding infra.

## References
[1] A Practical Survey of Retrieval-Augmented Generation — https://arxiv.org/abs/2401.00001 (accessed: 2025-10-24)
