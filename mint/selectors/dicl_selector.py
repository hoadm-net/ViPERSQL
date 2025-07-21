"""
DICL (Diverse In-Context Learning) Selector

Implements Maximal Marginal Relevance (MMR) based example selection for
few-shot learning with diversity-aware candidate selection.

Algorithm:
1. Generate embedding for test question using PhoBERT-base-v2
2. Find M nearest candidates using cosine similarity
3. Re-rank using MMR to balance relevance and diversity
4. Select k diverse examples for in-context learning

MMR Formula:
MMR(x, u, S_{i-1}; α) = α * θ(x, u) - (1 - α) * max_{s ∈ S_{i-1}} θ(u, s)

Where:
- x: test query
- u: candidate example
- S_{i-1}: previously selected examples
- θ(a, b): similarity function (cosine similarity)
- α ∈ [0, 1]: relevance vs diversity trade-off parameter
"""

import json
import numpy as np
import torch
from pathlib import Path
from typing import List, Dict, Any, Optional
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity

from .base_selector import BaseSelector


class PhoBERTEmbedder:
    """PhoBERT embedding generator for Vietnamese text."""

    def __init__(self, model_name: str = "vinai/phobert-base-v2"):
        """Initialize PhoBERT model and tokenizer."""
        print(f"[DICL] Loading PhoBERT model: {model_name}")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()

    def encode(self, text: str) -> np.ndarray:
        """Generate embedding for Vietnamese text."""
        try:
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                max_length=256,
                truncation=True,
                padding=True
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1)

            return embeddings.cpu().numpy().flatten()

        except Exception as e:
            print(f"[DICL] Error generating embedding: {e}")
            return np.zeros(768)  # PhoBERT base dimension


