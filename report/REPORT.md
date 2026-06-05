# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Tùng Lâm
**Nhóm:** [Tên nhóm]
**Ngày:** 5/6/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> *Viết 1-2 câu:*
Khi hai vector có độ tương đồng cosine cao, điều đó có nghĩa là hướng của chúng gần như trùng nhau. Trong không gian vector của các mô hình ngôn ngữ, hướng thường biểu thị cho ý nghĩa ngữ nghĩa (semantic meaning), do đó, high cosine similarity cho thấy hai đoạn văn bản có nội dung rất giống nhau.

**Ví dụ HIGH similarity:**
- Sentence A: "Việc học tiếng Anh mang lại cho tôi nhiều lợi ích trong công việc và cuộc sống."
- Sentence B: "Học tiếng Anh giúp tôi có nhiều cơ hội tốt hơn trong sự nghiệp và đời sống."
- Tại sao tương đồng: Cả hai câu đều nói về lợi ích của việc học tiếng Anh. 

**Ví dụ LOW similarity:**
- Sentence A: "Hôm nay trời rất đẹp, tôi quyết định ra công viên chơi." 
- Sentence B: "Món ăn này thật ngon, tôi rất thích ăn nó."
- Tại sao khác: 

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> *Viết 1-2 câu:*
Euclidean distance đo khoảng cách theo đường chim bay, nhạy cảm với độ lớn của vector. Trong khi đó, cosine similarity đo góc giữa các vector, chỉ quan tâm đến hướng (semantic meaning) và không bị ảnh hưởng bởi độ dài vector (document length), giúp nó phù hợp hơn cho việc so sánh sự tương đồng ngữ nghĩa của văn bản.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
Số chunk = (Tổng độ dài - Overlap) / (Chunk size - Overlap)

Số chunk = (10000 - 50) / (500 - 50) = 9950 / 450 ≈ 23 chunks

> *Đáp án:* 23 chunks

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> *Viết 1-2 câu:*
Việc tăng overlap giúp bảo toàn ngữ cảnh và ý nghĩa văn bản không bị đứt gãy tại các điểm cắt, từ đó cải thiện độ chính xác khi hệ thống AI truy xuất thông tin. Tuy nhiên, bạn chỉ nên giữ ở mức vừa đủ (khoảng 10-20%) vì overlap quá lớn sẽ tạo ra nhiều chunk dư thừa, dẫn đến lãng phí tài nguyên lưu trữ và chi phí xử lý API.
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

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| Working Remotely.md | FixedSizeChunker (`fixed_size`) | 15 | 476.0 | Không tốt lắm do cắt ngang câu, nhưng overlap gỡ lại một phần. |
| Working Remotely.md | SentenceChunker (`by_sentences`) | 14 | 487.2 | Tốt, bảo toàn được ý nghĩa từng câu trọn vẹn. |
| Working Remotely.md | RecursiveChunker (`recursive`) | 19 | 359.1 | Rất tốt, giữ được cấu trúc đoạn văn, không cắt giữa chừng. |
| Vacation and Sick Leave.md | FixedSizeChunker (`fixed_size`) | 3 | 341.3 | Cắt ngang câu/từ rủi ro làm đứt gãy thông tin. |
| Vacation and Sick Leave.md | SentenceChunker (`by_sentences`) | 2 | 489.5 | Tốt, bảo toàn ý nghĩa, dễ đọc. |
| Vacation and Sick Leave.md | RecursiveChunker (`recursive`) | 2 | 491.0 | Rất tốt, chia tách logic rõ ràng theo đoạn. |

### Strategy Của Tôi

**Loại:** FixedSizeChunker

