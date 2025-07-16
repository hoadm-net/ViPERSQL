# 🔍 Hướng Dẫn Sử Dụng Sample Viewer - ViText2SQL

## 📋 Tổng Quan

Tool `sample_viewer.py` là một công cụ toàn diện giúp bạn khám phá dataset ViText2SQL. Nó hiển thị thông tin chi tiết về từng sample bao gồm câu hỏi tiếng Việt, truy vấn SQL, schema database, và phân tích cấu trúc.

## 🚀 Cách Sử Dụng Cơ Bản

### 1. Xem Sample Đầu Tiên của Tập Train
```bash
python sample_viewer.py -s train -i 0
```

### 2. Xem Sample với Phân Tích SQL Chi Tiết
```bash
python sample_viewer.py -s train -i 0 --show-sql-structure
```

### 3. Xem Sample từ Tập Dev với Word-level Tokenization
```bash
python sample_viewer.py -s dev -i 5 -l word
```

### 4. Xem Sample từ Tập Test
```bash
python sample_viewer.py -s test -i 10
```

## 📝 Các Tham Số Command Line

| Tham số | Viết tắt | Bắt buộc | Tùy chọn | Mặc định | Mô tả |
|---------|----------|----------|----------|----------|--------|
| `--split` | `-s` | Có | `train`, `dev`, `test` | - | Chọn tập dữ liệu |
| `--index` | `-i` | Có | Số nguyên từ 0 | - | Chỉ số sample cần xem |
| `--level` | `-l` | Không | `syllable`, `word` | `syllable` | Mức độ tokenization |
| `--dataset-path` | - | Không | Đường dẫn | `dataset/ViText2SQL` | Thư mục chứa dataset |
| `--show-sql-structure` | - | Không | - | False | Hiển thị phân tích SQL chi tiết |

## 🎯 Ví Dụ Cụ Thể

### Ví Dụ 1: Xem Sample Cơ Bản
```bash
python sample_viewer.py -s train -i 0
```

**Kết quả sẽ hiển thị:**
- Thông tin meta: index, split, level, database ID
- Câu hỏi tiếng Việt và tokenization
- Truy vấn SQL và các biến thể tokenization
- Schema database (bảng, cột, khóa)
- Thống kê tổng hợp

### Ví Dụ 2: Phân Tích SQL Chi Tiết
```bash
python sample_viewer.py -s train -i 5 --show-sql-structure
```

**Thêm thông tin:**
- Đánh giá độ phức tạp (Easy/Medium/Hard/Extra Hard)
- Phân tích thành phần SQL (SELECT, WHERE, GROUP BY, v.v.)
- Cấu trúc JSON chi tiết của SQL được parse

### Ví Dụ 3: So Sánh Tokenization Levels
```bash
# Xem cùng sample với syllable-level
python sample_viewer.py -s dev -i 0 -l syllable

# Xem cùng sample với word-level
python sample_viewer.py -s dev -i 0 -l word
```

## 📊 Thông Tin Hiển Thị

### 🔢 Thông Tin Cơ Bản
- **Sample Index**: Vị trí của sample trong dataset
- **Split**: Tập dữ liệu (TRAIN/DEV/TEST)
- **Level**: Mức tokenization (syllable/word)
- **Database ID**: Tên database được sử dụng

### ❓ Thông Tin Câu Hỏi
- **Vietnamese Question**: Câu hỏi gốc bằng tiếng Việt
- **Tokenized Question**: Câu hỏi đã được tách từ
- **Question Length**: Số lượng token trong câu hỏi

### 🗃️ Thông Tin SQL Query
- **SQL Query**: Truy vấn SQL gốc
- **Tokenized SQL**: SQL đã được tách token
- **SQL Tokens (no values)**: SQL với giá trị được thay thế bằng "value"
- **SQL Length**: Số lượng token trong SQL

### 🗂️ Thông Tin Database Schema
- **Tables**: Danh sách các bảng với chỉ số
- **Columns**: Danh sách cột theo format `table.column`
- **Foreign Keys**: Các khóa ngoại
- **Primary Keys**: Các khóa chính

### 🔍 Phân Tích SQL (với --show-sql-structure)
- **Complexity**: Mức độ phức tạp của truy vấn
- **Components**: Các thành phần SQL có trong truy vấn
- **Detailed Structure**: Cấu trúc JSON đầy đủ

## 📈 Mức Độ Phức Tạp SQL

Tool tự động phân loại độ phức tạp của truy vấn SQL:

