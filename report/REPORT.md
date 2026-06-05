# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Hoàng Hiếu Trung
**Nhóm:** BAND2C401
**Ngày:** 05/06/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Cosine similarity đo góc giữa hai vector embedding trong không gian nhiều chiều. Giá trị gần 1.0 có nghĩa là hai vector gần như cùng hướng — tức hai đoạn văn bản chia sẻ ý nghĩa ngữ nghĩa tương tự nhau, bất kể độ dài hay từ ngữ cụ thể.

**Ví dụ HIGH similarity:**
- Sentence A: "The company provides 15 days of paid annual leave."
- Sentence B: "Employees are entitled to 15 vacation days per year."
- Tại sao tương đồng: Cả hai câu nói về cùng một khái niệm (ngày nghỉ phép có lương), dùng từ khác nhau nhưng ý nghĩa giống nhau → embedding của chúng sẽ gần nhau trong không gian vector.

**Ví dụ LOW similarity:**
- Sentence A: "New parents receive 16 weeks of paid parental leave."
- Sentence B: "Dogs are loyal companions and working animals."
- Tại sao khác: Hai câu nói về chủ đề hoàn toàn khác nhau (chính sách HR vs. động vật), không có từ nào trùng nghĩa → embedding nằm ở các góc phần tư khác nhau trong không gian vector.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity chỉ quan tâm đến **hướng** của vector, không bị ảnh hưởng bởi độ dài văn bản. Hai đoạn văn — một ngắn, một dài — có thể nói cùng ý nhưng có độ lớn vector rất khác nhau; Euclidean distance sẽ phạt sự chênh lệch độ dài này, trong khi cosine similarity vẫn cho ra kết quả cao nếu hướng giống nhau.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính:
> - Công thức: `num_chunks = ceil((doc_length - overlap) / (chunk_size - overlap))`
> - `= ceil((10000 - 50) / (500 - 50))`
> - `= ceil(9950 / 450)`
> - `= ceil(22.11)`
> - **Đáp án: 23 chunks**

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> - Với overlap=100: `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75)` = **25 chunks** (tăng thêm 2).
> - Overlap nhiều hơn tạo ra nhiều chunk hơn nhưng mỗi chunk dùng lại nhiều nội dung từ chunk trước, giúp **bảo toàn ngữ cảnh qua ranh giới chunk** — quan trọng khi câu quan trọng bị cắt ở giữa hai chunk.

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
| `target_audience` | String | `"all_employees"`, `"parents"`, `"remote_workers"` | Giúp giới hạn kết quả chỉ lấy chính sách áp dụng đúng đối tượng người hỏi. |
| `document_type` | String | `"policy"`, `"guidelines"` | Hỗ trợ lọc theo tính chất pháp lý hoặc định dạng tài liệu mà người dùng muốn tra cứu. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu (chunk_size=200):

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| Working Remotely.md (6,955 chars) | FixedSizeChunker (`fixed_size`) | 35 | 196 | Trung bình — cắt theo ký tự, đôi khi cắt giữa câu |
| Working Remotely.md | SentenceChunker (`by_sentences`) | 14 | 487 | Tốt — giữ câu trọn vẹn, chunk dài hơn |
| Working Remotely.md | RecursiveChunker (`recursive`) | 54 | 125 | Khá — tôn trọng cấu trúc văn bản |
| Salary and Equity (3,084 chars) | FixedSizeChunker | 16 | 193 | Trung bình |
| Salary and Equity | SentenceChunker | 7 | 438 | Tốt |
| Salary and Equity | RecursiveChunker | 25 | 122 | Khá |
| Code of Conduct (2,153 chars) | FixedSizeChunker | 11 | 196 | Trung bình |
| Code of Conduct | SentenceChunker | 5 | 429 | Tốt |
| Code of Conduct | RecursiveChunker | 17 | 125 | Khá |

### Strategy Của Tôi

**Loại:** RecursiveChunker (chunk_size=300, separators=["\n\n", "\n", ". ", " ", ""])

**Mô tả cách hoạt động:**
> `RecursiveChunker` thử từng separator theo thứ tự ưu tiên: trước tiên tách theo đoạn văn (`\n\n`), nếu các mảnh vẫn quá lớn thì thử `\n`, rồi `". "`, rồi khoảng trắng, cuối cùng cắt từng ký tự. Ở mỗi bước, thuật toán gom các mảnh theo chiến lược greedy (tích lũy vào `current_chunk` cho đến khi vượt `chunk_size`) và đệ quy vào mảnh nào vẫn còn quá lớn. Kết quả là các chunk tôn trọng cấu trúc tự nhiên của văn bản — ưu tiên ranh giới đoạn văn trước, rồi mới cắt ở cấp câu hoặc từ nếu cần.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Tài liệu chính sách Clef được cấu trúc theo từng mục (heading + đoạn văn giải thích). `RecursiveChunker` tôn trọng cấu trúc đó: nó ưu tiên giữ nguyên từng đoạn văn (`\n\n` separator) trước khi cắt nhỏ hơn. Với `chunk_size=300`, mỗi chunk đủ ngắn để embedding tập trung vào một chủ đề duy nhất (ví dụ: chỉ nói về "parental leave duration" chứ không trộn với "vacation policy"), giúp vector search chính xác hơn so với `SentenceChunker` có chunk trung bình ~487 ký tự.