**Mô tả cách hoạt động:**
> FixedSizeChunker chia văn bản thành các khối (chunk) có độ dài cố định theo số lượng ký tự (`chunk_size`). Thuật toán sử dụng phương pháp cửa sổ trượt (sliding window) với tham số `overlap` để đảm bảo có sự lặp lại một phần văn bản ở phần ranh giới giữa hai chunk liên tiếp. Điều này giúp tránh việc cắt đứt ngữ cảnh một cách đột ngột.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Domain Company Policies (Sách hướng dẫn/Chính sách nhân sự) có đặc thù là chứa nhiều quy định, định nghĩa, và bullet point có độ dài linh hoạt. Việc dùng `FixedSizeChunker` giúp kiểm soát chính xác độ lớn của mỗi vector đầu ra, đảm bảo mô hình embedder (vốn có max tokens) chạy mượt mà. Hơn nữa, việc thêm `overlap` giúp nối liền các phần nội dung có tính kế thừa trong cùng một điều khoản mà không cần xử lý cấu trúc phức tạp.

**Code snippet (nếu custom):**
```python
# Implementation đã có sẵn (FixedSizeChunker)
step = self.chunk_size - self.overlap
chunks = []
for start in range(0, len(text), step):
    chunks.append(text[start : start + self.chunk_size])
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| Working Remotely.md | best baseline (Recursive) | 19 | 359.1 | Rất tốt, nội dung gọn gàng, đúng ý, bao quát từng vấn đề riêng lẻ. |
| Working Remotely.md | **của tôi (FixedSize)** | 15 | 476.0 | Tương đối ổn, tuy đôi khi chứa thông tin thừa do kích thước cố định, nhưng đủ để model sinh câu trả lời. |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | FixedSizeChunker | 8/10 | Chạy nhanh, ổn định độ dài | Cắt ngang đoạn, ngữ cảnh yếu ở rìa |
| [Tên 1] | RecursiveChunker | 9/10 | Bảo toàn ngữ nghĩa tốt nhất | Chạy chậm hơn, số chunk nhiều hơn |
| [Tên 2] | SentenceChunker | 7.5/10 | Rất chi tiết, chính xác | Có thể mất ý khi câu liên kết nhau qua đại từ |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> Nhìn chung, `RecursiveChunker` hoạt động tốt nhất cho cấu trúc văn bản Policy/Handbook. Lý do là vì các chính sách thường được phân chia cấu trúc rõ ràng qua các Markdown Headers (`#`, `##`) và dấu xuống dòng kép (`\n\n`), nên RecursiveChunker có thể nhận diện và cắt văn bản tại đúng những điểm nghỉ logic này, giúp các chunk chứa nội dung trọn vẹn và cô đọng hơn.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Tôi sử dụng biểu thức chính quy (regex) `(?<=[.!?])\s+` để tách câu. Cấu trúc lookbehind `(?<=[.!?])` giúp giữ lại dấu ngắt câu ở cuối đoạn và chỉ cắt tại khoảng trắng. Sau đó, gộp các câu lại thành chunk tối đa `max_sentences_per_chunk` và xử lý khoảng trắng thừa (edge case chuỗi rỗng/chỉ có khoảng trắng).

**`RecursiveChunker.chunk` / `_split`** — approach:
> Thuật toán đệ quy (recursive). Base case là khi chuỗi nhỏ hơn `chunk_size` hoặc không còn separator. Thuật toán cố gắng cắt văn bản bằng separator hiện tại, rồi cộng dồn độ dài, nếu phần cắt ra vẫn lớn hơn `chunk_size`, nó gọi lại `_split` với các separator tiếp theo ở mức ưu tiên thấp hơn để cắt nhỏ thêm.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> `add_documents` duyệt qua các Document, gọi `_embedding_fn` tính vector và lưu vào `_store` (bộ nhớ in-memory) dưới dạng dictionary chứa đầy đủ content, vector và metadata. Khi `search`, tôi quét qua toàn bộ `_store`, tính điểm Cosine Similarity với query vector, sắp xếp giảm dần và cắt lấy top_k chunk tốt nhất.

**`search_with_filter` + `delete_document`** — approach:
> Tôi áp dụng metadata_filter *trước* khi gọi `_search_records` để giảm số lượng chunk phải tính similarity, giúp tối ưu hiệu suất. Chức năng `delete_document` hoạt động bằng cách giữ lại các chunk có `doc_id` khác giá trị yêu cầu xóa, đồng thời thực thi lệnh xóa trên cả collection của ChromaDB (nếu đang chạy).

