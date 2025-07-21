"""
ASTRES (AST-based Re-ranking with Structural Similarity) Selector

A novel example selection strategy that combines:
1. Zero-shot SQL generation for the test question
2. Semantic similarity using PhoBERT-base-v2 for candidate retrieval
3. Structural similarity using AST tree edit distance for re-ranking

Algorithm:
1. Generate SQL for test question using zero-shot strategy
2. Use PhoBERT to find M semantically similar candidates
3. Parse SQL queries to AST (both test and candidates)
4. Re-rank using AST tree edit distance
5. Select k most structurally similar examples
"""

import json
import numpy as np
import torch
import sqlparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
from sqlparse.sql import Statement, Token
from sqlparse.tokens import Keyword, Name, Punctuation

from .base_selector import BaseSelector
from ..strategies.zero_shot import ZeroShotStrategy


class SQLASTParser:
    """SQL AST parser and tree edit distance calculator."""

    def __init__(self):
        """Initialize the AST parser."""
        pass

    def parse_sql_to_ast(self, sql: str) -> Optional[Dict]:
        """
        Parse SQL query to AST representation.

        Args:
            sql: SQL query string

        Returns:
            AST representation as nested dict, None if parsing fails
        """
        try:
            # Clean and normalize SQL
            sql = sql.strip()
            if not sql:
                return None

            # Parse SQL using sqlparse
            parsed = sqlparse.parse(sql)
            if not parsed:
                return None

            # Convert to our AST representation
            ast = self._statement_to_ast(parsed[0])
            return ast

        except Exception as e:
            print(f"[ASTRES] Error parsing SQL '{sql}': {e}")
            return None

    def _statement_to_ast(self, statement: Statement) -> Dict:
        """Convert sqlparse Statement to AST dict."""
        ast = {
            'type': 'statement',
            'children': []
        }

        for token in statement.tokens:
            if token.is_whitespace:
                continue
            ast['children'].append(self._token_to_ast(token))

        return ast

    def _token_to_ast(self, token) -> Dict:
        """Convert sqlparse Token to AST node."""
        if hasattr(token, 'tokens'):  # Token group
            return {
                'type': token.__class__.__name__.lower(),
                'value': str(token.value).upper() if token.ttype in [Keyword] else str(token.value),
                'children': [self._token_to_ast(t) for t in token.tokens if not t.is_whitespace]
            }
        else:  # Single token
            return {
                'type': 'token',
                'token_type': str(token.ttype) if token.ttype else 'unknown',
                'value': str(token.value).upper() if token.ttype in [Keyword] else str(token.value),
                'children': []
            }

    def tree_edit_distance(self, ast1: Dict, ast2: Dict) -> float:
        """
        Calculate tree edit distance between two ASTs.

        Uses a simplified tree edit distance algorithm.
        Returns normalized distance (0-1, where 0 = identical).
        """
        if ast1 is None or ast2 is None:
            return 1.0  # Maximum distance if either AST is invalid

        # Use dynamic programming for tree edit distance
        return self._ted_recursive(ast1, ast2)

    def _ted_recursive(self, node1: Dict, node2: Dict) -> float:
        """Recursive tree edit distance calculation."""
        # Base cases
        if not node1 and not node2:
            return 0.0
        if not node1 or not node2:
            return 1.0

        # Node similarity
        node_similarity = self._node_similarity(node1, node2)

        # Children similarity
        children1 = node1.get('children', [])
        children2 = node2.get('children', [])

        if not children1 and not children2:
            return 1.0 - node_similarity

        # Calculate children edit distance
        children_distance = self._children_edit_distance(children1, children2)

        # Combine node and children similarities
        total_distance = (1.0 - node_similarity) * 0.5 + children_distance * 0.5
        return min(1.0, total_distance)

    def _node_similarity(self, node1: Dict, node2: Dict) -> float:
        """Calculate similarity between two nodes."""
        # Type similarity
        type_sim = 1.0 if node1.get('type') == node2.get('type') else 0.0

        # Value similarity
        val1 = str(node1.get('value', '')).upper()
        val2 = str(node2.get('value', '')).upper()
        value_sim = 1.0 if val1 == val2 else 0.0

        # Token type similarity (for leaf nodes)
        token_type_sim = 1.0 if node1.get('token_type') == node2.get('token_type') else 0.0

        # Weighted combination
        return (type_sim * 0.4 + value_sim * 0.4 + token_type_sim * 0.2)

    def _children_edit_distance(self, children1: List, children2: List) -> float:
        """Calculate edit distance between children lists."""
        if not children1 and not children2:
            return 0.0
        if not children1 or not children2:
            return 1.0

        # Simple approach: average of pairwise distances
        m, n = len(children1), len(children2)

        # Dynamic programming matrix
        dp = [[0.0] * (n + 1) for _ in range(m + 1)]

        # Initialize
        for i in range(m + 1):
            dp[i][0] = i / max(m, n)
        for j in range(n + 1):
            dp[0][j] = j / max(m, n)

        # Fill matrix
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                cost = self._ted_recursive(children1[i-1], children2[j-1])
                dp[i][j] = min(
                    dp[i-1][j] + 1.0 / max(m, n),      # deletion
                    dp[i][j-1] + 1.0 / max(m, n),      # insertion
                    dp[i-1][j-1] + cost                 # substitution
                )

        return dp[m][n]