- **Easy**: SELECT đơn giản với điều kiện WHERE cơ bản
- **Medium**: Có GROUP BY, ORDER BY, hoặc các phép toán đơn giản
- **Hard**: Truy vấn phức tạp với nhiều bảng hoặc phép toán nâng cao
- **Extra Hard**: Truy vấn lồng nhau, UNION, INTERSECT, hoặc rất phức tạp

## 🎯 Các Trường Hợp Sử Dụng

### 1. Khám Phá Dataset
```bash
# Xem các sample khác nhau để hiểu cấu trúc
python sample_viewer.py -s train -i 0
python sample_viewer.py -s train -i 100
python sample_viewer.py -s train -i 500
```

### 2. Phân Tích Độ Phức Tạp
```bash
# Tìm các sample đơn giản
python sample_viewer.py -s train -i 1 --show-sql-structure

# Tìm các sample phức tạp
python sample_viewer.py -s train -i 50 --show-sql-structure
```

### 3. So Sánh Tokenization
```bash
# So sánh syllable vs word level
python sample_viewer.py -s dev -i 0 -l syllable
python sample_viewer.py -s dev -i 0 -l word
```

### 4. Kiểm Tra Database Schemas
```bash
# Xem các database khác nhau
python sample_viewer.py -s train -i 0  # academic database
python sample_viewer.py -s dev -i 0   # architecture database
```

## 🔧 Troubleshooting

### Lỗi Index Out of Range
```bash
❌ Error: Index 10000 out of range. Dataset has 6831 samples (0-6830)
```
**Giải pháp**: Sử dụng index từ 0 đến (total_samples - 1)

### Lỗi File Not Found
```bash
❌ Error: Dataset file not found: dataset/ViText2SQL/syllable-level/train.json
```
**Giải pháp**: Kiểm tra đường dẫn dataset hoặc dùng `--dataset-path`

### Dataset Quá Lớn
Nếu bạn muốn xem thống kê nhanh về dataset:
```bash
# Xem một vài sample đầu
python sample_viewer.py -s train -i 0
python sample_viewer.py -s train -i 1
python sample_viewer.py -s train -i 2
```

## 💡 Tips Hữu Ích

### 1. Tìm Sample Theo Database
Để xem các sample của một database cụ thể, bạn có thể chạy nhiều lệnh:
```bash
# Xem các sample khác nhau để tìm database mong muốn
python sample_viewer.py -s train -i 0
python sample_viewer.py -s train -i 10
python sample_viewer.py -s train -i 20
```

### 2. Phân Tích Từng Tập Dữ Liệu
```bash
# Train set (6,831 samples)
python sample_viewer.py -s train -i 0

# Dev set (954 samples) 
python sample_viewer.py -s dev -i 0

# Test set (1,908 samples)
python sample_viewer.py -s test -i 0
```

### 3. So Sánh Complexity Levels
```bash
# Tìm sample Easy
python sample_viewer.py -s train -i 5 --show-sql-structure

# Tìm sample Hard (thường có index cao hơn)
python sample_viewer.py -s train -i 1000 --show-sql-structure
```

## 📚 Thông Tin Thống Kê Dataset

### Tổng Quan
- **Train**: 6,831 samples (70.5%)
- **Dev**: 954 samples (9.8%)
- **Test**: 1,908 samples (19.7%)
- **Tổng cộng**: 9,693 samples
- **Databases**: 166 databases độc lập

### Phân Bố Độ Phức Tạp
- **Easy**: 39.5% - Truy vấn SELECT đơn giản
- **Medium**: 13.5% - Có GROUP BY, ORDER BY
- **Hard**: 36.5% - JOINs phức tạp
- **Extra**: 10.5% - Truy vấn lồng nhau, UNION

## 🔗 Tích Hợp với Workflow

### Cho Research
```bash
# Khám phá dataset trước khi train model
python sample_viewer.py -s train -i 0 --show-sql-structure

# Phân tích validation samples
python sample_viewer.py -s dev -i 0 --show-sql-structure

# Kiểm tra test samples
python sample_viewer.py -s test -i 0 --show-sql-structure
```

### Cho Development
```bash
# Debug specific samples
python sample_viewer.py -s train -i 123 --show-sql-structure

# Validate preprocessing pipeline
python sample_viewer.py -s train -i 0 -l syllable
python sample_viewer.py -s train -i 0 -l word
```

## 🎉 Kết Luận

Tool `sample_viewer.py` là công cụ essential để:
- ✅ Hiểu cấu trúc dataset ViText2SQL
- ✅ Phân tích samples cụ thể
- ✅ Đánh giá độ phức tạp truy vấn
- ✅ So sánh tokenization levels
- ✅ Debug và validate data pipeline

Hãy thử các ví dụ trên để làm quen với tool và khám phá dataset ViText2SQL một cách hiệu quả! 