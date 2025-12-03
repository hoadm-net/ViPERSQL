# ViText2SQL Translation Quality Audit - Empirical Analysis

**Context:** This audit addresses Reviewer 1's request for quantitative evidence of translation quality issues in ViText2SQL dataset. We conducted a systematic analysis of 700 samples (10.2% of training data) using LLM-assisted annotation.

---

## 📊 Key Findings

We analyzed 700 randomly sampled questions from ViText2SQL training set and found that **52.4% contain translation artifacts** that may impact retrieval and SQL generation performance.

### Overall Statistics

| Issue Type | Prevalence | Count | Impact on Model |
|------------|-----------|-------|-----------------|
| **Schema Drift (SCH)** | **31.0%** | 217/700 | **High** - Vocabulary mismatch affects semantic retrieval |
| **Lexical/Fluency (LEX)** | **18.3%** | 128/700 | **Medium** - Unnatural phrasing confuses syntactic matching |
| **Entity Mismatch (ENT)** | **16.9%** | 118/700 | **Medium** - Named entities inconsistent with SQL literals |
| **Structural Mismatch (STR)** | **13.6%** | 95/700 | **High** - Question logic doesn't reflect SQL structure |
| **No Major Issues (OK)** | **47.6%** | 333/700 | Translation quality acceptable |

**Multi-issue cases:** 23.9% (167/700) - Questions with 2+ simultaneous problems

---

## 🔍 Critical Translation Issues

### 1. Schema Drift (31%) - Most Prevalent Problem

**Definition:** Vietnamese terminology in questions doesn't match actual database schema elements (table/column names) used in SQL queries.

