"""
Manual Validation Script for Audit Results
===========================================

Purpose: Sample random cases from audit results for human verification
         to ensure LLM annotation quality (target: >80% agreement)

Usage:
    python scripts/manual_validation_sampler.py --input results/audit_results.jsonl --num 100
"""

import json
import random
import argparse
from pathlib import Path
from typing import List, Dict


def load_audit_results(path: str) -> List[Dict]:
    """Load JSONL audit results."""
    results = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            results.append(json.loads(line))
    return results


def sample_for_validation(results: List[Dict], num_samples: int = 100, seed: int = 42) -> List[Dict]:
    """
    Sample cases for manual validation with stratification.
    
    Strategy:
    - Sample from both OK and issue cases
    - Prioritize cases with multiple issues (more interesting)
    """
    random.seed(seed)
    
    # Separate by issue type
    ok_cases = []
    issue_cases = []
    multi_issue_cases = []
    
    for item in results:
        ann = item.get('annotation', {})
        if ann.get('error'):
            continue
            
        issue_count = sum([ann.get(k, False) for k in ['LEX', 'SCH', 'STR', 'ENT']])
        
        if ann.get('OK'):
            ok_cases.append(item)
        elif issue_count >= 2:
            multi_issue_cases.append(item)
        else:
            issue_cases.append(item)
    
    # Stratified sampling
    # 30% OK, 30% single issue, 40% multi-issue (more interesting)
    n_ok = min(int(num_samples * 0.3), len(ok_cases))
    n_multi = min(int(num_samples * 0.4), len(multi_issue_cases))
    n_single = num_samples - n_ok - n_multi
    
    sampled = []
    sampled.extend(random.sample(ok_cases, n_ok) if ok_cases else [])
    sampled.extend(random.sample(multi_issue_cases, n_multi) if multi_issue_cases else [])
    sampled.extend(random.sample(issue_cases, min(n_single, len(issue_cases))) if issue_cases else [])
    
    # Shuffle
    random.shuffle(sampled)
    
    print(f"📊 Sampled {len(sampled)} cases:")
    print(f"   - OK cases: {n_ok}")
    print(f"   - Single-issue: {n_single}")
    print(f"   - Multi-issue: {n_multi}")
    
    return sampled


def create_validation_sheet(samples: List[Dict], output_path: str):
    """Create a human-readable validation sheet."""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Manual Validation Sheet for ViText2SQL Translation Audit\n\n")
        f.write("Instructions:\n")
        f.write("- Review each case below\n")
        f.write("- Check if you AGREE with LLM's annotation\n")
        f.write("- Mark your agreement: AGREE / DISAGREE / PARTIAL\n")
        f.write("- Add notes if needed\n\n")
        f.write("="*80 + "\n\n")
        
        for idx, item in enumerate(samples, 1):
            ann = item['annotation']
            
            f.write(f"## Case {idx}/{len(samples)}\n\n")
            f.write(f"**Database:** `{item['db_id']}`\n\n")
            f.write(f"**Vietnamese Question:**\n```\n{item['question']}\n```\n\n")
            f.write(f"**SQL Query:**\n```sql\n{item['query']}\n```\n\n")
            
            f.write("**LLM Annotation:**\n")
            f.write(f"- LEX (Lexical): {'✓' if ann.get('LEX') else '✗'}\n")
            f.write(f"- SCH (Schema): {'✓' if ann.get('SCH') else '✗'}\n")
            f.write(f"- STR (Structural): {'✓' if ann.get('STR') else '✗'}\n")
            f.write(f"- ENT (Entity): {'✓' if ann.get('ENT') else '✗'}\n")
            f.write(f"- OK (No issues): {'✓' if ann.get('OK') else '✗'}\n\n")
            
            f.write(f"**Explanation:** {ann.get('explanation', 'N/A')}\n\n")
            
            f.write("**Your Validation:**\n")
            f.write("```\n")
            f.write("Agreement: [ ] AGREE  [ ] DISAGREE  [ ] PARTIAL\n")
            f.write("Notes: \n\n\n")
            f.write("```\n\n")
            f.write("="*80 + "\n\n")
    
    print(f"✅ Validation sheet created: {output_path}")


def create_validation_csv(samples: List[Dict], output_path: str):
    """Create CSV for easier Excel/Google Sheets validation."""
    import csv
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'ID', 'db_id', 'question', 'query',
            'LEX', 'SCH', 'STR', 'ENT', 'OK',
            'explanation',
            'YOUR_AGREEMENT', 'YOUR_NOTES'
        ])
        
        # Data
        for idx, item in enumerate(samples, 1):
            ann = item['annotation']
            writer.writerow([
                idx,
                item['db_id'],
                item['question'],
                item['query'],
                'Yes' if ann.get('LEX') else 'No',
                'Yes' if ann.get('SCH') else 'No',
                'Yes' if ann.get('STR') else 'No',
                'Yes' if ann.get('ENT') else 'No',
                'Yes' if ann.get('OK') else 'No',
                ann.get('explanation', ''),
                '',  # For manual input
                ''   # For manual input
            ])
    
    print(f"✅ CSV validation file created: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Sample audit results for manual validation")
    parser.add_argument('--input', type=str, required=True, help='Input audit JSONL file')
    parser.add_argument('--num', type=int, default=100, help='Number of samples to validate')
    parser.add_argument('--output-md', type=str, default='results/validation_sheet.md', help='Output markdown file')
    parser.add_argument('--output-csv', type=str, default='results/validation_sheet.csv', help='Output CSV file')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    print("="*60)
    print("📋 Manual Validation Sampler")
    print("="*60)
    
    # Load results
    print(f"\n📂 Loading audit results: {args.input}")
    results = load_audit_results(args.input)
    print(f"   Total results: {len(results)}")
    
    # Sample for validation
    samples = sample_for_validation(results, args.num, args.seed)
    
    # Create validation sheets
    Path(args.output_md).parent.mkdir(parents=True, exist_ok=True)
    create_validation_sheet(samples, args.output_md)
    create_validation_csv(samples, args.output_csv)
    
    print(f"\n✨ Next steps:")
    print(f"   1. Review markdown: {args.output_md}")
    print(f"   2. Or use CSV in Excel: {args.output_csv}")
    print(f"   3. Mark your agreement for each case")
    print(f"   4. Calculate agreement rate (target: >80%)")


if __name__ == "__main__":
    main()