### KnowledgeBaseAgent

**`answer`** — approach:
> Gọi `search` từ store với question và top_k để truy xuất ngữ cảnh. Từ kết quả đó, trích xuất nội dung chữ (`content`) rồi kết hợp (join) chúng với dấu `\n`. Cuối cùng, tôi tạo prompt theo khuôn mẫu chứa Context và Question, đẩy vào model hàm `llm_fn` để sinh câu trả lời RAG.

### Test Results

```
================================================================================ test session starts =================================================================================
platform win32 -- Python 3.12.7, pytest-9.0.3, pluggy-1.6.0 -- C:\Program Files\Python312\python.exe
cachedir: .pytest_cache
rootdir: D:\Study\VinUni-Ai-Thuc-Chien\Ngày 7\Day-07-Lab-Data-Foundations-BAND2C401
plugins: anyio-4.13.0
collected 42 items                                                                                                                                                                    

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                                                                           [  2%] 
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                                                                    [  4%] 
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                                                                             [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                                                                              [  9%] 
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                                                                   [ 11%] 
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                                                                   [ 14%] 
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                                                                         [ 16%] 
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                                                                          [ 19%] 
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                                                                        [ 21%] 
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                                                                          [ 23%] 
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                                                                          [ 26%] 
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                                                                     [ 28%] 
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                                                                                 [ 30%] 
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                                                                           [ 33%] 
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                                                                                  [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                                                                      [ 38%] 
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                                                                                [ 40%] 
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                                                                      [ 42%] 
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                                                                          [ 45%] 
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                                                                            [ 47%] 
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                                                                              [ 50%] 
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                                                                    [ 52%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                                                                         [ 54%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                                                                           [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                                                                               [ 59%] 
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                                                                            [ 61%] 
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                                                                     [ 64%] 
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                                                                    [ 66%] 
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                                                                               [ 69%] 
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                                                                           [ 71%] 
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                                                                      [ 73%] 
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                                                                          [ 76%] 
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                                                                [ 78%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                                                                          [ 80%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                                                                       [ 83%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                                                                     [ 85%] 
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                                                                    [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                                                                        [ 90%] 
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                                                                   [ 92%] 
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                                                                            [ 95%] 
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                                                                  [ 97%] 
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED                                                                      [100%] 

================================================================================= 42 passed in 0.07s ================================================================================= 
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Mèo là loài động vật rất đáng yêu. | Những chú mèo thật dễ thương làm sao. | high | -0.0286 | Sai |
| 2 | Tôi thích ăn phở bò. | Trời hôm nay rất nhiều mây và có mưa nhỏ. | low | -0.0926 | Đúng |
| 3 | Học lập trình Python giúp giải quyết công việc tự động. | Kỹ năng code Python hỗ trợ tự động hóa các tác vụ. | high | 0.1362 | Sai |
| 4 | Trí tuệ nhân tạo đang phát triển nhanh chóng. | Hôm qua tôi đi siêu thị mua rất nhiều đồ. | low | -0.0034 | Đúng |
| 5 | Anh ấy rất tốt nhưng tôi rất tiếc. | Tôi rất tốt nhưng anh ấy rất tiếc. | high | 0.0736 | Sai |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> *Viết 2-3 câu:*
Kết quả bất ngờ nhất là tất cả các cặp đều có Actual Score rất thấp (quanh mức 0.0) và không phản ánh đúng ngữ nghĩa. Điều này xảy ra do hệ thống đang dùng `MockEmbedder` (sinh vector từ hàm băm MD5) nên các vector trở nên ngẫu nhiên và gần như vuông góc với nhau trong không gian. Nó chứng minh rằng nếu vector không được train bằng Machine Learning (như `LocalEmbedder`), thuật toán Cosine Similarity sẽ không thể bắt được bất kỳ sự tương đồng ý nghĩa (semantic similarity) nào của văn bản.
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
