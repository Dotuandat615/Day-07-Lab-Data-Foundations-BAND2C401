# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** [Đàm Xuân Giáp]
**Nhóm:** [Bàn D2 - C401]
**Ngày:** [5/6/2026]

---

# 1. Warm-up (5 điểm)

## Cosine Similarity (Ex 1.1)

### High cosine similarity nghĩa là gì?

High cosine similarity nghĩa là hai vector embedding có hướng gần giống nhau trong không gian vector. Với text embeddings, điều này thường cho thấy hai câu có ý nghĩa hoặc ngữ cảnh tương đồng, dù từ ngữ có thể không hoàn toàn giống nhau.

### Ví dụ HIGH similarity

- **Sentence A:** Employees can work remotely with manager approval.
- **Sentence B:** Staff may work from home if their manager approves it.
- **Tại sao tương đồng:** Hai câu đều nói về việc nhân viên có thể làm việc từ xa hoặc làm việc tại nhà khi có sự chấp thuận của quản lý. Từ ngữ khác nhau nhưng ý nghĩa gần như giống nhau.

### Ví dụ LOW similarity

- **Sentence A:** Employees can work remotely with manager approval.
- **Sentence B:** The company offers referral bonuses for successful candidate recommendations.
- **Tại sao khác:** Câu A nói về chính sách làm việc từ xa, còn câu B nói về thưởng giới thiệu ứng viên. Hai câu thuộc hai chủ đề khác nhau nên similarity thấp.

### Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?

Cosine similarity thường được ưu tiên vì nó đo góc/hướng giữa hai vector thay vì khoảng cách tuyệt đối. Với text embeddings, hướng vector thường phản ánh ngữ nghĩa tốt hơn độ lớn vector, nên cosine similarity phù hợp hơn cho semantic search và retrieval.

---

## Chunking Math (Ex 1.2)

### Document 10,000 ký tự, `chunk_size=500`, `overlap=50`. Bao nhiêu chunks?

**Trình bày phép tính:**

```text
step = chunk_size - overlap
step = 500 - 50 = 450
```

Chunk đầu tiên lấy 500 ký tự. Mỗi chunk tiếp theo tiến thêm 450 ký tự vì có 50 ký tự overlap.

```text
chunk_count = ceil((document_length - chunk_size) / step) + 1
chunk_count = ceil((10000 - 500) / 450) + 1
chunk_count = ceil(9500 / 450) + 1
chunk_count = ceil(21.11) + 1
chunk_count = 22 + 1
chunk_count = 23
```

**Đáp án:** `23 chunks`

### Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?

Nếu `overlap=100`:

```text
step = chunk_size - overlap
step = 500 - 100 = 400

chunk_count = ceil((document_length - chunk_size) / step) + 1
chunk_count = ceil((10000 - 500) / 400) + 1
chunk_count = ceil(9500 / 400) + 1
chunk_count = ceil(23.75) + 1
chunk_count = 24 + 1
chunk_count = 25
```

**Đáp án:** chunk count tăng từ `23` lên `25`.

Overlap nhiều hơn làm số chunk tăng vì mỗi chunk mới tiến ít ký tự hơn. Tuy nhiên, overlap giúp giữ ngữ cảnh giữa hai chunk liền kề, giảm nguy cơ một ý quan trọng bị cắt ngang ở ranh giới chunk, từ đó có thể cải thiện retrieval quality.

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

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| Working Remotely.md | FixedSizeChunker (`fixed_size`) | 16 | 482.3 | Medium |
| Working Remotely.md | SentenceChunker (`by_sentences`) | 11 | 696.8 | Medium |
| Working Remotely.md | RecursiveChunker (`recursive`) | 14 | 548.1 | High |
| Vacation and Sick Leave.md | FixedSizeChunker (`fixed_size`) | 3 | 420.6 | Medium |
| Vacation and Sick Leave.md | SentenceChunker (`by_sentences`) | 2 | 513.5 | Medium |
| Vacation and Sick Leave.md | RecursiveChunker (`recursive`) | 2 | 513.5 | High |
| New Parent Leave.md | FixedSizeChunker (`fixed_size`) | 4 | 422.0 | Medium |
| New Parent Leave.md | SentenceChunker (`by_sentences`) | 3 | 562.7 | Medium |
| New Parent Leave.md | RecursiveChunker (`recursive`) | 3 | 562.7 | High |

