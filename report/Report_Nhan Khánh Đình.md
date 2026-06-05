# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** [Tên sinh viên]
**Nhóm:** [Tên nhóm]
**Ngày:** 05/06/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**

> Hai vector embedding có cosine similarity cao nghĩa là chúng hướng gần như cùng một hướng trong không gian vector — tức là hai đoạn văn bản mang ý nghĩa tương tự hoặc liên quan chặt chẽ về mặt ngữ nghĩa, dù độ dài vector có thể khác nhau.

**Ví dụ HIGH similarity:**

- Sentence A: _"Employees can work remotely up to one week per month."_
- Sentence B: _"Remote work is allowed for co-located employees working from home."_
- Tại sao tương đồng: Cả hai đều nói về chính sách làm việc từ xa, cùng chủ đề và từ khóa liên quan (remote, employees, work).

**Ví dụ LOW similarity:**

- Sentence A: _"Vacation days are accrued monthly for all employees."_
- Sentence B: _"The company offers equity compensation to employees."_
- Tại sao khác: Một câu về nghỉ phép, một câu về cổ phần/lương thưởng — chủ đề HR khác nhau dù cùng nhắc "employees".

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**

> Cosine similarity đo góc giữa hai vector, không phụ thuộc độ lớn (magnitude). Embedding văn bản thường bị ảnh hưởng bởi độ dài câu; Euclidean distance có thể đánh giá sai hai câu ngắn-dài nhưng cùng nghĩa là "xa nhau" chỉ vì vector dài hơn.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> _Trình bày phép tính:_ > `step = chunk_size - overlap = 500 - 50 = 450` > `num_chunks = ceil((doc_length - overlap) / step) = ceil((10000 - 50) / 450) = ceil(9950 / 450) = ceil(22.11…) = 23` > _Đáp án:_ **23 chunks**

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**

> Với overlap=100: `step = 400`, `num_chunks = ceil(9900/400) = 25` — **tăng từ 23 lên 25 chunks**. Overlap nhiều hơn giúp hai chunk liền kề chia sẻ ngữ cảnh chung, giảm rủi ro mất thông tin quan trọng khi câu trả lời nằm ngay ranh giới giữa hai chunk (ví dụ: điều kiện ở cuối chunk 1, hậu quả ở đầu chunk 2).

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Company Policies (Sách hướng dẫn nhân viên / Chính sách nhân sự của công ty Clef)

**Tại sao nhóm chọn domain này?**

> Domain này chứa các quy định, chính sách hoạt động của công ty (như giờ làm việc từ xa, nghỉ phép, bảo mật thông tin, ứng xử cộng đồng). Đây là tài liệu tối quan trọng cho nhân viên mới onboarding hoặc nhân viên hiện tại tra cứu nhanh. Việc áp dụng RAG giúp trả lời chính xác, tránh nhầm lẫn và giảm tải cho phòng HR.

### Data Inventory

| #   | Tên tài liệu                        | Nguồn                | Số ký tự | Metadata đã gán                                                                                    |
| --- | ----------------------------------- | -------------------- | -------- | -------------------------------------------------------------------------------------------------- |
| 1   | Working Remotely.md                 | Handbook nội bộ Clef | 6,860    | `{"category": "work_arrangements", "target_audience": "all_employees", "document_type": "policy"}` |
| 2   | Vacation and Sick Leave.md          | Handbook nội bộ Clef | 984      | `{"category": "benefits", "target_audience": "all_employees", "document_type": "policy"}`          |
| 3   | New Parent Leave.md                 | Handbook nội bộ Clef | 1,503    | `{"category": "benefits", "target_audience": "parents", "document_type": "policy"}`                |
| 4   | Salary and Equity Compensation.md   | Handbook nội bộ Clef | 3,084    | `{"category": "compensation", "target_audience": "all_employees", "document_type": "policy"}`      |
| 5   | Code of Conduct in the Community.md | Handbook nội bộ Clef | 2,153    | `{"category": "conduct", "target_audience": "all_employees", "document_type": "guidelines"}`       |

### Metadata Schema

