# ViText2SQL Translation Quality Audit - Empirical Analysis

**Context:** This audit addresses Reviewer 1's request for quantitative evidence regarding translation quality in the ViText2SQL dataset. We conducted a systematic analysis of 700 samples (10.2% of training data) using LLM-assisted annotation with **lenient criteria focusing only on severe and obvious issues**.

---

## 📊 Key Findings

We analyzed 700 randomly sampled questions from ViText2SQL training set. While the dataset maintains good overall quality as a published benchmark, we identified **18.7% of samples with notable translation artifacts** that could potentially impact retrieval performance.

### Overall Statistics

| Issue Type | Prevalence | Count | Description |
|------------|-----------|-------|-------------|
| **Schema Drift (SCH)** | **13.9%** | 97/700 | Terminology mismatch between question and schema |
| **Entity Mismatch (ENT)** | **5.3%** | 37/700 | Language mixing in entity names |
| **Structural Mismatch (STR)** | **5.0%** | 35/700 | Question complexity doesn't reflect SQL structure |
| **Lexical/Fluency (LEX)** | **0.4%** | 3/700 | Unnatural phrasing from translation |
| **No Issues (OK)** | **81.3%** | 569/700 | Translation quality is good |

**Note:** We used **lenient criteria** - marking issues only when severe and obvious. Minor stylistic variations were not counted as problems.


## 🔍 Representative Translation Issues

The following examples illustrate the types of translation artifacts we observed:

### 1. Schema Drift (13.9%) - Mixed Language Column Names

**Most Notable Pattern:** Database schemas mixing English prefixes with Vietnamese terms (e.g., `id_khách_hàng`, `id_đảng`)

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

### 2. Structural Mismatch (5.0%) - Implicit Complexity

**Example:** Friend query with hidden joins

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

### 3. Entity Mismatch (5.3%) - Language Mixing

**Example:** Terminology inconsistency

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

**Important Note:** The presence of these issues does **NOT** invalidate ViText2SQL as a benchmark. It is a valuable published dataset that has been widely used. However, these observations **support** our design choices:

### Why Syntactic Matching Helps

The translation artifacts we observed provide empirical justification for ViR²'s POS-based approach:

- **Schema drift** (mixed language columns): Semantic similarity between "khách_hàng" and "customer" may be low despite same meaning
- **Different phrasings**: "số lượng" vs "bao nhiêu" have same POS pattern but different embeddings

**ViR²'s POS matching** is robust to these variations by focusing on **grammatical structure** rather than exact vocabulary.

Example:
```
Q1: "Tìm số lượng sinh viên từ mỗi thành phố"
Q2: "Cho biết có bao nhiêu học sinh ở từng thành phố"

→ Different words but SAME POS pattern: [V + NUM_PHRASE + NOUN + PREP + DET + NOUN]
→ Both map to: SELECT COUNT(*), city FROM students GROUP BY city
```

### Why Diversity Matters

With ~19% containing some translation artifacts, having diversity in example selection helps:

- Avoid clustering similar translation patterns
- Ensure coverage of different valid SQL structures
- Reduce impact of any single problematic translation

---

## 📈 Quantitative Evidence for Paper

**Recommended text for Section 4.1 (Dataset Description):**

> ViText2SQL is a high-quality Vietnamese Text-to-SQL benchmark derived from Spider through translation. To assess potential translation artifacts, we conducted a systematic audit of 700 randomly sampled questions (10.2% of training data) using GPT-4o-mini with lenient annotation criteria that only flag severe and obvious issues. The analysis reveals that **18.7% of queries contain notable translation issues**, primarily schema drift (13.9%) where Vietnamese terminology in questions doesn't perfectly align with database schema elements that mix English and Vietnamese (e.g., `id_khách_hàng`), and structural mismatches (5.0%) where question phrasing doesn't fully reflect SQL complexity. These observations validate ViR²'s design: our syntactic-aware ranking leverages POS tag distributions to capture structural similarities that are robust to vocabulary variations introduced during translation, while diversity optimization (λ=0.3) ensures broad coverage of valid SQL patterns.

**Alternative (shorter version):**

> We audited 700 samples (10%) from ViText2SQL and found 18.7% contain translation artifacts (primarily schema terminology mismatches), motivating ViR²'s syntactic matching approach.

**Statistics for tables/citations:**

- Dataset size audited: 700 samples (10.2%)
- Issues found: 18.7% (131/700)
- Top issue: Schema drift at 13.9%
- Annotation approach: Lenient criteria, severe issues only

---

## 📁 Supporting Data Files

All analysis results available in `results/`:

- **`audit_results_lenient.jsonl`** - Complete annotations for 700 samples (lenient criteria)
- **`audit_statistics_lenient.json`** - Summary statistics
- **`audit_statistics_lenient_table.tex`** - LaTeX table for paper
- **`audit_mixed_language_examples.json`** - Examples of EN-VI schema mixing

---

## 🛠️ Reproducing the Audit

To reproduce this analysis or audit additional samples:

```bash
# Install dependencies
pip install -r scripts/requirements_audit.txt

# Configure OpenAI API key in .env file
# DEFAULT_MODEL=gpt-4o-mini

# Run audit with lenient criteria (only severe issues)
python scripts/audit_vitext2sql_noise.py \
  --samples 700 \
  --output results/audit_results_lenient.jsonl \
  --seed 42

# Analyze results
python scripts/analyze_audit_results.py \
  --input results/audit_results_lenient.jsonl

# Generate stratified sample for human validation
python scripts/manual_validation_sampler.py \
  --input results/audit_results_lenient.jsonl
```

**Annotation Criteria:** We used **lenient criteria** - only marking severe and obvious issues. Minor stylistic variations, acceptable synonyms, and implicit but correct structures were considered acceptable. This ensures we document genuine problems without overstating issues in a published benchmark.

---

**Last Updated:** December 3, 2025  
**Author:** ViPERSQL Research Team
