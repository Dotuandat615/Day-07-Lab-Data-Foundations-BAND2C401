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
        sentences = re.split(r'\. |! |\? |\.\n', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return [text.strip()] if text.strip() else []
        chunks = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            chunks.append(" ".join(group))
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
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators:
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        if separator == "":
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        parts = current_text.split(separator)
        result: list[str] = []
        current_chunk = ""

        for part in parts:
            if not part:
                continue
            candidate = (current_chunk + separator + part) if current_chunk else part
            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    result.append(current_chunk)
                    current_chunk = ""
                if len(part) <= self.chunk_size:
                    current_chunk = part
                else:
                    result.extend(self._split(part, next_separators))

        if current_chunk:
            result.append(current_chunk)

        return result if result else [current_text]


class MarkdownSectionChunker:
    """
    Split on markdown headers (## / ###), one policy section per chunk.
    Falls back to paragraph splitting for sections that exceed max_chunk_size.
    """

    def __init__(self, max_chunk_size: int = 1000) -> None:
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        sections = re.split(r'(?m)^(?=#{1,3}\s)', text)
        chunks = []
        for section in sections:
            section = section.strip()
            if not section:
                continue
            if len(section) <= self.max_chunk_size:
                chunks.append(section)
            else:
                paragraphs = section.split('\n\n')
                current = ""
                for para in paragraphs:
                    candidate = (current + "\n\n" + para).strip() if current else para.strip()
                    if len(candidate) <= self.max_chunk_size:
                        current = candidate
                    else:
                        if current:
                            chunks.append(current)
                        current = para.strip()
                if current:
                    chunks.append(current)
        return chunks if chunks else [text]


class ContextualChunker:
    """
    MarkdownSectionChunker that prepends '[doc_name — Section Name]' to every
    chunk so the LLM knows exactly which document and section it is reading.
    """

    def __init__(self, doc_name: str = "", max_chunk_size: int = 1000) -> None:
        self.doc_name = doc_name
        self._base = MarkdownSectionChunker(max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        base_chunks = self._base.chunk(text)
        result = []
        for c in base_chunks:
            header_match = re.match(r'^#{1,3}\s+(.+?)(?:\n|$)', c)
            section_name = header_match.group(1).strip() if header_match else ""
            if self.doc_name and section_name:
                prefix = f"[{self.doc_name} — {section_name}]\n\n"
            elif self.doc_name:
                prefix = f"[{self.doc_name}]\n\n"
            else:
                prefix = ""
            result.append(prefix + c)
        return result


class ParagraphMergeChunker:
    """
    Accumulate paragraphs (split on blank lines) up to target_size chars,
    with optional paragraph-level overlap between consecutive chunks.
    Better than RecursiveChunker for short docs with no markdown headers.
    """

    def __init__(self, target_size: int = 400, overlap_paragraphs: int = 1) -> None:
        self.target_size = target_size
        self.overlap_paragraphs = max(0, overlap_paragraphs)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if not paragraphs:
            return [text.strip()] if text.strip() else []

        chunks = []
        current_paras: list[str] = []

        for para in paragraphs:
            current_paras.append(para)
            if len('\n\n'.join(current_paras)) >= self.target_size:
                chunks.append('\n\n'.join(current_paras))
                current_paras = current_paras[-self.overlap_paragraphs:] if self.overlap_paragraphs else []

        if current_paras:
            last = '\n\n'.join(current_paras)
            if not chunks or last != chunks[-1]:
                chunks.append(last)

        return chunks


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
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size).chunk(text),
            "by_sentences": SentenceChunker().chunk(text),
            "recursive": RecursiveChunker(chunk_size=chunk_size).chunk(text),
        }
        result = {}
        for name, chunks in strategies.items():
            avg_len = sum(len(c) for c in chunks) / len(chunks) if chunks else 0.0
            result[name] = {
                "count": len(chunks),
                "avg_length": avg_len,
                "chunks": chunks,
            }
        return result
