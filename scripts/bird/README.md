# BIRD Dataset Integration Scripts

Scripts để tích hợp tập dữ liệu BIRD vào ViPERSQL project.

## 📁 Structure

```
scripts/bird/
├── bird_integration.py      # Main entry point (recommended)
├── process_bird_dataset.py  # Core processing pipeline
├── analyze_bird.py          # Analysis and testing tools
└── test_10_samples.py       # Quick test with small samples
```

## 🚀 Quick Start

### 1. Basic Analysis
```bash
# Analyze original BIRD dataset structure
python scripts/bird/bird_integration.py analyze
```

### 2. Test Translation (10 samples)
```bash
# Test with 10 samples first
export OPENAI_API_KEY="your-key-here"
python scripts/bird/bird_integration.py test
```

### 3. Full Processing (200 samples)
```bash
# Process full 200 samples
python scripts/bird/bird_integration.py process --samples 200
```

### 4. Check Results
```bash
# Analyze processed file
python scripts/bird/bird_integration.py check --file dataset/BIRD/bird_vietnamese_200.json
```

## 📊 Expected Output

### Main Output File: `dataset/BIRD/bird_vietnamese_200.json`
```json
[
  {
    "question_id": 73,
    "db_id": "california_schools",
    "question": "What is the free or reduced price meal count...",
    "question_vn": "Số lượng bữa ăn miễn phí hoặc giảm giá...",
    "evidence": "",
    "SQL": "SELECT T1.`FRPM Count (Ages 5-17)` FROM...",
    "difficulty": "simple"
  }
]
```

### Summary Report: `dataset/BIRD/bird_vietnamese_200.summary.txt`
- Distribution statistics
- Sample translations  
- Processing metrics

## 🔧 Advanced Usage

### Direct Script Usage
```bash
# Use individual scripts directly if needed
python scripts/bird/process_bird_dataset.py --help
python scripts/bird/analyze_bird.py original dataset/BIRD/dev.json
python scripts/bird/test_10_samples.py
```

### Custom Parameters
```bash
# Custom sample size
python scripts/bird/bird_integration.py process --samples 100

# Custom input/output
python scripts/bird/bird_integration.py process \
  --input-file custom/bird.json \
  --output-dir custom/output \
  --samples 50
```

## 📈 Processing Statistics

From our test runs:
- **Total BIRD samples**: 1,534
- **Databases covered**: 11 (california_schools, financial, toxicology, etc.)
- **Difficulty distribution**: 60.3% simple, 30.2% moderate, 9.5% challenging
- **Processing time**: ~5 minutes for 200 samples
- **Translation accuracy**: 100% success rate in tests

## 🔍 Data Quality

### Translation Quality Examples:
- ✅ **Simple**: "How many clients..." → "Có bao nhiêu khách hàng..."
- ✅ **Technical**: "non-chartered schools" → "trường không có giấy phép"
- ✅ **Complex**: Multi-clause questions with proper Vietnamese structure

### Coverage:
- ✅ All 11 databases represented
- ✅ Balanced difficulty distribution
- ✅ Technical terms preserved
- ✅ Context from evidence field integrated

## 🛠 Troubleshooting

### Common Issues:
1. **API Key**: Set `OPENAI_API_KEY` environment variable
2. **Rate Limits**: Script includes 1-second delays
3. **Dependencies**: Run `pip install openai python-dotenv`

### File Locations:
- ✅ Input: `dataset/BIRD/dev.json` (1,534 samples)
- ✅ Output: `dataset/BIRD/bird_vietnamese_200.json` (200 processed)
- ✅ Test: `dataset/BIRD/sample_translations.json` (10 samples)

## 🔄 Integration with ViPERSQL

After processing, the BIRD dataset can be integrated into ViPERSQL:

1. **Update config** to support BIRD dataset
2. **Create English templates** for prompts  
3. **Adapt selectors** for cross-lingual scenarios
4. **Run evaluations** to compare with ViText2SQL

Next steps are documented in `docs/BIRD_INTEGRATION_COMPLETE.md`.
