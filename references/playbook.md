# Undergrad Admissions Expert — Playbook v3.0

## Overview

Each query targets one school. Output is exactly four things:

```
Step 0  Parse inputs
Step 1  CDS data              → cds_manager.py
Step 2  Community cases       → collegeresults_scraper.py + CC web_fetch
Step 3  Essay analysis        → essay_collector.py
Step 4  Assemble output
```

No probability estimates. No rankings. No generic advice.
Everything must have a source URL or it doesn't exist.

---

## Step 0 — Parse Inputs

Required:
- School name (exact, for CDS and script matching)
- Applicant profile (optional but preferred):
  - GPA (UW / W)
  - SAT or ACT, or "test-optional"
  - Nationality / background
  - Financial situation (full pay / aid required / unknown)
  - ECs (specific, not "I love science")
  - Target round (ED / EA / REA / RD)

If school name is ambiguous (e.g. "Chicago"), confirm before proceeding.

---

## Step 1 — CDS Data

```bash
python3 scripts/cds_manager.py --school "School Name"
```

Extracts from the official Common Data Set PDF:

| Section | Fields |
|---------|--------|
| C1 | Total applicants, admitted, enrolled, acceptance rate, yield |
| C7 | Admission factors and their weight (Very Important / Important / Considered / Not Considered) |
| C9 | SAT / ACT score ranges (25th–75th percentile), % submitting |
| C11 | GPA distribution of enrolled class |

**Cache behavior:** PDF cached locally by school + CDS year. Auto-refreshes when a newer academic year's CDS becomes available (threshold: August of each year).

**If download fails:** Use `--url` flag with direct PDF link, or manually verify the school's IR/Institutional Research page.

---

## Step 2 — Community Cases

**Target: 40 cases. Minimum: 20 cases.**

### 2A — r/collegeresults (primary)

```bash
python3 scripts/collegeresults_scraper.py --school "School Name" --limit 40
```

Searches r/collegeresults, r/ApplyingToCollege, r/chanceme, r/IntltoUSA.
Deduplicates across sources. Sorts by data quality score.

### 2B — College Confidential (supplemental)

Search for the school's current-cycle official thread. Priority targets:
- User-created Google Sheets with self-reported results (best structure)
- Official RD / ED megathreads

Use `web_fetch` to extract structured data from CC threads and Sheets.

### 2C — Merge and validate

After collecting from all sources:
- Remove cases with no result (A/R/WL)
- Flag cases with no GPA or test scores as "low data"
- Check distribution: aim for ≥30% admitted, ≥40% rejected (realistic balance)
- If sample skews heavily admitted → note self-selection bias

### Case output format

Every case must use this template. Empty fields are "Unknown", not omitted:

```
结果         : Accepted / Rejected / Waitlisted / Deferred
来源 URL     : [required — no URL = skip this case]
平台         : Reddit r/xxx / College Confidential / Other
申请轮次     : EA / ED / ED2 / REA / RD / Unknown
GPA          : X.XX UW / X.XX W
标化         : SAT XXXX / ACT XX / Not submitted
AP / IB      :
专业方向     :
国籍背景     : International / Domestic / Unknown
财务情况     : Full pay / Aid / Unknown
Hook         : Legacy / Athlete / First-gen / None / Unknown
ECs          : [specific — reject vague descriptions]
申请人自述   : [direct quote or close paraphrase from original post]
```

---

## Step 3 — Essay Analysis

```bash
python3 scripts/essay_collector.py --school "School Name"
```

### 3A — Official sources (highest priority)

Schools that publish "Essays That Worked" — access via web_fetch:

| School | URL |
|--------|-----|
| Johns Hopkins | https://apply.jhu.edu/apply/essays-that-worked/ |
| UPenn | https://admissions.upenn.edu/admissions-and-financial-aid/what-penn-looks-for/essays-that-worked |
| Tufts | https://admissions.tufts.edu/blogs/jumbo-talk/post/essays-that-worked/ |
| MIT | https://mitadmissions.org/apply/process/essays/ |
| Vanderbilt | https://admissions.vanderbilt.edu/vandybloggers/essays-that-rocked/ |
| Hamilton | https://www.hamilton.edu/admission/essays-that-worked |

For schools without official publications: use Reddit + CollegeVine community posts.

**Stanford 专项**：无官方文书，但以下社区来源有真实录取学生样本：
- CollegeAdvisor: `https://www.collegeadvisor.com/essay-guides/stanford-essays-examples/`
- CollegeVine: `https://blog.collegevine.com/stanford-essay-example`
- Aces Coaching (含完整 roommate letter 样本): `https://www.acescollegeessaycoaching.com/blog/stanford-roommate-essay-guide`

### 3B — Essay analysis output format

Do not reproduce full essay text. Output analysis only:

```
── 文书风格分析：[School] ──────────────────────────────────
样本量：N 篇（来源：官方 X 篇 / 社区 Y 篇）

【该校文书特点】
  • [school-specific — not generic advice]

【话题分布】
  • Intellectual curiosity / academic passion  ████ (N)
  • Identity / cultural background             ███  (N)

【写作风格信号】
  • [patterns seen in 2+ samples]

【应该避免的模式】
  ✗ [concrete and school-specific]

【官方/社区文书原文来源】
  [list of URLs]
────────────────────────────────────────────────────────────
```

---

## Step 4 — Output Assembly

Final output structure:

```
═══════════════════════════════════════════════════════════
[School Name] — Admissions Intelligence Report
CDS Year: 20XX-XX  |  Generated: YYYY-MM-DD
═══════════════════════════════════════════════════════════

1. OFFICIAL CDS DATA
   [C1 / C7 / C9 / C11]

2. COMMUNITY CASES (N total)
   [Per-case blocks]
   [Quick stats: avg GPA, avg SAT, test-optional rate]

3. ESSAY ANALYSIS
   [Analysis block]

4. PATTERNS
   [Data-derived — every statement cites a case or CDS point]
   [Self-selection bias warnings if applicable]
═══════════════════════════════════════════════════════════
```

### Patterns section rules

- Every statement must reference at least one specific case or data point
- No statements valid for all schools (useless)
- If data contradicts CDS, flag it explicitly
- Financial patterns are critical for international applicants — always surface

---

## Error Handling

| Situation | Action |
|-----------|--------|
| CDS PDF unavailable | Search "[school] common data set 2024-25 PDF" — update URL registry |
| Cases < 20 | Expand to r/IntltoUSA, CC older threads; note data limitation |
| School not in CDS registry | Use `--url` flag with manually found PDF |
| No official essay examples | Community sources only; note in output |
| Reddit rate limited | Wait 60s, retry; fall back to web_search |

---

## Quality Gates

Before delivering output:

- [ ] CDS year matches latest available
- [ ] All case URLs spot-checked (3 minimum)
- [ ] Case sample includes both admits and rejects
- [ ] Essay analysis cites specific sources
- [ ] No probability statements anywhere
- [ ] No essay text reproduced
