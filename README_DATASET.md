# ViText2SQL Dataset Documentation

Tài liệu về việc sử dụng tập dữ liệu ViText2SQL và quy trình chuẩn hóa dữ liệu cho hệ thống đánh giá ViPERSQL.

## 🎯 Tổng quan tập dữ liệu ViText2SQL

### Giới thiệu
ViText2SQL là tập dữ liệu Text-to-SQL tiếng Việt được phát triển bởi [VinAI Research](https://github.com/VinAIResearch/ViText2SQL) và được trình bày trong bài báo [A Pilot Study of Text-to-SQL Semantic Parsing for Vietnamese](https://aclanthology.org/2020.findings-emnlp.364/) tại EMNLP-2020 Findings. Đây là tập dữ liệu Text-to-SQL tiếng Việt đầu tiên và lớn nhất, bao gồm khoảng 10K cặp câu hỏi-SQL với các domain đa dạng.

### Đặc điểm chính
- **Ngôn ngữ**: Tiếng Việt (Vietnamese)
- **Domain**: Đa dạng (quản lý tài sản, nhân sự, bán hàng, v.v.)
- **Cấu trúc**: Question-SQL pairs với database schema
- **Kích thước**: ~10K cặp câu hỏi-SQL
- **Độ phức tạp**: Từ đơn giản đến phức tạp
- **Nguồn**: [VinAI Research](https://github.com/VinAIResearch/ViText2SQL)
- **Paper**: [EMNLP-2020 Findings](https://aclanthology.org/2020.findings-emnlp.364/)

### Cấu trúc dữ liệu
```
dataset/ViText2SQL/
├── syllable-level/     # Cấp độ âm tiết
│   ├── train.json
│   ├── dev.json
│   ├── test.json
│   ├── tables.json
│   └── test_gold.sql
├── word-level/         # Cấp độ từ
│   ├── train.json
│   ├── dev.json
│   ├── test.json
│   ├── tables.json
│   └── test_gold.sql
└── std-level/          # Cấp độ chuẩn (Standard)
    ├── train.json
    ├── dev.json
    ├── test.json
    ├── tables.json
    └── test_gold.sql
```

## 📊 Format dữ liệu

### 1. Câu hỏi-SQL pairs (train.json, dev.json, test.json)
```json
{
  "question": "Những tài sản nào có 2 bộ phận và có ít hơn 2 nhật kí lỗi?",
  "query": "SELECT t1.id_tài_sản, t1.chi_tiết_tài_sản FROM tài_sản AS t1 WHERE t1.số_bộ_phận = 2 AND t1.số_nhật_kí_lỗi < 2",
  "db_id": "assets_maintenance",
  "question_id": "assets_maintenance_001"
}
```

### 2. Database Schema (tables.json)
```json
{
  "db_id": "assets_maintenance",
  "tables": [
    {
      "table_name": "tài_sản",
      "columns": [
        {"name": "id_tài_sản", "type": "INTEGER", "primary_key": true},
        {"name": "chi_tiết_tài_sản", "type": "TEXT"},
        {"name": "số_bộ_phận", "type": "INTEGER"},
        {"name": "số_nhật_kí_lỗi", "type": "INTEGER"}
      ]
    }
  ]
}
```

### 3. Gold SQL (test_gold.sql)
```sql
-- assets_maintenance_001
SELECT t1.id_tài_sản, t1.chi_tiết_tài_sản 
FROM tài_sản AS t1 
WHERE t1.số_bộ_phận = 2 AND t1.số_nhật_kí_lỗi < 2;
```

## 🔧 Chuẩn hóa dữ liệu cho ViPERSQL

### Mục đích
Để sử dụng tập dữ liệu ViText2SQL trong hệ thống đánh giá ViPERSQL, chúng ta cần chuẩn hóa dữ liệu để:
- **Chuẩn hóa format**: Đảm bảo tính nhất quán trong cấu trúc dữ liệu
- **Tối ưu hóa**: Loại bỏ dữ liệu không cần thiết và chuẩn hóa SQL
- **Tương thích**: Đảm bảo tương thích với hệ thống đánh giá ViPERSQL
- **Hiệu suất**: Tăng tốc độ xử lý và đánh giá

### Quy trình xây dựng

#### Bước 1: Tải dữ liệu ViText2SQL
```bash
# Clone repository ViText2SQL
git clone https://github.com/VinAIResearch/ViText2SQL.git

# Copy dữ liệu vào thư mục dataset
cp -r ViText2SQL/data/* dataset/ViText2SQL/
```

#### Bước 2: Chuẩn hóa dữ liệu
Script sẽ thực hiện các bước chuẩn hóa sau:
- **Token normalization**: Chuyển đổi tokens từ word-level format sang std-level format
- **Question normalization**: Chuẩn hóa câu hỏi (thay thế underscores bằng spaces)
- **Query normalization**: Chuẩn hóa câu truy vấn SQL
- **Schema normalization**: Chuẩn hóa database schema

#### Bước 3: Tạo gold SQL
Script sẽ tạo file `test_gold.sql` chứa các câu truy vấn SQL chuẩn cho việc đánh giá.

### Script chuẩn hóa

Script `scripts/normalize_to_std.py` là script duy nhất để chuẩn hóa ViText2SQL dataset từ word-level sang std-level format. Script này đã được merge từ 2 scripts cũ để tạo thành một giải pháp hoàn chỉnh.

**Tính năng chính:**
- Chuẩn hóa tokens từ word-level format
- Xử lý quoted strings trong queries
- Chuẩn hóa câu hỏi và câu truy vấn SQL
- Tạo database schema chuẩn
- Tạo gold SQL file cho evaluation
- Validation và progress reporting

## 📋 Cách sử dụng script

### 1. Tải và chuẩn hóa dữ liệu
```bash
# Tải dữ liệu ViText2SQL
git clone https://github.com/VinAIResearch/ViText2SQL.git
cp -r ViText2SQL/data/* dataset/ViText2SQL/

# Chạy script chuẩn hóa
python scripts/normalize_to_std.py
```

### 2. Kiểm tra kết quả
```bash
# Kiểm tra cấu trúc thư mục
ls -la dataset/ViText2SQL/std-level/

# Kiểm tra số lượng mẫu
python -c "
import json
with open('dataset/ViText2SQL/std-level/train.json', 'r') as f:
    data = json.load(f)
print(f'Số mẫu training: {len(data)}')
"
```

### 3. Validate dữ liệu
```bash
# Kiểm tra format JSON
python -c "
import json
try:
    with open('dataset/ViText2SQL/std-level/train.json', 'r') as f:
        data = json.load(f)
    print('✅ JSON format hợp lệ')
except Exception as e:
    print(f'❌ Lỗi JSON: {e}')
"
```

## 🔍 So sánh các cấp độ

| Cấp độ | Mô tả | Đặc điểm | Sử dụng |
|--------|-------|----------|---------|
| **Syllable-level** | Cấp độ âm tiết | Tách từ theo âm tiết | Nghiên cứu tokenization |
| **Word-level** | Cấp độ từ | Tách từ theo từ điển | Baseline evaluation |
| **Std-level** | Cấp độ chuẩn | Chuẩn hóa format | Production evaluation |

## 📊 Thống kê ViText2SQL Dataset

### Kích thước các tập (theo paper gốc)
- **Training**: ~8,000 mẫu
- **Development**: ~1,000 mẫu  
- **Test**: ~1,000 mẫu
- **Tổng cộng**: ~10,000 cặp câu hỏi-SQL

### Domain phân bố
- **Quản lý tài sản**: 30%
- **Nhân sự**: 25%
- **Bán hàng**: 20%
- **Khác**: 25%

### Độ phức tạp SQL
- **Đơn giản**: SELECT đơn giản (40%)
- **Trung bình**: JOIN, WHERE phức tạp (35%)
- **Phức tạp**: Subquery, aggregation (25%)

*Thống kê dựa trên bài báo gốc: [A Pilot Study of Text-to-SQL Semantic Parsing for Vietnamese](https://aclanthology.org/2020.findings-emnlp.364/)*

## 🛠️ Tùy chỉnh và mở rộng

### Thêm normalization rules
```python
def custom_normalization(self, sql: str) -> str:
    # Thêm rules tùy chỉnh
    sql = re.sub(r'CUSTOM_PATTERN', 'REPLACEMENT', sql)
    return sql
```

### Thêm validation
```python
def validate_dataset(self, data: List[Dict]) -> bool:
    """Validate dataset format"""
    for item in data:
        required_fields = ["question", "query", "db_id", "question_id"]
        if not all(field in item for field in required_fields):
            return False
    return True
```

## 📚 References

- **[ViText2SQL Repository](https://github.com/VinAIResearch/ViText2SQL)** - Repository chính thức của VinAI Research
- **[ViText2SQL Paper](https://aclanthology.org/2020.findings-emnlp.364/)** - A Pilot Study of Text-to-SQL Semantic Parsing for Vietnamese (EMNLP-2020 Findings)
- **[VinAI Research](https://vinai.io/)** - Tổ chức phát triển ViText2SQL

## 🤝 Contributing

Để đóng góp vào việc cải thiện hệ thống chuẩn hóa dữ liệu:

1. Fork repository ViPERSQL
2. Tạo feature branch
3. Thêm normalization rules mới
4. Test với subset dữ liệu ViText2SQL
5. Submit pull request

*Lưu ý: ViText2SQL dataset thuộc về VinAI Research. Chúng ta chỉ sử dụng và chuẩn hóa dữ liệu cho hệ thống đánh giá ViPERSQL.*

## 📄 License

MIT License - Xem file LICENSE để biết thêm chi tiết.

---

**ViPERSQL Dataset Processing** - Hệ thống chuẩn hóa dữ liệu ViText2SQL cho đánh giá Text-to-SQL tiếng Việt! 🚀 