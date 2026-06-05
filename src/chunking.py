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
            chunk = text[start: start + self.chunk_size]
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

    _SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sentences = [s.strip() for s in self._SENTENCE_BOUNDARY.split(text.strip())]
        sentences = [s for s in sentences if s]

        chunks: list[str] = []
        step = self.max_sentences_per_chunk

        for i in range(0, len(sentences), step):
            group = sentences[i: i + step]
            chunks.append(" ".join(group).strip())

        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]

    Idea:
        - Try coarse separators first: paragraph -> line -> sentence -> word -> character.
        - If a piece is still too long, recursively split it with a finer separator.
        - Finally merge small pieces until close to chunk_size to avoid tiny chunks.
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        pieces = self._split(text, self.separators)
        return self._merge(pieces)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text] if current_text else []

        if not remaining_separators or remaining_separators[0] == "":
            return [
                current_text[i: i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
                if current_text[i: i + self.chunk_size]
            ]

        sep = remaining_separators[0]
        rest = remaining_separators[1:]

        pieces: list[str] = []

        for part in current_text.split(sep):
            if not part:
                continue

            if len(part) <= self.chunk_size:
                pieces.append(part)
            else:
                pieces.extend(self._split(part, rest))

        return pieces

    def _merge(self, pieces: list[str]) -> list[str]:
        if not pieces:
            return []

        merged: list[str] = []
        buffer = ""

        for piece in pieces:
            candidate = piece if not buffer else f"{buffer} {piece}"

            if len(candidate) <= self.chunk_size:
                buffer = candidate
            else:
                if buffer:
                    merged.append(buffer)
                buffer = piece

        if buffer:
            merged.append(buffer)

        return merged


class PolicySectionChunker:
    """
    Custom chunker for company policy documents in Markdown format.

    This strategy is designed for Employee Handbook / Company Policies.
    It splits documents by Markdown headings (#, ##, ###), and each chunk keeps:
        - document title
        - section heading
        - section body

    If a section is too long, it is split further by paragraphs while keeping overlap.
    """

    def __init__(self, max_chars: int = 1200, overlap_chars: int = 150) -> None:
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        lines = text.splitlines()

        document_title = ""
        current_heading = ""
        current_lines: list[str] = []
        chunks: list[str] = []

        for line in lines:
            heading_match = re.match(r"^(#{1,3})\s+(.*)", line.strip())

            if heading_match:
                if current_lines:
                    chunk_text = self._build_chunk(
                        document_title=document_title,
                        section_heading=current_heading,
                        body="\n".join(current_lines).strip(),
                    )
                    chunks.extend(self._split_long_chunk(chunk_text))

                heading_level = heading_match.group(1)
                heading_text = heading_match.group(2).strip()

                if heading_level == "#" and not document_title:
                    document_title = heading_text

                current_heading = line.strip()
                current_lines = []
            else:
                current_lines.append(line)

        if current_lines:
            chunk_text = self._build_chunk(
                document_title=document_title,
                section_heading=current_heading,
                body="\n".join(current_lines).strip(),
            )
            chunks.extend(self._split_long_chunk(chunk_text))

        return [chunk for chunk in chunks if chunk.strip()]

    def _build_chunk(self, document_title: str, section_heading: str, body: str) -> str:
        parts: list[str] = []

        if document_title:
            parts.append(f"Document: {document_title}")

        if section_heading:
            parts.append(f"Section: {section_heading}")

        if body:
            parts.append(body)

        return "\n\n".join(parts)

    def _split_long_chunk(self, chunk: str) -> list[str]:
        if len(chunk) <= self.max_chars:
            return [chunk]

        paragraphs = re.split(r"\n\s*\n", chunk)
        result: list[str] = []
        current = ""

        for paragraph in paragraphs:
            if len(current) + len(paragraph) + 2 <= self.max_chars:
                current = current + "\n\n" + paragraph if current else paragraph
            else:
                if current:
                    result.append(current.strip())

                if self.overlap_chars > 0 and result:
                    overlap = result[-1][-self.overlap_chars:]
                    current = overlap + "\n\n" + paragraph
                else:
                    current = paragraph

        if current:
            result.append(current.strip())

        return result


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
    """
    Run chunking strategies and compare their results.

    Built-in strategies:
        - fixed_size
        - by_sentences
        - recursive

    Custom strategy:
        - policy_section
    """

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size).chunk(text),
            "by_sentences": SentenceChunker().chunk(text),
            "recursive": RecursiveChunker(chunk_size=chunk_size).chunk(text),
            "policy_section": PolicySectionChunker(max_chars=chunk_size * 6).chunk(text),
        }

        comparison: dict = {}

        for name, chunks in strategies.items():
            count = len(chunks)
            avg_length = (sum(len(c) for c in chunks) / count) if count else 0.0

            comparison[name] = {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks,
            }

        return comparison