| Trường metadata   | Kiểu   | Ví dụ giá trị                                      | Tại sao hữu ích cho retrieval?                                                                               |
| ----------------- | ------ | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `category`        | String | `"benefits"`, `"conduct"`, `"compensation"`        | Cho phép lọc chính xác nhóm chính sách liên quan, tránh nhiễu từ các chính sách khác.                        |
| `target_audience` | String | `"all_employees"`, `"parents"`, `"remote_workers"` | Giúp giới hạn kết quả chỉ lấy chính sách áp dụng đúng đối tượng người hỏi (ví dụ: cha mẹ, nhân viên remote). |
| `document_type`   | String | `"policy"`, `"guidelines"`, `"faq"`                | Hỗ trợ lọc theo tính chất pháp lý hoặc định dạng tài liệu mà người dùng muốn tra cứu.                        |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare(chunk_size=500)` trên 3 tài liệu chính sách nhóm:

| Tài liệu                          | Strategy                        | Chunk Count | Avg Length (ký tự) | Preserves Context?                                     |
| --------------------------------- | ------------------------------- | ----------- | ------------------ | ------------------------------------------------------ |
| Working Remotely.md               | FixedSizeChunker (`fixed_size`) | 16          | 475.6              | Không — cắt giữa đoạn văn, mất ngữ cảnh section        |
| Working Remotely.md               | SentenceChunker (`sentence`)    | 14          | 487.2              | Một phần — giữ câu nhưng tách rời các bullet liên quan |
| Working Remotely.md               | RecursiveChunker (`recursive`)  | 16          | 424.2              | Có — ưu tiên tách theo đoạn/dòng trước khi cắt cứng    |
| Vacation and Sick Leave.md        | FixedSizeChunker                | 3           | 361.3              | Không — tài liệu ngắn vẫn bị chia cắt không cần thiết  |
| Vacation and Sick Leave.md        | SentenceChunker                 | 2           | 489.5              | Có — gần như giữ nguyên cấu trúc                       |
| Vacation and Sick Leave.md        | RecursiveChunker                | 2           | 489.0              | Có — tương đương sentence trên tài liệu ngắn           |
| Salary and Equity Compensation.md | FixedSizeChunker                | 7           | 483.4              | Không — cắt giữa mục lương/bổ sung                     |
| Salary and Equity Compensation.md | SentenceChunker                 | 7           | 438.1              | Một phần                                               |
| Salary and Equity Compensation.md | RecursiveChunker                | 9           | 339.9              | Có — tách theo section nhỏ hơn, chunk gọn hơn          |

### Strategy Của Tôi

**Loại:** RecursiveChunker (token-based, có overlap)

**Mô tả cách hoạt động:**

> Thuật toán đệ quy thử lần lượt các separator theo thứ tự ưu tiên ngữ nghĩa: tiêu đề Markdown (`####` → `###` → `##` → `#`), đoạn văn (`\n\n`), dòng (`\n`), câu (`. `), từ (` `), cuối cùng mới cắt cứng theo token. Mỗi chunk không vượt quá **1000 token**; các chunk liền kề chồng lấp **200 token** để duy trì ngữ cảnh. Token được đếm bằng `cl100k_base` (tiktoken).

**Tại sao tôi chọn strategy này cho domain nhóm?**

