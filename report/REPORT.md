# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Phan Hieu
**Nhóm:** [Tên nhóm]
**Ngày:** 2026-06-05

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**

Hai đoạn text có high cosine similarity khi vector embedding của chúng tạo góc nhỏ trong không gian n chiều — nghĩa là chúng "hướng về" cùng một phía trong không gian ngữ nghĩa, bất kể độ dài văn bản.

**Ví dụ HIGH similarity:**
- Sentence A: "Python is a high-level programming language used for software development."
- Sentence B: "Python is a popular coding language widely used to build applications."
- Tại sao tương đồng: Cùng chủ đề (Python), cùng domain (lập trình), dùng các từ và khái niệm liên quan chặt chẽ.

**Ví dụ LOW similarity:**
- Sentence A: "I enjoy eating pizza on weekends."
- Sentence B: "The stock market experienced a sharp decline yesterday."
- Tại sao khác: Hai chủ đề hoàn toàn không liên quan — ẩm thực và tài chính — không có từ hay khái niệm chung.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**

Cosine similarity chỉ quan tâm đến góc giữa hai vector, không bị ảnh hưởng bởi magnitude — vì vậy một đoạn văn ngắn và dài nhưng cùng nội dung vẫn cho similarity cao. Euclidean distance sẽ phạt những vector có magnitude khác nhau, dẫn đến kết quả sai lệch khi so sánh văn bản ngắn với văn bản dài.

---

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

Dùng công thức: `num_chunks = ceil((doc_length - overlap) / (chunk_size - overlap))`

```
= ceil((10000 - 50) / (500 - 50))
= ceil(9950 / 450)
= ceil(22.11)
= 23 chunks
```

**Đáp án: 23 chunks**

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào?**

```
= ceil((10000 - 100) / (500 - 100))
= ceil(9900 / 400)
= ceil(24.75)
= 25 chunks
```

Tăng overlap từ 50 → 100 làm tăng chunk count từ 23 → 25, vì step size (`chunk_size - overlap`) giảm từ 450 xuống 400, cần nhiều bước hơn để phủ toàn bộ văn bản. Lợi ích: mỗi chunk chia sẻ nhiều context hơn với chunk liền kề, giảm nguy cơ mất thông tin tại ranh giới.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** [ví dụ: Customer support FAQ, Vietnamese law, cooking recipes, ...]

**Tại sao nhóm chọn domain này?**
> *[Điền sau khi nhóm thống nhất]*

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| | | | |
| | | | |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

*(Điền sau khi nhóm có bộ tài liệu chính thức)*

### Strategy Của Tôi

**Loại:** RecursiveChunker

**Mô tả cách hoạt động:**

RecursiveChunker thử tách văn bản theo danh sách separator theo thứ tự ưu tiên giảm dần: `["\n\n", "\n", ". ", " ", ""]`. Với mỗi separator, nó tích lũy các pieces vào chunk hiện tại chừng nào còn trong giới hạn `chunk_size`. Khi một piece đơn lẻ vượt quá `chunk_size`, nó tiếp tục đệ quy với separator tiếp theo trong danh sách. Khi hết separator, nó fallback về character split.

**Tại sao tôi chọn strategy này cho domain nhóm?**

RecursiveChunker tôn trọng cấu trúc tự nhiên của văn bản — chia theo paragraph trước, rồi mới theo câu, rồi mới theo từ. Điều này giúp mỗi chunk giữ được ý trọn vẹn thay vì cắt giữa câu như FixedSizeChunker. Với tài liệu kỹ thuật hoặc policy thường có cấu trúc section rõ ràng, strategy này khai thác được cấu trúc đó tốt hơn.

