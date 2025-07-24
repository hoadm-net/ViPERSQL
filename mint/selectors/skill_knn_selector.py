"""
Skill-based KNN Example Selector for Few-shot Learning

This module implements a sophisticated example selection strategy that:
1. Uses LLM to extract SQL skills from natural language questions
2. Uses BERT to create embeddings for skill sets
3. Uses cosine similarity to find the most relevant examples
"""

import json
import numpy as np
import torch
from pathlib import Path
from typing import List, Dict, Any, Optional
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity

from .base_selector import BaseSelector
from ..core.llm_interface import LLMInterface


class BERTEmbedder:
    """BERT embedding generator using google-bert/bert-base-uncased."""

    def __init__(self, model_name: str = "google-bert/bert-base-uncased"):
        """Initialize BERT model and tokenizer."""
        print(f"[SkillKNN] Loading BERT model: {model_name}")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[SkillKNN] Using device: {self.device}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()

    def encode(self, text: str) -> List[float]:
        """Generate embedding for input text."""
        try:
            # Tokenize and encode
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                max_length=512,
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
            print(f"[SkillKNN] Error generating embedding for text '{text}': {e}")
            # Return zero vector as fallback
            return [0.0] * 768  # BERT base has 768 dimensions


class SkillKNNSelector(BaseSelector):
    """
    Skill-based KNN example selector for Few-shot learning.

    This selector uses LLM to extract skills from questions and finds
    the most similar examples based on skill similarity using BERT embeddings.
    """

    def __init__(self, config):
        """Initialize the Skill KNN Selector."""
        super().__init__(config)
        self.llm_interface = LLMInterface(config)
        self.embedder = BERTEmbedder()

        # Load skill extraction template
        self.skill_template_path = Path(config.template_dir) / "skill_extraction_vietnamese.txt"
        self._load_skill_template()

        # Cache for training examples with skills and embeddings
        self._skill_examples_cache = None

    def _load_skill_template(self):
        """Load the skill extraction template."""
        if not self.skill_template_path.exists():
            raise FileNotFoundError(f"Skill extraction template not found: {self.skill_template_path}")

        with open(self.skill_template_path, 'r', encoding='utf-8') as f:
            self.skill_template = f.read()

    def load_skill_training_data(self, dataset_path: str) -> List[Dict]:
        """Load training data with pre-computed skills and embeddings."""
        skill_knn_file = Path(dataset_path) / "std-level" / "skill_knn_train.json"

        if not skill_knn_file.exists():
            raise FileNotFoundError(
                f"Skill KNN training data not found: {skill_knn_file}\n"
                f"Please run: python scripts/skill_knn_preprocessing.py to generate this file."
            )

        print(f"[SkillKNN] Loading skill training data from {skill_knn_file}")

        with open(skill_knn_file, 'r', encoding='utf-8') as f:
            skill_data = json.load(f)

        self._skill_examples_cache = skill_data
        print(f"[SkillKNN] Loaded {len(skill_data)} examples with skills and embeddings")
        return skill_data

    def extract_skills_from_question(self, question: str) -> str:
        """Extract SQL skills from a natural language question using LLM."""
        try:
            # Prepare prompt with the skill extraction template
            prompt = self.skill_template.replace("{question}", question)

            # Get skills from LLM
            response = self.llm_interface.generate(
                prompt=prompt,
                model=self.config.model_name,
                temperature=0.1,  # Low temperature for consistent skill extraction
                max_tokens=500
            )

            # Clean and format the response
            skills = response.strip()
            if skills:
                print(f"[SkillKNN] Extracted skills: {skills}")
                return skills
            else:
                print(f"[SkillKNN] No skills extracted from question")
                return ""

        except Exception as e:
            print(f"[SkillKNN] Error extracting skills: {e}")
            return ""

    def select_examples(
        self,
        question: str,
        k: int = 3,
        db_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Select k most similar examples based on skill similarity.

        Args:
            question: The input natural language question
            k: Number of examples to select
            db_id: Database ID for filtering (optional)

        Returns:
            List of k most similar examples
        """
        # Load training data if not cached
        if self._skill_examples_cache is None:
            dataset_path = self.config.dataset_path
            self.load_skill_training_data(dataset_path)

        # Extract skills from the input question
        print(f"[SkillKNN] Extracting skills from question...")
        question_skills = self.extract_skills_from_question(question)
        print(f"[SkillKNN] Extracted skills: {question_skills}")

        if not question_skills:
            print("[SkillKNN] No skills extracted, falling back to random selection")
            return self._fallback_random_selection(k, db_id)

        # Generate embedding for question skills
        question_embedding = self.embedder.encode(question_skills)
        question_embedding = np.array(question_embedding).reshape(1, -1)

        # Filter examples by db_id if specified
        candidate_examples = self._skill_examples_cache
        if db_id:
            candidate_examples = [ex for ex in candidate_examples if ex.get('db_id') == db_id]
            if not candidate_examples:
                print(f"[SkillKNN] No examples found for db_id {db_id}, using all examples")
                candidate_examples = self._skill_examples_cache

        # Calculate similarities
        similarities = []
        for i, example in enumerate(candidate_examples):
            try:
                # Get pre-computed embedding or compute on-the-fly
                if 'skills_embedding' in example and example['skills_embedding']:
                    example_embedding = np.array(example['skills_embedding']).reshape(1, -1)
                else:
                    # Fallback: compute embedding on-the-fly
                    example_skills = example.get('skills', '')
                    if not example_skills:
                        continue
                    example_embedding = np.array(self.embedder.encode(example_skills)).reshape(1, -1)

                # Calculate cosine similarity
                similarity = cosine_similarity(question_embedding, example_embedding)[0][0]
                similarities.append((i, similarity, example))

            except Exception as e:
                print(f"[SkillKNN] Error calculating similarity for example {i}: {e}")
                continue

        if not similarities:
            print("[SkillKNN] No valid similarities computed, falling back to random selection")
            return self._fallback_random_selection(k, db_id)

        # Sort by similarity (descending) and select top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        selected_examples = [item[2] for item in similarities[:k]]

        print(f"[SkillKNN] Selected {len(selected_examples)} examples based on skill similarity")
        for i, (_, sim, _) in enumerate(similarities[:k]):
            print(f"[SkillKNN] Example {i+1} similarity: {sim:.4f}")

        return selected_examples

    def _fallback_random_selection(self, k: int, db_id: Optional[str] = None) -> List[Dict]:
        """Fallback to random selection when skill-based selection fails."""
        import random

        candidate_examples = self._skill_examples_cache
        if db_id:
            candidate_examples = [ex for ex in candidate_examples if ex.get('db_id') == db_id]
            if not candidate_examples:
                candidate_examples = self._skill_examples_cache

        if not candidate_examples:
            return []

        if len(candidate_examples) <= k:
            return candidate_examples.copy()
        return random.sample(candidate_examples, k)
