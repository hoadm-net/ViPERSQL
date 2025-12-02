"""
Multi-language ViR2 (Two-Stage Example Selection) Selector for ViPERSQL

Implements a two-stage selection strategy with multi-language support:
1. Stage 1: Language-aware semantic retrieval from meaning pool (top-M candidates)
   - Vietnamese: PhoBERT-base-v2 embeddings
   - English: BERT-base-uncased embeddings
2. Stage 2: Beam search re-ranking with POS matching and diversity
   - Vietnamese: underthesea + spaCy POS tagging
   - English: spaCy POS tagging
"""

import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import heapq
from sklearn.metrics.pairwise import cosine_similarity

from .base_selector import BaseSelector
from ..utils.multilang_embedder import MultiLanguageEmbedder
from ..utils.language_detector import LanguageDetector
from ..metrics.pos_match_multilang import POSMatcher


class MultiLanguageViR2Selector(BaseSelector):
    """
    Multi-language ViR2 (Two-Stage Example Selection) Selector

    Stage 1: Language-aware semantic retrieval from meaning pool
    Stage 2: Beam search with POS matching and diversity optimization
    
    Supports both Vietnamese and English with automatic language detection.
    """

    def __init__(self, config):
        """Initialize multi-language ViR2 selector with configurable parameters."""
        super().__init__(config)

        # Configurable hyperparameters
        self.M = getattr(config, 'vir2_candidate_pool_size', 50)  # Stage 1 pool size
        self.beam_size = getattr(config, 'vir2_beam_size', 5)     # Beam search size
        self.diversity_weight = getattr(config, 'vir2_diversity_weight', 0.3)  # λ parameter

        # Multi-language components
        self.embedder = MultiLanguageEmbedder(cache_models=True)
        self.language_detector = LanguageDetector()
        self.pos_matcher = POSMatcher()

        # Data storage
        self.meaning_pool = []
        self.meaning_pool_embeddings = None
        self.meaning_pool_language = None  # Track language of meaning pool

        print(f"[MultiLanguageViR2] Initialized with M={self.M}, beam_size={self.beam_size}, λ={self.diversity_weight}")

    def load_training_data(self, dataset_path: str) -> List[Dict]:
        """Load meaning pool from dicl_candidates.json with language detection."""
        try:
            # Load from dicl_candidates.json (meaning pool)
            candidates_path = dataset_path.replace('train.json', 'dicl_candidates.json')
            with open(candidates_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.meaning_pool = data

            # Detect language from first few examples
            if len(data) > 0:
                sample_questions = [ex['question'] for ex in data[:5] if 'question' in ex]
                if sample_questions:
                    # Use majority vote for language detection
                    language_votes = [self.language_detector.detect_language(q) for q in sample_questions]
                    self.meaning_pool_language = max(set(language_votes), key=language_votes.count)
                    print(f"[MultiLanguageViR2] Detected meaning pool language: {self.meaning_pool_language}")
                else:
                    self.meaning_pool_language = "vi"  # Default fallback
            else:
                self.meaning_pool_language = "vi"

            # Check for pre-computed embeddings that match current language
            if self._check_embedding_compatibility(data):
                self.meaning_pool_embeddings = np.array([
                    example['embedding'] for example in data
                ])
                print(f"[MultiLanguageViR2] Loaded {len(self.meaning_pool)} examples with compatible embeddings")
            else:
                print(f"[MultiLanguageViR2] Pre-computed embeddings incompatible or missing, computing new embeddings...")
                self._compute_meaning_pool_embeddings()

            return self.meaning_pool

        except Exception as e:
            print(f"[MultiLanguageViR2] Error loading meaning pool: {e}")
            return []

    def _check_embedding_compatibility(self, data: List[Dict]) -> bool:
        """Check if pre-computed embeddings are compatible with current language setup."""
        if len(data) == 0 or 'embedding' not in data[0]:
            return False
        
        # Check if embedding dimension matches expected dimension (768 for both BERT and PhoBERT)
        expected_dim = self.embedder.get_embedding_dimension()
        actual_dim = len(data[0]['embedding'])
        
        if actual_dim != expected_dim:
            print(f"[MultiLanguageViR2] Embedding dimension mismatch: expected {expected_dim}, got {actual_dim}")
            return False
        
        # Additional checks could include verifying model metadata if stored
        return True

    def _compute_meaning_pool_embeddings(self):
        """Compute embeddings for meaning pool using appropriate language model."""
        print(f"[MultiLanguageViR2] Computing embeddings for {len(self.meaning_pool)} examples using {self.meaning_pool_language} model...")
        
        # Extract questions
        questions = [example['question'] for example in self.meaning_pool]
        
        # Generate embeddings in batches
        embeddings = self.embedder.encode_batch(questions, language=self.meaning_pool_language, batch_size=32)
        
        self.meaning_pool_embeddings = embeddings
        print(f"[MultiLanguageViR2] Finished computing embeddings: {embeddings.shape}")

    def select_examples(self, question: str, k: int = 3, db_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Select k examples using two-stage ViR2 strategy with language awareness.
        
        Args:
            question: Input natural language question
            k: Number of examples to select  
            db_id: Database ID for filtering (optional)
            
        Returns:
            List of k selected examples
        """
        if not self.meaning_pool or self.meaning_pool_embeddings is None:
            print(f"[MultiLanguageViR2] No training data available")
            return []

        # Detect question language
        question_language = self.language_detector.detect_language(question)
        print(f"[MultiLanguageViR2] Question language: {question_language}, Pool language: {self.meaning_pool_language}")

        try:
            # Stage 1: Semantic retrieval
            candidates = self._stage1_retrieve(question, question_language)
            
            if len(candidates) == 0:
                print(f"[MultiLanguageViR2] No candidates found in Stage 1")
                return []

            # Stage 2: Beam search re-ranking  
            selected = self._stage2_beam_search(question, candidates, k, question_language)
            
            print(f"[MultiLanguageViR2] Selected {len(selected)} examples using two-stage selection")
            return selected

        except Exception as e:
            print(f"[MultiLanguageViR2] Error in example selection: {e}")
            # Fallback to random selection from meaning pool
            import random
            fallback_k = min(k, len(self.meaning_pool))
            return random.sample(self.meaning_pool, fallback_k)

    def _stage1_retrieve(self, question: str, question_language: str) -> List[Dict]:
        """Stage 1: Retrieve top-M candidates using semantic similarity."""
        # Encode question using appropriate language model
        question_embedding = self.embedder.encode(question, language=question_language)
        
        # Handle cross-lingual scenarios
        if question_language != self.meaning_pool_language:
            print(f"[MultiLanguageViR2] Cross-lingual retrieval: {question_language} -> {self.meaning_pool_language}")
            # Could implement cross-lingual embeddings or translation here
            # For now, proceed with direct comparison (may have reduced performance)
        
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
            candidate['similarity'] = float(similarities[idx])
            candidate['stage1_rank'] = len(candidates) + 1
            candidates.append(candidate)

        print(f"[MultiLanguageViR2] Stage 1: Retrieved {len(candidates)} candidates (similarity range: {similarities[top_indices[-1]:.3f} - {similarities[top_indices[0]:.3f})")
        return candidates

    def _stage2_beam_search(self, question: str, candidates: List[Dict], k: int, question_language: str) -> List[Dict]:
        """Stage 2: Beam search re-ranking with POS matching and diversity."""
        if len(candidates) <= k:
            return candidates

        # Initialize beam with best semantic candidate
        beam = [candidates[0]]
        candidates = candidates[1:]  # Remove first candidate from pool

        # Beam search to select remaining k-1 examples
        for step in range(k - 1):
            if not candidates:
                break

            best_candidate = None
            best_score = float('-inf')

            # Evaluate each candidate
            for candidate in candidates:
                score = self._calculate_beam_score(question, candidate, beam, question_language)
                
                if score > best_score:
                    best_score = score
                    best_candidate = candidate

            if best_candidate is not None:
                beam.append(best_candidate)
                candidates.remove(best_candidate)

        print(f"[MultiLanguageViR2] Stage 2: Beam search selected {len(beam)} examples")
        return beam

    def _calculate_beam_score(self, question: str, candidate: Dict, current_beam: List[Dict], question_language: str) -> float:
        """Calculate beam search score combining POS match and diversity."""
        # POS matching score
        pos_score = self.pos_matcher.pos_match(
            question, 
            candidate['question'], 
            language=question_language
        )

        # Diversity score (minimum similarity to already selected examples)
        if len(current_beam) == 0:
            diversity_score = 1.0
        else:
            similarities = []
            for selected in current_beam:
                # Use semantic similarity for diversity
                sim = self._calculate_question_similarity(candidate['question'], selected['question'], question_language)
                similarities.append(sim)
            
            # Use minimum similarity as diversity measure (lower = more diverse)
            min_similarity = min(similarities)
            diversity_score = 1.0 - min_similarity

        # Combined score: λ * pos_score + (1-λ) * diversity_score
        combined_score = self.diversity_weight * pos_score + (1 - self.diversity_weight) * diversity_score

        return combined_score

    def _calculate_question_similarity(self, question1: str, question2: str, language: str) -> float:
        """Calculate semantic similarity between two questions."""
        try:
            emb1 = self.embedder.encode(question1, language=language)
            emb2 = self.embedder.encode(question2, language=language)
            
            similarity = cosine_similarity(emb1.reshape(1, -1), emb2.reshape(1, -1))[0][0]
            return float(similarity)
        except Exception as e:
            print(f"[MultiLanguageViR2] Error calculating similarity: {e}")
            return 0.0

    def get_selection_info(self, question: str, k: int = 3) -> Dict[str, Any]:
        """Get detailed information about the selection process for debugging."""
        question_language = self.language_detector.detect_language(question)
        
        # Stage 1 info
        candidates = self._stage1_retrieve(question, question_language)
        
        # Stage 2 info  
        if len(candidates) > k:
            selected = self._stage2_beam_search(question, candidates, k, question_language)
            
            return {
                "question_language": question_language,
                "pool_language": self.meaning_pool_language,
                "stage1_candidates": len(candidates),
                "stage2_selected": len(selected),
                "hyperparameters": {
                    "M": self.M,
                    "beam_size": self.beam_size,
                    "diversity_weight": self.diversity_weight
                },
                "candidates_info": [
                    {
                        "question": c['question'][:100] + "..." if len(c['question']) > 100 else c['question'],
                        "similarity": c.get('similarity', 0.0),
                        "stage1_rank": c.get('stage1_rank', 0)
                    } for c in candidates[:10]  # Show top 10
                ],
                "selected_info": [
                    {
                        "question": s['question'][:100] + "..." if len(s['question']) > 100 else s['question'],
                        "similarity": s.get('similarity', 0.0)
                    } for s in selected
                ]
            }
        else:
            return {
                "question_language": question_language,
                "pool_language": self.meaning_pool_language,
                "stage1_candidates": len(candidates),
                "stage2_selected": len(candidates),
                "note": "Not enough candidates for beam search"
            }
