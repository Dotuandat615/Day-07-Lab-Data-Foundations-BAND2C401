# Phase 1 Implementation Plan

This document outlines the proposed changes to complete the "Phase 1 - Cá Nhân" requirements of the lab, modifying `src/chunking.py`, `src/store.py`, and `src/agent.py`.

## User Review Required
Please review the proposed implementation for the chunking logic and the `EmbeddingStore` functionality.
> [!IMPORTANT]
> Since the project operates with an optional ChromaDB, the `EmbeddingStore` will maintain an in-memory `_store` list alongside `ChromaDB` (if installed) to ensure tests pass in all environments. The fallback mechanism will seamlessly switch to the in-memory list if Chroma isn't available.

## Proposed Changes

---

### `src/chunking.py`
This component will be updated to implement sentence chunking, recursive chunking, and similarity computation.

#### [MODIFY] [chunking.py](file:///d:/Study/VinUni-Ai-Thuc-Chien/Ngày%207/Day-07-Lab-Data-Foundations-BAND2C401/src/chunking.py)
- **`SentenceChunker.chunk`**: Will use regular expressions to split sentences at `. `, `! `, `? `, or `.\n`, and group them into chunks of `max_sentences_per_chunk`.
- **`RecursiveChunker._split` & `.chunk`**: Will iterate through separators recursively. If a segment exceeds `chunk_size`, it will split it further using the next separator. Empty separators `""` will force character-level division up to `chunk_size`.
- **`compute_similarity`**: Will implement the cosine similarity mathematical formula: `dot(a, b) / (||a|| * ||b||)` using the existing `_dot` helper.
- **`ChunkingStrategyComparator.compare`**: Will run the `FixedSizeChunker`, `SentenceChunker`, and `RecursiveChunker` on the input text and compile a dictionary detailing the `count`, `avg_length`, and the `chunks` themselves for each strategy.

---

### `src/store.py`
This component will manage the vector knowledge base using an in-memory store and/or ChromaDB.

#### [MODIFY] [store.py](file:///d:/Study/VinUni-Ai-Thuc-Chien/Ngày%207/Day-07-Lab-Data-Foundations-BAND2C401/src/store.py)
- **`__init__`**: Initialize `chromadb.Client` and `create_collection` if the library is importable.
- **`_make_record`**: Convert a `Document` into a dictionary containing `id`, `content`, `embedding`, and `metadata`. Ensures `doc_id` is embedded in the metadata.
- **`add_documents`**: Loops through the documents, computes embeddings, appends them to the in-memory `_store` and also updates the Chroma collection if active.
- **`_search_records`**: Computes similarity scores for the provided query against all given records and sorts them descending.
- **`search`**: Delegates to `_search_records` passing the complete `_store`.
- **`search_with_filter`**: Pre-filters `_store` records matching `metadata_filter` dict keys/values, then delegates to `_search_records`.
- **`delete_document`**: Removes records whose `metadata['doc_id'] == doc_id` from both the in-memory `_store` and ChromaDB collection.
- **`get_collection_size`**: Returns the `len()` of the in-memory `_store`.

---

### `src/agent.py`
This component implements the RAG pattern to answer questions.

#### [MODIFY] [agent.py](file:///d:/Study/VinUni-Ai-Thuc-Chien/Ngày%207/Day-07-Lab-Data-Foundations-BAND2C401/src/agent.py)
- **`__init__`**: Save `store` and `llm_fn` as instance variables.
- **`answer`**: Retrieve `top_k` documents from the vector `store` using `search(question)`. Combine their contents into a context string, create a prompt, and pass it to `llm_fn`.

## Verification Plan

### Automated Tests
I will execute the test suite to verify all implementations meet the requirements:
- `pytest tests/ -v`

### Manual Verification
No manual verification is strictly necessary if the automated tests successfully pass. All core logic handles the provided cases correctly.
