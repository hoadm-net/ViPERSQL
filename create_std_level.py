#!/usr/bin/env python3
"""
Script tổng hợp để tạo std-level từ word-level.
Bao gồm:
1. Tạo tables.json (chuẩn hóa schema)
2. Tạo train.json, dev.json, test.json (chuẩn hóa dữ liệu)
"""

import json
import re
from pathlib import Path

def load_json_file(file_path):
    """Load JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(data, file_path):
    """Save data to JSON file."""
    # Tạo thư mục nếu chưa tồn tại
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def normalize_token(token):
    """
    Normalize a token from word-level to std-level format.
    - Replace underscores with spaces first, then convert to snake_case
    """
    # First, replace underscores with spaces to get the original form
    token_with_spaces = token.replace('_', ' ')
    
    # Then convert to proper snake_case
    # Split by spaces and join with underscores
    parts = token_with_spaces.split()
    normalized = '_'.join(parts)
    
    return normalized

def fix_quoted_strings(query):
    """
    Fix quoted strings in query: replace underscores with spaces inside quotes.
    """
    def replace_in_quotes(match):
        quoted_content = match.group(1)
        # Replace underscores with spaces inside quotes
        fixed_content = quoted_content.replace('_', ' ')
        return f'"{fixed_content}"'
    
    # Find all quoted strings and fix them
    pattern = r'"([^"]*)"'
    fixed_query = re.sub(pattern, replace_in_quotes, query)
    
    return fixed_query

def normalize_question(question):
    """
    Normalize question: replace all underscores with spaces.
    """
    return question.replace('_', ' ')

def normalize_schema(word_schema):
    """
    Normalize schema from word-level to std-level format.
    """
    normalized_schema = {}
    
    # Copy basic fields
    for key in ['db_id', 'foreign_keys', 'primary_keys']:
        if key in word_schema:
            normalized_schema[key] = word_schema[key]
    
    # Normalize table names
    normalized_schema['table_names'] = []
    normalized_schema['table_names_original'] = []
    for table_name in word_schema['table_names']:
        normalized_name = normalize_token(table_name)
        normalized_schema['table_names'].append(normalized_name)
        normalized_schema['table_names_original'].append(normalized_name)
    
    # Normalize column names
    normalized_schema['column_names'] = []
    normalized_schema['column_names_original'] = []
    for col_info in word_schema['column_names']:
        table_idx, col_name = col_info
        normalized_col_name = normalize_token(col_name)
        normalized_schema['column_names'].append([table_idx, normalized_col_name])
        normalized_schema['column_names_original'].append([table_idx, normalized_col_name])
    
    # Normalize column types
    if 'column_types' in word_schema:
        normalized_schema['column_types'] = word_schema['column_types']
    
    return normalized_schema

def process_query_toks(query_toks):
    """
    Process query_toks and normalize tokens using simple replace.
    """
    normalized_toks = []
    
    for token in query_toks:
        # Simply normalize each token
        normalized_toks.append(normalize_token(token))
    
    return normalized_toks

def normalize_data(word_level_data):
    """
    Normalize data from word-level to std-level format.
    """
    normalized_data = []
    
    for word_item in word_level_data:
        # Process query_toks
        normalized_toks = process_query_toks(word_item['query_toks'])
        
        # Join tokens to create normalized query
        normalized_query = ' '.join(normalized_toks)
        
        # Fix quoted strings (replace underscores with spaces inside quotes)
        normalized_query = fix_quoted_strings(normalized_query)
        
        # Normalize question (replace underscores with spaces)
        normalized_question = normalize_question(word_item['question'])
        
        # Create normalized item
        normalized_item = {
            'db_id': word_item['db_id'],
            'question': normalized_question,
            'query': normalized_query
        }
        
        normalized_data.append(normalized_item)
    
    return normalized_data

def create_std_level():
    """
    Main function to create std-level from word-level.
    """
    print("🚀 Bắt đầu tạo std-level từ word-level...")
    
    # File paths
    word_level_dir = Path('dataset/ViText2SQL/word-level')
    std_level_dir = Path('dataset/ViText2SQL/std-level')
    
    # Input files
    word_tables = word_level_dir / 'tables.json'
    word_train = word_level_dir / 'train.json'
    word_dev = word_level_dir / 'dev.json'
    word_test = word_level_dir / 'test.json'
    
    # Output files
    std_tables = std_level_dir / 'tables.json'
    std_train = std_level_dir / 'train.json'
    std_dev = std_level_dir / 'dev.json'
    std_test = std_level_dir / 'test.json'
    
    # 1. Tạo tables.json
    print("\n📋 Bước 1: Tạo tables.json...")
    word_schemas = load_json_file(word_tables)
    std_schemas = []
    
    for schema in word_schemas:
        normalized_schema = normalize_schema(schema)
        std_schemas.append(normalized_schema)
    
    save_json_file(std_schemas, std_tables)
    print(f"✅ Đã tạo {std_tables}")
    
    # 2. Tạo train.json
    print("\n📚 Bước 2: Tạo train.json...")
    if word_train.exists():
        word_train_data = load_json_file(word_train)
        normalized_train = normalize_data(word_train_data)
        save_json_file(normalized_train, std_train)
        print(f"✅ Đã tạo {std_train} với {len(normalized_train)} samples")
    else:
        print("⚠️ Không tìm thấy train.json trong word-level")
    
    # 3. Tạo dev.json
    print("\n🧪 Bước 3: Tạo dev.json...")
    if word_dev.exists():
        word_dev_data = load_json_file(word_dev)
        normalized_dev = normalize_data(word_dev_data)
        save_json_file(normalized_dev, std_dev)
        print(f"✅ Đã tạo {std_dev} với {len(normalized_dev)} samples")
    else:
        print("⚠️ Không tìm thấy dev.json trong word-level")
    
    # 4. Tạo test.json
    print("\n🧪 Bước 4: Tạo test.json...")
    if word_test.exists():
        word_test_data = load_json_file(word_test)
        normalized_test = normalize_data(word_test_data)
        save_json_file(normalized_test, std_test)
        print(f"✅ Đã tạo {std_test} với {len(normalized_test)} samples")
    else:
        print("⚠️ Không tìm thấy test.json trong word-level")
    
    # 5. Kiểm tra kết quả
    print("\n🔍 Bước 5: Kiểm tra kết quả...")
    
    # Kiểm tra một số ví dụ
    if word_dev.exists() and std_dev.exists():
        word_dev_data = load_json_file(word_dev)
        std_dev_data = load_json_file(std_dev)
        
        print("\n📊 Ví dụ chuẩn hóa:")
        for i, (word_item, std_item) in enumerate(zip(word_dev_data[:3], std_dev_data[:3])):
            print(f"\nVí dụ {i+1}:")
            print(f"  Word-level question: {word_item['question']}")
            print(f"  Std-level question: {std_item['question']}")
            print(f"  Word-level query_toks: {word_item['query_toks'][:10]}...")
            print(f"  Std-level query: {std_item['query'][:100]}...")
    
    print(f"\n🎉 Hoàn thành! Std-level đã được tạo tại: {std_level_dir}")
    print(f"📁 Các file đã tạo:")
    print(f"   - {std_tables}")
    print(f"   - {std_train}")
    print(f"   - {std_dev}")
    print(f"   - {std_test}")

if __name__ == "__main__":
    create_std_level() 