**Code snippet (nếu custom):**
```python
# Dùng RecursiveChunker built-in với chunk_size điều chỉnh theo domain
from src import RecursiveChunker
chunker = RecursiveChunker(chunk_size=400)  # ~2-3 câu mỗi chunk
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| | best baseline | | | |
| | **RecursiveChunker (của tôi)** | | | |

*(Điền sau khi chạy benchmark với bộ tài liệu nhóm)*

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi (Phan Hieu) | RecursiveChunker | | | |
| [Tên] | | | | |
| [Tên] | | | | |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> *[Điền sau khi so sánh trong nhóm]*

---

## 4. My Approach — Cá nhân (10 điểm)

### Chunking Functions

**`SentenceChunker.chunk`** — approach:

Dùng `re.split(r'\. |! |\? |\.\n', text)` để tách text thành các câu riêng lẻ theo đúng 4 delimiter mà docstring yêu cầu. Sau khi split, strip whitespace và lọc bỏ chuỗi rỗng để tránh "phantom sentences". Các câu được nhóm lại bằng vòng lặp với bước nhảy `max_sentences_per_chunk`, join bằng dấu cách.

**`RecursiveChunker.chunk` / `_split`** — approach:

`chunk()` là entry point đơn giản, delegate toàn bộ cho `_split(text, self.separators)`. `_split()` có hai base cases: (1) nếu `len(text) <= chunk_size` trả về `[text]` ngay; (2) nếu `remaining_separators` rỗng hoặc separator là `""`, thực hiện character split cố định. Recursive case: split text theo separator, tích lũy pieces vào `current_chunk`. Khi candidate vượt chunk_size: flush, nếu piece đơn lẻ cũng quá to thì gọi đệ quy `_split(piece, next_separators)`. Fallback `result if result else [current_text]` đảm bảo không bao giờ trả về list rỗng.

---

### EmbeddingStore

**`add_documents` + `search`** — approach:

`_make_record()` embed content bằng `embedding_fn`, copy metadata gốc và inject thêm `doc_id = doc.id` vào metadata để `delete_document()` có thể dùng sau. `add_documents()` loop qua từng doc, gọi `_make_record()`, append vào `self._store` (list of dicts). `_search_records()` embed query, tính dot product với từng stored embedding bằng helper `_dot()` có sẵn, sort descending và lấy top_k. `search()` delegate trực tiếp sang `_search_records(self._store, ...)`.

**`search_with_filter` + `delete_document`** — approach:

`search_with_filter()` dùng chiến lược **filter-first**: nếu có `metadata_filter`, dùng list comprehension với `all(record["metadata"].get(k) == v for k, v in filter.items())` để tạo `filtered` list trước, rồi mới gọi `_search_records()` trên tập nhỏ đó. Thiết kế này tránh lãng phí compute trên records không thỏa điều kiện. `delete_document()` rebuild `self._store` bằng list comprehension loại bỏ mọi record có `metadata["doc_id"] == doc_id`, trả về `True` nếu kích thước giảm.

---

### KnowledgeBaseAgent

**`answer`** — approach:

Gọi `self.store.search(question, top_k=top_k)` để retrieve, join content các chunks bằng `\n\n` thành `context`. Build prompt theo cấu trúc:

```
Context:
{context}

Question: {question}

Answer based on the context above:
```

Cấu trúc này đặt context trước câu hỏi để LLM ưu tiên ground answer vào retrieved text thay vì dùng knowledge nội tại (giảm hallucination). Gọi `self.llm_fn(prompt)` và trả về kết quả trực tiếp.

---

### Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.14.0, pytest-9.0.3, pluggy-1.6.0
rootdir: D:\HocLieu\VinAI\Day-07-Lab-Data-Foundations-BAND2C401
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED   [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.10s ==============================
```

**Số tests pass: 42 / 42**

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

> **Lưu ý:** Các scores dưới đây được tính bằng `_mock_embed` — một hash-based embedder
> (MD5 → LCG PRNG → normalized vector). Scores này **không phản ánh ngữ nghĩa thật**
> mà chỉ là pseudo-random. Để thấy semantic similarity thực sự cần dùng `LocalEmbedder`
> hoặc `OpenAIEmbedder`.

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Python is a programming language used for software development." | "Python is a popular coding language for building applications." | high | 0.2028 | Không (score thấp hơn kỳ vọng) |
| 2 | "Machine learning uses algorithms to learn patterns from data." | "Deep learning is a subset of machine learning using neural networks." | high | -0.0598 | Không |
| 3 | "I enjoy eating pizza on weekends." | "The stock market experienced a sharp decline yesterday." | low | -0.1721 | Có (âm = low) |
| 4 | "Vector databases store embeddings for similarity search." | "SQL databases store structured data in tables and rows." | medium | -0.0086 | Gần đúng (~0) |
| 5 | "Paris is the capital and largest city of France." | "France is a country located in Western Europe." | high | 0.0522 | Không |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**

Bất ngờ nhất là Pair 2 (machine learning vs deep learning) cho score âm (-0.06), dù hai câu chia sẻ từ khoá "learning" và cùng domain AI. Điều này xác nhận rằng `_mock_embed` hoàn toàn bỏ qua ngữ nghĩa — nó hash text thành vector ngẫu nhiên, nên similarity gần bằng 0 với mọi cặp câu. Để thấy semantic similarity thực sự (cặp semantically similar → score cao, cặp khác domain → score thấp), cần dùng embedder được trained trên ngôn ngữ như `all-MiniLM-L6-v2` hay `text-embedding-3-small`.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

*(Điền sau khi nhóm thống nhất 5 benchmark queries)*

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu queries trả về chunk relevant trong top-3?** __ / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> *[Điền sau khi so sánh trong nhóm]*

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *[Điền sau buổi demo]*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> *[Điền sau khi có kết quả benchmark]*

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | / 10 |
| Chunking strategy | Nhóm | / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | / 5 |
| **Tổng (phần cá nhân)** | | **50 / 60** |