class DICLSelector(BaseSelector):
    """
    DICL (Diverse In-Context Learning) selector using MMR algorithm.

    This selector implements a two-stage process:
    1. Retrieve M nearest candidates based on similarity
    2. Re-rank using MMR to select k diverse examples
    """

    def __init__(self, config, alpha: float = 0.7, M: int = 50):
        """
        Initialize DICL selector.

        Args:
            config: Configuration object
            alpha: Trade-off parameter between relevance and diversity (0 ≤ α ≤ 1)
                   α = 1.0: Pure relevance (no diversity)
                   α = 0.0: Pure diversity (no relevance)
                   α = 0.7: Balanced (recommended)
            M: Number of candidates to retrieve before re-ranking (M > k)
        """
        super().__init__(config)
        self.alpha = alpha
        self.M = M
        self.embedder = PhoBERTEmbedder()
        self.candidates = None
        self.candidate_embeddings = None

        print(f"[DICL] Initialized with α={alpha}, M={M}")

    def _load_candidates(self):
        """Load DICL candidate pool with embeddings."""
        if self.candidates is not None:
            return  # Already loaded

        candidates_path = Path(self.config.dataset_path) / "std-level" / "dicl_candidates.json"

        if not candidates_path.exists():
            raise FileNotFoundError(
                f"DICL candidates not found: {candidates_path}\n"
                f"Please run: python scripts/build_dicl_candidates.py to generate candidates."
            )

        print(f"[DICL] Loading candidates from: {candidates_path}")

        with open(candidates_path, 'r', encoding='utf-8') as f:
            self.candidates = json.load(f)

        # Extract embeddings
        self.candidate_embeddings = []
        for candidate in self.candidates:
            embedding = candidate.get('question_embedding', [])
            if not embedding:
                print(f"[DICL] Warning: Missing embedding for candidate")
                embedding = [0.0] * 768
            self.candidate_embeddings.append(np.array(embedding))

        self.candidate_embeddings = np.array(self.candidate_embeddings)

        print(f"[DICL] Loaded {len(self.candidates)} candidates")
        print(f"[DICL] Embedding matrix shape: {self.candidate_embeddings.shape}")

    def _compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        try:
            # Reshape to 2D for sklearn
            emb1 = embedding1.reshape(1, -1)
            emb2 = embedding2.reshape(1, -1)

            similarity = cosine_similarity(emb1, emb2)[0][0]
            return float(similarity)
        except:
            return 0.0

    def _retrieve_candidates(self, query_embedding: np.ndarray, M: int) -> List[int]:
        """
        Retrieve M nearest candidates based on cosine similarity.

        Args:
            query_embedding: Embedding of the test question
            M: Number of candidates to retrieve

        Returns:
            List of candidate indices sorted by similarity (descending)
        """
        # Compute similarities with all candidates
        query_emb = query_embedding.reshape(1, -1)
        similarities = cosine_similarity(query_emb, self.candidate_embeddings)[0]

        # Get top M candidates
        top_indices = np.argsort(similarities)[::-1][:M]

        print(f"[DICL] Retrieved top {len(top_indices)} candidates")
        print(f"[DICL] Similarity range: [{similarities[top_indices[-1]]:.4f}, {similarities[top_indices[0]]:.4f}]")

        return top_indices.tolist()

    def _compute_mmr_score(self,
                          query_embedding: np.ndarray,
                          candidate_idx: int,
                          selected_indices: List[int]) -> float:
        """
        Compute MMR score for a candidate.

        MMR(x, u, S_{i-1}; α) = α * θ(x, u) - (1 - α) * max_{s ∈ S_{i-1}} θ(u, s)

        Args:
            query_embedding: Test question embedding
            candidate_idx: Index of candidate to score
            selected_indices: Indices of previously selected examples

        Returns:
            MMR score
        """
        candidate_embedding = self.candidate_embeddings[candidate_idx]

        # Relevance term: similarity to query
        relevance = self._compute_similarity(query_embedding, candidate_embedding)

        # Diversity term: max similarity to selected examples
        if not selected_indices:
            # No examples selected yet, diversity term is 0
            max_similarity = 0.0
        else:
            similarities = []
            for selected_idx in selected_indices:
                selected_embedding = self.candidate_embeddings[selected_idx]
                sim = self._compute_similarity(candidate_embedding, selected_embedding)
                similarities.append(sim)
            max_similarity = max(similarities)

        # MMR formula
        mmr_score = self.alpha * relevance - (1 - self.alpha) * max_similarity

        return mmr_score

    def _mmr_rerank(self, query_embedding: np.ndarray, candidate_indices: List[int], k: int) -> List[int]:
        """
        Re-rank candidates using MMR algorithm.

        Args:
            query_embedding: Test question embedding
            candidate_indices: Retrieved candidate indices
            k: Number of examples to select

        Returns:
            List of k selected candidate indices
        """
        selected_indices = []
        remaining_indices = candidate_indices.copy()

        print(f"[DICL] MMR re-ranking: selecting {k} from {len(remaining_indices)} candidates")

        for i in range(k):
            if not remaining_indices:
                break

            # Compute MMR scores for all remaining candidates
            mmr_scores = []
            for candidate_idx in remaining_indices:
                mmr_score = self._compute_mmr_score(query_embedding, candidate_idx, selected_indices)
                mmr_scores.append((candidate_idx, mmr_score))

            # Select candidate with highest MMR score
            best_candidate_idx, best_score = max(mmr_scores, key=lambda x: x[1])

            selected_indices.append(best_candidate_idx)
            remaining_indices.remove(best_candidate_idx)

            print(f"[DICL] Selected example {i+1}/{k}: candidate {best_candidate_idx} (MMR={best_score:.4f})")

        return selected_indices

    def select_examples(self,
                       question: str,
                       k: int = 3,
                       db_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Select k diverse examples using DICL algorithm.

        Args:
            question: Test question in Vietnamese
            k: Number of examples to select
            db_id: Database ID (optional, not used in DICL)

        Returns:
            List of k selected examples
        """
        # Load candidates if not already loaded
        self._load_candidates()

        if not self.candidates:
            print("[DICL] No candidates available")
            return []

        # Adjust M if needed
        M = min(self.M, len(self.candidates))
        if M <= k:
            M = min(len(self.candidates), k * 3)  # Ensure M > k
            print(f"[DICL] Adjusted M to {M} (must be > k={k})")

        print(f"[DICL] Starting DICL selection for question: '{question[:50]}...'")
        print(f"[DICL] Parameters: k={k}, M={M}, α={self.alpha}")

        # Step 1: Generate embedding for test question
        query_embedding = self.embedder.encode(question)

        # Step 2: Retrieve M nearest candidates
        candidate_indices = self._retrieve_candidates(query_embedding, M)

        # Step 3: Re-rank using MMR
        selected_indices = self._mmr_rerank(query_embedding, candidate_indices, k)

        # Return selected examples
        selected_examples = []
        for idx in selected_indices:
            candidate = self.candidates[idx]
            # Remove embedding from output (too large)
            example = {
                "db_id": candidate.get("db_id", ""),
                "question": candidate.get("question", ""),
                "query": candidate.get("query", ""),
                "sql_type": candidate.get("sql_type", "UNKNOWN")
            }
            selected_examples.append(example)

        print(f"[DICL] Selected {len(selected_examples)} diverse examples")

        # Print SQL type diversity
        sql_types = [ex["sql_type"] for ex in selected_examples]
        type_counts = {}
        for sql_type in sql_types:
            type_counts[sql_type] = type_counts.get(sql_type, 0) + 1

        print(f"[DICL] SQL type diversity: {dict(type_counts)}")

        return selected_examples