**Impact:** This is the most serious issue as it directly affects:
- Semantic similarity-based example retrieval (words don't match)
- Schema linking in prompts
- Model's ability to map natural language to database elements

**Examples:**

**Example 1:** Entity name mismatch
```
Question: "Tìm các mô tả liên quan đến 'Câu lạc bộ quần vợt'."
SQL: SELECT mô_tả_về_câu_lạc_bộ FROM câu_lạc_bộ 
     WHERE tên_câu_lạc_bộ = "Tennis Club"

❌ Problem: 
   - Question uses Vietnamese translation: "Câu lạc bộ quần vợt"
   - SQL uses English literal: "Tennis Club"
   - Column name "mô_tả_về_câu_lạc_bộ" not reflected in question phrasing
```

**Example 2:** Mixed English-Vietnamese column names (`tracking_orders` database)
```
Question: "Cho biết tên của những khách hàng đã từng huỷ mua sản phẩm 
          'thực phẩm' (trạng thái mặt hàng là 'huỷ')."
SQL: SELECT t1.tên_khách_hàng FROM khách_hàng AS t1 
     JOIN đơn_đặt_hàng AS t2 JOIN mặt_hàng_được_đặt AS t3 
     ON t1.id_khách_hàng = t2.id_khách_hàng 
     AND t2.id_đơn_hàng = t3.id_đơn_hàng ...

❌ Problem:
   - Schema has mixed language: **id_khách_hàng**, **id_đơn_hàng** (English 
     "id" + Vietnamese noun)
   - Question: "thực phẩm" (Vietnamese) vs SQL: "food" (English)
   - Question: "huỷ" (Vietnamese) vs SQL: "Cancel" (English)
```

**Example 3:** Mixed schema with political database (`e_government`)
```
Question: "Đảng nào đã sử dụng các dịch vụ nhiều lần nhất? Cho biết email 
          được sử dụng bởi đảng này."
SQL: SELECT t1.địa_chỉ_email_đảng FROM đảng AS t1 
     JOIN dịch_vụ_của_đảng AS t2 ON t1.id_đảng = t2.id_khách_hàng ...

❌ Problem:
   - Column **id_đảng** mixes English "id" + Vietnamese "đảng" (party)
   - Schema inconsistency: t2.id_khách_hàng (customer_id) refers to parties
   - Question lacks GROUP BY/COUNT clarity despite asking "nhiều lần nhất"
```

**Example 4:** Product characteristics database (`products_gen_characteristics`)
```
Question: "Tìm tên của các sản phẩm có mô tả về màu sắc là 'màu đỏ' và 
          có đặc tính là 'nhanh'."
SQL: SELECT tên_sản_phẩm FROM sản_phẩm AS t1 
     JOIN đặc_tính_của_sản_phẩm AS t2 ON t1.id_sản_phẩm = t2.id_sản_phẩm 
     JOIN đặc_tính AS t3 ON t2.id_đặc_tính = t3.id_đặc_tính ...
     WHERE t4.mã_màu = "red" AND t3.tên_đặc_tính = "fast"

❌ Problem:
   - Columns: **id_sản_phẩm**, **id_đặc_tính** (EN "id" + VI nouns)
   - Question: "màu đỏ" (Vietnamese) vs SQL: "red" (English)
   - Question: "nhanh" (Vietnamese) vs SQL: "fast" (English)
```

---

### 2. Lexical/Fluency Issues (18.3%)

**Definition:** Unnatural Vietnamese phrasing resulting from literal/word-by-word translation from English.

**Impact:** 
- Questions sound awkward to native speakers
- May confuse POS-based syntactic matching
- Reduces quality of in-context examples

**Examples:**

**Example 1:** Awkward phrasing
```
Question: "Các sân bay đang hợp tác làm việc với máy bay 'Robinson R-22' 
          có số lượng hành khách trung bình là bao nhiêu?"
SQL: SELECT AVG(t3.tổng_số_hành_khách) FROM máy_bay AS t1 
     JOIN máy_bay_ở_sân_bay AS t2 ON ... 

❌ Problem: 
   - "đang hợp tác làm việc với máy bay" (airports cooperating/working with 
     aircraft) is unnatural and confusing
   - Natural Vietnamese would be: "Các sân bay có máy bay ... có trung bình 
     bao nhiêu hành khách?"
```

**Example 2:** Overly literal translation
```
Question: "Tìm các mô tả liên quan đến 'Câu lạc bộ quần vợt'."

❌ Problem:
   - "mô tả liên quan đến" (descriptions related to) is literal from English
   - Native Vietnamese would say: "Tìm thông tin về..." or "Cho biết mô tả của..."
```

---

### 3. Structural Mismatch (13.6%)

**Definition:** Question's reasoning structure doesn't align with SQL query logic (aggregation, joins, conditions).

**Impact:**
- Misleads models about query complexity
- POS tag distribution won't reflect actual SQL structure
- Hard to learn correct SQL patterns from such examples

**Example:**

```
Question: "Tìm những người bạn có giới tính nữ của Alice."
SQL: SELECT t2.bạn_bè FROM cá_nhân AS t1 
     JOIN bạn_bè AS t2 ON t1.tên = t2.bạn_bè 
     WHERE t2.tên = "Alice" AND t1.giới_tính = "female"

❌ Problem:
   - Question structure: Simple request for "friends of Alice who are female"
   - SQL structure: Complex self-join on person table with friend table
   - Question doesn't hint at the join complexity or dual filtering
   - "người bạn" (friend - singular/general) vs "bạn_bè" (friends - schema term)
```

---

### 4. Entity/Number Inconsistency (16.9%)

**Definition:** Proper names, technical terms, and numeric values in questions don't match SQL string literals exactly.

**Impact:**
- Affects exact matching and entity recognition
- Confuses models about literal values vs. concepts

**Example:**

```
Question: "Có bao nhiêu nhân viên là 'nhân viên CNTT' đến từ mỗi thành phố?"
SQL: SELECT COUNT(*), thành_phố FROM nhân_viên 
     WHERE chức_danh = "IT Staff" GROUP BY thành_phố

❌ Problem:
   - Question: "nhân viên CNTT" (Vietnamese abbreviation for IT staff)
   - SQL: "IT Staff" (English term)
   - Inconsistent terminology makes pattern matching difficult
```

---

## 💡 Implications for ViR² Design

These findings **validate the motivation for ViR²'s design choices**:

### Why POS-based Syntactic Matching Helps

Traditional semantic retrieval (BERT/PhoBERT) struggles with:
- Schema drift: "danh sách nhạc" vs "danh_sách_phát" have low semantic similarity despite same intent
- Lexical variations: Different phrasings of same structure get scattered

**ViR²'s POS matching** provides robustness by:
- Focusing on **grammatical structure** rather than exact vocabulary
- Capturing question **complexity patterns** (aggregation, multi-entity queries)
- Being **invariant to word-level translation noise**

Example:
```
Q1: "Tìm số lượng sinh viên từ mỗi thành phố"
Q2: "Cho biết có bao nhiêu học sinh ở từng thành phố"

→ Different words ("số lượng"/"bao nhiêu", "sinh viên"/"học sinh", "từ"/"ở")
→ But SAME POS pattern: [V + NUM_PHRASE + NOUN + PREP + DET + NOUN]
→ Both map to: SELECT COUNT(*), city FROM students GROUP BY city
```

### Why Diversity Optimization Matters

With 52.4% of training data containing noise:
- Random selection likely picks problematic examples
- Single-criterion retrieval may cluster noisy translations

**Diversity component** (λ=0.3) ensures:
- Examples cover different **syntactic patterns**
- Reduces risk of selecting multiple **similarly-flawed** translations
- Better coverage of valid SQL structure variations

---

## 📈 Quantitative Evidence for Paper

**Recommended text for Section 4.1 (Dataset Description):**

> To assess translation quality in ViText2SQL, we conducted a systematic audit of 700 randomly sampled questions (10.2% of training data) using GPT-4o-mini annotation. The analysis reveals that **52.4% of queries contain translation artifacts**, with schema drift (31.0%) being the most prevalent issue—Vietnamese terminology in questions frequently mismatches actual database schema elements used in SQL queries (e.g., "danh sách nhạc" vs. "danh_sách_phát"). Lexical/fluency issues (18.3%) manifest as unnatural phrasing from literal translation (e.g., "đang hợp tác làm việc với máy bay"), while structural mismatches (13.6%) occur when question reasoning doesn't reflect SQL complexity (e.g., simple phrasing for complex joins). Entity inconsistencies (16.9%) arise from mixed Vietnamese-English entity names ("nhân viên CNTT" vs. "IT Staff"). Notably, 23.9% of questions exhibit multiple simultaneous issues. These findings confirm **non-negligible translation noise** that motivates ViR²'s syntactic-aware ranking approach, which leverages POS tag distributions to capture structural similarities robust to surface-form variations introduced by translation.

**Statistics for tables/citations:**
- Dataset size audited: 700 samples (10.2%)
- Issues found: 52.4% (367/700)
- Top issue: Schema drift at 31.0%
- Multi-issue cases: 23.9% (167/700)

---

## 📁 Supporting Data Files

All analysis results are available in `results/`:

- **`audit_results.jsonl`** - Complete annotations for 700 samples
- **`audit_statistics.json`** - Summary statistics (JSON format)
- **`audit_statistics_table.tex`** - LaTeX table ready for paper inclusion
- **`audit_analysis_multi_issue.json`** - 167 cases with multiple problems
- **`audit_analysis_schema_drift.json`** - All 217 schema drift cases
- **`audit_analysis_lexical.json`** - All 128 lexical/fluency issues
- **`audit_analysis_examples.md`** - Top 10 worst cases with detailed explanations
- **`audit_examples_by_type.json`** - Representative examples for each issue category

---

## 🛠️ Reproducing the Audit

To reproduce this analysis or audit additional samples:

```bash
# Install dependencies
pip install -r scripts/requirements_audit.txt

# Configure OpenAI API key in .env file
# DEFAULT_MODEL=gpt-4o-mini

# Run audit on 700 samples (takes ~30 minutes, costs ~$0.50)
./scripts/run_audit.sh

# Analyze results
python scripts/analyze_audit_results.py

# Generate stratified sample for human validation
python scripts/manual_validation_sampler.py
```

For detailed methodology and implementation, see `scripts/audit_vitext2sql_noise.py`.

---

**Last Updated:** December 3, 2025  
**Author:** ViPERSQL Research Team
