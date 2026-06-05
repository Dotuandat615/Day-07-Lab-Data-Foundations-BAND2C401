# So Sánh Kết Quả Strategy Nhóm

File này được dùng để lưu trữ 5 câu hỏi benchmark chung của nhóm cùng với Gold Answers, đồng thời là nơi để các thành viên tổng hợp và so sánh kết quả khi chạy với các chiến lược chunking/metadata khác nhau.

## 1. Benchmark Queries & Gold Answers

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | How long can I work remotely before needing manager approval? | Any extended remote work period longer than 2 days or working from a non-regular location requires your manager's approval at least 2 weeks in advance. |
| 2 | How many vacation days do I accrue each month? | You accrue 1.25 days of paid vacation for every month of work (totaling 15 days/year). |
| 3 | How long is the New Parent Leave policy for birth or adoption? | The company offers 12 weeks of paid leave for all full-time employees after the birth or adoption of a child, to be taken within the first year. |
| 4 | What is the salary for a technical employee with less than 5 years of experience? | Technical employees with less than 5 years of experience receive a salary of $100k/year. |
| 5 | Who should I contact if I notice harassment in the company? | You should contact B (b@getclef.com) or one of the other founders immediately. |

---

## 2. Kết Quả Của Các Thành Viên

*(Các thành viên copy phần kết quả bảng của mình từ `REPORT.md` vào đây)*

### Thành viên 1: Nguyễn Tùng Lâm
**Strategy sử dụng:** `FixedSizeChunker(chunk_size=500, overlap=50)`

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | How long can I work remotely before needing manager approval? | "ly for an extended period of time. This check-in should happ..." | 0.234 | Có | ly for an extended period of time. This check-in should happen at least two weeks in advance, before you make any travel arrangements, and you should come prepared with a plan for how you will handle the logistics and extra communication work involved in extended remote work. In order for an employee to work remotely for an extended period of time, they should have demonstrated in the pas... |     
| 2 | How many vacation days do I accrue each month? | "s).  These equity grants are larger than industry standard, ..." | 0.251 | Có | s).  These equity grants are larger than industry standard, but also vest over a longer period of time. Employee equity vests over 6 years with a 1 year cliff (while 4 years with a 1 year cliff is standard).  At Clef, we’re hoping to build a team that stays with the company and grows with us, so offering larger ownership of the company over a greater period of time aligns with our goals. ... |
| 3 | How long is the New Parent Leave policy for birth or adoption? | "s).  These equity grants are larger than industry standard, ..." | 0.244 | Không | s).  These equity grants are larger than industry standard, but also vest over a longer period of time. Employee equity vests over 6 years with a 1 year cliff (while 4 years with a 1 year cliff is standard).  At Clef, we’re hoping to build a team that stays with the company and grows with us, so offering larger ownership of the company over a greater period of time aligns with our goals. ... | 
| 4 | What is the salary for a technical employee with less than 5 years of experience? | "rubric to make sure it stays at market rate.  Note: The thre..." | 0.280 | Có | rubric to make sure it stays at market rate.  Note: The three Clef founders' salaries do not follow this rubric and are all $50k per year.  ##Equity  Every employee will be offered 41,963 Clef stock options (~.9% of outstanding shares, including the option pool these are drawn from). As mentioned above, they can also choose to reduce their salary by $5k/year in exchange for 4,663 more opt... |
| 5 | Who should I contact if I notice harassment in the company? | "lef for 4 years will be eligible to take a sabbatical after ..." | 0.219 | Không | lef for 4 years will be eligible to take a sabbatical after 1 more year of work. If they took 12 weeks of new parent leave, when they returned they would still have 1 full year of work before they were eligible for their sabbatical.  In California, State Disability Insurance and Paid Family Leave programs will pay part of an employees salary who are unable to work due to pregnancy and chi... | 

**Bao nhiêu queries trả về chunk relevant trong top-3?** 3 / 5

### Thành viên 2: [Tên thành viên]
**Strategy sử dụng:** [Tên strategy, ví dụ: SentenceChunker(max_sentences=3)]

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | How long can I work remotely before needing manager approval? | | | | |
| 2 | How many vacation days do I accrue each month? | | | | |
| 3 | How long is the New Parent Leave policy for birth or adoption? | | | | |
| 4 | What is the salary for a technical employee with less than 5 years of experience? | | | | |
| 5 | Who should I contact if I notice harassment in the company? | | | | |

**Bao nhiêu queries trả về chunk relevant trong top-3?** ... / 5

### Thành viên 3: [Tên thành viên]
**Strategy sử dụng:** [Tên strategy, ví dụ: RecursiveChunker(chunk_size=1000)]

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | How long can I work remotely before needing manager approval? | | | | |
| 2 | How many vacation days do I accrue each month? | | | | |
| 3 | How long is the New Parent Leave policy for birth or adoption? | | | | |
| 4 | What is the salary for a technical employee with less than 5 years of experience? | | | | |
| 5 | Who should I contact if I notice harassment in the company? | | | | |

**Bao nhiêu queries trả về chunk relevant trong top-3?** ... / 5

---

## 3. Tổng Kết So Sánh
*(Điền tóm tắt vào đây sau khi cả nhóm hoàn thành chạy và paste kết quả)*

| Thành viên | Strategy | Relevant Queries (/5) | Điểm mạnh | Điểm yếu |
|------------|----------|-----------------------|-----------|----------|
| Nguyễn Tùng Lâm | FixedSizeChunker(500, 50) | 3 | | |
| [Tên] | | | | |
| [Tên] | | | | |

**Kết luận chung:** Strategy nào mang lại kết quả tốt nhất cho tập tài liệu này và tại sao?