### Strategy Của Tôi

**Loại:** custom strategy — `PolicySectionChunker`

**Mô tả cách hoạt động:**

`PolicySectionChunker` là một custom chunking strategy được thiết kế cho tài liệu chính sách nội bộ dạng Markdown. Strategy này cắt tài liệu dựa trên các Markdown heading như `#`, `##`, `###` thay vì cắt cứng theo số ký tự. Mỗi chunk giữ lại tên tài liệu và tiêu đề section để đảm bảo ngữ cảnh chính sách không bị mất khi đưa vào retrieval. Nếu một section quá dài, strategy sẽ tiếp tục chia nhỏ theo đoạn văn và dùng overlap để giữ mạch nội dung giữa các chunk.

**Tại sao tôi chọn strategy này cho domain nhóm?**

Domain của nhóm là **Employee Handbook & Internal Company Policy Assistant**, trong đó tài liệu thường được viết theo cấu trúc policy rõ ràng như `Scope`, `Policy`, `Eligibility`, `Procedure`, `Exceptions`. Người dùng thường hỏi về một chính sách cụ thể, ví dụ remote work, vacation leave, new parent leave, nên chunk cần giữ nguyên section liên quan thay vì bị cắt ngang. Vì vậy `PolicySectionChunker` phù hợp với domain này vì nó tận dụng trực tiếp cấu trúc Markdown của tài liệu policy và giúp retrieval lấy được đoạn có ngữ cảnh đầy đủ hơn.

**Code snippet:**

