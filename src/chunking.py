from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        # Split on sentence boundaries: ". ", "! ", "? " or ".\n"
        # Use a regex that keeps the delimiter attached to the preceding sentence
        raw_sentences = re.split(r'(?<=[.!?]) +|(?<=\.)\n', text)
        sentences = [s.strip() for s in raw_sentences if s.strip()]

        if not sentences:
            return []

        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            combined = " ".join(group).strip()
            if combined:
                chunks.append(combined)

        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        seps = list(self.separators)
        return self._split(text, seps)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Base case: text fits in one chunk
        if len(current_text) <= self.chunk_size:
            return [current_text] if current_text else []

        # No separators left — fall back to character-level slicing
        if not remaining_separators:
            chunks = []
            for i in range(0, len(current_text), self.chunk_size):
                piece = current_text[i : i + self.chunk_size]
                if piece:
                    chunks.append(piece)
            return chunks

        separator = remaining_separators[0]
        next_seps = remaining_separators[1:]

        # Empty-string separator: character-level split
        if separator == "":
            chunks = []
            for i in range(0, len(current_text), self.chunk_size):
                piece = current_text[i : i + self.chunk_size]
                if piece:
                    chunks.append(piece)
            return chunks

        # Split by current separator, then reassemble greedily
        parts = current_text.split(separator)
        results: list[str] = []
        current_chunk = ""

        for part in parts:
            if not part:
                continue
            # Try appending this part (with separator) to the running chunk
            candidate = current_chunk + (separator if current_chunk else "") + part
            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                # Flush the current accumulated chunk first
                if current_chunk:
                    results.append(current_chunk)
                # If the individual part is too big, recurse deeper
                if len(part) > self.chunk_size:
                    sub_chunks = self._split(part, next_seps)
                    results.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = part

        if current_chunk:
            results.append(current_chunk)

        return results


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    mag_a = math.sqrt(_dot(vec_a, vec_a))
    mag_b = math.sqrt(_dot(vec_b, vec_b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed_chunks = FixedSizeChunker(chunk_size=chunk_size, overlap=0).chunk(text)
        sentence_chunks = SentenceChunker(max_sentences_per_chunk=3).chunk(text)
        recursive_chunks = RecursiveChunker(chunk_size=chunk_size).chunk(text)

        def _stats(chunks: list[str]) -> dict:
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count > 0 else 0.0
            return {"count": count, "avg_length": avg_length, "chunks": chunks}

        return {
            "fixed_size": _stats(fixed_chunks),
            "by_sentences": _stats(sentence_chunks),
            "recursive": _stats(recursive_chunks),
        }