**Code snippet:**
```python
class RecursiveChunker:
    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators=None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, list(self.separators))

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text] if current_text else []
        if not remaining_separators:
            return [current_text[i:i+self.chunk_size]
                    for i in range(0, len(current_text), self.chunk_size)]
        separator = remaining_separators[0]
        next_seps = remaining_separators[1:]
        if separator == "":
            return [current_text[i:i+self.chunk_size]
                    for i in range(0, len(current_text), self.chunk_size)]
        parts = current_text.split(separator)
        results, current_chunk = [], ""
        for part in parts:
            if not part:
                continue
            candidate = current_chunk + (separator if current_chunk else "") + part
            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    results.append(current_chunk)
                if len(part) > self.chunk_size:
                    results.extend(self._split(part, next_seps))
                    current_chunk = ""
                else:
                    current_chunk = part
        if current_chunk:
            results.append(current_chunk)
        return results
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|-----------------|
| Working Remotely.md | FixedSizeChunker (baseline, size=200) | 35 | 196 | Trung bình — cắt giữa câu, mất ngữ cảnh |
| Working Remotely.md | **RecursiveChunker (của tôi, size=300)** | 36 | 187 | **Tốt hơn** — tôn trọng ranh giới đoạn văn, ít pha trộn chủ đề |
| Salary and Equity | FixedSizeChunker (baseline) | 16 | 193 | Trung bình |
| Salary and Equity | **RecursiveChunker (của tôi)** | 14 | 218 | **Tốt hơn** — chunk theo đoạn ngắn gọn |

**Nhận xét:** `RecursiveChunker(size=300)` tạo số lượng chunk tương đương `FixedSizeChunker(size=200)` nhưng chunk có cấu trúc hơn — ít cắt giữa câu hơn vì ưu tiên split ở `\n\n` và `\n` trước. Trade-off: nếu đoạn văn rất dài (như phần "Working Remotely" giải thích chi tiết), chunk vẫn phải bị cắt nhỏ hơn bằng separator cấp thấp hơn.

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi (Hoàng Hiếu Trung) | RecursiveChunker (size=300) | 7/10 | Tôn trọng cấu trúc đoạn văn, chunk tập trung 1 chủ đề | Đôi khi cắt giữa câu ở cấp ". " |
| [Thành viên 2] | SentenceChunker (3 câu/chunk) | 6/10 | Không bao giờ cắt giữa câu | Chunk dài → embedding pha loãng |
| [Thành viên 3] | FixedSizeChunker (size=300, overlap=50) | 5/10 | Chunk đều nhau, dễ kiểm soát | Cắt giữa câu, mất ngữ cảnh |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> `RecursiveChunker` phù hợp nhất với tài liệu policy của Clef vì các file được viết theo cấu trúc đoạn văn rõ ràng (mỗi đoạn là một chính sách hoặc điều khoản). Bằng cách ưu tiên tách ở `\n\n` trước, các chunk giữ nguyên từng điều khoản đầy đủ và tránh trộn thông tin từ hai chính sách khác nhau vào cùng một chunk. So với `SentenceChunker`, chunk ngắn hơn (~187 ký tự vs ~487 ký tự) giúp vector embedding tập trung hơn và retrieval precision cao hơn.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`RecursiveChunker.chunk` / `_split`** — approach (đây là strategy tôi chọn):
> Algorithm hoạt động theo kiểu divide-and-conquer với danh sách separator theo thứ tự ưu tiên: `["\n\n", "\n", ". ", " ", ""]`. Base case: nếu `len(text) <= chunk_size`, trả về `[text]` ngay. Recursive case: split text theo separator hiện tại, gom các mảnh theo chiến lược greedy — tích lũy vào `current_chunk` cho đến khi candidate vượt `chunk_size`, flush và tiếp tục. Nếu một mảnh riêng lẻ vẫn quá lớn, gọi đệ quy `_split(part, next_seps)`. Separator `""` là fallback cuối: cắt cứng theo ký tự. Cách tiếp cận này đảm bảo chunk luôn ≤ chunk_size trong phần lớn trường hợp, đồng thời tôn trọng cấu trúc tự nhiên (đoạn văn > dòng > câu > từ).

**`SentenceChunker.chunk`** — approach:
> Dùng `re.split(r'(?<=[.!?]) +|(?<=\.)\n', text)` để tách câu — regex này dùng lookbehind để tìm dấu câu kết thúc (`.!?`) theo sau bởi khoảng trắng hoặc newline. Sau khi tách, gom các câu thành nhóm theo `max_sentences_per_chunk` bằng vòng lặp bước nhảy. Edge case xử lý: text rỗng trả về `[]`, câu có khoảng trắng thừa được `strip()`.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> `add_documents` loop qua từng `Document`, gọi `_make_record` để embed content và đóng gói thành dict `{id, content, embedding, metadata}` (thêm `doc_id` vào metadata để hỗ trợ delete sau này), rồi append vào `self._store`. `search` embed query bằng cùng embedding function, tính dot-product với mọi stored embedding (dùng `_dot` helper), sort theo score giảm dần, trả top-k. Dùng dot-product thay vì cosine vì MockEmbedder đã normalize sẵn vector (unit vectors → dot-product = cosine).

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter` **filter trước** bằng list comprehension — chọn các records có tất cả metadata keys khớp với `metadata_filter` — rồi chạy `_search_records` trên subset đó. `delete_document` dùng list comprehension để xây lại `self._store` loại bỏ mọi record có `metadata['doc_id'] == doc_id`, trả `True` nếu list shrink (có xóa), `False` nếu không tìm thấy.