class PhoBERTEmbedder:
    """PhoBERT embedding generator for Vietnamese text."""

    def __init__(self, model_name: str = "vinai/phobert-base-v2"):
        """Initialize PhoBERT model and tokenizer."""
        print(f"[ASTRES] Loading PhoBERT model: {model_name}")
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
            print(f"[ASTRES] Error generating embedding: {e}")
            return np.zeros(768)


class ASTRESSelector(BaseSelector):
    """
    ASTRES (AST-based Re-ranking with Structural Similarity) selector.

    Combines semantic similarity for candidate retrieval with structural
    similarity for final ranking using SQL AST analysis.
    """

    def __init__(self, config, M: int = 50):
        """
        Initialize ASTRES selector.

        Args:
            config: Configuration object
            M: Number of candidates to retrieve before re-ranking
        """
        super().__init__(config)
        self.M = M
        self.embedder = PhoBERTEmbedder()
        self.ast_parser = SQLASTParser()
        self.zero_shot_strategy = ZeroShotStrategy(config)

        # Caches
        self.candidates = None
        self.candidate_embeddings = None

        print(f"[ASTRES] Initialized with M={M}")

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

        print(f"[ASTRES] Loading candidates from: {candidates_path}")

        with open(candidates_path, 'r', encoding='utf-8') as f:
            self.candidates = json.load(f)

        # Extract embeddings
        self.candidate_embeddings = []
        for candidate in self.candidates:
            embedding = candidate.get('question_embedding', [])
            if not embedding:
                print(f"[ASTRES] Warning: Missing embedding for candidate")
                embedding = [0.0] * 768
            self.candidate_embeddings.append(np.array(embedding))

        self.candidate_embeddings = np.array(self.candidate_embeddings)

        print(f"[ASTRES] Loaded {len(self.candidates)} candidates")

    def _generate_zero_shot_sql(self, question: str, schema_info: Dict) -> Optional[str]:
        """Generate SQL using zero-shot strategy."""
        try:
            print(f"[ASTRES] Generating zero-shot SQL for question...")

            # Use existing zero-shot strategy
            result = self.zero_shot_strategy.generate_sql(
                question=question,
                schema_info=schema_info,
                db_id="temp"  # Temporary db_id
            )

            if result and result.sql_query:
                print(f"[ASTRES] Zero-shot SQL generated: {result.sql_query[:100]}...")
                return result.sql_query
            else:
                print(f"[ASTRES] Zero-shot generation failed")
                return None

        except Exception as e:
            print(f"[ASTRES] Error in zero-shot generation: {e}")
            return None

    def _fallback_to_few_shot_random(self, question: str, k: int, db_id: Optional[str] = None) -> List[Dict]:
        """Fallback to few-shot with random examples when zero-shot fails."""
        print(f"[ASTRES] Falling back to few-shot with random examples")

        try:
            from .random_selector import RandomSelector
            random_selector = RandomSelector(self.config)
            return random_selector.select_examples(question, k, db_id)
        except Exception as e:
            print(f"[ASTRES] Fallback also failed: {e}")
            return []

    def _retrieve_semantic_candidates(self, question: str, M: int) -> List[int]:
        """Retrieve M semantically similar candidates using PhoBERT."""
        # Generate embedding for question
        query_embedding = self.embedder.encode(question)

        # Compute similarities
        query_emb = query_embedding.reshape(1, -1)
        similarities = cosine_similarity(query_emb, self.candidate_embeddings)[0]

        # Get top M candidates
        top_indices = np.argsort(similarities)[::-1][:M]

        print(f"[ASTRES] Retrieved {len(top_indices)} semantic candidates")
        print(f"[ASTRES] Similarity range: [{similarities[top_indices[-1]]:.4f}, {similarities[top_indices[0]]:.4f}]")

        return top_indices.tolist()

    def _rerank_by_ast_similarity(self, test_sql: str, candidate_indices: List[int], k: int) -> List[int]:
        """Re-rank candidates by AST similarity."""
        print(f"[ASTRES] Re-ranking {len(candidate_indices)} candidates by AST similarity")

        # Parse test SQL to AST
        test_ast = self.ast_parser.parse_sql_to_ast(test_sql)
        if test_ast is None:
            print(f"[ASTRES] Failed to parse test SQL, using semantic ranking")
            return candidate_indices[:k]

        # Calculate AST similarities
        similarities = []
        for idx in candidate_indices:
            candidate = self.candidates[idx]
            candidate_sql = candidate.get('query', '')

            if not candidate_sql:
                continue

            # Parse candidate SQL
            candidate_ast = self.ast_parser.parse_sql_to_ast(candidate_sql)
            if candidate_ast is None:
                print(f"[ASTRES] Skipping candidate {idx} - failed to parse SQL")
                continue

            # Calculate tree edit distance (lower = more similar)
            distance = self.ast_parser.tree_edit_distance(test_ast, candidate_ast)
            similarity = 1.0 - distance  # Convert to similarity

            similarities.append((idx, similarity, candidate))

        if not similarities:
            print(f"[ASTRES] No valid AST similarities, using semantic ranking")
            return candidate_indices[:k]

        # Sort by AST similarity (descending) and select top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        selected_indices = [item[0] for item in similarities[:k]]

        print(f"[ASTRES] Selected {len(selected_indices)} examples by AST similarity")
        for i, (_, sim, _) in enumerate(similarities[:k]):
            print(f"[ASTRES] Example {i+1} AST similarity: {sim:.4f}")

        return selected_indices

    def select_examples(
        self,
        question: str,
        k: int = 3,
        db_id: Optional[str] = None,
        schema_info: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Select k examples using ASTRES algorithm.

        Args:
            question: Test question in Vietnamese
            k: Number of examples to select
            db_id: Database ID (optional)
            schema_info: Database schema information (required for zero-shot)

        Returns:
            List of k selected examples
        """
        print(f"[ASTRES] Starting ASTRES selection for question: '{question[:50]}...'")

        # Load candidates
        self._load_candidates()

        if not self.candidates:
            print("[ASTRES] No candidates available")
            return []

        # Adjust M if needed
        M = min(self.M, len(self.candidates))
        print(f"[ASTRES] Using M={M}, k={k}")

        # Step 1: Generate zero-shot SQL
        if schema_info is None:
            print("[ASTRES] No schema info provided, skipping zero-shot generation")
            return self._fallback_to_few_shot_random(question, k, db_id)

        test_sql = self._generate_zero_shot_sql(question, schema_info)

        if test_sql is None:
            print("[ASTRES] Zero-shot failed, falling back to few-shot random")
            return self._fallback_to_few_shot_random(question, k, db_id)

        # Step 2: Retrieve semantic candidates
        semantic_candidates = self._retrieve_semantic_candidates(question, M)

        # Step 3 & 4: Re-rank by AST similarity
        selected_indices = self._rerank_by_ast_similarity(test_sql, semantic_candidates, k)

        # Return selected examples
        selected_examples = [self.candidates[i] for i in selected_indices]

        print(f"[ASTRES] Successfully selected {len(selected_examples)} examples")
        return selected_examples
