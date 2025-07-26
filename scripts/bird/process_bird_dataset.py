#!/usr/bin/env python3
"""
BIRD Dataset Processing Script for ViPERSQL

This script processes the BIRD dataset to:
1. Extract 200 samples with balanced distribution across databases and difficulties
2. Translate English questions to Vietnamese using ChatGPT
3. Save processed samples to a new file

Usage:
    python scripts/process_bird_dataset.py --api-key YOUR_OPENAI_API_KEY
"""

import json
import argparse
import os
import time
from collections import defaultdict, Counter
from typing import List, Dict, Any
import openai
from pathlib import Path


class BirdDatasetProcessor:
    """Processor for BIRD dataset with Vietnamese translation"""
    
    def __init__(self, api_key: str, output_dir: str = "dataset/BIRD"):
        """
        Initialize processor with OpenAI API key
        
        Args:
            api_key: OpenAI API key for ChatGPT
            output_dir: Directory to save processed files
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def load_bird_data(self, file_path: str) -> List[Dict]:
        """Load BIRD dataset from JSON file"""
        print(f"Loading BIRD dataset from {file_path}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"Loaded {len(data)} samples")
        return data
    
    def analyze_dataset_distribution(self, data: List[Dict]) -> Dict:
        """Analyze distribution of databases and difficulties"""
        db_count = Counter()
        difficulty_count = Counter()
        db_difficulty_count = defaultdict(lambda: defaultdict(int))
        
        for item in data:
            db_id = item['db_id']
            difficulty = item['difficulty']
            
            db_count[db_id] += 1
            difficulty_count[difficulty] += 1
            db_difficulty_count[db_id][difficulty] += 1
        
        print("\n=== Dataset Distribution Analysis ===")
        print(f"\nTotal samples: {len(data)}")
        
        print(f"\nDifficulty distribution:")
        for difficulty, count in difficulty_count.most_common():
            print(f"  {difficulty}: {count} ({count/len(data)*100:.1f}%)")
        
        print(f"\nDatabase distribution:")
        for db_id, count in db_count.most_common():
            print(f"  {db_id}: {count}")
            
        print(f"\nDatabase-Difficulty matrix:")
        for db_id in sorted(db_count.keys()):
            print(f"  {db_id}:")
            for difficulty in ['simple', 'moderate', 'challenging']:
                count = db_difficulty_count[db_id][difficulty]
                print(f"    {difficulty}: {count}")
        
        return {
            'db_count': dict(db_count),
            'difficulty_count': dict(difficulty_count),
            'db_difficulty_count': dict(db_difficulty_count)
        }
    
    def stratified_sampling(self, data: List[Dict], target_samples: int = 200) -> List[Dict]:
        """
        Perform stratified sampling to get balanced representation
        
        Args:
            data: Full dataset
            target_samples: Number of samples to extract (default: 200)
            
        Returns:
            List of selected samples
        """
        print(f"\n=== Stratified Sampling for {target_samples} samples ===")
        
        # Group by database and difficulty
        groups = defaultdict(list)
        for item in data:
            key = (item['db_id'], item['difficulty'])
            groups[key].append(item)
        
        # Calculate target samples per group
        total_groups = len(groups)
        base_samples_per_group = target_samples // total_groups
        remaining_samples = target_samples % total_groups
        
        selected_samples = []
        group_selections = {}
        
        # First, allocate base samples to each group
        for i, (group_key, group_items) in enumerate(groups.items()):
            samples_for_group = base_samples_per_group
            
            # Distribute remaining samples to first few groups
            if i < remaining_samples:
                samples_for_group += 1
            
            # Don't exceed available samples in group
            samples_for_group = min(samples_for_group, len(group_items))
            
            # Random sampling from group
            import random
            selected_from_group = random.sample(group_items, samples_for_group)
            selected_samples.extend(selected_from_group)
            
            group_selections[group_key] = len(selected_from_group)
            print(f"  {group_key[0]} - {group_key[1]}: {len(selected_from_group)}/{len(group_items)} samples")
        
        print(f"\nTotal selected: {len(selected_samples)} samples")
        return selected_samples
    
    def translate_to_vietnamese(self, question: str, evidence: str = "") -> str:
        """
        Translate English question to Vietnamese using ChatGPT
        
        Args:
            question: English question
            evidence: Additional evidence/context
            
        Returns:
            Vietnamese translation
        """
        # Construct prompt for translation
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
            response = self.client.chat.completions.create(
                model="gpt-4",
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
    
    def process_samples(self, samples: List[Dict]) -> List[Dict]:
        """
        Process samples by adding Vietnamese translations
        
        Args:
            samples: List of samples to process
            
        Returns:
            List of processed samples with Vietnamese translations
        """
        print(f"\n=== Processing {len(samples)} samples ===")
        
        processed_samples = []
        
        for i, sample in enumerate(samples):
            print(f"Processing {i+1}/{len(samples)}: {sample['question_id']}")
            
            # Translate question to Vietnamese
            question_vn = self.translate_to_vietnamese(
                sample['question'], 
                sample.get('evidence', '')
            )
            
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
            
            # Rate limiting - wait 1 second between API calls
            time.sleep(1)
            
            # Progress update every 10 samples
            if (i + 1) % 10 == 0:
                print(f"  Completed {i+1}/{len(samples)} translations")
        
        return processed_samples
    
    def save_processed_data(self, processed_data: List[Dict], filename: str = "bird_vietnamese_200.json"):
        """Save processed data to JSON file"""
        output_path = self.output_dir / filename
        
        print(f"\n=== Saving processed data ===")
        print(f"Output file: {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully saved {len(processed_data)} processed samples")
        
        # Create summary report
        self.create_summary_report(processed_data, output_path.with_suffix('.summary.txt'))
    
    def create_summary_report(self, data: List[Dict], summary_path: Path):
        """Create a summary report of the processed data"""
        db_count = Counter()
        difficulty_count = Counter()
        
        for item in data:
            db_count[item['db_id']] += 1
            difficulty_count[item['difficulty']] += 1
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("BIRD Vietnamese Dataset Processing Summary\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Total samples: {len(data)}\n\n")
            
            f.write("Difficulty distribution:\n")
            for difficulty, count in difficulty_count.most_common():
                f.write(f"  {difficulty}: {count} ({count/len(data)*100:.1f}%)\n")
            
            f.write("\nDatabase distribution:\n")
            for db_id, count in db_count.most_common():
                f.write(f"  {db_id}: {count}\n")
            
            f.write("\nSample questions:\n")
            for i, item in enumerate(data[:5]):
                f.write(f"\n{i+1}. Question ID: {item['question_id']}\n")
                f.write(f"   Database: {item['db_id']}\n")
                f.write(f"   Difficulty: {item['difficulty']}\n")
                f.write(f"   English: {item['question']}\n")
                f.write(f"   Vietnamese: {item['question_vn']}\n")
        
        print(f"Summary report saved to: {summary_path}")
    
    def run(self, input_file: str, target_samples: int = 200):
        """
        Main processing pipeline
        
        Args:
            input_file: Path to input BIRD JSON file
            target_samples: Number of samples to extract and process
        """
        print("🚀 Starting BIRD Dataset Processing Pipeline")
        print("=" * 60)
        
        # Step 1: Load data
        data = self.load_bird_data(input_file)
        
        # Step 2: Analyze distribution
        distribution = self.analyze_dataset_distribution(data)
        
        # Step 3: Stratified sampling
        selected_samples = self.stratified_sampling(data, target_samples)
        
        # Step 4: Process samples (translate to Vietnamese)
        processed_samples = self.process_samples(selected_samples)
        
        # Step 5: Save results
        self.save_processed_data(processed_samples)
        
        print("\n✅ Processing pipeline completed successfully!")


def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(description="Process BIRD dataset for ViPERSQL")
    
    parser.add_argument(
        '--api-key',
        type=str,
        help='OpenAI API key for ChatGPT translation'
    )
    
    parser.add_argument(
        '--input-file',
        type=str,
        default='dataset/BIRD/dev.json',
        help='Path to input BIRD JSON file (default: dataset/BIRD/dev.json)'
    )
    
    parser.add_argument(
        '--samples',
        type=int,
        default=200,
        help='Number of samples to extract (default: 200)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='dataset/BIRD',
        help='Output directory for processed files (default: dataset/BIRD)'
    )
    
    args = parser.parse_args()
    
    # Get API key from argument or environment
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ Error: OpenAI API key is required!")
        print("   Use --api-key argument or set OPENAI_API_KEY environment variable")
        return 1
    
    # Initialize processor
    processor = BirdDatasetProcessor(api_key, args.output_dir)
    
    # Run processing pipeline
    try:
        processor.run(args.input_file, args.samples)
        return 0
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
