#!/usr/bin/env python3
"""
Small Test for BIRD Processing with 10 samples

Uses the existing test_subset.json to test translation with real API.
"""

import json
import os
import time
from pathlib import Path
import openai
from dotenv import load_dotenv


def load_test_samples(limit=10):
    """Load first 10 samples from test subset"""
    test_file = "dataset/BIRD/test_subset.json"
    
    with open(test_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data[:limit]


def translate_to_vietnamese(client, question, evidence=""):
    """Translate question to Vietnamese using ChatGPT"""
    prompt = f"""Bạn là một chuyên gia dịch thuật chuyên về SQL và cơ sở dữ liệu. 
Hãy dịch câu hỏi tiếng Anh sau sang tiếng Việt một cách tự nhiên và chính xác, giữ nguyên ý nghĩa và ngữ cảnh kỹ thuật.

Câu hỏi tiếng Anh: "{question}"
"""
    
    if evidence.strip():
        prompt += f"""
Thông tin bổ sung: "{evidence}"
"""
    
    prompt += """
Yêu cầu:
1. Dịch sang tiếng Việt tự nhiên, dễ hiểu
2. Giữ nguyên các thuật ngữ kỹ thuật quan trọng
3. Đảm bảo ý nghĩa chính xác
4. Chỉ trả về câu dịch tiếng Việt, không giải thích thêm

Câu dịch tiếng Việt:"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use cheaper model for testing
            messages=[
                {"role": "system", "content": "Bạn là một chuyên gia dịch thuật chuyên về SQL và cơ sở dữ liệu."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.3
        )
        
        translation = response.choices[0].message.content.strip()
        return translation
        
    except Exception as e:
        print(f"Translation error: {e}")
        return f"[TRANSLATION_ERROR] {question}"


def test_bird_translation():
    """Test BIRD translation with 10 samples"""
    print("🧪 Testing BIRD Translation with 10 samples")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        return
    
    print(f"✅ API key found: {api_key[:8]}...")
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=api_key)
    
    # Load test samples
    samples = load_test_samples(10)
    print(f"✅ Loaded {len(samples)} test samples")
    
    # Process samples
    processed_samples = []
    
    for i, sample in enumerate(samples):
        print(f"\n📝 Processing sample {i+1}/10...")
        print(f"   ID: {sample['question_id']}")
        print(f"   DB: {sample['db_id']}")
        print(f"   Difficulty: {sample['difficulty']}")
        print(f"   EN: {sample['question'][:80]}...")
        
        # Translate
        question_vn = translate_to_vietnamese(
            client, 
            sample['question'], 
            sample.get('evidence', '')
        )
        
        print(f"   VN: {question_vn[:80]}...")
        
        # Create processed sample
        processed_sample = {
            'question_id': sample['question_id'],
            'db_id': sample['db_id'],
            'question': sample['question'],
            'question_vn': question_vn,
            'evidence': sample.get('evidence', ''),
            'SQL': sample['SQL'],
            'difficulty': sample['difficulty']
        }
        
        processed_samples.append(processed_sample)
        
        # Rate limiting
        time.sleep(1)
    
    # Save results
    output_file = "dataset/BIRD/test_translation_10.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_samples, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Show summary
    print(f"\n📊 Translation Summary:")
    errors = sum(1 for s in processed_samples if s['question_vn'].startswith('[TRANSLATION_ERROR]'))
    print(f"   Total samples: {len(processed_samples)}")
    print(f"   Successful translations: {len(processed_samples) - errors}")
    print(f"   Translation errors: {errors}")
    
    # Show sample results
    print(f"\n📋 Sample Results:")
    for i, sample in enumerate(processed_samples[:3]):
        print(f"\n{i+1}. {sample['question_id']} ({sample['db_id']}, {sample['difficulty']})")
        print(f"   EN: {sample['question']}")
        print(f"   VN: {sample['question_vn']}")
        if sample['evidence']:
            print(f"   Evidence: {sample['evidence'][:60]}...")
    
    print(f"\n✅ Test completed successfully!")
    return processed_samples


if __name__ == "__main__":
    test_bird_translation()