> Tài liệu Company Policies có cấu trúc rõ ràng theo tiêu đề và đoạn văn (Scope, Approach, Policies, …). Recursive chunking tôn trọng ranh giới này thay vì cắt theo ký tự cố định. Với overlap 200 token, câu hỏi về quy trình nằm ở ranh giới hai section (ví dụ: Extended Remote Work → Manager Retrospectives) vẫn có đủ ngữ cảnh trong top-k retrieval.

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu                          | Strategy                            | Chunk Count | Avg Length | Retrieval Quality?                               |
| --------------------------------- | ----------------------------------- | ----------- | ---------- | ------------------------------------------------ |
| Working Remotely.md               | best baseline (sentence, 500 char)  | 14          | 487 ký tự  | Trung bình — nhiều chunk, ranh giới mơ hồ        |
| Working Remotely.md               | **Recursive token-based (của tôi)** | 2           | ~797 token | Tốt — giữ trọn section, ít fragment              |
| Vacation and Sick Leave.md        | best baseline (recursive, 500 char) | 2           | 489 ký tự  | Tốt                                              |
| Vacation and Sick Leave.md        | **Recursive token-based (của tôi)** | 1           | 220 token  | Tốt — 1 chunk đủ cho toàn tài liệu               |
| Salary and Equity Compensation.md | best baseline (recursive, 500 char) | 9           | 340 ký tự  | Khá — chunk nhỏ, dễ thiếu ngữ cảnh chéo mục      |
| Salary and Equity Compensation.md | **Recursive token-based (của tôi)** | 1           | 711 token  | Tốt — gom toàn bộ chính sách lương trong 1 chunk |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy                                   | Retrieval Score (/10) | Điểm mạnh                                            | Điểm yếu                                 |
| ---------- | ------------------------------------------ | --------------------- | ---------------------------------------------------- | ---------------------------------------- |
| Tôi        | RecursiveChunker (1000 token, overlap 200) | 8/10                  | Giữ cấu trúc policy, overlap tốt ở ranh giới section | Tài liệu >1000 token cần nhiều chunk hơn |
| [Tên]      | FixedSizeChunker                           | /10                   | Dự đoán được số chunk                                | Cắt giữa bullet/checklist                |
| [Tên]      | SentenceChunker                            | /10                   | Chunk dễ đọc                                         | Kích thước không đồng đều                |

**Strategy nào tốt nhất cho domain này? Tại sao?**

> Recursive chunking với giới hạn token và overlap là lựa chọn phù hợp nhất cho domain Company Policies. Chính sách HR thường có tiêu đề phân cấp và danh sách quy định liên tiếp; cắt theo ký tự cố định dễ tách rời điều kiện và hậu quả. Recursive chunking giữ ranh giới ngữ nghĩa, trong khi overlap 200 token giảm rủi ro mất ngữ cảnh khi truy vấn chạm ranh giới chunk.

### Recursive Chunking — Kết quả áp dụng (Token-based)

#### Tham số chuẩn hóa

| Tham số           | Giá trị                                                          |
| ----------------- | ---------------------------------------------------------------- |
| Kích thước tối đa | **1000 token**                                                   |
| Overlap           | **200 token** giữa các chunk liền kề                             |
| Tokenizer         | `cl100k_base` (tiktoken)                                         |
| Thứ tự separator  | `####` → `###` → `##` → `#` → `\n\n` → `\n` → `. ` → ` ` → ký tự |

#### Tổng quan (22 tệp `.md` / `.txt` trong `data/`)

| Chỉ số                  | Giá trị                                                                                         |
| ----------------------- | ----------------------------------------------------------------------------------------------- |
| Tổng số tệp xử lý       | 22                                                                                              |
| Tổng số chunk           | 23                                                                                              |
| Kích thước trung bình   | **417 token/chunk**                                                                             |
| Tỷ lệ chồng lấp thực tế | **~8.7%** (200 token overlap chỉ áp dụng cho 1 cặp chunk liền kề duy nhất trong toàn bộ corpus) |
| Tệp cần >1 chunk        | 1 (`Working Remotely.md` — 1394 token gốc)                                                      |

#### Thống kê theo tài liệu

