"""
Random example selector for few-shot learning.
"""

import random
from typing import List, Dict, Any, Optional
from .base_selector import BaseSelector


class RandomSelector(BaseSelector):
    """
    Random example selector that randomly selects k examples from training data.

    This is a simple but effective baseline selector that doesn't consider
    any similarity between the input question and training examples.
    """

    def __init__(self, config):
        """Initialize the random selector."""
        super().__init__(config)
        self._training_examples = None

    def select_examples(
        self,
        question: str,
        k: int = 3,
        db_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Randomly select k examples from training data.

        Args:
            question: The input natural language question (not used in random selection)
            k: Number of examples to select
            db_id: Database ID for filtering (optional)

        Returns:
            List of k randomly selected examples
        """
        # Load training data if not cached
        if self._training_examples is None:
            dataset_path = self.config.dataset_full_path
            self._training_examples = self.load_training_data(dataset_path)

        if not self._training_examples:
            print(f"[RandomSelector] No training examples available")
            return []

        # Filter by db_id if specified
        candidate_examples = self._training_examples
        if db_id:
            candidate_examples = [ex for ex in self._training_examples if ex.get('db_id') == db_id]
            if not candidate_examples:
                print(f"[RandomSelector] No examples found for database {db_id}, using all examples")
                candidate_examples = self._training_examples

        # Randomly select k examples
        if len(candidate_examples) <= k:
            selected = candidate_examples.copy()
        else:
            selected = random.sample(candidate_examples, k)

        print(f"[RandomSelector] Selected {len(selected)} examples randomly")
        return selected
