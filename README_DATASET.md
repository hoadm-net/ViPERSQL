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
```python
# scripts/normalize_to_std.py
import json
import re
from typing import Dict, List, Any

def normalize_sql_query(sql: str) -> str:
    """Chuẩn hóa câu truy vấn SQL cho ViPERSQL"""
    # Loại bỏ khoảng trắng dư thừa
    sql = re.sub(r'\s+', ' ', sql.strip())
    
    # Chuẩn hóa alias format
    sql = re.sub(r'FROM\s+(\w+)\s+AS\s+(\w+)', r'FROM \1 AS \2', sql)
    
    # Loại bỏ dấu chấm phẩy cuối
    sql = sql.rstrip(';')
    
    return sql

def normalize_dataset(input_file: str, output_file: str):
    """Chuẩn hóa dataset ViText2SQL cho ViPERSQL"""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    normalized_data = []
    for item in data:
        normalized_item = {
            "question": item["question"].strip(),
            "query": normalize_sql_query(item["query"]),
            "db_id": item["db_id"],
            "question_id": item["question_id"]
        }
        normalized_data.append(normalized_item)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(normalized_data, f, ensure_ascii=False, indent=2)
```

#### Bước 3: Chuẩn hóa schema
```python
def normalize_schema(input_file: str, output_file: str):
    """Chuẩn hóa database schema"""
    with open(input_file, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    # Chuẩn hóa tên bảng và cột
    for table in schema["tables"]:
        table["table_name"] = table["table_name"].strip()
        for column in table["columns"]:
            column["name"] = column["name"].strip()
            column["type"] = column["type"].upper()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
```

#### Bước 4: Tạo gold SQL file
```python
def create_gold_sql(data_file: str, output_file: str):
    """Tạo file gold SQL cho test set"""
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    gold_sql = []
    for item in data:
        sql_line = f"-- {item['question_id']}\n{item['query']};"
        gold_sql.append(sql_line)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(gold_sql))
```

### Script hoàn chỉnh

```python
#!/usr/bin/env python3
"""
Script chuẩn hóa ViText2SQL dataset cho hệ thống đánh giá ViPERSQL
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any

class DatasetNormalizer:
    def __init__(self, base_path: str = "dataset/ViText2SQL"):
        self.base_path = Path(base_path)
        self.std_path = self.base_path / "std-level"
        self.std_path.mkdir(exist_ok=True)
    
    def normalize_sql_query(self, sql: str) -> str:
        """Chuẩn hóa câu truy vấn SQL"""
        # Loại bỏ khoảng trắng dư thừa
        sql = re.sub(r'\s+', ' ', sql.strip())
        
        # Chuẩn hóa alias format
        sql = re.sub(r'FROM\s+(\w+)\s+AS\s+(\w+)', r'FROM \1 AS \2', sql)
        
        # Loại bỏ dấu chấm phẩy cuối
        sql = sql.rstrip(';')
        
        return sql
    
    def normalize_dataset(self, input_file: str, output_file: str):
        """Chuẩn hóa dataset file"""
        print(f"Chuẩn hóa {input_file} -> {output_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        normalized_data = []
        for item in data:
            normalized_item = {
                "question": item["question"].strip(),
                "query": self.normalize_sql_query(item["query"]),
                "db_id": item["db_id"],
                "question_id": item["question_id"]
            }
            normalized_data.append(normalized_item)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(normalized_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Đã chuẩn hóa {len(normalized_data)} mẫu")
    
    def normalize_schema(self, input_file: str, output_file: str):
        """Chuẩn hóa database schema"""
        print(f"Chuẩn hóa schema {input_file} -> {output_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        # Chuẩn hóa tên bảng và cột
        for table in schema["tables"]:
            table["table_name"] = table["table_name"].strip()
            for column in table["columns"]:
                column["name"] = column["name"].strip()
                column["type"] = column["type"].upper()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
        
        print("✅ Đã chuẩn hóa schema")
    
    def create_gold_sql(self, data_file: str, output_file: str):
        """Tạo file gold SQL cho test set"""
        print(f"Tạo gold SQL {data_file} -> {output_file}")
        
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        gold_sql = []
        for item in data:
            sql_line = f"-- {item['question_id']}\n{item['query']};"
            gold_sql.append(sql_line)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(gold_sql))
        
        print(f"✅ Đã tạo gold SQL cho {len(gold_sql)} mẫu")
    
    def process_all(self):
        """Xử lý toàn bộ dataset ViText2SQL cho ViPERSQL"""
        print("🚀 Bắt đầu chuẩn hóa ViText2SQL dataset cho ViPERSQL...")
        
        # Sử dụng word-level làm nguồn dữ liệu gốc
        source_path = self.base_path / "word-level"
        
        # Chuẩn hóa các file dataset
        for split in ["train", "dev", "test"]:
            input_file = source_path / f"{split}.json"
            output_file = self.std_path / f"{split}.json"
            
            if input_file.exists():
                self.normalize_dataset(str(input_file), str(output_file))
        
        # Chuẩn hóa schema
        schema_input = source_path / "tables.json"
        schema_output = self.std_path / "tables.json"
        
        if schema_input.exists():
            self.normalize_schema(str(schema_input), str(schema_output))
        
        # Tạo gold SQL cho test set
        test_file = self.std_path / "test.json"
        gold_sql_file = self.std_path / "test_gold.sql"
        
        if test_file.exists():
            self.create_gold_sql(str(test_file), str(gold_sql_file))
        
        print("🎉 Hoàn thành chuẩn hóa dataset cho ViPERSQL!")

def main():
    normalizer = DatasetNormalizer()
    normalizer.process_all()

if __name__ == "__main__":
    main()
```

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