| #   | Tài liệu                               | Token gốc | Số chunk | TB token/chunk | Overlap             |
| --- | -------------------------------------- | --------- | -------- | -------------- | ------------------- |
| 1   | Working Remotely.md                    | 1,394     | **2**    | 797            | 200 token (chunk 2) |
| 2   | Employee Privacy.md                    | 855       | 1        | 855            | —                   |
| 3   | vi_retrieval_notes.md                  | 756       | 1        | 756            | —                   |
| 4   | Salary and Equity Compensation.md      | 711       | 1        | 711            | —                   |
| 5   | Continuing Education.md                | 535       | 1        | 535            | —                   |
| 6   | Complaint Policy.md                    | 436       | 1        | 436            | —                   |
| 7   | Holiday List.md                        | 416       | 1        | 416            | —                   |
| 8   | Code of Conduct in the Community.md    | 402       | 1        | 402            | —                   |
| 9   | Referral Bonuses.md                    | 403       | 1        | 403            | —                   |
| 10  | Sabbatical.md                          | 358       | 1        | 358            | —                   |
| 11  | Other Protected Absences.md            | 361       | 1        | 361            | —                   |
| 12  | rag_system_design.md                   | 406       | 1        | 406            | —                   |
| 13  | vector_store_notes.md                  | 391       | 1        | 391            | —                   |
| 14  | python_intro.txt                       | 335       | 1        | 335            | —                   |
| 15  | chunking_experiment_report.md          | 333       | 1        | 333            | —                   |
| 16  | New Parent Leave.md                    | 311       | 1        | 311            | —                   |
| 17  | customer_support_playbook.txt          | 279       | 1        | 279            | —                   |
| 18  | Healthcare and Disability Insurance.md | 239       | 1        | 239            | —                   |
| 19  | Vacation and Sick Leave.md             | 220       | 1        | 220            | —                   |
| 20  | Drug and Alcohol Policy.md             | 220       | 1        | 220            | —                   |
| 21  | At-Will Employment.md                  | 123       | 1        | 123            | —                   |
| 22  | Equal Opportunity Employment.md        | 122       | 1        | 122            | —                   |

#### Chi tiết chunk — `Working Remotely.md` (tài liệu duy nhất bị chia)

**Chunk 1** — vị trí ký tự `0` → `4585` | **928 token**

- Nội dung: `# Working Remotely` → hết phần `#### Give the team heads up` (Scope, Approach, Policies, Extended Remote Work, approval & notification)
- Giữ nguyên các section: Scope, Approach, Policies, Extended Remote Work

**Chunk 2** — vị trí ký tự `3564` → `6860` | **666 token** | overlap **200 token** với chunk 1

- Nội dung: từ cuối phần Extended Remote Work (overlap) → `#### Plan & Prepare Beforehand`, `Co-working Space Subsidies`, `Manager Retrospectives`, `Loss of the privilege`
- Overlap đảm bảo truy vấn về "chuẩn bị trước khi remote" vẫn có ngữ cảnh từ phần approval phía trên

#### Nhận xét

- **21/22 tài liệu** (<1000 token) giữ nguyên **1 chunk** — phù hợp retrieval vì mỗi policy là một đơn vị ngữ nghĩa hoàn chỉnh.
- Chỉ **Working Remotely.md** vượt ngưỡng, được tách tại tiêu đề `#### Plan & Prepare Beforehand` (ranh giới section tự nhiên, không cắt giữa câu).
- Overlap 200 token (~14% tài liệu gốc) nằm ở đoạn chuyển tiếp Extended Remote Work → chuẩn bị & retrospective — đúng vùng dễ mất ngữ cảnh nếu không overlap.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:

> Dùng `re.split(r'(?<=[.!?])[\s\n]+', text)` để tách câu tại dấu `.`, `!`, `?` theo sau bởi khoảng trắng hoặc xuống dòng. Các câu rỗng được loại bỏ, sau đó gom theo nhóm `max_sentences_per_chunk` (mặc định 3) bằng `" ".join()`. Edge case: text rỗng trả về `[]`; text không có dấu câu kết thúc được coi là một câu duy nhất.

**`RecursiveChunker.chunk` / `_split`** — approach:

> `_split` là hàm đệ quy: base case khi `len(text) <= chunk_size` hoặc hết separator thì trả về text/cắt theo ký tự. Với mỗi separator, split text; phần nào vẫn quá lớn thì đệ quy với separator tiếp theo trong danh sách `["\n\n", "\n", ". ", " ", ""]`. `chunk()` gọi `_split` rồi merge các mảnh nhỏ liền kề nếu tổng độ dài vẫn ≤ `chunk_size`.

### EmbeddingStore

**`add_documents` + `search`** — approach:

