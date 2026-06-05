# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Đỗ Tuấn Đạt
**Nhóm:**  BAN D2, Class 401
**Ngày:** 6/5/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Hai text chunk có high cosine similarity nghĩa là vector embedding của chúng hướng về cùng một phía trong không gian nhiều chiều — tức là chúng chia sẻ nhiều ý nghĩa ngữ nghĩa tương đồng. Góc giữa hai vector càng nhỏ, cosine của góc đó càng gần 1.0, thể hiện mức độ tương đồng cao.

**Ví dụ HIGH similarity:**
- Sentence A: "The dog ran quickly across the field."
- Sentence B: "A dog sprinted fast through the park."
- Tại sao tương đồng: Cả hai câu cùng mô tả hành động của một con chó di chuyển nhanh ở ngoài trời — cùng chủ thể, hành động và ngữ cảnh → embedding nằm rất gần nhau trong vector space.

**Ví dụ LOW similarity:**
- Sentence A: "The quarterly revenue report shows a 15% increase."
- Sentence B: "Photosynthesis converts sunlight into chemical energy."
- Tại sao khác: Một câu thuộc lĩnh vực tài chính doanh nghiệp, câu kia thuộc sinh học thực vật — không có sự chia sẻ ngữ nghĩa nào → vector embedding hướng về hai chiều hoàn toàn khác nhau.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Euclidean distance bị ảnh hưởng bởi độ lớn (magnitude) của vector — tài liệu dài và ngắn về cùng chủ đề có thể bị coi là khác nhau chỉ vì độ dài văn bản. Cosine similarity chỉ đo góc giữa hai vector nên bất biến với độ dài tài liệu; hai văn bản cùng chủ đề sẽ có cosine similarity cao dù một bên là câu ngắn và bên kia là đoạn văn dài.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> - Công thức: `num_chunks = ceil((doc_length - overlap) / (chunk_size - overlap))`
> - Thay số: `num_chunks = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23`
>
> *Đáp án:* **23 chunks**

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> - Thay số: `num_chunks = ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25`
> - Chunk count **tăng từ 23 lên 25** vì step (= chunk_size − overlap) ngắn hơn, các chunk chồng lấp nhiều hơn. Overlap lớn hơn giúp đảm bảo thông tin nằm ở ranh giới hai chunk không bị mất — đặc biệt quan trọng khi một ý tưởng quan trọng vắt ngang qua biên giới của hai chunk liền kề.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Company Policies (Sách hướng dẫn nhân viên / Chính sách nhân sự của công ty Clef)

**Tại sao nhóm chọn domain này?**
> Domain này chứa các quy định, chính sách hoạt động của công ty (như giờ làm việc từ xa, nghỉ phép, bảo mật thông tin, ứng xử cộng đồng). Đây là tài liệu tối quan trọng cho nhân viên mới onboarding hoặc nhân viên hiện tại tra cứu nhanh. Việc áp dụng RAG giúp trả lời chính xác, tránh nhầm lẫn và giảm tải cho phòng HR.

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

Chạy `ChunkingStrategyComparator().compare()` trên 5 tài liệu (chunk_size=300):

