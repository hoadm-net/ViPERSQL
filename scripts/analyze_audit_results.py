"""
Analyze audit results to find problematic cases
================================================

Purpose: Extract and categorize problematic translations from audit results
         Focus on cases that may impact model performance

Usage:
    python scripts/analyze_audit_results.py --input results/audit_results.jsonl
"""

import json
import argparse
from collections import defaultdict
from typing import List, Dict


def load_results(path: str) -> List[Dict]:
    """Load audit results from JSONL."""
    results = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            results.append(json.loads(line))
    return results


def categorize_issues(results: List[Dict]) -> Dict:
    """Categorize results by issue type."""
    categories = {
        'LEX_only': [],
        'SCH_only': [],
        'STR_only': [],
        'ENT_only': [],
        'multi_issue': [],
        'ok': []
    }
    
    for item in results:
        ann = item.get('annotation', {})
        
        if ann.get('error'):
            continue
        
        if ann.get('OK'):
            categories['ok'].append(item)
            continue
        
        # Count issues
        issues = []
        if ann.get('LEX'): issues.append('LEX')
        if ann.get('SCH'): issues.append('SCH')
        if ann.get('STR'): issues.append('STR')
        if ann.get('ENT'): issues.append('ENT')
        
        if len(issues) == 0:
            categories['ok'].append(item)
        elif len(issues) == 1:
            categories[f'{issues[0]}_only'].append(item)
        else:
            categories['multi_issue'].append(item)
    
    return categories


def find_worst_cases(results: List[Dict], top_n: int = 50) -> List[Dict]:
    """Find worst cases (multiple issues)."""
    scored = []
    
    for item in results:
        ann = item.get('annotation', {})
        if ann.get('error'):
            continue
        
        # Score: number of issues
        score = sum([
            ann.get('LEX', False),
            ann.get('SCH', False),
            ann.get('STR', False),
            ann.get('ENT', False)
        ])
        
        if score > 0:
            scored.append((score, item))
    
    # Sort by score descending
    scored.sort(reverse=True, key=lambda x: x[0])
    
    return [item for score, item in scored[:top_n]]


def print_summary(categories: Dict):
    """Print summary statistics."""
    total = sum(len(v) for v in categories.values())
    
    print("\n" + "="*60)
    print("📊 ISSUE CATEGORIZATION")
    print("="*60)
    
    print(f"\nTotal analyzed: {total}")
    print(f"\n{'Category':<20} {'Count':<10} {'%'}")
    print("-"*60)
    
    for cat, items in categories.items():
        pct = len(items) / total * 100 if total > 0 else 0
        print(f"{cat:<20} {len(items):<10} {pct:.1f}%")
    
    print("="*60)


def save_problematic_cases(categories: Dict, output_prefix: str):
    """Save problematic cases to separate files."""
    
    # Save multi-issue cases (most problematic)
    multi_path = f"{output_prefix}_multi_issue.json"
    with open(multi_path, 'w', encoding='utf-8') as f:
        json.dump(categories['multi_issue'], f, indent=2, ensure_ascii=False)
    print(f"\n💾 Multi-issue cases: {multi_path}")
    
    # Save schema drift (impacts retrieval)
    sch_path = f"{output_prefix}_schema_drift.json"
    sch_cases = categories['SCH_only'] + [
        item for item in categories['multi_issue']
        if item['annotation'].get('SCH')
    ]
    with open(sch_path, 'w', encoding='utf-8') as f:
        json.dump(sch_cases, f, indent=2, ensure_ascii=False)
    print(f"💾 Schema drift cases: {sch_path}")
    
    # Save lexical issues
    lex_path = f"{output_prefix}_lexical.json"
    lex_cases = categories['LEX_only'] + [
        item for item in categories['multi_issue']
        if item['annotation'].get('LEX')
    ]
    with open(lex_path, 'w', encoding='utf-8') as f:
        json.dump(lex_cases, f, indent=2, ensure_ascii=False)
    print(f"💾 Lexical issues: {lex_path}")


def generate_examples_for_paper(worst_cases: List[Dict], output_path: str):
    """Generate example cases for paper."""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Translation Quality Issues - Examples for Paper\n\n")
        
        for idx, item in enumerate(worst_cases[:10], 1):  # Top 10
            ann = item['annotation']
            
            f.write(f"## Example {idx}\n\n")
            f.write(f"**Database:** `{item['db_id']}`\n\n")
            f.write(f"**Vietnamese Question:**\n```\n{item['question']}\n```\n\n")
            f.write(f"**SQL:**\n```sql\n{item['query']}\n```\n\n")
            
            f.write("**Issues:**\n")
            if ann.get('LEX'):
                f.write("- ✗ **LEX**: Lexical/fluency problem\n")
            if ann.get('SCH'):
                f.write("- ✗ **SCH**: Schema drift\n")
            if ann.get('STR'):
                f.write("- ✗ **STR**: Structural mismatch\n")
            if ann.get('ENT'):
                f.write("- ✗ **ENT**: Entity inconsistency\n")
            
            f.write(f"\n**Explanation:** {ann.get('explanation', 'N/A')}\n\n")
            f.write("---\n\n")
    
    print(f"📄 Paper examples: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Analyze audit results")
    parser.add_argument('--input', type=str, required=True, help='Input audit JSONL')
    parser.add_argument('--output-prefix', type=str, default='results/audit_analysis',
                       help='Output files prefix')
    
    args = parser.parse_args()
    
    print("="*60)
    print("🔍 Audit Results Analyzer")
    print("="*60)
    
    # Load results
    print(f"\n📂 Loading: {args.input}")
    results = load_results(args.input)
    print(f"   Loaded: {len(results)} samples")
    
    # Categorize
    categories = categorize_issues(results)
    print_summary(categories)
    
    # Find worst cases
    worst = find_worst_cases(results, top_n=50)
    print(f"\n🔥 Found {len(worst)} problematic cases")
    
    # Save outputs
    save_problematic_cases(categories, args.output_prefix)
    
    # Generate examples for paper
    examples_path = f"{args.output_prefix}_examples.md"
    generate_examples_for_paper(worst, examples_path)
    
    print("\n✨ Analysis complete!")
    print(f"\nKey findings:")
    print(f"- Multi-issue cases: {len(categories['multi_issue'])}")
    print(f"- Schema drift: {len([i for i in results if i.get('annotation', {}).get('SCH')])}")
    print(f"- Lexical issues: {len([i for i in results if i.get('annotation', {}).get('LEX')])}")
    print(f"\nNext: Review {examples_path} for paper examples")


if __name__ == "__main__":
    main()
