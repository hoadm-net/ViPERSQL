#!/usr/bin/env python3
"""
Migration Script: Convert ViR2 to Multi-Language ViR2

This script helps migrate from existing ViR2 selectors to the new multi-language
version while maintaining backward compatibility.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mint.utils.language_detector import LanguageDetector
from mint.utils.multilang_embedder import MultiLanguageEmbedder


def detect_dataset_language(dataset_path: str) -> str:
    """Detect the primary language of a dataset."""
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            return "vi"  # Default fallback
        
        # Sample questions for language detection
        detector = LanguageDetector()
        sample_size = min(50, len(data))
        sample_questions = [item.get('question', '') for item in data[:sample_size]]
        
        # Vote on language
        language_votes = []
        for question in sample_questions:
            if question.strip():
                lang = detector.detect_language(question)
                language_votes.append(lang)
        
        if not language_votes:
            return "vi"
        
        # Return majority vote
        vi_count = language_votes.count("vi")
        en_count = language_votes.count("en")
        
        primary_lang = "vi" if vi_count >= en_count else "en"
        confidence = max(vi_count, en_count) / len(language_votes)
        
        print(f"Dataset language detection: {primary_lang} (confidence: {confidence:.2f})")
        print(f"  Vietnamese questions: {vi_count}")
        print(f"  English questions: {en_count}")
        
        return primary_lang
        
    except Exception as e:
        print(f"Error detecting dataset language: {e}")
        return "vi"  # Default fallback


def migrate_embeddings(dataset_path: str, target_language: str, force_recompute: bool = False) -> bool:
    """Migrate or recompute embeddings for multi-language compatibility."""
    try:
        candidates_path = Path(dataset_path).parent / "dicl_candidates.json"
        
        if not candidates_path.exists():
            print(f"Candidates file not found: {candidates_path}")
            return False
        
        with open(candidates_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            print("No data found in candidates file")
            return False
        
        # Check if embeddings exist and are compatible
        has_embeddings = len(data) > 0 and 'embedding' in data[0]
        
        if has_embeddings and not force_recompute:
            # Check embedding dimension
            embedding_dim = len(data[0]['embedding'])
            expected_dim = 768  # Both BERT and PhoBERT use 768
            
            if embedding_dim == expected_dim:
                print(f"Embeddings already compatible (dim={embedding_dim})")
                # Add metadata if missing
                return add_embedding_metadata(candidates_path, target_language)
            else:
                print(f"Incompatible embedding dimension: {embedding_dim} (expected {expected_dim})")
                force_recompute = True
        
        if not has_embeddings or force_recompute:
            print(f"Computing new embeddings for language: {target_language}")
            return recompute_embeddings(candidates_path, target_language)
        
        return True
        
    except Exception as e:
        print(f"Error migrating embeddings: {e}")
        return False


def recompute_embeddings(candidates_path: Path, language: str) -> bool:
    """Recompute embeddings using appropriate language model."""
    try:
        print(f"Loading multi-language embedder...")
        embedder = MultiLanguageEmbedder(cache_models=True)
        
        with open(candidates_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Computing embeddings for {len(data)} examples...")
        
        # Extract questions
        questions = [item['question'] for item in data]
        
        # Compute embeddings in batches
        embeddings = embedder.encode_batch(questions, language=language, batch_size=32)
        
        # Add embeddings to data
        for i, item in enumerate(data):
            item['embedding'] = embeddings[i].tolist()
            item['embedding_model'] = embedder.get_model_info(language)['embedding_model']
            item['embedding_language'] = language
        
        # Create backup
        backup_path = candidates_path.with_suffix('.json.backup')
        if candidates_path.exists():
            candidates_path.rename(backup_path)
            print(f"Created backup: {backup_path}")
        
        # Write updated data
        with open(candidates_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully updated embeddings in {candidates_path}")
        
        # Clear embedder cache
        embedder.clear_cache()
        
        return True
        
    except Exception as e:
        print(f"Error recomputing embeddings: {e}")
        return False


def add_embedding_metadata(candidates_path: Path, language: str) -> bool:
    """Add metadata to existing embeddings."""
    try:
        with open(candidates_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Add metadata if missing
        updated = False
        model_info = {
            "vi": "vinai/phobert-base-v2",
            "en": "google-bert/bert-base-uncased"
        }
        
        for item in data:
            if 'embedding_model' not in item:
                item['embedding_model'] = model_info.get(language, model_info["vi"])
                updated = True
            if 'embedding_language' not in item:
                item['embedding_language'] = language
                updated = True
        
        if updated:
            # Create backup
            backup_path = candidates_path.with_suffix('.json.backup')
            if candidates_path.exists():
                candidates_path.rename(backup_path)
                print(f"Created backup: {backup_path}")
            
            # Write updated data
            with open(candidates_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"Added embedding metadata to {candidates_path}")
        
        return True
        
    except Exception as e:
        print(f"Error adding metadata: {e}")
        return False


def create_migration_report(dataset_path: str) -> Dict[str, Any]:
    """Create a migration report."""
    report = {
        "timestamp": str(pd.Timestamp.now()),
        "dataset_path": dataset_path,
        "language_detected": None,
        "candidates_file": None,
        "embeddings_status": "unknown",
        "migration_needed": False,
        "recommendations": []
    }
    
    try:
        # Detect language
        train_file = Path(dataset_path) / "train.json"
        if train_file.exists():
            report["language_detected"] = detect_dataset_language(str(train_file))
        
        # Check candidates file
        candidates_file = Path(dataset_path) / "dicl_candidates.json"
        if candidates_file.exists():
            report["candidates_file"] = str(candidates_file)
            
            with open(candidates_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data and 'embedding' in data[0]:
                embedding_dim = len(data[0]['embedding'])
                has_metadata = 'embedding_model' in data[0]
                
                report["embeddings_status"] = f"present (dim={embedding_dim}, metadata={has_metadata})"
                
                if embedding_dim != 768:
                    report["migration_needed"] = True
                    report["recommendations"].append("Recompute embeddings (incompatible dimension)")
                elif not has_metadata:
                    report["migration_needed"] = True
                    report["recommendations"].append("Add embedding metadata")
            else:
                report["embeddings_status"] = "missing"
                report["migration_needed"] = True
                report["recommendations"].append("Compute embeddings")
        else:
            report["candidates_file"] = "missing"
            report["recommendations"].append("Create candidates file first")
    
    except Exception as e:
        report["error"] = str(e)
    
    return report


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description="Migrate ViR2 to Multi-Language ViR2")
    parser.add_argument("dataset_path", help="Path to dataset directory")
    parser.add_argument("--language", choices=["auto", "vi", "en"], default="auto",
                       help="Target language (auto-detect, Vietnamese, or English)")
    parser.add_argument("--force-recompute", action="store_true",
                       help="Force recomputation of embeddings")
    parser.add_argument("--report-only", action="store_true",
                       help="Generate report only, don't migrate")
    
    args = parser.parse_args()
    
    dataset_path = Path(args.dataset_path)
    
    if not dataset_path.exists():
        print(f"Error: Dataset path does not exist: {dataset_path}")
        return 1
    
    print("=" * 60)
    print("ViR2 to Multi-Language Migration")
    print("=" * 60)
    print(f"Dataset: {dataset_path}")
    print(f"Target language: {args.language}")
    print(f"Force recompute: {args.force_recompute}")
    print("-" * 60)
    
    # Generate report
    try:
        import pandas as pd
    except ImportError:
        # Create simple timestamp
        import datetime
        pd = type('MockPD', (), {
            'Timestamp': type('MockTimestamp', (), {
                'now': lambda: datetime.datetime.now()
            })
        })
    
    report = create_migration_report(str(dataset_path))
    
    print("Migration Report:")
    for key, value in report.items():
        if key != "recommendations":
            print(f"  {key}: {value}")
    
    if report["recommendations"]:
        print("  Recommendations:")
        for rec in report["recommendations"]:
            print(f"    - {rec}")
    
    if args.report_only:
        print("\nReport-only mode: No changes made")
        return 0
    
    if not report["migration_needed"]:
        print("\nNo migration needed")
        return 0
    
    # Determine target language
    target_language = args.language
    if target_language == "auto":
        target_language = report.get("language_detected", "vi")
    
    print(f"\nStarting migration to language: {target_language}")
    
    # Perform migration
    success = migrate_embeddings(str(dataset_path), target_language, args.force_recompute)
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\nYou can now use the multi-language ViR2 selector:")
        print("python vipersql.py --strategy few-shot --example-selection-strategy multilang-vir2")
    else:
        print("\n❌ Migration failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