### KnowledgeBaseAgent

**`answer`** — approach:
> Bước 1: gọi `self.store.search(question, top_k=top_k)` để retrieve chunks. Bước 2: format context thành chuỗi `[1] chunk1\n\n[2] chunk2\n\n[3] chunk3` để LLM dễ tham chiếu. Bước 3: build system prompt rõ ràng — hướng dẫn LLM chỉ trả lời dựa trên context, không hallucinate. Inject question ở cuối. Gọi `self.llm_fn(prompt)` và trả về kết quả.

### Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
rootdir: D:\tai lieu gi do\VinUni\Group repo\Day-07-Lab-Data-Foundations-BAND2C401
plugins: anyio-4.9.0
collecting ... collected 42 items

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

============================= 42 passed in 0.08s ==============================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

*(Dùng `MockEmbedder` — deterministic hash-based embeddings, dim=64)*

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "The company allows employees to work from home." | "Remote work is permitted for all staff." | HIGH | -0.0773 | ❌ |
| 2 | "Employees get 15 days of paid vacation per year." | "Annual leave policy grants 15 days off." | HIGH | 0.2603 | ✅ |
| 3 | "Python is a high-level programming language." | "Machine learning uses neural networks." | MEDIUM | 0.0087 | ✅ |
| 4 | "New parents receive 16 weeks of paid parental leave." | "Dogs are loyal companions." | LOW | -0.1076 | ✅ |
| 5 | "Salary is reviewed annually based on performance." | "The capital of France is Paris." | LOW | -0.0203 | ✅ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Pair 1 bất ngờ nhất — hai câu đồng nghĩa hoàn toàn ("work from home" = "remote work") nhưng score lại âm (-0.0773). Điều này xảy ra vì `MockEmbedder` dùng hash MD5 để tạo vector ngẫu nhiên (không học được nghĩa từ dữ liệu) — khác hoàn toàn với embedder thật (như `all-MiniLM-L6-v2`) sẽ cho hai câu này score rất gần 1.0. Điều này nhắc nhở rằng chất lượng retrieval phụ thuộc **hoàn toàn** vào chất lượng embedding model; mock embedder chỉ dùng để test logic code, không phản ánh semantic similarity thực tế.

---

## 6. Results — Cá nhân (10 điểm)

*Chạy 5 benchmark queries trên 79 chunks từ 5 tài liệu Company Policies, dùng **RecursiveChunker(size=300)** + MockEmbedder.*

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer | Source |
|---|-------|-------------|--------|
| Q1 | How long can I work remotely before needing manager approval? | Any extended remote work period longer than 2 days or working from a non-regular location requires your manager's approval at least 2 weeks in advance. | Working Remotely.md |
| Q2 | How many vacation days do I accrue each month? | You accrue 1.25 days of paid vacation for every month of work (totaling 15 days/year). | Vacation and Sick Leave.md |
| Q3 | How long is the New Parent Leave policy for birth or adoption? | The company offers 12 weeks of paid leave for all full-time employees after the birth or adoption of a child, to be taken within the first year. | New Parent Leave.md |
| Q4 | What is the salary for a technical employee with less than 5 years of experience? | Technical employees with less than 5 years of experience receive a salary of $100k/year. | Salary and Equity Compensation.md |
| Q5 | Who should I contact if I notice harassment in the company? | You should contact B (b@getclef.com) or one of the other founders immediately. | Code of Conduct in the Community.md |