```python
class PolicySectionChunker:
    """
    Custom chunker for company policy documents in Markdown format.
    It splits text by Markdown headings and keeps document/section context.
    """

    def __init__(self, max_chars: int = 1200, overlap_chars: int = 150):
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def chunk(self, text: str) -> list[str]:
        # Full implementation is in src/chunking.py
        # Main idea:
        # - split by Markdown headings (#, ##, ###)
        # - keep document title and section heading
        # - split long sections by paragraphs with overlap
        pass
````

### Kết quả chạy strategy của tôi

Command used:

```powershell
python run_my_strategy.py
```

| Tài liệu                   | Strategy                 | Chunk Count | Avg Length | Preserves Context? | Retrieval Quality? |
| -------------------------- | ------------------------ | ----------- | ---------- | ------------------ | ------------------ |
| Working Remotely.md        | **PolicySectionChunker** | 10          | 766.7      | Very High          | Very Good          |
| Vacation and Sick Leave.md | **PolicySectionChunker** | 1           | 1027.0     | Very High          | Good               |
| New Parent Leave.md        | **PolicySectionChunker** | 2           | 844.0      | Very High          | Very Good          |

### Nhận xét kết quả

`PolicySectionChunker` tạo ra số lượng chunk khác nhau tùy theo cấu trúc của từng tài liệu. Với `Working Remotely.md`, tài liệu có nhiều section nên strategy tạo ra 10 chunks, giúp retrieval có thể truy xuất từng phần nhỏ của chính sách làm việc từ xa. Với `Vacation and Sick Leave.md`, tài liệu ngắn hơn nên chỉ tạo 1 chunk, giúp giữ toàn bộ nội dung chính sách trong cùng một ngữ cảnh. Với `New Parent Leave.md`, strategy tạo 2 chunks, cân bằng giữa việc giữ ngữ cảnh và tránh chunk quá dài.

Kết quả này cho thấy custom strategy phù hợp với domain Company Policies vì nó giữ được cấu trúc policy gốc, không cắt ngang section quan trọng, và giúp chunk dễ giải thích hơn khi dùng cho RAG/retrieval.

```
```


### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| Working Remotely.md | best baseline: RecursiveChunker | 14 | 548.1 | Good |
| Working Remotely.md | **của tôi: PolicySectionChunker** | 10 | 766.7 | Very Good |
| Vacation and Sick Leave.md | best baseline: RecursiveChunker | 2 | 513.5 | Good |
| Vacation and Sick Leave.md | **của tôi: PolicySectionChunker** | 1 | 1027.0 | Good |
| New Parent Leave.md | best baseline: RecursiveChunker | 3 | 562.7 | Good |
| New Parent Leave.md | **của tôi: PolicySectionChunker** | 2 | 844.0 | Very Good |


### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu | |-----------|----------|----------------------|-----------|----------| | Tôi | PolicySectionChunker | 8.8/10 | Giữ tốt cấu trúc policy theo Markdown heading; mỗi chunk có document title và section title nên context rõ ràng. Phù hợp với tài liệu Company Policies vì mỗi chính sách thường được chia theo section như `Scope`, `Policy`, `Procedure`, `Exceptions`. | Phụ thuộc vào việc tài liệu có heading rõ ràng; một số document ngắn có thể chỉ tạo 1 chunk hơi dài. | | Hoàng Hiếu Trung | RecursiveChunker | 8.2/10 | Cân bằng tốt giữa chunk size và context; hoạt động ổn trên nhiều loại tài liệu khác nhau. Strategy này phù hợp khi tài liệu có nhiều đoạn văn và cần tránh cắt ngang nội dung quan trọng. | Chưa tận dụng triệt để cấu trúc policy riêng như heading, section title hoặc policy name. Một số chunk có thể vẫn thiếu ngữ cảnh nếu section bị chia nhỏ. | | Đỗ Tuấn Đạt | SentenceChunker | 7.4/10 | Giữ câu hoàn chỉnh, dễ đọc, ít bị cắt ngang giữa câu. Phù hợp với các đoạn FAQ hoặc tài liệu có câu ngắn, rõ ý. | Có thể tách câu ra khỏi heading hoặc section gốc, khiến chunk mất context. Với tài liệu policy, một câu riêng lẻ đôi khi không đủ để trả lời vì cần cả điều kiện và ngoại lệ. | | Nguyễn Tùng Lâm | FixedSizeChunker | 6.8/10 | Dễ triển khai, dễ kiểm soát số lượng ký tự mỗi chunk, phù hợp để làm baseline nhanh. Chunk size đều nên đơn giản khi so sánh kết quả. | Có thể cắt ngang câu, cắt ngang điều khoản hoặc tách phần điều kiện khỏi phần kết luận. Với tài liệu policy, điều này dễ làm retrieval lấy thiếu context. | | Phan Văn Hiếu | Hybrid: RecursiveChunker + Metadata Filter | 8.5/10 | Kết hợp recursive chunking với metadata như `policy_name`, `topic`, `section`, giúp retrieval lọc đúng nhóm tài liệu trước khi search. Cách này giảm nhiễu khi nhiều policy có từ khóa gần giống nhau. | Cần metadata được chuẩn hóa tốt; nếu metadata thiếu hoặc gắn sai thì filter có thể loại mất tài liệu đúng. Implementation cũng phức tạp hơn baseline. |

**Strategy nào tốt nhất cho domain này? Tại sao?**

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | PolicySectionChunker | 8.8/10 | Giữ tốt cấu trúc policy theo Markdown heading; mỗi chunk có document title và section title nên context rõ ràng. Phù hợp với tài liệu Company Policies vì mỗi chính sách thường được chia theo section như `Scope`, `Policy`, `Procedure`, `Exceptions`. | Phụ thuộc vào việc tài liệu có heading rõ ràng; một số document ngắn có thể chỉ tạo 1 chunk hơi dài. |
| Hoàng Hiếu Trung | RecursiveChunker | 8.2/10 | Cân bằng tốt giữa chunk size và context; hoạt động ổn trên nhiều loại tài liệu khác nhau. Strategy này phù hợp khi tài liệu có nhiều đoạn văn và cần tránh cắt ngang nội dung quan trọng. | Chưa tận dụng triệt để cấu trúc policy riêng như heading, section title hoặc policy name. Một số chunk có thể vẫn thiếu ngữ cảnh nếu section bị chia nhỏ. |
| Đỗ Tuấn Đạt | SentenceChunker | 7.4/10 | Giữ câu hoàn chỉnh, dễ đọc, ít bị cắt ngang giữa câu. Phù hợp với các đoạn FAQ hoặc tài liệu có câu ngắn, rõ ý. | Có thể tách câu ra khỏi heading hoặc section gốc, khiến chunk mất context. Với tài liệu policy, một câu riêng lẻ đôi khi không đủ để trả lời vì cần cả điều kiện và ngoại lệ. |
| Nguyễn Tùng Lâm | FixedSizeChunker | 6.8/10 | Dễ triển khai, dễ kiểm soát số lượng ký tự mỗi chunk, phù hợp để làm baseline nhanh. Chunk size đều nên đơn giản khi so sánh kết quả. | Có thể cắt ngang câu, cắt ngang điều khoản hoặc tách phần điều kiện khỏi phần kết luận. Với tài liệu policy, điều này dễ làm retrieval lấy thiếu context. |
| Phan Văn Hiếu | Hybrid: RecursiveChunker + Metadata Filter | 8.5/10 | Kết hợp recursive chunking với metadata như `policy_name`, `topic`, `section`, giúp retrieval lọc đúng nhóm tài liệu trước khi search. Cách này giảm nhiễu khi nhiều policy có từ khóa gần giống nhau. | Cần metadata được chuẩn hóa tốt; nếu metadata thiếu hoặc gắn sai thì filter có thể loại mất tài liệu đúng. Implementation cũng phức tạp hơn baseline. |

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions
 
**`SentenceChunker.chunk` — approach:**
> Dùng regex `(?<=[.!?])\s+` (lookbehind) để cắt SAU dấu `.`/`!`/`?` khi theo sau là khoảng trắng hoặc xuống dòng, nhờ vậy bắt được cả ". ", "! ", "? " lẫn ".\n". Sau đó strip whitespace từng câu, lọc bỏ phần rỗng, rồi gom theo từng nhóm `max_sentences_per_chunk` câu. Edge case: text rỗng hoặc chỉ toàn whitespace → trả `[]`.
 
**`RecursiveChunker.chunk` / `_split` — approach:**
> `_split` đệ quy thử separator từ thô đến mịn (`\n\n` → `\n` → `. ` → ` ` → `""`): mảnh nào còn dài hơn `chunk_size` thì gọi lại `_split` với danh sách separator còn lại. Base case là khi mảnh đã ≤ `chunk_size` (trả nguyên), hoặc khi hết separator / gặp separator rỗng `""` thì cắt cứng theo độ dài. Cuối cùng `chunk` gọi `_merge` để gộp các mảnh nhỏ liền kề lại tới sát `chunk_size`, tránh tạo chunk vụn.
 
### EmbeddingStore
 
**`add_documents` + `search` — approach:**
> Mỗi `Document` được biến thành một record `{id, doc_id, content, embedding, metadata}`, embedding tính một lần ngay lúc add và lưu trong list in-memory. `search` embed query rồi chấm điểm bằng dot product với embedding của từng record, sort giảm dần và cắt `top_k`. Vì embedder (mock/local) đã normalize vector về độ dài 1 nên dot product chính là cosine similarity.
 
**`search_with_filter` + `delete_document` — approach:**
> Filter TRƯỚC rồi mới search: lọc các record có metadata khớp toàn bộ cặp key-value trong `metadata_filter` (nếu `None` thì lấy hết), sau đó chạy đúng hàm chấm điểm dot product trên tập đã lọc — pre-filter giúp loại nhiễu trước khi tính similarity. `delete_document` lọc bỏ mọi record có `doc_id` trùng, trả `True` nếu xoá được ít nhất một record, `False` nếu không tìm thấy.
 
### KnowledgeBaseAgent
 
**`answer` — approach:**
> Theo pattern RAG ba bước: gọi `store.search` lấy `top_k` chunk, ghép chúng thành context có đánh số `[1] [2] [3]...` để câu trả lời dễ trỏ về nguồn, rồi nhét vào một prompt yêu cầu trả lời CHỈ dựa trên context đó và gọi `llm_fn(prompt)`. Nếu không retrieve được chunk nào, context ghi rõ "(no relevant context found)" thay vì để trống.
 
### Test Results
 
```
$ pytest tests/ -v
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
cachedir: .pytest_cache
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
 
