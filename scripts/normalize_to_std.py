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
        print(f"📁 Chuẩn hóa dữ liệu ViText2SQL cho ViPERSQL")
        print(f"📂 Thư mục gốc: {self.base_path}")
        print(f"📂 Thư mục đích: {self.std_path}")
    
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
        """Xử lý toàn bộ dataset"""
        print("🚀 Bắt đầu chuẩn hóa ViText2SQL dataset...")
        
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
        
        print("🎉 Hoàn thành chuẩn hóa dataset!")

def main():
    normalizer = DatasetNormalizer()
    normalizer.process_all()

if __name__ == "__main__":
    main() 