### Kết Quả Của Tôi

*Strategy: RecursiveChunker(chunk_size=300) · Tổng 79 chunks · MockEmbedder (dim=64)*

| # | Query | Top-1 Retrieved Chunk (summary) | Score | Relevant? | Agent Answer (summary) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| Q1 | Remote work — manager approval? | Working Remotely — "If you're planning to work remotely for more than two consecutive days..." | 0.2704 | **Yes** | MockLLM: Context contains relevant policy |
| Q2 | Vacation days accrued per month? | Working Remotely — "not shorter than a day at the office..." | 0.3408 | No | MockLLM: Insufficient context (wrong source) |
| Q3 | New Parent Leave duration? | Code of Conduct — "harassing behavior are expected to comply..." | 0.2836 | No | MockLLM: Insufficient context (wrong source) |
| Q4 | Salary for technical <5 yrs exp? | Salary and Equity Compensation — "The following policy will apply to compensation..." | 0.2433 | **Yes** | MockLLM: Context contains relevant policy |
| Q5 | Who to contact for harassment? | Working Remotely — "fast, consistent wi-fi connection..." | 0.2775 | No | MockLLM: Insufficient context (wrong source) |

**Bao nhiêu queries trả về chunk relevant trong top-3 (plain search)?** 2 / 5

**Với `search_with_filter` (metadata filter):** 5 / 5

### Failure Analysis

**Q1 — Hit! (plain top-1 correct)**
> English query "How long can I work remotely..." closely matches the Working Remotely.md wording. MockEmbedder hash of this query happened to score highest against the correct chunk: "If you're planning to work remotely for more than two consecutive days..." (score 0.2704). This is one of the two lucky plain-search hits.

**Q2 — Plain miss, filter hit**
> Top-1 is Working Remotely.md (score 0.3408). The correct chunk in Vacation.md ("accrues 1.25 of a day per month") is very short (~35 chars) and gets outscored by longer chunks with higher random hash similarity. With `category=benefits` filter (16 chunks), Vacation.md appears in top-3.

**Q4 — Hit! (plain top-1 correct)**
> English query "What is the salary for a technical employee..." directly matches Salary and Equity Compensation.md content (score 0.2433). The hash-based vector for this query happened to score highest on the correct document.

**Q3 & Q5 — Plain miss, filter hit**
> Both queries retrieve wrong files in plain search. Metadata filter (`category=benefits+parents` for Q3, `category=conduct` for Q5) narrows the search space, allowing the correct file to surface in top-3.

**Why does filter search achieve 5/5 while plain search only 2/5?**
> `search_with_filter` narrows the search space from 79 chunks down to 13–36 chunks per category. With MockEmbedder (random hash vectors), the probability of the correct chunk reaching top-3 in a smaller subset is much higher than in the full store. This demonstrates: **good metadata design compensates for poor embedding quality**.

**Conclusion:** With a real embedder (`all-MiniLM-L6-v2`), plain search top-3 hit is expected to reach ≥4/5 because English queries match English policy text semantically — RecursiveChunker's focused small chunks would produce sharper, more discriminative embeddings.

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Thành viên dùng `SentenceChunker` chỉ ra rằng dù chunk dài hơn (~487 ký tự), việc **không bao giờ cắt giữa câu** là lợi thế lớn với tài liệu policy — mỗi câu thường là một quy định độc lập. So sánh này giúp tôi hiểu rõ trade-off của RecursiveChunker: có thể cắt giữa câu khi separator cấp cao (`\n\n`, `\n`) không hạn chế được chunk_size, trong khi SentenceChunker luôn giữ toàn vẹn câu nhưng tạo chunk có thể quá dài cho embedding tập trung.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Một nhóm khác dùng metadata `language` để filter tài liệu tiếng Việt vs tiếng Anh riêng biệt trước khi search — giải pháp đơn giản nhưng hiệu quả cao cho corpus đa ngôn ngữ. Bài học: metadata filter là công cụ rất mạnh để tăng precision mà không cần thay đổi chunking strategy.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Tôi sẽ dùng `LocalEmbedder` (`all-MiniLM-L6-v2`) thay vì `MockEmbedder` để có kết quả retrieval thực tế. Ngoài ra, tôi sẽ thêm metadata `section_title` (tiêu đề phần trong tài liệu) để filter chính xác hơn — ví dụ, câu hỏi về "vacation" chỉ nên tìm trong section "Benefits", không phải toàn bộ handbook.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 9 / 10 |
| Chunking strategy | Nhóm | 13 / 15 |
| My approach | Cá nhân | 9 / 10 |
| Similarity predictions | Cá nhân | 4 / 5 |
| Results | Cá nhân | 6 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 4 / 5 |
| **Tổng** | | **80 / 100** |