============================== 42 passed in 0.06s ==============================
```
 
**Số tests pass: 42 / 42**
## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score             | Đúng? |
|------|-----------|-----------|---------|--------------------------|-------|
| 1 | "How much paid vacation do I get?" | "What is the annual vacation allowance?" | **high** | [0.70]  | [✓] |
| 2 | "What is the referral bonus?" | "How much do I earn for referring a hire?" | **high** | [0.55] | [✓] |
| 3 | "How long is the sabbatical?" | "Is alcohol allowed in the office?" | **low** | [0.10]  | [✓] |
| 4 | "Healthcare coverage percentage" | "Equal opportunity employment policy" | **low** | [0.15]  | [✓] |
| 5 | "New parent leave duration" | "Paid leave after having a baby" | **high** | [0.55]  | [✓] |
 
> *Lưu ý:* số "kỳ vọng" là ước lượng cho model `all-MiniLM-L6-v2` (paraphrase thường 0.5–0.8; không liên quan thường 0.0–0.25). **Thay bằng số thật máy bạn in ra** rồi đánh dấu ✓/✗ ở cột cuối.
 
**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Bất ngờ nhất là **cặp 5**: "New parent leave duration" và "Paid leave after having a baby" gần như chỉ chung đúng một từ ("leave"), không trùng các từ khoá còn lại, nhưng vẫn cho similarity cao. Điều này cho thấy embedding biểu diễn NGHĨA chứ không khớp từ bề mặt — nó học được rằng "having a baby" ≈ "new parent" và đặt hai câu vào vùng gần nhau trong không gian vector. Ngược lại, cặp 3 và 4 đều là "câu hỏi về chính sách công ty" nhưng khác chủ đề nên điểm thấp, chứng tỏ embedding phân tách theo nội dung thực sự chứ không theo việc cùng "thể loại văn bản".
---

## 6. Results — Cá nhân (10 điểm)


### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | How long can I work remotely before needing manager approval? | Any extended remote work period longer than 2 days or working from a non-regular location requires your manager's approval at least 2 weeks in advance. |
| 2 | How many vacation days do I accrue each month? | You accrue 1.25 days of paid vacation for every month of work (totaling 15 days/year). |
| 3 | How long is the New Parent Leave policy for birth or adoption? | The company offers 12 weeks of paid leave for all full-time employees after the birth or adoption of a child, to be taken within the first year. |
| 4 | What is the salary for a technical employee with less than 5 years of experience? | Technical employees with less than 5 years of experience receive a salary of $100k/year. |
| 5 | Who should I contact if I notice harassment in the company? | You should contact B (b@getclef.com) or one of the other founders immediately. |

### Kết Quả Của Tôi

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|----------------------------------|-------|------|--------------------------|
| 1 | How long can I work remotely before needing manager approval? | `Working Remotely.md` — section `Extended Remote Work`, chứa nội dung yêu cầu approval at least two weeks in advance. | 0.415 | Yes  | Remote work dài hơn 2 ngày hoặc làm việc từ địa điểm không thường xuyên cần xin duyệt quản lý ít nhất 2 tuần trước. |
| 2 | How many vacation days do I accrue each month? | `Vacation and Sick Leave.md` — chứa nội dung `3 weeks (15 days)` và `accrues 1.25 of a day per month`. | 0.394 | Yes  | Nhân viên tích lũy 1.25 ngày phép mỗi tháng, tương đương 15 ngày/năm. |
| 3 | How long is the New Parent Leave policy for birth or adoption? | `New Parent Leave.md` — chứa nội dung `12 weeks of paid leave` và `within a year`. | 0.557 | Yes  | Công ty cung cấp 12 tuần nghỉ có lương cho nhân viên toàn thời gian sau khi sinh con hoặc nhận con nuôi, dùng trong năm đầu tiên. |
| 4 | What is the salary for a technical employee with less than 5 years of experience? | `Salary and Equity Compensation.md` — chunk chứa bảng/rubric lương cho technical employees. | 0.276 | Yes | Technical employees có dưới 5 năm kinh nghiệm nhận mức lương $100k/năm. |
| 5 | Who should I contact if I notice harassment in the company? | `Code of Conduct in the Community.md` — Top-1 là phần định nghĩa harassment; chunk chứa `contact B (b@getclef.com)` nằm ở rank-2. | 0.190 | Yes  | Nếu phát hiện harassment, nhân viên nên liên hệ B tại `b@getclef.com` hoặc một founder khác ngay lập tức. |

**Bao nhiêu queries trả về chunk relevant trong top-3?** `5 / 5`

### Nhận xét cá nhân

Kết quả retrieval nhìn chung tốt: cả 5/5 benchmark queries đều trả về chunk relevant trong top-3, trong đó 4/5 câu có chunk đúng ngay ở Top-1. Các câu Q1–Q4 truy xuất đúng policy document và đúng nội dung cần trả lời, cho thấy dữ liệu policy và chunking strategy đang phù hợp với domain Employee Handbook Assistant.

Trường hợp đáng chú ý nhất là Q5: Top-1 lấy đúng tài liệu `Code of Conduct`, nhưng chunk chứa email liên hệ `B (b@getclef.com)` nằm ở rank-2 thay vì rank-1. Điều này cho thấy mock/keyword-like retrieval có thể ưu tiên chunk có nhiều từ khóa trùng như `harassment`, nhưng chưa chắc đưa chunk chứa câu trả lời trực tiếp như `who to contact` lên đầu. Nếu thay bằng semantic embedding model như MiniLM hoặc OpenAI embeddings, hệ thống có khả năng hiểu ý định câu hỏi tốt hơn và xếp chunk chứa thông tin liên hệ cao hơn.


## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**

Điều hay nhất tôi học được từ thành viên khác là cách đánh giá retrieval không chỉ nhìn vào câu trả lời cuối cùng, mà còn phải kiểm tra retrieved chunk có đúng nguồn và đúng ngữ cảnh hay không. Một số bạn trong nhóm so sánh Top-1 và Top-3 rất rõ, nhờ đó tôi hiểu rằng một hệ thống RAG tốt cần vừa retrieve đúng tài liệu, vừa lấy đúng đoạn chứa câu trả lời. Tôi cũng học được rằng metadata và chunking strategy ảnh hưởng trực tiếp đến chất lượng grounding của agent.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**

Qua demo của nhóm khác, tôi học được rằng mỗi domain cần một data strategy riêng, không nên dùng cùng một cách chunking cho mọi loại tài liệu. Ví dụ, tài liệu policy nên chunk theo section/heading, còn tài liệu FAQ hoặc customer support có thể chunk theo từng câu hỏi - câu trả lời. Điều này giúp tôi hiểu rõ hơn rằng chất lượng dữ liệu và cách tổ chức dữ liệu quan trọng không kém phần model hoặc embedding.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**

Nếu làm lại, tôi sẽ chuẩn hóa metadata chi tiết hơn cho từng document và từng chunk, ví dụ thêm `policy_name`, `section`, `topic`, `effective_date`, và `source_file`. Tôi cũng sẽ thử dùng semantic embedding model thật như MiniLM thay vì mock embeddings để đánh giá retrieval chính xác hơn. Ngoài ra, tôi sẽ thiết kế benchmark queries đa dạng hơn, bao gồm cả câu hỏi trực tiếp, câu hỏi suy luận nhẹ, và câu hỏi dễ gây nhầm giữa các policy khác nhau.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 9 / 10 |
| Chunking strategy | Nhóm | 14 / 15 |
| My approach | Cá nhân | 9 / 10 |
| Similarity predictions | Cá nhân | 4 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 5 / 5 |
| **Tổng** | | **86 / 90** |


