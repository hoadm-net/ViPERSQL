"""
Base class for example selectors in few-shot learning.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseSelector(ABC):
    """
    Abstract base class for example selectors.

    All example selectors should inherit from this class and implement
    the select_examples method.
    """

    def __init__(self, config):
        """Initialize the selector with configuration."""
        self.config = config

    @abstractmethod
    def select_examples(
        self,
        question: str,
        k: int = 3,
        db_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Select k examples for the given question.

        Args:
            question: The input natural language question
            k: Number of examples to select
            db_id: Database ID for filtering (optional)

        Returns:
            List of k selected examples
        """
        pass

    def load_training_data(self, dataset_path: str) -> List[Dict]:
        """
        Load training data from dataset.

        Args:
            dataset_path: Path to the dataset

        Returns:
            List of training examples
        """
        try:
            import json
            from pathlib import Path
            train_file = Path(dataset_path) / "train.json"
            if not train_file.exists():
                print(f"[{self.__class__.__name__}] Training file not found: {train_file}")
                return []
            with open(train_file, 'r', encoding='utf-8') as f:
                train_data = json.load(f)
            print(f"[{self.__class__.__name__}] Loaded {len(train_data)} training examples")
            return train_data
        except Exception as e:
            print(f"[{self.__class__.__name__}] Failed to load training examples: {e}")
            return []