| Tài liệu | Strategy | Chunk Count | Avg Length (chars) | Preserves Context? |
|-----------|----------|-------------|--------------------|--------------------|
| Working Remotely.md (6,860 chars) | `fixed_size` | 23 | 298.3 | ⚠️ Cắt giữa câu |
| Working Remotely.md | `by_sentences` | 14 | 487.2 | ✅ Giữ trọn câu |
| Working Remotely.md | `recursive` | 36 | 188.6 | ✅ Giữ theo đoạn |
| Vacation and Sick Leave.md (984 chars) | `fixed_size` | 4 | 246.0 | ⚠️ Cắt giữa câu |
| Vacation and Sick Leave.md | `by_sentences` | 2 | 489.5 | ✅ Giữ trọn câu |
| Vacation and Sick Leave.md | `recursive` | 7 | 139.0 | ✅ Giữ theo đoạn |
| New Parent Leave.md (1,503 chars) | `fixed_size` | 6 | 250.5 | ⚠️ Cắt giữa câu |
| New Parent Leave.md | `by_sentences` | 4 | 373.8 | ✅ Giữ trọn câu |
| New Parent Leave.md | `recursive` | 9 | 165.0 | ✅ Giữ theo đoạn |
| Salary and Equity Compensation.md (3,084 chars) | `fixed_size` | 11 | 280.4 | ⚠️ Cắt giữa câu |
| Salary and Equity Compensation.md | `by_sentences` | 7 | 438.1 | ✅ Giữ trọn câu |
| Salary and Equity Compensation.md | `recursive` | 14 | 218.4 | ✅ Giữ theo đoạn |
| Code of Conduct in the Community.md (2,153 chars) | `fixed_size` | 8 | 269.1 | ⚠️ Cắt giữa câu |
| Code of Conduct in the Community.md | `by_sentences` | 5 | 428.6 | ✅ Giữ trọn câu |
| Code of Conduct in the Community.md | `recursive` | 13 | 164.0 | ✅ Giữ theo đoạn |

### Strategy Của Tôi

**Loại:** SentenceChunker (`by_sentences`, max_sentences_per_chunk=3)

**Mô tả cách hoạt động:**
> `SentenceChunker` phát hiện ranh giới câu bằng regex `(?<=[.!?])\s+` (positive lookbehind sau dấu `.`, `!`, `?`), tách văn bản thành danh sách câu đơn lẻ mà không xóa dấu câu. Sau đó gom liên tiếp mỗi `max_sentences_per_chunk` câu thành một chunk bằng `" ".join(group)`. Kết quả là mỗi chunk luôn chứa trọn vẹn 1–3 câu hoàn chỉnh, không bao giờ cắt đứt giữa chừng một ý nghĩa. Edge case: văn bản rỗng → `[]`; text không có dấu câu → trả về toàn bộ text làm 1 chunk.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Các tài liệu Company Policies viết theo chuẩn văn bản pháp lý — mỗi câu thường chứa một điều khoản hoặc quy định độc lập có nghĩa đầy đủ. `SentenceChunker` phù hợp vì nó giữ nguyên tính toàn vẹn của từng điều khoản, tránh tình trạng câu bị cắt đôi làm mất ngữ cảnh pháp lý quan trọng. Khi người dùng hỏi về một quy định cụ thể, chunk trả về sẽ chứa trọn ý của quy định đó.

**Code snippet (built-in strategy — không cần custom):**
```python
from src.chunking import SentenceChunker

chunker = SentenceChunker(max_sentences_per_chunk=3)
chunks = chunker.chunk(document_text)
```

### So Sánh: SentenceChunker (tôi) vs FixedSizeChunker (baseline)