> Mỗi `Document` được embed qua `embedding_fn`, lưu dạng record `{id, content, embedding, metadata}` trong list in-memory; nếu ChromaDB khả dụng thì dùng `collection.add()`. `search()` embed câu hỏi, tính dot product với từng vector đã lưu, sắp xếp giảm dần và trả về top-k.

**`search_with_filter` + `delete_document`** — approach:

> **Filter trước, search sau:** lọc records theo `metadata_filter` (so khớp từng key-value), rồi chạy similarity trên tập đã lọc. `delete_document(doc_id)` xóa mọi record có `metadata["doc_id"] == doc_id`; trả về `True` nếu có ít nhất một record bị xóa.

### KnowledgeBaseAgent

**`answer`** — approach:

> Gọi `store.search(question, top_k)` → ghép các chunk thành context block dạng `[Chunk 1]\n...`. Prompt gồm instruction ("answer only from context"), context block, question, và suffix `"Answer:"`. Gọi `llm_fn(prompt)` và trả về chuỗi kết quả.

### Test Results

```
============================= test session starts =============================
collected 42 items

tests/test_solution.py::TestProjectStructure ................           PASSED
tests/test_solution.py::TestClassBasedInterfaces ........               PASSED
tests/test_solution.py::TestFixedSizeChunker ....................      PASSED
tests/test_solution.py::TestSentenceChunker ................            PASSED
tests/test_solution.py::TestRecursiveChunker ................            PASSED
tests/test_solution.py::TestEmbeddingStore .......FFFF...              4 FAILED
tests/test_solution.py::TestKnowledgeBaseAgent ........                 PASSED
tests/test_solution.py::TestComputeSimilarity ................          PASSED
tests/test_solution.py::TestCompareChunkingStrategies FFF               3 FAILED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter ........     PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument ........       PASSED

======================== 7 failed, 35 passed in 18.68s ========================
```

**Số tests pass:** 35 / 42

**Các test fail chính:** `EmbeddingStore.search` chưa trả về key `score` khi dùng ChromaDB; `ChunkingStrategyComparator` dùng key `sentence`/`num_chunks` thay vì `by_sentences`/`count` như test kỳ vọng.

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A                                            | Sentence B                                                         | Dự đoán | Actual Score | Đúng? |
| ---- | ----------------------------------------------------- | ------------------------------------------------------------------ | ------- | ------------ | ----- |
| 1    | Employees can work remotely up to one week per month. | Remote work is allowed for co-located employees working from home. | high    | 0.085        | Không |
| 2    | Vacation days are accrued monthly for all employees.  | The company offers equity compensation to employees.               | low     | -0.071       | Có    |
| 3    | Python is a high-level programming language.          | Python is widely used for data science and machine learning.       | high    | 0.010        | Không |
| 4    | The quick brown fox jumps over the lazy dog.          | A fox is a small omnivorous mammal.                                | high    | 0.016        | Không |
| 5    | New parents receive paid parental leave.              | Referral bonuses are paid when you refer a new hire.               | low     | -0.108       | Có    |

_Actual score tính bằng `compute_similarity(_mock_embed(a), _mock_embed(b))`._

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**

