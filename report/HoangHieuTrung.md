# Hoang Hieu Trung — Comparison Sheet (Lab 7)

> **Branch:** `Trung` | **Group:** BAND2C401 | **Date:** 05/06/2026

---

## 1. Chunking Strategy

| Field | Value |
|-------|-------|
| **Strategy** | `RecursiveChunker` |
| **Parameters** | `chunk_size=300`, `separators=["\n\n", "\n", ". ", " ", ""]` |
| **Embedder** | `MockEmbedder` (dim=64, deterministic hash MD5) |
| **Total chunks** | **79 chunks** across 5 documents |

### Chunk stats per document

| Document | Chunks | Avg length (chars) |
|----------|--------|--------------------|
| Working Remotely.md | 36 | 188 |
| Vacation and Sick Leave.md | 7 | 139 |
| New Parent Leave.md | 9 | 165 |
| Salary and Equity Compensation.md | 14 | 218 |
| Code of Conduct in the Community.md | 13 | 164 |

### Why RecursiveChunker?
> Policy documents from Clef are structured by paragraph (heading + explanation block). RecursiveChunker respects that structure by trying `\n\n` first (paragraph boundary), then `\n`, then `. `, before falling back to character-level splitting. With `chunk_size=300`, each chunk stays focused on a single topic, reducing embedding noise vs. SentenceChunker (~487 chars avg).

---

## 2. Document Corpus

| # | Document | Chars | Metadata |
|---|----------|-------|----------|
| 1 | Working Remotely.md | ~6,955 | `category=work_arrangements, target_audience=all_employees` |
| 2 | Vacation and Sick Leave.md | ~993 | `category=benefits, target_audience=all_employees` |
| 3 | New Parent Leave.md | ~1,513 | `category=benefits, target_audience=parents` |
| 4 | Salary and Equity Compensation.md | ~3,134 | `category=compensation, target_audience=all_employees` |
| 5 | Code of Conduct in the Community.md | ~2,166 | `category=conduct, target_audience=all_employees` |

---

## 3. Benchmark Queries & Gold Answers

*(Shared across the group — same 5 queries for all members)*

| # | Query | Gold Answer | Source |
|---|-------|-------------|--------|
| Q1 | How long can I work remotely before needing manager approval? | Any extended remote work period longer than 2 days or working from a non-regular location requires your manager's approval at least 2 weeks in advance. | Working Remotely.md |
| Q2 | How many vacation days do I accrue each month? | You accrue 1.25 days of paid vacation for every month of work (totaling 15 days/year). | Vacation and Sick Leave.md |
| Q3 | How long is the New Parent Leave policy for birth or adoption? | The company offers 12 weeks of paid leave for all full-time employees after the birth or adoption of a child, to be taken within the first year. | New Parent Leave.md |
| Q4 | What is the salary for a technical employee with less than 5 years of experience? | Technical employees with less than 5 years of experience receive a salary of $100k/year. | Salary and Equity Compensation.md |
| Q5 | Who should I contact if I notice harassment in the company? | You should contact B (b@getclef.com) or one of the other founders immediately. | Code of Conduct in the Community.md |

---

## 4. Benchmark Results

### Plain Search (no filter)

| # | Query | Top-1 Source Retrieved | Score | Top-1 Correct? | Top-3 Correct? |
|---|-------|------------------------|-------|----------------|----------------|
| Q1 | Remote work — manager approval? | **Working Remotely.md** | 0.2704 | ✅ Yes | ✅ Yes |
| Q2 | Vacation days accrued per month? | Working Remotely.md | 0.3408 | ❌ No | ❌ No |
| Q3 | New Parent Leave duration? | Code of Conduct in the Community.md | 0.2836 | ❌ No | ❌ No |
| Q4 | Salary for technical <5 yrs exp? | **Salary and Equity Compensation.md** | 0.2433 | ✅ Yes | ✅ Yes |
| Q5 | Who to contact for harassment? | Working Remotely.md | 0.2775 | ❌ No | ❌ No |

**Plain search — Top-1 hit: 2 / 5 | Top-3 hit: 2 / 5**

### Filter Search (`search_with_filter` with metadata)

| # | Filter applied | Filter Top-1 Source | Correct? |
|---|---------------|---------------------|----------|
| Q1 | `category=work_arrangements` | Working Remotely.md | ✅ Yes |
| Q2 | `category=benefits` | Vacation and Sick Leave.md (in top-3) | ✅ Yes |
| Q3 | `category=benefits, target_audience=parents` | New Parent Leave.md | ✅ Yes |
| Q4 | `category=compensation` | Salary and Equity Compensation.md | ✅ Yes |
| Q5 | `category=conduct` | Code of Conduct in the Community.md | ✅ Yes |

**Filter search — Top-3 hit: 5 / 5**

---

## 5. Summary for Group Comparison

| Metric | Hoang Hieu Trung (RecursiveChunker) |
|--------|--------------------------------------|
| Strategy | RecursiveChunker(chunk_size=300) |
| Total chunks | 79 |
| Avg chunk length | ~175 chars |
| Plain top-1 hit | **2 / 5** |
| Plain top-3 hit | **2 / 5** |
| Filter top-3 hit | **5 / 5** |
| Embedder | MockEmbedder (dim=64) |

### Key Observations
- **Strength:** RecursiveChunker respects paragraph boundaries → chunks are thematically focused → avoids mixing two policies in one chunk.
- **Weakness (with MockEmbedder):** Short chunks (~35 chars like "accrues 1.25 of a day per month") get outscored by longer chunks with higher random hash similarity (Q2 failure case).
- **Metadata filter is essential:** Narrowing from 79 → ~13–36 chunks per category is what enables 5/5 retrieval with a mock embedder.
- **Expected with real embedder:** English queries + English documents → `all-MiniLM-L6-v2` would likely score ≥ 4/5 plain, 5/5 filter.

---

## 6. Baseline Comparison (RecursiveChunker vs FixedSizeChunker)

| Document | Strategy | Chunk Count | Avg Length | Context Preserved? |
|----------|----------|-------------|------------|--------------------|
| Working Remotely.md | FixedSizeChunker(size=200, baseline) | 35 | 196 chars | Medium — cuts mid-sentence |
| Working Remotely.md | **RecursiveChunker(size=300, mine)** | 36 | 187 chars | **Better** — respects paragraph boundaries |
| Salary & Equity | FixedSizeChunker(size=200, baseline) | 16 | 193 chars | Medium |
| Salary & Equity | **RecursiveChunker(size=300, mine)** | 14 | 218 chars | **Better** — clean clause-level chunks |
