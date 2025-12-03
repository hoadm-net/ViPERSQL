"""
ViText2SQL Translation Quality Audit Script
============================================

Purpose: LLM-assisted annotation of translation quality issues in ViText2SQL dataset
         to quantify translation noise (lexical, schema drift, structural mismatch, etc.)

Author: ViPERSQL Team
Date: December 2025

Usage:
    python scripts/audit_vitext2sql_noise.py [--samples 700] [--output results/audit_results.jsonl]
"""

import json
import random
import argparse
import os
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm
import time

# Load environment variables
load_dotenv()


class ViText2SQLAuditor:
    """LLM-assisted auditor for ViText2SQL translation quality."""
    
    def __init__(self, model: str = None):
        """
        Initialize auditor with OpenAI client.
        
        Args:
            model: OpenAI model name (default from .env)
        """
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
        
        print(f"🤖 Initialized auditor with model: {self.model}")
        
    def create_audit_prompt(self, item: Dict[str, Any]) -> str:
        """
        Create structured prompt for LLM annotation.
        
        Args:
            item: Dictionary with 'db_id', 'question', 'query'
            
        Returns:
            Formatted prompt string
        """
        question_vi = item['question']
        sql_query = item['query']
        db_id = item['db_id']
        
        # Extract schema elements from SQL (simple parsing)
        # Tables: extract from FROM clause
        # Columns: extract from SELECT, WHERE clauses
        schema_hint = self._extract_schema_from_sql(sql_query)
        
        prompt = f"""You are auditing the translation quality of a published Vietnamese Text-to-SQL dataset.

**Given:**
- Database: `{db_id}`
- Vietnamese question: "{question_vi}"
- SQL query: `{sql_query}`
- Schema elements used: {schema_hint}

**Task:** Identify ONLY **severe and obvious** translation issues. Be LENIENT - this is a published dataset.

Mark TRUE only if the issue is **clear and significant**:

1. **LEX** (Lexical/Fluency): Mark TRUE only if:
   - Completely broken grammar or nonsensical phrasing
   - Words that absolutely don't exist in Vietnamese
   - Severe awkwardness that makes the question confusing
   - DO NOT mark minor stylistic variations or acceptable synonyms

2. **SCH** (Schema Drift): Mark TRUE only if:
   - Vietnamese term is COMPLETELY different from SQL schema element (e.g., "tác_giả" vs "writer")
   - Mixed language in SQL schema itself (e.g., "id_khách_hàng" mixing English + Vietnamese)
   - DO NOT mark if just different phrasing of the same concept

3. **STR** (Structural Mismatch): Mark TRUE only if:
   - Question asks for single value but SQL returns multiple (or vice versa)
   - Question implies simple query but SQL has complex multi-table joins that are not hinted
   - Completely missing aggregation that changes meaning (e.g., "how many" → SELECT without COUNT)
   - DO NOT mark if structure is just implicit but still correct

4. **ENT** (Entity/Number Inconsistency): Mark TRUE only if:
   - Proper names are COMPLETELY different languages (e.g., "Việt Nam" vs "Vietnam")
   - Numbers don't match at all
   - DO NOT mark minor transliterations or acceptable translations

5. **OK** (No Major Issues): Mark TRUE if the translation is acceptable and usable, even if not perfect.

**CRITICAL INSTRUCTIONS:**
- BE VERY LENIENT - only mark severe problems
- When in doubt, mark OK=true
- This is a published dataset, we're just documenting that "some issues exist", not finding all problems
- Minor imperfections are ACCEPTABLE

**Output ONLY valid JSON:**
{{
  "LEX": true/false,
  "SCH": true/false,
  "STR": true/false,
  "ENT": true/false,
  "OK": true/false,
  "explanation": "brief explanation in Vietnamese (1-2 sentences max)"
}}"""
        
        return prompt
    
    def _extract_schema_from_sql(self, sql: str) -> str:
        """Extract schema hints from SQL query (simple heuristic)."""
        # Convert to lowercase for parsing
        sql_lower = sql.lower()
        
        tables = []
        columns = []
        
        # Extract tables (after FROM, JOIN)
        if 'from' in sql_lower:
            parts = sql_lower.split('from')[1].split('where')[0].split('join')
            for part in parts:
                words = part.strip().split()
                if words:
                    tables.append(words[0].strip(','))
        
        # Extract columns (rough - just show some used)
        import re
        # Find Vietnamese column names (contain underscore typically)
        cols = re.findall(r'(\w+_\w+)', sql)
        columns = list(set(cols))[:5]  # Limit to 5 for brevity
        
        return f"Tables: {', '.join(tables[:3]) if tables else 'N/A'} | Columns: {', '.join(columns) if columns else 'N/A'}"
    
    def annotate_sample(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Annotate a single sample using LLM.
        
        Args:
            item: Sample dictionary
            
        Returns:
            Item with annotation added
        """
        prompt = self.create_audit_prompt(item)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Vietnamese NLP expert auditing translation quality. Always output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON (handle markdown code blocks)
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            annotation = json.loads(content)
            
            # Add annotation to item
            result = item.copy()
            result['annotation'] = annotation
            result['model'] = self.model
            
            return result
            
        except Exception as e:
            print(f"\n❌ Error annotating sample: {e}")
            print(f"   Question: {item['question'][:50]}...")
            
            # Return with error annotation
            result = item.copy()
            result['annotation'] = {
                "LEX": False,
                "SCH": False,
                "STR": False,
                "ENT": False,
                "OK": True,
                "explanation": f"Error: {str(e)}",
                "error": True
            }
            result['model'] = self.model
            return result
    
    def audit_dataset(self, 
                     data: List[Dict], 
                     num_samples: int = 700,
                     output_path: str = "results/audit_results.jsonl",
                     seed: int = 42) -> List[Dict]:
        """
        Audit a sample of the dataset.
        
        Args:
            data: Full dataset
            num_samples: Number of samples to audit (default 700 = ~10%)
            output_path: Output JSONL path
            seed: Random seed for reproducibility
            
        Returns:
            List of annotated samples
        """
        # Set random seed
        random.seed(seed)
        
        # Sample data
        if num_samples > len(data):
            num_samples = len(data)
            print(f"⚠️  Requested {num_samples} samples but dataset has {len(data)}. Using all.")
        
        sampled = random.sample(data, k=num_samples)
        print(f"📊 Sampled {num_samples} / {len(data)} ({num_samples/len(data)*100:.1f}%) with seed={seed}")
        
        # Create output directory
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Annotate samples with progress bar
        results = []
        errors = 0
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in tqdm(sampled, desc="Auditing samples"):
                result = self.annotate_sample(item)
                results.append(result)
                
                # Write to JSONL immediately (streaming)
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
                f.flush()
                
                if result['annotation'].get('error'):
                    errors += 1
                
                # Small delay to avoid rate limits
                time.sleep(0.1)
        
        print(f"\n✅ Audit complete!")
        print(f"   Total: {len(results)} samples")
        print(f"   Errors: {errors}")
        print(f"   Output: {output_path}")
        
        return results


def compute_statistics(results: List[Dict]) -> Dict[str, float]:
    """
    Compute frequency statistics from audit results.
    
    Args:
        results: List of annotated samples
        
    Returns:
        Dictionary with percentages for each issue type
    """
    counts = {
        "LEX": 0,
        "SCH": 0, 
        "STR": 0,
        "ENT": 0,
        "OK": 0,
        "TOTAL": len(results)
    }
    
    for item in results:
        annotation = item.get('annotation', {})
        
        # Skip error cases
        if annotation.get('error'):
            continue
            
        for key in ["LEX", "SCH", "STR", "ENT", "OK"]:
            if annotation.get(key, False):
                counts[key] += 1
    
    # Compute percentages
    stats = {}
    for key in ["LEX", "SCH", "STR", "ENT", "OK"]:
        stats[key] = (counts[key] / counts["TOTAL"]) * 100
    
    stats["TOTAL"] = counts["TOTAL"]
    stats["TOTAL_ISSUES"] = counts["TOTAL"] - counts["OK"]
    stats["ISSUE_RATE"] = (stats["TOTAL_ISSUES"] / counts["TOTAL"]) * 100
    
    return stats


def print_statistics(stats: Dict[str, float]):
    """Print statistics in a nice format."""
    print("\n" + "="*60)
    print("📊 AUDIT STATISTICS")
    print("="*60)
    print(f"\nTotal samples audited: {int(stats['TOTAL'])}")
    print(f"Samples with issues: {int(stats['TOTAL_ISSUES'])} ({stats['ISSUE_RATE']:.1f}%)")
    print(f"\n{'Issue Type':<30} {'Count':<10} {'%'}")
    print("-"*60)
    
    issue_types = [
        ("LEX - Lexical/Fluency", "LEX"),
        ("SCH - Schema Drift", "SCH"),
        ("STR - Structural Mismatch", "STR"),
        ("ENT - Entity/Number Mismatch", "ENT"),
        ("OK - No Major Issues", "OK")
    ]
    
    for label, key in issue_types:
        count = int(stats['TOTAL'] * stats[key] / 100)
        print(f"{label:<30} {count:<10} {stats[key]:.1f}%")
    
    print("="*60)


def save_statistics_report(stats: Dict[str, float], output_path: str = "results/audit_statistics.json"):
    """Save statistics to JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Statistics saved to: {output_path}")


def generate_latex_table(stats: Dict[str, float]) -> str:
    """Generate LaTeX table for paper."""
    latex = """\\begin{{table}}[h]
\\centering
\\caption{{Translation Quality Audit Results (10\\% of ViText2SQL)}}
\\label{{tab:translation-audit}}
\\begin{{tabular}}{{lcc}}
\\hline
\\textbf{{Issue Type}} & \\textbf{{Description}} & \\textbf{{\\%}} \\\\
\\hline
LEX & Lexical/fluency issues & {lex:.1f}\\% \\\\
SCH & Schema drift & {sch:.1f}\\% \\\\
STR & Structural mismatch & {struct:.1f}\\% \\\\
ENT & Entity/number mismatch & {ent:.1f}\\% \\\\
OK & No major issues & {ok:.1f}\\% \\\\
\\hline
\\end{{tabular}}
\\end{{table}}"""
    
    return latex.format(
        lex=stats['LEX'],
        sch=stats['SCH'],
        struct=stats['STR'],
        ent=stats['ENT'],
        ok=stats['OK']
    )


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Audit ViText2SQL translation quality")
    parser.add_argument('--samples', type=int, default=700, help='Number of samples to audit (default: 700)')
    parser.add_argument('--output', type=str, default='results/audit_results.jsonl', help='Output JSONL path')
    parser.add_argument('--stats', type=str, default='results/audit_statistics.json', help='Statistics JSON path')
    parser.add_argument('--dataset', type=str, default='dataset/ViText2SQL/std-level/train.json', help='Dataset path')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--model', type=str, default=None, help='OpenAI model (default from .env)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("🔍 ViText2SQL Translation Quality Audit")
    print("="*60)
    
    # Load dataset
    print(f"\n📂 Loading dataset: {args.dataset}")
    with open(args.dataset, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"   Total samples: {len(data)}")
    
    # Initialize auditor
    auditor = ViText2SQLAuditor(model=args.model)
    
    # Run audit
    print(f"\n🚀 Starting audit (this will take ~{args.samples * 0.5 / 60:.1f} minutes)...")
    results = auditor.audit_dataset(
        data=data,
        num_samples=args.samples,
        output_path=args.output,
        seed=args.seed
    )
    
    # Compute statistics
    stats = compute_statistics(results)
    
    # Print results
    print_statistics(stats)
    
    # Save statistics
    save_statistics_report(stats, args.stats)
    
    # Generate LaTeX table
    latex_table = generate_latex_table(stats)
    latex_path = args.stats.replace('.json', '_table.tex')
    with open(latex_path, 'w', encoding='utf-8') as f:
        f.write(latex_table)
    print(f"📄 LaTeX table saved to: {latex_path}")
    
    print("\n✨ Audit complete! Next steps:")
    print(f"   1. Manual validation: Check {args.output} and verify ~100 random samples")
    print(f"   2. Review statistics: {args.stats}")
    print(f"   3. Add LaTeX table to paper: {latex_path}")
    print(f"   4. Write analysis paragraph for Section 4.1")


if __name__ == "__main__":
    main()