| Tài liệu | Strategy | Chunk Count | Avg Length (chars) | Nhận xét |
|-----------|----------|-------------|--------------------|-----------|
| Working Remotely.md | fixed_size (baseline) | 23 | 298.3 | Cắt ngẫu nhiên, có thể cắt đứt câu |
| Working Remotely.md | **SentenceChunker (tôi)** | **14** | **487.2** | Ít chunk hơn, mỗi chunk chứa 3 câu trọn vẹn |
| Vacation and Sick Leave.md | fixed_size (baseline) | 4 | 246.0 | Cắt ngẫu nhiên |
| Vacation and Sick Leave.md | **SentenceChunker (tôi)** | **2** | **489.5** | Doc ngắn → chỉ 2 chunk, coverage tốt |
| New Parent Leave.md | fixed_size (baseline) | 6 | 250.5 | Cắt ngẫu nhiên |
| New Parent Leave.md | **SentenceChunker (tôi)** | **4** | **373.8** | Giữ trọn điều khoản nghỉ phép |
| Salary and Equity Compensation.md | fixed_size (baseline) | 11 | 280.4 | Cắt ngẫu nhiên |
| Salary and Equity Compensation.md | **SentenceChunker (tôi)** | **7** | **438.1** | Giữ trọn quy định lương/equity |
| Code of Conduct in the Community.md | fixed_size (baseline) | 8 | 269.1 | Cắt ngẫu nhiên |
| Code of Conduct in the Community.md | **SentenceChunker (tôi)** | **5** | **428.6** | Giữ trọn từng quy tắc ứng xử |

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Tôi dùng regex `(?<=[.!?])\s+` (positive lookbehind) để tách văn bản thành các câu đơn lẻ — pattern này detect ranh giới câu sau dấu `.`, `!`, `?` mà không loại bỏ dấu câu khỏi câu gốc. Sau khi có danh sách câu, tôi group liên tiếp mỗi `max_sentences_per_chunk` câu lại thành một chunk bằng `" ".join(group)`. Edge case được xử lý: văn bản rỗng trả về `[]`; nếu regex không tách được gì (không có dấu câu), trả về toàn bộ text làm một chunk duy nhất.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Algorithm hoạt động theo kiểu **greedy merge + recurse**: với mỗi separator trong danh sách ưu tiên (`\n\n` → `\n` → `. ` → ` ` → char), tôi split text rồi merge các phần nhỏ vào `current_buffer` cho đến khi vượt `chunk_size`. Nếu một phần đơn lẻ vẫn vượt size, tôi gọi đệ quy `_split` với danh sách separator còn lại. Base case: text ngắn hơn `chunk_size` → trả về `[text]`; separator rỗng hoặc không match → force-split theo ký tự.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Với **in-memory store**, mỗi `Document` được embed thành vector bằng `embedding_fn`, sau đó lưu dưới dạng dict `{id, content, embedding, metadata}` trong `self._store`. Metadata được gắn thêm trường `doc_id` để hỗ trợ delete sau này. Khi `search`, tôi embed query thành vector rồi tính **dot product** với từng stored embedding (phương pháp tương đương cosine similarity vì `MockEmbedder` trả về unit vector đã chuẩn hóa), sort giảm dần và lấy top_k.

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter` thực hiện **filter trước, search sau**: lọc `self._store` chỉ giữ các record có metadata match toàn bộ key-value trong `metadata_filter`, rồi gọi `_search_records` trên tập đã lọc. Khi `metadata_filter=None` thì fallback về `search` thông thường trên toàn bộ store. `delete_document` dùng list comprehension để loại bỏ tất cả record có `metadata["doc_id"] == doc_id`; trả `True` nếu có ít nhất một record bị xóa, `False` nếu không tìm thấy.

### KnowledgeBaseAgent

**`answer`** — approach:
> RAG pipeline gồm 3 bước: **(1) Retrieve** — gọi `store.search(question, top_k=top_k)` để lấy các chunk liên quan nhất; **(2) Build prompt** — xây dựng prompt có cấu trúc với numbered context blocks (`[Context 1]`, `[Context 2]`, ...) kèm source metadata để LLM biết trích dẫn từ nguồn nào, phần `Question:` và `Answer:` rõ ràng ở cuối; **(3) Generate** — gọi `llm_fn(prompt)` và trả về kết quả. Nếu store rỗng, context block vẫn xuất hiện với thông báo "No relevant context found." để tránh crash.

### Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.12.6, pytest-9.0.3, pluggy-1.6.0
rootdir: F:\PYTHON\Day-07-Lab-Data-Foundations-BAND2C401

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
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
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

============================= 42 passed in 0.05s ==============================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "The dog ran quickly across the field." | "A dog sprinted fast through the park." | high | 0.2194 | ✅ Đúng hướng (cao nhất trong 5 cặp) |
| 2 | "Remote work requires a stable internet connection." | "Employees working from home need reliable Wi-Fi." | high | 0.1086 | ⚠️ Đúng hướng nhưng thấp hơn kỳ vọng |
| 3 | "Salary is paid on the last business day of each month." | "Photosynthesis converts sunlight into chemical energy." | low | 0.0746 | ✅ Đúng (thấp hơn các cặp cùng domain) |
| 4 | "Employees are entitled to paid sick leave." | "Workers can take time off when they are ill." | high | 0.1729 | ✅ Đúng hướng (cao thứ 2) |
| 5 | "The company prohibits discrimination based on race or gender." | "Equal opportunity employment is a core company value." | high | -0.0848 | ❌ Sai — score âm dù cùng chủ đề! |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> **Pair 5 bất ngờ nhất**: hai câu nói về cùng một chính sách (equal opportunity / chống phân biệt đối xử) nhưng lại cho score âm (−0.085). Lý do là `MockEmbedder` không phải embedding thật — nó dùng MD5 hash của văn bản để sinh **vector ngẫu nhiên có tính tất định (deterministic random)**, hoàn toàn không nắm bắt ngữ nghĩa. Điều này nhấn mạnh tầm quan trọng của embedding model thực sự (như `all-MiniLM-L6-v2` hay `text-embedding-3-small`): chỉ có semantic embedding thật mới có thể ánh xạ các câu cùng nghĩa về gần nhau trong vector space, còn hash-based mock chỉ dùng để test infrastructure, không phản ánh độ tương đồng ý nghĩa.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

> **Setup:** SentenceChunker (max_sentences=3), MockEmbedder (64-dim), 5 tài liệu Company Policies → 32 chunks tổng.

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | How long can I work remotely before needing manager approval? | Any extended remote work period longer than 2 days or working from a non-regular location requires your manager's approval at least 2 weeks in advance. |
| 2 | How many vacation days do I accrue each month? | You accrue 1.25 days of paid vacation for every month of work (totaling 15 days/year). |
| 3 | How long is the New Parent Leave policy for birth or adoption? | The company offers 12 weeks of paid leave for all full-time employees after the birth or adoption of a child, to be taken within the first year. |
| 4 | What is the salary for a technical employee with less than 5 years of experience? | Technical employees with less than 5 years of experience receive a salary of $100k/year. |
| 5 | Who should I contact if I notice harassment in the company? | You should contact B (b@getclef.com) or one of the other founders immediately. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Remote work — manager approval? | "...plan & prepare in your free time before you leave to work remotely..." (Working Remotely) | 0.3696 | ⚠️ Partial — đúng doc, sai đoạn cụ thể về 2-day rule | Dựa trên Working Remotely context |
| 2 | Vacation days per month? | "...salary goal is enough to not be a distraction..." (Salary Compensation) | 0.3650 | ❌ Sai — lấy nhầm doc Salary thay vì Vacation | Không liên quan đến câu hỏi |
| 3 | New Parent Leave duration? | "...give everyone on the team at least 7 days notice..." (Working Remotely) | 0.2541 | ❌ Sai — lấy nhầm Working Remotely thay vì New Parent Leave | Không liên quan đến câu hỏi |
| 4 | Salary < 5 years experience? | "...interpret remote work as a co-located employee of Clef..." (Working Remotely) | 0.3200 | ❌ Sai — lấy nhầm Working Remotely thay vì Salary doc | Không liên quan đến câu hỏi |
| 5 | Contact for harassment? | "...equity vests over 6 years with a 1 year cliff..." (Salary Compensation) | 0.2176 | ❌ Sai — lấy nhầm Salary doc thay vì Code of Conduct | Không liên quan đến câu hỏi |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 1 / 5

> **Nhận xét:** Kết quả thấp (1/5) hoàn toàn do `MockEmbedder` — nó sinh vector từ MD5 hash nên không nắm bắt ngữ nghĩa, dẫn đến retrieval ngẫu nhiên. Với real embedding model (như `all-MiniLM-L6-v2`), kết quả kỳ vọng đạt 4–5/5 vì các query và chunk cùng chủ đề sẽ có vector gần nhau thật sự.

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> *Viết 2-3 câu:*

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *Viết 2-3 câu:*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | / 5 |
| Document selection | Nhóm | / 10 |
| Chunking strategy | Nhóm | / 15 |
| My approach | Cá nhân | / 10 |
| Similarity predictions | Cá nhân | / 5 |
| Results | Cá nhân | / 10 |
| Core implementation (tests) | Cá nhân | / 30 |
| Demo | Nhóm | / 5 |
| **Tổng** | | **/ 100** |
