"""
ViR2 (Two-Stage Example Selection) Selector for ViPERSQL

Implements a two-stage selection strategy:
1. Stage 1: PhoBERT-based semantic retrieval from meaning pool (top-M candidates)
2. Stage 2: Beam search re-ranking with POS matching and diversity
"""

import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import heapq

from .base_selector import BaseSelector
from ..metrics.pos_match import POSMatcher


class ViR2Selector(BaseSelector):
    """
    ViR2 (Two-Stage Example Selection) Selector

    Stage 1: PhoBERT semantic retrieval from meaning pool
    Stage 2: Beam search with POS matching and diversity optimization
    """

    def __init__(self, config):
        """Initialize ViR2 selector with configurable parameters."""
        super().__init__(config)

        # Configurable hyperparameters
        self.M = getattr(config, 'vir2_candidate_pool_size', 50)  # Stage 1 pool size
        self.beam_size = getattr(config, 'vir2_beam_size', 5)     # Beam search size
        self.diversity_weight = getattr(config, 'vir2_diversity_weight', 0.3)  # λ parameter

        # Model components
        self.tokenizer = None
        self.model = None
        self.pos_matcher = POSMatcher()

        # Data storage
        self.meaning_pool = []
        self.meaning_pool_embeddings = None

        self._load_phobert()

    def _load_phobert(self):
        """Load PhoBERT-base-v2 model and tokenizer."""
        try:
            model_name = "vinai/phobert-base-v2"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            self.model.eval()
            print(f"Loaded PhoBERT model: {model_name}")
        except Exception as e:
            print(f"Error loading PhoBERT: {e}")
            print("Make sure to install: pip install transformers torch")

    def _encode_question(self, question: str) -> np.ndarray:
        """Encode question using PhoBERT with mean pooling."""
        if self.tokenizer is None or self.model is None:
            raise RuntimeError("PhoBERT model not loaded")

        # Tokenize and encode
        inputs = self.tokenizer(question, return_tensors="pt",
                              truncation=True, max_length=512, padding=True)

        with torch.no_grad():
            outputs = self.model(**inputs)
            # Mean pooling
            embeddings = outputs.last_hidden_state.mean(dim=1)

        return embeddings.numpy().flatten()

    def load_training_data(self, dataset_path: str) -> List[Dict]:
        """Load meaning pool from dicl_candidates.json with pre-computed embeddings."""
        try:
            # Load from dicl_candidates.json (meaning pool)
            candidates_path = dataset_path.replace('train.json', 'dicl_candidates.json')
            with open(candidates_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.meaning_pool = data

            # Extract pre-computed embeddings
            if len(data) > 0 and 'embedding' in data[0]:
                self.meaning_pool_embeddings = np.array([
                    example['embedding'] for example in data
                ])
                print(f"Loaded {len(self.meaning_pool)} examples from meaning pool with pre-computed embeddings")
            else:
                print("Warning: No pre-computed embeddings found in meaning pool")
                # Fallback: compute embeddings
                self._compute_meaning_pool_embeddings()

            return self.meaning_pool

        except Exception as e:
            print(f"Error loading meaning pool: {e}")
            return []

    def _compute_meaning_pool_embeddings(self):
        """Fallback: compute embeddings for meaning pool if not available."""
        print("Computing PhoBERT embeddings for meaning pool...")
        embeddings = []

        for i, example in enumerate(self.meaning_pool):
            if i % 100 == 0:
                print(f"Processing {i}/{len(self.meaning_pool)}")

            question = example['question']
            embedding = self._encode_question(question)
            embeddings.append(embedding)

        self.meaning_pool_embeddings = np.array(embeddings)
        print("Finished computing embeddings")

    def _stage1_retrieve(self, question: str) -> List[Dict]:
        """Stage 1: Retrieve top-M candidates from meaning pool using PhoBERT similarity."""
        # Encode new question
        question_embedding = self._encode_question(question)

        # Compute cosine similarities
        similarities = cosine_similarity(
            question_embedding.reshape(1, -1),
            self.meaning_pool_embeddings
        )[0]

        # Get top-M candidates
        top_indices = np.argsort(similarities)[::-1][:self.M]

        candidates = []
        for idx in top_indices:
            candidate = self.meaning_pool[idx].copy()
            candidate['similarity'] = similarities[idx]
            candidates.append(candidate)

        print(f"Stage 1: Retrieved {len(candidates)} candidates")
        return candidates

    def _calculate_pos_match_score(self, question: str, example_question: str) -> float:
        """Calculate POS matching score between questions."""
        try:
            return self.pos_matcher.pos_match(question, example_question)
        except Exception as e:
            print(f"Error calculating POS match: {e}")
            return 0.0

    def _calculate_diversity_score(self, selected_examples: List[Dict]) -> float:
        """Calculate diversity score for selected examples."""
        if len(selected_examples) <= 1:
            return 1.0

        k = len(selected_examples)
        total_similarity = 0.0
        count = 0

        for i in range(k):
            for j in range(i + 1, k):
                # Use pre-computed embeddings for diversity calculation
                idx_i = next(idx for idx, ex in enumerate(self.meaning_pool)
                           if ex['question'] == selected_examples[i]['question'])
                idx_j = next(idx for idx, ex in enumerate(self.meaning_pool)
                           if ex['question'] == selected_examples[j]['question'])

                emb_i = self.meaning_pool_embeddings[idx_i]
                emb_j = self.meaning_pool_embeddings[idx_j]

                sim = cosine_similarity(emb_i.reshape(1, -1), emb_j.reshape(1, -1))[0][0]
                total_similarity += sim
                count += 1

        # Diversity = 1 - average pairwise similarity
        avg_similarity = total_similarity / count if count > 0 else 0
        diversity = 1 - avg_similarity

        return max(0, diversity)  # Ensure non-negative

    def _calculate_beam_score(self, selected_examples: List[Dict], question: str) -> float:
        """Calculate beam search score for selected examples."""
        if not selected_examples:
            return 0.0

        # POS matching component
        pos_scores = []
        for example in selected_examples:
            pos_score = self._calculate_pos_match_score(question, example['question'])
            pos_scores.append(pos_score)

        avg_pos_score = np.mean(pos_scores)

        # Diversity component
        diversity_score = self._calculate_diversity_score(selected_examples)

        # Combined score
        total_score = avg_pos_score + self.diversity_weight * diversity_score

        return total_score

    def _stage2_rerank(self, candidates: List[Dict], question: str, k: int) -> List[Dict]:
        """Stage 2: Beam search re-ranking with POS matching and diversity."""
        if k >= len(candidates):
            return candidates[:k]

        # Initialize beam with empty sequence
        beam = [([], 0.0)]  # (selected_examples, score)

        for step in range(k):
            new_beam = []

            for current_examples, current_score in beam:
                # Try adding each remaining candidate
                used_indices = set(
                    next(i for i, c in enumerate(candidates) if c['question'] == ex['question'])
                    for ex in current_examples
                )

                remaining_candidates = [
                    (i, candidates[i]) for i in range(len(candidates))
                    if i not in used_indices
                ]

                for idx, candidate in remaining_candidates:
                    new_examples = current_examples + [candidate]
                    new_score = self._calculate_beam_score(new_examples, question)
                    new_beam.append((new_examples, new_score))

            # Keep top beam_size sequences
            new_beam.sort(key=lambda x: x[1], reverse=True)
            beam = new_beam[:self.beam_size]

        # Return best sequence
        best_examples, best_score = beam[0]
        print(f"Stage 2: Selected {len(best_examples)} examples with score {best_score:.4f}")

        return best_examples

    def select_examples(
        self,
        question: str,
        k: int = 3,
        db_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Select k examples for the given question (BaseSelector interface).

        Args:
            question: The input question
            k: Number of examples to select
            db_id: Database ID (not used in ViR2 as it works with meaning pool)

        Returns:
            List of selected examples
        """
        return self.select(question, k)

    def select(self, question: str, k: int = 5) -> List[Dict]:
        """
        Select examples using ViR2 two-stage approach.

        Args:
            question: The input question
            k: Number of examples to select

        Returns:
            List of selected examples
        """
        if not self.meaning_pool:
            print("Warning: No meaning pool loaded")
            return []

        print(f"ViR2 selection for question: {question[:50]}...")

        # Stage 1: Retrieve candidates from meaning pool
        candidates = self._stage1_retrieve(question)

        if not candidates:
            print("No candidates found in stage 1")
            return []

        # Stage 2: Re-rank with beam search
        selected = self._stage2_rerank(candidates, question, k)

        print(f"ViR2 selected {len(selected)} examples")
        return selected