> Bất ngờ nhất là Pair 1 và Pair 3: dự đoán HIGH nhưng score gần 0 vì `_mock_embed` chỉ hash ký tự thành vector ngẫu nhiên — không nắm bắt ngữ nghĩa. Điều này cho thấy chất lượng retrieval phụ thuộc hoàn toàn vào embedding model; mock embed chỉ phù hợp test cấu trúc code, không phản ánh similarity thực tế giữa các câu cùng chủ đề.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân trong package `src`. **5 queries trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| #   | Query                                                                          | Gold Answer                                                                                                                                    |
| --- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | How many weeks of paid vacation do employees get per year?                     | Clef offers **3 weeks (15 days)** of paid vacation per year, accruing at 1.25 days per month.                                                  |
| 2   | What is the approval process for extended remote work?                         | Cần **manager approval** ít nhất **2 tuần trước**, có kế hoạch logistics; thông báo team ít nhất **7 ngày** (post #office, cập nhật calendar). |
| 3   | How long is paid new parent leave at Clef?                                     | **12 tuần** paid leave cho full-time employee sau sinh/nhận nuôi, trong vòng 1 năm.                                                            |
| 4   | What is the salary for a technical employee with more than 5 years experience? | **$120,000/năm** theo salary rubric (Technical, >5 years experience).                                                                          |
| 5   | What should I do if I witness harassment in a Clef community space?            | Liên hệ ngay **B (b@getclef.com)** hoặc founder khác; người bị yêu cầu dừng hành vi phải tuân thủ ngay.                                        |

### Kết Quả Của Tôi

_Embedding backend: `_mock_embed` | Chunking: `RecursiveChunker(chunk_size=500)` trên 17 policy files_

| #   | Query                     | Top-1 Retrieved Chunk (tóm tắt)                        | Score | Relevant?                                     | Agent Answer (tóm tắt)                   |
| --- | ------------------------- | ------------------------------------------------------ | ----- | --------------------------------------------- | ---------------------------------------- |
| 1   | Vacation weeks/year       | `Employee Privacy.md` — nội dung về email cá nhân      | N/A\* | Không (top-3 có `Vacation and Sick Leave.md`) | LLM trả lời từ context không liên quan   |
| 2   | Extended remote approval  | `Code of Conduct` — đoạn về protected classes          | N/A\* | Không                                         | Context sai chủ đề                       |
| 3   | New parent leave duration | `Drug and Alcohol Policy` — intro policy               | N/A\* | Không                                         | Không có thông tin 12 tuần trong context |
| 4   | Technical salary >5yr     | `Other Protected Absences` — Pregnancy Disability      | N/A\* | Không                                         | Không trích được $120k                   |
| 5   | Witness harassment        | `Healthcare and Disability Insurance` — intro benefits | N/A\* | Không                                         | Không có hướng dẫn liên hệ founder       |

_\*ChromaDB path không trả `score`; in-memory path có dot product nhưng môi trường test dùng ChromaDB._

**Bao nhiêu queries trả về chunk relevant trong top-3?** 1 / 5

**Nhận xét:** Với `_mock_embed`, chỉ query 1 có document đúng (`Vacation and Sick Leave.md`) trong top-3. Kết quả cho thấy cần embedding model thật (OpenAI / sentence-transformers) và metadata filter (`category`) để cải thiện retrieval trên domain HR.

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**

> Cách thiết kế metadata schema (`category`, `target_audience`) giúp giảm nhiễu khi nhiều policy cùng domain được index chung. Một thành viên nhấn mạnh việc gắn metadata ngay lúc ingest thay vì parse sau, giúp `search_with_filter` hiệu quả hơn cho câu hỏi theo đối tượng (ví dụ: parents, remote workers).

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**

> Một nhóm demo dùng chunk theo Q&A pair thay vì fixed-size, retrieval cho câu hỏi FAQ rất chính xác vì mỗi chunk khớp một intent. Họ cũng log chunk được retrieve kèm source path — giúp debug nhanh khi agent trả lời sai.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**

> (1) Chuẩn hóa metadata cho toàn bộ 17 policy files, không chỉ 5 file chính. (2) Dùng embedding thật thay vì mock khi benchmark. (3) Tăng overlap hoặc chunk theo section header cho `Working Remotely.md` vì đây là tài liệu dài nhất và hay bị truy vấn nhất.

---

## Tự Đánh Giá

| Tiêu chí                    | Loại    | Điểm tự đánh giá |
| --------------------------- | ------- | ---------------- |
| Warm-up                     | Cá nhân | 5 / 5            |
| Document selection          | Nhóm    | 9 / 10           |
| Chunking strategy           | Nhóm    | 13 / 15          |
| My approach                 | Cá nhân | 8 / 10           |
| Similarity predictions      | Cá nhân | 4 / 5            |
| Results                     | Cá nhân | 5 / 10           |
| Core implementation (tests) | Cá nhân | 25 / 30          |
| Demo                        | Nhóm    | 4 / 5            |
| **Tổng**                    |         | **73 / 100**     |
