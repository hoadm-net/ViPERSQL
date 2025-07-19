# Tạo Std-Level từ Word-Level

Script `create_std_level.py` được sử dụng để chuyển đổi dữ liệu từ format **word-level** sang format **std-level** chuẩn hóa.

## 🎯 Mục đích

Chuẩn hóa dữ liệu ViText2SQL để có format nhất quán:
- **Word-level**: Format hỗn hợp (có cả space và underscore)
- **Std-level**: Format chuẩn snake_case cho SQL, space cho text

## 📁 Cấu trúc Input/Output

### Input (Word-Level)
```
dataset/ViText2SQL/word-level/
├── tables.json      # Schema với format hỗn hợp
├── train.json       # Dữ liệu training
├── dev.json         # Dữ liệu validation  
└── test.json        # Dữ liệu testing
```

### Output (Std-Level)
```
dataset/ViText2SQL/std-level/
├── tables.json      # Schema đã chuẩn hóa
├── train.json       # Dữ liệu đã chuẩn hóa
├── dev.json         # Dữ liệu đã chuẩn hóa
└── test.json        # Dữ liệu đã chuẩn hóa
```

## 🔧 Cách sử dụng

```bash
python create_std_level.py
```

Script sẽ tự động:
1. Tạo thư mục `std-level` nếu chưa tồn tại
2. Chuẩn hóa schema trong `tables.json`
3. Chuẩn hóa dữ liệu trong `train.json`, `dev.json`, `test.json`

## 📝 Quy tắc chuẩn hóa

### 1. Schema (tables.json)
- **Table names**: `"rạp chiếu_phim"` → `"rạp_chiếu_phim"`
- **Column names**: `"năm xây_dựng"` → `"năm_xây_dựng"`

### 2. Query (trong train/dev/test.json)
- **Tokens**: `"năm xây_dựng"` → `"năm_xây_dựng"`
- **Quoted strings**: `"Plaza_Museum"` → `"Plaza Museum"`

### 3. Question (trong train/dev/test.json)
- **Text**: `"năm mở_cửa"` → `"năm mở cửa"`

## 🔄 Quy trình xử lý

```python
# 1. Chuẩn hóa token
def normalize_token(token):
    token_with_spaces = token.replace('_', ' ')
    parts = token_with_spaces.split()
    return '_'.join(parts)

# 2. Xử lý chuỗi trong nháy kép
def fix_quoted_strings(query):
    # "Plaza_Museum" → "Plaza Museum"
    pattern = r'"([^"]*)"'
    return re.sub(pattern, replace_in_quotes, query)

# 3. Chuẩn hóa question
def normalize_question(question):
    # "năm mở_cửa" → "năm mở cửa"
    return question.replace('_', ' ')
```

## 📊 Ví dụ chuyển đổi

### Input (Word-Level)
```json
{
  "db_id": "cinema",
  "question": "Hiển_thị tên và năm mở_cửa của rạp chiếu_phim .",
  "query_toks": ["select", "tên", ",", "năm mở_cửa", "from", "rạp chiếu_phim"],
  "query": "select tên , năm mở_cửa from rạp chiếu_phim"
}
```

### Output (Std-Level)
```json
{
  "db_id": "cinema", 
  "question": "Hiển thị tên và năm mở cửa của rạp chiếu phim .",
  "query": "select tên , năm_mở_cửa from rạp_chiếu_phim"
}
```

## ✅ Kết quả

Script sẽ tạo ra:
- ✅ **6831 samples** trong `train.json`
- ✅ **954 samples** trong `dev.json` 
- ✅ **1908 samples** trong `test.json`
- ✅ **Schema chuẩn hóa** trong `tables.json`

## 🚀 Tính năng

- **Tự động**: Không cần cấu hình thêm
- **Nhanh chóng**: Xử lý hàng nghìn samples trong vài giây
- **An toàn**: Tạo backup tự động, không ghi đè dữ liệu gốc
- **Linh hoạt**: Có thể chạy lại nhiều lần

## 🔍 Kiểm tra kết quả

Script sẽ hiển thị ví dụ chuyển đổi để kiểm tra:

```
📊 Ví dụ chuẩn hóa:

Ví dụ 1:
  Word-level question: Có tất_cả bao_nhiêu kiến_trúc_sư nữ ?
  Std-level question: Có tất cả bao nhiêu kiến trúc sư nữ ?
  Word-level query_toks: ['select', 'count', '(', '*', ')', 'from', 'kiến_trúc_sư', 'where', 'giới_tính', '=']...
  Std-level query: select count ( * ) from kiến_trúc_sư where giới_tính = "female"...
```

## 📝 Lưu ý

- Dữ liệu gốc trong `word-level/` không bị thay đổi
- Script có thể chạy lại nhiều lần an toàn
- Nếu có lỗi, kiểm tra đường dẫn file input
- Đảm bảo có đủ quyền ghi vào thư mục `dataset/`

---

**Tác giả**: ViPERSQL Team  
**Ngày tạo**: 2024  
**Phiên bản**: 1.0 