#!/usr/bin/env python3
"""
DICL Candidate Pool Builder

Builds a candidate pool for DICL (Diverse In-Context Learning) selection by:
1. Reading train_with_sql_labels.json
2. Sampling ~20 examples from each SQL type
3. Creating embeddings using PhoBERT-base-v2
4. Saving to dicl_candidates.json

Output format:
{
  "db_id": "database_id",
  "question": "Vietnamese question",
  "query": "SQL query",
  "sql_type": "JOIN",
  "question_embedding": [0.1, 0.2, ...]
}
"""

import json
import random
import argparse
from pathlib import Path
from typing import Dict, List, Any
import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np


class PhoBERTEmbedder:
    """PhoBERT embedding generator for Vietnamese text."""

    def __init__(self, model_name: str = "vinai/phobert-base-v2"):
        """Initialize PhoBERT model and tokenizer."""
        print(f"[DICL] Loading PhoBERT model: {model_name}")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[DICL] Using device: {self.device}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()

        print(f"[DICL] PhoBERT model loaded successfully")

    def encode(self, text: str) -> List[float]:
        """Generate embedding for Vietnamese text."""
        try:
            # Tokenize and encode
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                max_length=256,  # Shorter for questions
                truncation=True,
                padding=True
            ).to(self.device)

            # Generate embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use mean pooling of last hidden state
                embeddings = outputs.last_hidden_state.mean(dim=1)

            # Convert to list and move to CPU
            return embeddings.cpu().numpy().flatten().tolist()

        except Exception as e:
            print(f"[DICL] Error generating embedding for text '{text[:50]}...': {e}")
            # Return zero vector as fallback
            return [0.0] * 768  # PhoBERT base has 768 dimensions


def sample_candidates_by_type(data: List[Dict], samples_per_type: int = 20) -> List[Dict]:
    """
    Sample candidates from each SQL type.

    Args:
        data: List of training samples with sql_type
        samples_per_type: Number of samples to take from each type

    Returns:
        List of selected candidate samples
    """
    # Group by SQL type
    type_groups = {}
    for sample in data:
        sql_type = sample.get('sql_type', 'UNKNOWN')
        if sql_type not in type_groups:
            type_groups[sql_type] = []
        type_groups[sql_type].append(sample)

    print(f"[DICL] Found {len(type_groups)} SQL types:")
    for sql_type, samples in type_groups.items():
        print(f"  {sql_type}: {len(samples)} samples")

    # Sample from each type
    candidates = []
    total_requested = 0
    total_selected = 0

    for sql_type, samples in type_groups.items():
        available = len(samples)
        to_select = min(samples_per_type, available)

        if to_select > 0:
            # Randomly sample
            selected = random.sample(samples, to_select)
            candidates.extend(selected)

            print(f"[DICL] Selected {to_select}/{available} samples from {sql_type}")
            total_selected += to_select

        total_requested += samples_per_type

    print(f"[DICL] Total candidates selected: {total_selected}")
    print(f"[DICL] Requested: {total_requested}, Selected: {total_selected}")

    return candidates


def build_dicl_candidates(
    input_path: str,
    output_path: str,
    samples_per_type: int = 20,
    random_seed: int = 42
) -> List[Dict]:
    """
    Build DICL candidate pool with embeddings.

    Args:
        input_path: Path to train_with_sql_labels.json
        output_path: Path to save dicl_candidates.json
        samples_per_type: Number of samples per SQL type
        random_seed: Random seed for reproducible sampling

    Returns:
        List of candidate samples with embeddings
    """
    # Set random seed for reproducibility
    random.seed(random_seed)
    np.random.seed(random_seed)
    torch.manual_seed(random_seed)

    print(f"[DICL] Building candidate pool...")
    print(f"[DICL] Input: {input_path}")
    print(f"[DICL] Output: {output_path}")
    print(f"[DICL] Samples per type: {samples_per_type}")
    print(f"[DICL] Random seed: {random_seed}")

    # Load training data with SQL labels
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    print(f"[DICL] Loading training data from: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        train_data = json.load(f)

    print(f"[DICL] Loaded {len(train_data)} training samples")

    # Sample candidates from each SQL type
    candidates = sample_candidates_by_type(train_data, samples_per_type)

    if not candidates:
        raise ValueError("No candidates selected!")

    # Initialize PhoBERT embedder
    embedder = PhoBERTEmbedder()

    # Generate embeddings for each candidate
    print(f"[DICL] Generating embeddings for {len(candidates)} candidates...")

    enhanced_candidates = []
    for i, candidate in enumerate(candidates):
        if i % 10 == 0:
            print(f"[DICL] Processing candidate {i+1}/{len(candidates)}...")

        # Create enhanced candidate with embedding
        enhanced_candidate = {
            "db_id": candidate.get("db_id", ""),
            "question": candidate.get("question", ""),
            "query": candidate.get("query", ""),
            "sql_type": candidate.get("sql_type", "UNKNOWN")
        }

        # Generate embedding for the question
        question = enhanced_candidate["question"]
        if question:
            embedding = embedder.encode(question)
            enhanced_candidate["question_embedding"] = embedding
        else:
            print(f"[DICL] Warning: Empty question for candidate {i}")
            enhanced_candidate["question_embedding"] = [0.0] * 768

        enhanced_candidates.append(enhanced_candidate)

    # Save enhanced candidates
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enhanced_candidates, f, indent=2, ensure_ascii=False)

    print(f"[DICL] Saved {len(enhanced_candidates)} candidates to: {output_file}")

    # Print statistics
    print(f"\n[DICL] Candidate Pool Statistics:")
    print("=" * 50)

    type_counts = {}
    for candidate in enhanced_candidates:
        sql_type = candidate["sql_type"]
        type_counts[sql_type] = type_counts.get(sql_type, 0) + 1

    total_candidates = len(enhanced_candidates)
    for sql_type, count in sorted(type_counts.items()):
        percentage = (count / total_candidates) * 100 if total_candidates > 0 else 0
        print(f"{sql_type:12}: {count:3d} candidates ({percentage:5.1f}%)")

    print("=" * 50)
    print(f"{'TOTAL':12}: {total_candidates:3d} candidates (100.0%)")

    return enhanced_candidates


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(
        description="Build DICL candidate pool with PhoBERT embeddings"
    )
    parser.add_argument(
        '--input',
        default='dataset/ViText2SQL/std-level/train_with_sql_labels.json',
        help='Input path to training data with SQL labels'
    )
    parser.add_argument(
        '--output',
        default='dataset/ViText2SQL/std-level/dicl_candidates.json',
        help='Output path for DICL candidates'
    )
    parser.add_argument(
        '--samples-per-type',
        type=int,
        default=20,
        help='Number of samples to select per SQL type'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducible sampling'
    )

    args = parser.parse_args()

    print("🚀 Starting DICL Candidate Pool Builder")
    print("=" * 60)

    try:
        candidates = build_dicl_candidates(
            args.input,
            args.output,
            args.samples_per_type,
            args.seed
        )

        print(f"\n🎉 DICL candidate pool built successfully!")
        print(f"📂 Output saved to: {args.output}")
        print(f"📊 Total candidates: {len(candidates)}")

    except Exception as e:
        print(f"\n❌ Error building candidate pool: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
