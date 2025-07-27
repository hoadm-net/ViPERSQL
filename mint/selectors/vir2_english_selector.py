"""
ViR2 English Selector - Adaptation of ViR2 for English language

Uses BERT-base-uncased and simple POS matching instead of spaCy
to avoid dependency issues.
"""

import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import heapq
import re

from mint.selectors.base_selector import BaseSelector


class SimplePOSMatcher:
    """Simple English POS matcher without spaCy dependency."""

    def __init__(self):
        # Simple word lists for basic POS matching
        self.question_words = {'what', 'who', 'where', 'when', 'why', 'how', 'which'}
        self.verbs = {'is', 'are', 'was', 'were', 'have', 'has', 'had', 'do', 'does', 'did', 'can', 'could', 'will', 'would', 'should'}
        self.prepositions = {'in', 'on', 'at', 'by', 'for', 'with', 'from', 'to', 'of', 'about', 'under', 'over'}

    def pos_match(self, question1: str, question2: str) -> float:
        """Calculate simple POS matching score between two English questions."""
        try:
            # Convert to lowercase and split
            words1 = set(question1.lower().split())
            words2 = set(question2.lower().split())

            # Calculate overlap for different word types
            q_words1 = words1 & self.question_words
            q_words2 = words2 & self.question_words

            verbs1 = words1 & self.verbs
            verbs2 = words2 & self.verbs

            prep1 = words1 & self.prepositions
            prep2 = words2 & self.prepositions

            # Calculate similarity for each category
            q_sim = len(q_words1 & q_words2) / max(len(q_words1 | q_words2), 1)
            v_sim = len(verbs1 & verbs2) / max(len(verbs1 | verbs2), 1)
            p_sim = len(prep1 & prep2) / max(len(prep1 | prep2), 1)

            # Overall similarity (weighted average)
            return (q_sim * 0.4 + v_sim * 0.3 + p_sim * 0.3)

        except Exception as e:
            print(f"Error in simple POS matching: {e}")
            return 0.0


class ViR2EnglishSelector(BaseSelector):
    """
    ViR2 English Selector - Two-Stage Example Selection for English

    Stage 1: BERT-base-uncased semantic retrieval from meaning pool
    Stage 2: Beam search re-ranking with simple English POS matching and diversity
    """

    def __init__(self, config):
        """Initialize ViR2 English selector with configurable parameters."""
        super().__init__(config)

        # Configurable hyperparameters
        self.M = getattr(config, 'vir2_candidate_pool_size', 50)  # Stage 1 pool size
        self.beam_size = getattr(config, 'vir2_beam_size', 5)     # Beam search size
        self.diversity_weight = getattr(config, 'vir2_diversity_weight', 0.3)  # λ parameter

        # Model components
        self.tokenizer = None
        self.model = None
        self.pos_matcher = SimplePOSMatcher()

        # Data storage
        self.meaning_pool = []
        self.meaning_pool_embeddings = None

        self._load_bert_english()

    def _load_bert_english(self):
        """Load BERT-base-uncased model and tokenizer for English."""
        try:
            model_name = "google-bert/bert-base-uncased"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            self.model.eval()
            print(f"Loaded English BERT model: {model_name}")
        except Exception as e:
            print(f"Error loading BERT: {e}")
            print("Make sure to install: pip install transformers torch")

    def _encode_question(self, question: str) -> np.ndarray:
        """Encode English question using BERT with mean pooling."""
        if self.tokenizer is None or self.model is None:
            raise RuntimeError("BERT model not loaded")

        # Tokenize and encode
        inputs = self.tokenizer(question, return_tensors="pt",
                              truncation=True, max_length=512, padding=True)

        with torch.no_grad():
            outputs = self.model(**inputs)
            # Mean pooling
            embeddings = outputs.last_hidden_state.mean(dim=1)

        return embeddings.numpy().flatten()

    def load_training_data(self, dataset_path: str) -> List[Dict]:
        """Load English meaning pool from candidates.json."""
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.meaning_pool = data

            # Compute embeddings for English meaning pool
            print(f"Loaded {len(self.meaning_pool)} English examples from meaning pool")
            self._compute_meaning_pool_embeddings()

            return self.meaning_pool

        except Exception as e:
            print(f"Error loading English meaning pool: {e}")
            return []

    def _compute_meaning_pool_embeddings(self):
        """Compute BERT embeddings for English meaning pool."""
        print("Computing BERT embeddings for English meaning pool...")
        embeddings = []

        for i, example in enumerate(self.meaning_pool):
            if i % 100 == 0:
                print(f"Processing {i}/{len(self.meaning_pool)}")

            question = example['question']
            embedding = self._encode_question(question)
            embeddings.append(embedding)

        self.meaning_pool_embeddings = np.array(embeddings)
        print("Finished computing English embeddings")

    def _stage1_retrieve(self, question: str) -> List[Dict]:
        """Stage 1: Retrieve top-M candidates from English meaning pool using BERT similarity."""
        # Encode new English question
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

        print(f"Stage 1: Retrieved {len(candidates)} English candidates")
        return candidates

    def _calculate_pos_match_score(self, question: str, example_question: str) -> float:
        """Calculate English POS matching score between questions."""
        try:
            return self.pos_matcher.pos_match(question, example_question)
        except Exception as e:
            print(f"Error calculating English POS match: {e}")
            return 0.0

    def _calculate_diversity_score(self, selected_examples: List[Dict]) -> float:
        """Calculate diversity score for selected English examples."""
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
        """Calculate beam search score for selected English examples."""
        if not selected_examples:
            return 0.0

        # English POS matching component
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
        """Stage 2: Beam search re-ranking with English POS matching and diversity."""
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
        print(f"Stage 2: Selected {len(best_examples)} English examples with score {best_score:.4f}")

        return best_examples

    def select_examples(
        self,
        question: str,
        k: int = 3,
        db_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Select k English examples for the given question (BaseSelector interface).

        Args:
            question: The input English question
            k: Number of examples to select
            db_id: Database ID (not used in ViR2 as it works with meaning pool)

        Returns:
            List of selected examples
        """
        return self.select(question, k)

    def select(self, question: str, k: int = 5) -> List[Dict]:
        """
        Select English examples using ViR2 two-stage approach.

        Args:
            question: The input English question
            k: Number of examples to select

        Returns:
            List of selected examples
        """
        if not self.meaning_pool:
            print("Warning: No English meaning pool loaded")
            return []

        print(f"ViR2 English selection for question: {question[:50]}...")

        # Stage 1: Retrieve candidates from meaning pool
        candidates = self._stage1_retrieve(question)

        if not candidates:
            print("No English candidates found in stage 1")
            return []

        # Stage 2: Re-rank with beam search
        selected = self._stage2_rerank(candidates, question, k)

        print(f"ViR2 English selected {len(selected)} examples")
        return selected
