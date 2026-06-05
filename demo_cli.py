"""
Demo CLI — Company Policies RAG
Usage:
    python demo_cli.py
    python demo_cli.py --filter category=compensation
    python demo_cli.py --top-k 5
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from src import (
    Document,
    EmbeddingStore,
    KnowledgeBaseAgent,
    MarkdownSectionChunker,
    _mock_embed,
)

load_dotenv(override=False)

POLICY_DIR = Path("data/Company Policies")
DOC_CONFIGS = [
    ("Working Remotely.md",                {"category": "work_arrangements", "target_audience": "all_employees",  "document_type": "policy"}),
    ("Vacation and Sick Leave.md",          {"category": "benefits",          "target_audience": "all_employees",  "document_type": "policy"}),
    ("New Parent Leave.md",                {"category": "benefits",           "target_audience": "parents",        "document_type": "policy"}),
    ("Salary and Equity Compensation.md",   {"category": "compensation",      "target_audience": "all_employees",  "document_type": "policy"}),
    ("Code of Conduct in the Community.md", {"category": "conduct",           "target_audience": "all_employees",  "document_type": "guidelines"}),
]


def build_store() -> EmbeddingStore:
    chunker = MarkdownSectionChunker(max_chunk_size=1000)
    store   = EmbeddingStore(collection_name="company_policies", embedding_fn=_mock_embed)
    docs: list[Document] = []

    for filename, meta in DOC_CONFIGS:
        path = POLICY_DIR / filename
        if not path.exists():
            print(f"[warn] skipping missing file: {path}", file=sys.stderr)
            continue
        text   = path.read_text(encoding="utf-8")
        chunks = chunker.chunk(text)
        doc_id = path.stem.lower().replace(" ", "_")
        for i, chunk in enumerate(chunks):
            docs.append(Document(
                id=f"{doc_id}_chunk{i}",
                content=chunk,
                metadata={**meta, "source": filename, "chunk_index": i},
            ))

    store.add_documents(docs)
    return store


def make_llm(store: EmbeddingStore):
    """Simple LLM that echoes the retrieved context as the answer."""
    def llm(prompt: str) -> str:
        ctx_start = len("Context:\n")
        ctx_end   = prompt.find("\n\nQuestion:")
        return prompt[ctx_start:ctx_end].strip()
    return llm


def parse_filter(raw: str | None) -> dict | None:
    if not raw:
        return None
    try:
        key, val = raw.split("=", 1)
        return {key.strip(): val.strip()}
    except ValueError:
        print(f"[warn] invalid filter '{raw}', expected key=value", file=sys.stderr)
        return None


def run(top_k: int, meta_filter: dict | None) -> None:
    print("Building store...", end=" ", flush=True)
    store = build_store()
    print(f"{store.get_collection_size()} chunks indexed.")

    agent = KnowledgeBaseAgent(store=store, llm_fn=make_llm(store))

    filter_desc = f"  filter: {meta_filter}" if meta_filter else ""
    print(f"\nEmbedder : _mock_embed (hash-based)")
    print(f"Strategy : MarkdownSectionChunker(max_chunk_size=1000)")
    print(f"top_k    : {top_k}{filter_desc}")
    print("\nType your query and press Enter. Type 'exit' or Ctrl-C to quit.\n")

    SEP = "-" * 60

    while True:
        try:
            query = input("Query > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            break

        if not query:
            continue
        if query.lower() in {"exit", "quit", "q"}:
            print("Bye.")
            break

        if meta_filter:
            results = store.search_with_filter(query, top_k=top_k, metadata_filter=meta_filter)
        else:
            results = store.search(query, top_k=top_k)

        print(f"\n{SEP}")
        print(f"Top-{top_k} retrieved chunks:")
        for i, r in enumerate(results, 1):
            src     = r["metadata"].get("source", "?")
            score   = r["score"]
            preview = r["content"][:120].replace("\n", " ")
            print(f"  [{i}] score={score:+.4f}  {src}")
            print(f"       {preview}")

        print(f"\n{SEP}")
        answer = agent.answer(query, top_k=top_k) if not meta_filter else \
            "\n\n".join(r["content"] for r in results)
        print("Answer:\n")
        print(answer[:800])
        print(SEP + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Company Policies RAG demo")
    parser.add_argument("--top-k",  type=int,  default=3,    help="Number of chunks to retrieve (default: 3)")
    parser.add_argument("--filter", type=str,  default=None, help="Metadata filter as key=value (e.g. category=compensation)")
    args = parser.parse_args()

    run(top_k=args.top_k, meta_filter=parse_filter(args.filter))


if __name__ == "__main__":
    main()
