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
| 1 | Working Remotely.md | Handbook nội bộ Clef | ~6,955 | `{"category": "work_arrangements", "target_audience": "all_employees", "document_type": "policy"}` |
| 2 | Vacation and Sick Leave.md | Handbook nội bộ Clef | ~993 | `{"category": "benefits", "target_audience": "all_employees", "document_type": "policy"}` |
| 3 | New Parent Leave.md | Handbook nội bộ Clef | ~1,513 | `{"category": "benefits", "target_audience": "parents", "document_type": "policy"}` |
| 4 | Salary and Equity Compensation.md | Handbook nội bộ Clef | ~3,134 | `{"category": "compensation", "target_audience": "all_employees", "document_type": "policy"}` |
| 5 | Code of Conduct in the Community.md | Handbook nội bộ Clef | ~2,166 | `{"category": "conduct", "target_audience": "all_employees", "document_type": "guidelines"}` |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| `category` | String | `"benefits"`, `"conduct"`, `"compensation"` | Cho phép lọc chính xác nhóm chính sách liên quan, tránh nhiễu từ các chính sách khác. |
| `target_audience` | String | `"all_employees"`, `"parents"`, `"remote_workers"` | Giúp giới hạn kết quả chỉ lấy chính sách áp dụng đúng đối tượng người hỏi (ví dụ: cha mẹ, nhân viên remote). |
| `document_type` | String | `"policy"`, `"guidelines"`, `"faq"` | Hỗ trợ lọc theo tính chất pháp lý hoặc định dạng tài liệu mà người dùng muốn tra cứu. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare(text, chunk_size=500)` trên 3 tài liệu đại diện:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| Working Remotely (6860c) | `fixed_size` | 16 | 476 | Không — cắt ngang bullet list và section |
| Working Remotely (6860c) | `by_sentences` | 14 | 484 | Một phần — bullet là fragment, không phải câu hoàn chỉnh |
| Working Remotely (6860c) | `recursive` | 19 | 359 | Một phần — chunk nhỏ, đôi khi chia vụn ý |
| Salary & Equity (3084c) | `fixed_size` | 7 | 483 | Không — cắt ngang bảng HTML lương |
| Salary & Equity (3084c) | `by_sentences` | 7 | 435 | Một phần |
| Salary & Equity (3084c) | `recursive` | 9 | 341 | Một phần |
| Vacation & Sick Leave (984c) | `fixed_size` | 3 | 361 | Một phần — tài liệu ngắn bị chia không cần thiết |
| Vacation & Sick Leave (984c) | `by_sentences` | 2 | 487 | Có |
| Vacation & Sick Leave (984c) | `recursive` | 2 | 491 | Có |

**Nhận xét baseline:** `fixed_size` cho kết quả tệ nhất với tài liệu có cấu trúc (cắt ngang section/table). `by_sentences` tốt hơn với tài liệu ngắn flat, nhưng gặp vấn đề với bullet list. `recursive` chunk quá nhỏ (avg 341–359c) làm mất coherence ngữ nghĩa của từng policy section.

### Strategy Của Tôi

**Loại:** MarkdownSectionChunker (custom — mới implement)

**Mô tả cách hoạt động:**

`MarkdownSectionChunker` dùng regex `(?m)^(?=#{1,3}\s)` để split text tại mỗi dòng bắt đầu bằng `#`, `##`, hoặc `###`, giữ nguyên header trong chunk. Nếu một section vượt quá `max_chunk_size=1000`, nó tiếp tục chia theo paragraph (`\n\n`). Không dùng sliding window cứng — mỗi chunk tương ứng đúng một mục chính sách.

**Tại sao tôi chọn strategy này cho domain nhóm?**

Tài liệu Company Policies có cấu trúc Markdown rõ ràng: *Working Remotely* có 8 subsection (`## Scope`, `## Approach`, `### Extended Remote Work`...), mỗi subsection trả lời một câu hỏi nhân viên cụ thể. `MarkdownSectionChunker` khai thác cấu trúc này để tạo chunk ngữ nghĩa — query "Do I need manager approval?" sẽ match đúng section `### Extended Remote Work > Get Approval` thay vì một cửa sổ ký tự ngẫu nhiên.

**Code snippet:**
```python
from src import MarkdownSectionChunker
chunker = MarkdownSectionChunker(max_chunk_size=1000)
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|--------------------|
| Working Remotely | `by_sentences` (best baseline) | 14 | 484 | Một phần |
| Working Remotely | **MarkdownSectionChunker** | **11** | **620** | **Có — mỗi chunk = 1 section policy** |
| Salary & Equity | `by_sentences` (best baseline) | 7 | 435 | Một phần |
| Salary & Equity | **MarkdownSectionChunker** | **4** | **769** | **Có — tách Salary vs Equity rõ ràng** |
| Vacation & Sick | `recursive` (best baseline) | 2 | 491 | Có |
| Vacation & Sick | **MarkdownSectionChunker** | **1** | **983** | Kém — doc flat, 1 chunk duy nhất không retrieve được |

**Nhận xét:** `MarkdownSectionChunker` vượt trội trên tài liệu có headers (`##`/`###`). Điểm yếu là tài liệu flat như *Vacation & Sick Leave* chỉ cho 1 chunk — dùng `ParagraphMergeChunker` cho loại này sẽ tốt hơn.

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

**Setup:** `MarkdownSectionChunker(max_chunk_size=1000)` · `EmbeddingStore` (in-memory) · `_mock_embed` · 21 chunks từ 5 tài liệu.

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer | Chunk nguồn |
|---|-------|-------------|-------------|
| 1 | Tôi có thể làm việc từ xa bao lâu thì cần xin phép quản lý? | Bất kỳ đợt làm việc từ xa nào kéo dài hơn 2 ngày hoặc ở địa điểm bất thường đều cần phê duyệt của quản lý trước ít nhất 2 tuần. | Working Remotely — `### Extended Remote Work` |
| 2 | Mỗi tháng tôi tích lũy được bao nhiêu ngày phép năm? | Mỗi tháng làm việc tích lũy được 1.25 ngày phép (tổng 15 ngày/năm). | Vacation and Sick Leave — chunk duy nhất |
| 3 | Chính sách nghỉ thai sản hoặc nhận con nuôi là bao lâu? | 12 tuần nghỉ phép có lương, áp dụng trong vòng 1 năm đầu sau khi sinh/nhận con nuôi. | New Parent Leave — chunk 0 |
| 4 | Mức lương cho nhân viên kỹ thuật có dưới 5 năm kinh nghiệm là bao nhiêu? | Nhân viên Technical < 5 năm kinh nghiệm nhận $100k/năm. | Salary & Equity — chunk chứa bảng lương HTML |
| 5 | Tôi nên liên hệ với ai nếu phát hiện có hành vi quấy rối? | Liên hệ ngay B (b@getclef.com) hoặc một trong các founders khác. | Code of Conduct — chunk 3 (reporting) |

### Kết Quả Của Tôi

> **Embedder:** `_mock_embed` (hash-based, không phản ánh ngữ nghĩa). Queries bằng tiếng Việt, documents bằng tiếng Anh — đây là điều kiện thực tế nhất để quan sát failure modes.

| # | Query (rút gọn) | Top-1 Chunk | Score | Relevant trong top-3? | Agent Answer (tóm tắt) |
|---|----------------|-------------|-------|----------------------|------------------------|
| 1 | Xin phép WFH bao lâu? | Vacation and Sick Leave (sai doc) | 0.2626 | ❌ Không | Echo Vacation doc — sai hoàn toàn |
| 2 | Tích lũy bao nhiêu ngày phép/tháng? | Code of Conduct (sai doc) | 0.1950 | ❌ Không | Echo Code of Conduct — sai hoàn toàn |
| 3 | New Parent Leave bao lâu? *(filter: parents)* | New Parent Leave chunk 1 (accrual) | -0.0678 | ✅ Top-2 có (12 weeks chunk) | Echo chunk accrual — thiếu thông tin chính |
| 4 | Lương Technical <5yr? *(filter: compensation)* | Equity vesting chunk (sai) | 0.1714 | ✅ Top-3 có (salary table chunk) | Echo equity info — không trả lời câu hỏi |
| 5 | Liên hệ ai khi bị quấy rối? *(filter: conduct)* | Code of Conduct scope chunk | 0.1042 | ✅ Top-3 có (reporting chunk) | Echo scope — thiếu tên liên hệ |

**Bao nhiêu queries trả về chunk relevant trong top-3? 3 / 5**

### Phân Tích Kết Quả

**2 queries thất bại hoàn toàn (Q1, Q2):** `_mock_embed` dùng MD5 hash — query tiếng Việt không có quan hệ vector nào với document tiếng Anh. Score cao nhất (0.26) rơi vào doc sai. Đây là failure mode dự đoán được khi dùng mock embedder với cross-lingual queries.

**3 queries có relevant chunk trong top-3 (Q3–Q5):** Nhờ `metadata_filter` — filter trước giảm search space xuống 2–4 chunks thay vì 21, nên dù similarity score không có nghĩa, vẫn tìm được đúng doc. Tuy nhiên chunk ordering sai (relevant ở top-2 hoặc top-3 thay vì top-1) làm agent answer thiếu chính xác.

**Kết luận:** Với semantic embedder thực (LocalEmbedder/OpenAI), Q1 và Q2 sẽ pass vì query-document similarity sẽ có nghĩa. Metadata filter đã cứu Q3–Q5 — minh chứng rõ ràng cho Metadata Utility.

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
