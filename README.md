# ViPERSQL: Vietnamese NL2SQL Prompting & Evaluation Toolkit

## Mục đích
Project này cung cấp các chiến lược Prompting hiện đại cho bài toán Vietnamese Text-to-SQL (NL2SQL) và bộ công cụ đánh giá kết quả truy vấn SQL.

## Thành phần chính
- **3 chiến lược Prompting:**
  - **Zero-shot**: Chuyển đổi câu hỏi sang SQL không cần ví dụ.
  - **Few-shot**: Sử dụng k ví dụ mẫu để hướng dẫn LLM sinh SQL.
  - **Chain-of-Thought (CoT)**: Hỗ trợ suy luận từng bước trước khi sinh SQL.
- **Đánh giá:**
  - Đánh giá exact match, component-wise F1, phân tích độ phức tạp, v.v.

## Cấu trúc project
```
mint/
├── strategies/           # Các chiến lược prompting
│   ├── zero_shot.py
│   ├── few_shot.py
│   ├── cot.py
│   ├── base.py
│   └── __init__.py
├── metrics.py            # Đánh giá F1, exact match, difficulty...
├── evaluator.py          # Module đánh giá tổng hợp
├── strategy_manager.py   # Quản lý và gọi các chiến lược
├── template_manager.py   # Quản lý template prompt
├── config.py             # Cấu hình hệ thống
├── utils.py              # Tiện ích chung
└── __init__.py           # Khởi tạo package
```

## Hướng dẫn sử dụng
### 1. Chọn và chạy chiến lược Prompting
```python
from mint import StrategyManager, ViPERConfig

config = ViPERConfig(strategy="few-shot", model_name="gpt-4o-mini")
manager = StrategyManager(config)

question = "Có bao nhiêu sinh viên?"
schema_info = {...}  # Thông tin schema
result = manager.generate_sql(question, schema_info, db_id="school")
print(result.sql_query)
```

### 2. Đánh giá kết quả truy vấn
```python
from mint.metrics import EvaluationMetrics
metrics = EvaluationMetrics()

predicted = ["SELECT COUNT(*) FROM students"]
gold = ["SELECT COUNT(*) FROM students"]
print(metrics.exact_match_accuracy(predicted, gold))
print(metrics.component_wise_f1_score(predicted, gold))
```

## Lưu ý
- Project đã clean, chỉ giữ lại các module cần thiết cho Prompting và Đánh giá.
- Không còn các file log, test, markdown cũ, hoặc các module không liên quan.
- Nếu muốn mở rộng thêm chiến lược hoặc đánh giá, chỉ cần thêm vào các module tương ứng.

## Liên hệ
- Nếu có vấn đề về sử dụng hoặc muốn đóng góp chiến lược mới, hãy tạo issue hoặc pull request trên GitHub.