#!/usr/bin/env python3
"""
Test and Analysis Script for BIRD Dataset Processing

This script helps test the BIRD dataset processing pipeline and analyze results.
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict


def analyze_original_bird(file_path: str):
    """Analyze the original BIRD dataset"""
    print("🔍 Analyzing Original BIRD Dataset")
    print("=" * 50)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Total samples: {len(data)}")
    
    # Database distribution
    db_count = Counter()
    difficulty_count = Counter()
    db_difficulty = defaultdict(lambda: defaultdict(int))
    
    for item in data:
        db_id = item['db_id']
        difficulty = item['difficulty']
        db_count[db_id] += 1
        difficulty_count[difficulty] += 1
        db_difficulty[db_id][difficulty] += 1
    
    print(f"\nDatabases ({len(db_count)}):")
    for db_id, count in db_count.most_common():
        print(f"  {db_id}: {count}")
    
    print(f"\nDifficulty levels:")
    for difficulty, count in difficulty_count.most_common():
        print(f"  {difficulty}: {count} ({count/len(data)*100:.1f}%)")
    
    print(f"\nDatabase-Difficulty Matrix:")
    difficulties = ['simple', 'moderate', 'challenging']
    print(f"{'Database':<25} {'Simple':<8} {'Moderate':<10} {'Challenging':<12} {'Total':<8}")
    print("-" * 70)
    
    for db_id in sorted(db_count.keys()):
        simple = db_difficulty[db_id]['simple']
        moderate = db_difficulty[db_id]['moderate']
        challenging = db_difficulty[db_id]['challenging']
        total = simple + moderate + challenging
        
        print(f"{db_id:<25} {simple:<8} {moderate:<10} {challenging:<12} {total:<8}")
    
    return {
        'total': len(data),
        'databases': dict(db_count),
        'difficulties': dict(difficulty_count),
        'matrix': dict(db_difficulty)
    }


def test_sampling_strategy(file_path: str, target_samples: int = 200):
    """Test the sampling strategy without actually processing"""
    print(f"\n🧪 Testing Sampling Strategy for {target_samples} samples")
    print("=" * 50)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Group by database and difficulty
    groups = defaultdict(list)
    for item in data:
        key = (item['db_id'], item['difficulty'])
        groups[key].append(item)
    
    # Calculate allocation
    total_groups = len(groups)
    base_samples_per_group = target_samples // total_groups
    remaining_samples = target_samples % total_groups
    
    print(f"Total groups: {total_groups}")
    print(f"Base samples per group: {base_samples_per_group}")
    print(f"Remaining samples to distribute: {remaining_samples}")
    
    total_allocated = 0
    allocations = {}
    
    print(f"\nAllocation plan:")
    print(f"{'Database':<20} {'Difficulty':<12} {'Available':<10} {'Allocated':<10} {'Ratio':<8}")
    print("-" * 70)
    
    for i, (group_key, group_items) in enumerate(groups.items()):
        samples_for_group = base_samples_per_group
        
        if i < remaining_samples:
            samples_for_group += 1
        
        samples_for_group = min(samples_for_group, len(group_items))
        allocations[group_key] = samples_for_group
        total_allocated += samples_for_group
        
        ratio = f"{samples_for_group/len(group_items)*100:.1f}%"
        print(f"{group_key[0]:<20} {group_key[1]:<12} {len(group_items):<10} {samples_for_group:<10} {ratio:<8}")
    
    print(f"\nTotal allocated: {total_allocated}")
    
    # Check if we achieve balanced representation
    db_allocation = defaultdict(int)
    difficulty_allocation = defaultdict(int)
    
    for (db_id, difficulty), count in allocations.items():
        db_allocation[db_id] += count
        difficulty_allocation[difficulty] += count
    
    print(f"\nFinal distribution by database:")
    for db_id, count in sorted(db_allocation.items()):
        print(f"  {db_id}: {count}")
    
    print(f"\nFinal distribution by difficulty:")
    for difficulty, count in sorted(difficulty_allocation.items()):
        print(f"  {difficulty}: {count}")
    
    return allocations


def sample_questions_preview(file_path: str, num_samples: int = 5):
    """Show sample questions for preview"""
    print(f"\n📖 Sample Questions Preview")
    print("=" * 50)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get diverse samples
    import random
    samples = random.sample(data, min(num_samples, len(data)))
    
    for i, sample in enumerate(samples, 1):
        print(f"\n{i}. Question ID: {sample['question_id']}")
        print(f"   Database: {sample['db_id']}")
        print(f"   Difficulty: {sample['difficulty']}")
        print(f"   Question: {sample['question']}")
        if sample.get('evidence'):
            print(f"   Evidence: {sample['evidence']}")
        print(f"   SQL: {sample['SQL'][:100]}..." if len(sample['SQL']) > 100 else f"   SQL: {sample['SQL']}")


def analyze_processed_file(file_path: str):
    """Analyze the processed Vietnamese file"""
    if not Path(file_path).exists():
        print(f"❌ Processed file not found: {file_path}")
        return
    
    print(f"\n📊 Analyzing Processed File: {file_path}")
    print("=" * 50)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Total processed samples: {len(data)}")
    
    # Check for translation errors
    translation_errors = 0
    for item in data:
        if item['question_vn'].startswith('[TRANSLATION_ERROR]'):
            translation_errors += 1
    
    print(f"Translation errors: {translation_errors}")
    
    # Sample translations
    print(f"\nSample translations:")
    for i, item in enumerate(data[:3]):
        print(f"\n{i+1}. English: {item['question']}")
        print(f"   Vietnamese: {item['question_vn']}")
    
    return data


def main():
    """Main analysis function"""
    if len(sys.argv) < 2:
        print("Usage: python scripts/analyze_bird.py <command> [args]")
        print("\nCommands:")
        print("  original [file]     - Analyze original BIRD dataset")
        print("  sampling [file]     - Test sampling strategy")
        print("  preview [file]      - Preview sample questions")
        print("  processed [file]    - Analyze processed file")
        print("  all [file]          - Run all analyses")
        return
    
    command = sys.argv[1]
    file_path = sys.argv[2] if len(sys.argv) > 2 else "dataset/BIRD/dev.json"
    
    if command == "original":
        analyze_original_bird(file_path)
    
    elif command == "sampling":
        analyze_original_bird(file_path)
        test_sampling_strategy(file_path)
    
    elif command == "preview":
        sample_questions_preview(file_path)
    
    elif command == "processed":
        analyze_processed_file(file_path)
    
    elif command == "all":
        analyze_original_bird(file_path)
        test_sampling_strategy(file_path)
        sample_questions_preview(file_path)
        
        # Try to analyze processed file if it exists
        processed_file = "dataset/BIRD/bird_vietnamese_200.json"
        if Path(processed_file).exists():
            analyze_processed_file(processed_file)
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
