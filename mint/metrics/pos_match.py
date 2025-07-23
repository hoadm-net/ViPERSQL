"""
POS_match module for ViPERSQL
Implements POS tag-based similarity using Jensen-Shannon divergence for Vietnamese questions
"""

import numpy as np
from typing import List, Dict, Any
from collections import Counter
try:
    from underthesea import pos_tag
except ImportError:
    print("Warning: underthesea not installed. Install with: pip install underthesea")
    pos_tag = None


class POSMatcher:
    """
    POS_match calculator for Vietnamese questions using Jensen-Shannon divergence.

    Formula: POS_match(q1, q2) = 1 - D_JS(P1 || P2)

    Where:
    - P1, P2 are POS tag distributions of questions q1, q2
    - D_JS is Jensen-Shannon divergence
    """

    def __init__(self):
        """Initialize POS matcher with Vietnamese POS tag set."""
        self.standard_pos_tags = [
            'N',      # Noun
            'V',      # Verb
            'A',      # Adjective
            'R',      # Adverb
            'P',      # Pronoun
            'L',      # Determiner
            'M',      # Numeral
            'E',      # Preposition
            'C',      # Conjunction
            'I',      # Interjection
            'T',      # Particle
            'Y',      # Abbreviation
            'S',      # Affix
            'X',      # Unknown
            'CH',     # Punctuation
            'FW'      # Foreign word
        ]

    def pos_match(self, question1: str, question2: str) -> float:
        """
        Calculate POS_match score between two Vietnamese questions.

        Args:
            question1 (str): First Vietnamese question
            question2 (str): Second Vietnamese question

        Returns:
            float: POS match score between 0 and 1 (1 = identical POS distributions)
        """
        if pos_tag is None:
            raise ImportError("underthesea library is required for POS tagging. Install with: pip install underthesea")

        try:
            # Get POS tag distributions for both questions
            pos_dist1 = self._get_pos_distribution(question1)
            pos_dist2 = self._get_pos_distribution(question2)

            # Calculate Jensen-Shannon divergence
            js_divergence = self._jensen_shannon_divergence(pos_dist1, pos_dist2)

            # Convert to similarity score
            pos_match_score = 1.0 - js_divergence

            return max(0.0, min(1.0, pos_match_score))  # Ensure score is in [0, 1]

        except Exception as e:
            print(f"Error calculating POS match: {e}")
            return 0.0

    def _get_pos_distribution(self, text: str) -> np.ndarray:
        """
        Extract POS tag distribution from Vietnamese text.

        Args:
            text (str): Vietnamese text

        Returns:
            np.ndarray: Normalized POS tag distribution
        """
        if not text or not text.strip():
            return np.zeros(len(self.standard_pos_tags))

        try:
            # Perform POS tagging using underthesea
            pos_tags = pos_tag(text)

            # Extract just the POS tags
            tags = [tag[1] for tag in pos_tags if len(tag) >= 2]

            if not tags:
                return np.zeros(len(self.standard_pos_tags))

            # Count tag frequencies
            tag_counts = Counter(tags)

            # Create distribution vector
            total_tags = sum(tag_counts.values())
            distribution = np.zeros(len(self.standard_pos_tags))

            for i, pos_tag_name in enumerate(self.standard_pos_tags):
                count = tag_counts.get(pos_tag_name, 0)
                distribution[i] = count / total_tags if total_tags > 0 else 0.0

            return distribution

        except Exception as e:
            print(f"Error getting POS distribution: {e}")
            return np.zeros(len(self.standard_pos_tags))

    def _jensen_shannon_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        """
        Calculate Jensen-Shannon divergence between two probability distributions.

        D_JS(P || Q) = 0.5 * D_KL(P || M) + 0.5 * D_KL(Q || M)
        where M = 0.5 * (P + Q)

        Args:
            p (np.ndarray): First probability distribution
            q (np.ndarray): Second probability distribution

        Returns:
            float: Jensen-Shannon divergence (0 to 1)
        """
        if len(p) == 0 or len(q) == 0:
            return 1.0  # Maximum divergence for empty distributions

        if len(p) != len(q):
            # Pad shorter distribution with zeros
            max_len = max(len(p), len(q))
            p_padded = np.zeros(max_len)
            q_padded = np.zeros(max_len)

            p_padded[:len(p)] = p
            q_padded[:len(q)] = q

            p, q = p_padded, q_padded

        # Ensure distributions are normalized
        p = p / np.sum(p) if np.sum(p) > 0 else np.ones_like(p) / len(p)
        q = q / np.sum(q) if np.sum(q) > 0 else np.ones_like(q) / len(q)

        # Add small epsilon to avoid log(0)
        epsilon = 1e-10
        p = p + epsilon
        q = q + epsilon

        # Renormalize after adding epsilon
        p = p / np.sum(p)
        q = q / np.sum(q)

        # Calculate middle distribution M
        m = 0.5 * (p + q)

        # Calculate KL divergences
        kl_pm = self._kl_divergence(p, m)
        kl_qm = self._kl_divergence(q, m)

        # Jensen-Shannon divergence
        js_div = 0.5 * kl_pm + 0.5 * kl_qm

        return js_div

    def _kl_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        """
        Calculate Kullback-Leibler divergence D_KL(P || Q).

        D_KL(P || Q) = sum(P(i) * log(P(i) / Q(i)))

        Args:
            p (np.ndarray): First probability distribution
            q (np.ndarray): Second probability distribution

        Returns:
            float: KL divergence
        """
        # Handle the case where P(i) = 0: 0 * log(0/x) := 0
        kl = 0.0
        for i in range(len(p)):
            if p[i] > 0 and q[i] > 0:
                kl += p[i] * np.log(p[i] / q[i])

        return kl

    def batch_pos_match(self, questions1: List[str], questions2: List[str]) -> List[float]:
        """
        Calculate POS_match scores for batches of question pairs.

        Args:
            questions1 (List[str]): First set of Vietnamese questions
            questions2 (List[str]): Second set of Vietnamese questions

        Returns:
            List[float]: List of POS match scores
        """
        if len(questions1) != len(questions2):
            raise ValueError("Both question lists must have the same length")

        scores = []
        for q1, q2 in zip(questions1, questions2):
            score = self.pos_match(q1, q2)
            scores.append(score)

        return scores

    def pos_match_analysis(self, questions1: List[str], questions2: List[str]) -> Dict[str, Any]:
        """
        Comprehensive POS match analysis with detailed statistics.

        Args:
            questions1 (List[str]): First set of Vietnamese questions
            questions2 (List[str]): Second set of Vietnamese questions

        Returns:
            Dict[str, Any]: Detailed POS match analysis
        """
        if len(questions1) != len(questions2):
            raise ValueError("Both question lists must have the same length")

        scores = self.batch_pos_match(questions1, questions2)

        # Calculate statistics
        analysis = {
            'pos_match_scores': scores,
            'statistics': {
                'mean': float(np.mean(scores)),
                'median': float(np.median(scores)),
                'std': float(np.std(scores)),
                'min': float(np.min(scores)),
                'max': float(np.max(scores))
            },
            'distribution': {
                'high_similarity': len([s for s in scores if s >= 0.8]),
                'medium_similarity': len([s for s in scores if 0.5 <= s < 0.8]),
                'low_similarity': len([s for s in scores if s < 0.5])
            },
            'pos_analysis': []
        }

        # Detailed POS analysis for sample pairs (up to 5 examples)
        if len(questions1) > 0:
            sample_size = min(5, len(questions1))
            sample_indices = np.random.choice(len(questions1), sample_size, replace=False)

            for idx in sample_indices:
                q1, q2 = questions1[idx], questions2[idx]
                pos_dist1 = self._get_pos_distribution(q1)
                pos_dist2 = self._get_pos_distribution(q2)

                analysis['pos_analysis'].append({
                    'index': int(idx),
                    'question1': q1,
                    'question2': q2,
                    'pos_match_score': scores[idx],
                    'pos_distribution1': pos_dist1.tolist(),
                    'pos_distribution2': pos_dist2.tolist(),
                    'pos_tags': self.standard_pos_tags
                })

        return analysis

    def get_detailed_pos_info(self, text: str) -> Dict[str, Any]:
        """
        Get detailed POS information for a Vietnamese text.

        Args:
            text (str): Vietnamese text

        Returns:
            Dict[str, Any]: Detailed POS information
        """
        if pos_tag is None:
            raise ImportError("underthesea library is required for POS tagging.")

        try:
            # Perform POS tagging
            pos_tags = pos_tag(text)

            # Extract tags
            tags = [tag[1] for tag in pos_tags if len(tag) >= 2]
            words = [tag[0] for tag in pos_tags if len(tag) >= 2]

            # Count frequencies
            tag_counts = Counter(tags)

            # Get distribution
            pos_distribution = self._get_pos_distribution(text)

            return {
                'text': text,
                'word_pos_pairs': list(zip(words, tags)),
                'tag_counts': dict(tag_counts),
                'pos_distribution': pos_distribution.tolist(),
                'standard_pos_tags': self.standard_pos_tags,
                'total_words': len(words)
            }

        except Exception as e:
            print(f"Error getting detailed POS info: {e}")
            return {
                'text': text,
                'error': str(e)
            }
