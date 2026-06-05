from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb

            # Client ephemeral (in-memory). Tạo collection mới, tránh dính dữ liệu cũ.
            self._client = chromadb.Client()
            try:
                self._client.delete_collection(collection_name)
            except Exception:
                pass
            self._collection = self._client.create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            # Không có chroma hoặc lỗi khởi tạo -> dùng in-memory.
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        # Mỗi document = 1 record. Lưu kèm doc_id trong metadata để filter/delete.
        record_id = f"{doc.id}__{self._next_index}"
        self._next_index += 1
        return {
            "id": record_id,
            "doc_id": doc.id,
            "content": doc.content,
            "embedding": self._embedding_fn(doc.content),
            "metadata": {**doc.metadata, "doc_id": doc.id},
        }

    def _search_records(
        self, query: str, records: list[dict[str, Any]], top_k: int
    ) -> list[dict[str, Any]]:
        # Embed query 1 lần, chấm điểm dot product với từng record.
        # Mock/local embeddings đã normalize nên dot product == cosine similarity.
        query_vec = self._embedding_fn(query)
        scored = [
            {
                "id": rec["id"],
                "doc_id": rec["doc_id"],
                "content": rec["content"],
                "metadata": rec["metadata"],
                "score": _dot(query_vec, rec["embedding"]),
            }
            for rec in records
        ]
        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        for doc in docs:
            record = self._make_record(doc)
            self._store.append(record)
            if self._use_chroma and self._collection is not None:
                self._collection.add(
                    ids=[record["id"]],
                    documents=[record["content"]],
                    embeddings=[record["embedding"]],
                    metadatas=[record["metadata"]],
                )

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(
        self, query: str, top_k: int = 3, metadata_filter: dict = None
    ) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if metadata_filter:
            records = [
                rec
                for rec in self._store
                if all(rec["metadata"].get(k) == v for k, v in metadata_filter.items())
            ]
        else:
            records = self._store
        return self._search_records(query, records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        to_remove = [rec for rec in self._store if rec["doc_id"] == doc_id]
        if not to_remove:
            return False

        self._store = [rec for rec in self._store if rec["doc_id"] != doc_id]
        if self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(ids=[rec["id"] for rec in to_remove])
            except Exception:
                pass
        return True