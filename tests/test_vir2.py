#!/usr/bin/env python3
"""
Test script for ViR2Selector - Two-Stage Example Selection

This script tests the ViR2 selector implementation with a small example.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mint.config import ViPERConfig
from mint.selectors.vir2_selector import ViR2Selector
import json

def test_vir2_selector():
    """Test ViR2Selector with sample configuration."""
    print("=" * 60)
    print("Testing ViR2 (Two-Stage Example Selection) Selector")
    print("=" * 60)

    # Create test configuration
    config = ViPERConfig(
        dataset_path="dataset/ViText2SQL",
        level="std",
        vir2_candidate_pool_size=50,  # M=50 như đã thống nhất
        vir2_beam_size=5,
        vir2_diversity_weight=0.3
    )

    print(f"Configuration:")
    print(f"  - Candidate pool size (M): {config.vir2_candidate_pool_size}")
    print(f"  - Beam size (B): {config.vir2_beam_size}")
    print(f"  - Diversity weight (λ): {config.vir2_diversity_weight}")
    print(f"  - Dataset path: {config.dataset_path}")
    print()

    # Initialize ViR2Selector
    print("Initializing ViR2Selector...")
    selector = ViR2Selector(config)

    # Load training data
    print("Loading training data...")
    dataset_path = f"{config.dataset_path}/{config.level}-level/dicl_candidates.json"

    try:
        training_data = selector.load_training_data(dataset_path)
        print(f"Loaded {len(training_data)} training examples")

        if len(training_data) == 0:
            print("No training data loaded. Exiting.")
            return

        # Test example selection
        test_question = "Có bao nhiêu khách hàng ở Hà Nội?"
        k = 3

        print(f"\nTesting example selection:")
        print(f"  Question: {test_question}")
        print(f"  Number of examples to select (k): {k}")
        print()

        print("Running ViR2 two-stage selection...")
        selected_examples = selector.select_examples(test_question, k)

        print(f"\nSelected {len(selected_examples)} examples:")
        print("-" * 40)

        for i, example in enumerate(selected_examples):
            print(f"Example {i+1}:")
            print(f"  Question: {example.get('question', 'N/A')}")
            print(f"  SQL: {example.get('query', 'N/A')}")
            print(f"  DB ID: {example.get('db_id', 'N/A')}")
            print(f"  Selection rank: {example.get('selection_rank', 'N/A')}")
            print(f"  Selection method: {example.get('selection_method', 'N/A')}")
            print()

        print("=" * 60)
        print("ViR2Selector test completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vir2_selector()
