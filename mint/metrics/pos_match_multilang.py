"""
Multi-language POS_match module for ViPERSQL
Implements POS tag-based similarity using Jensen-Shannon divergence for Vietnamese and English questions
"""

import numpy as np
from typing import List, Dict, Any, Optional
from collections import Counter

# Language-specific imports
try:
    from underthesea import pos_tag as vi_pos_tag
except ImportError:
    print("Warning: underthesea not installed. Install with: pip install underthesea")
    vi_pos_tag = None

try:
    import spacy
    # Load language models
    try:
        nlp_en = spacy.load("en_core_web_sm")
    except OSError:
        print("Warning: English spaCy model not found. Install with: python -m spacy download en_core_web_sm")
        nlp_en = None
    
    try:
        nlp_vi = spacy.load("vi_core_news_sm")
    except OSError:
        print("Warning: Vietnamese spaCy model not found. Install with: python -m spacy download vi_core_news_sm")
        nlp_vi = None
        
except ImportError:
    print("Warning: spaCy not installed. Install with: pip install spacy")
    nlp_en = None
    nlp_vi = None

from ..utils.language_detector import LanguageDetector


class POSMatcher:
    """
    Multi-language POS_match calculator for Vietnamese and English questions using Jensen-Shannon divergence.

    Formula: POS_match(q1, q2) = 1 - D_JS(P1 || P2)

    Where:
    - P1, P2 are POS tag distributions of questions q1, q2
    - D_JS is Jensen-Shannon divergence
    """

    def __init__(self):
        """Initialize POS matcher with language detector and POS tag sets."""
        self.language_detector = LanguageDetector()
        
        # Vietnamese POS tags (underthesea format)
        self.vietnamese_pos_tags = [
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
        
        # English POS tags (spaCy format)
        self.english_pos_tags = [
            'NOUN',   'VERB',   'ADJ',    'ADV',    'PRON',
            'DET',    'NUM',    'ADP',    'CONJ',   'INTJ', 
            'PART',   'PUNCT',  'SYM',    'X',      'SPACE'
        ]

    def detect_and_pos_tag(self, text: str, language: Optional[str] = None) -> List[tuple]:
        """
        Detect language and perform POS tagging.
        
        Args:
            text: Input text
            language: Optional language override ('vi' or 'en')
            
        Returns:
            List of (word, pos_tag) tuples
        """
        if language is None:
            language = self.language_detector.detect_language(text)
        
        if language == "vi":
            return self._pos_tag_vietnamese(text)
        elif language == "en":
            return self._pos_tag_english(text)
        else:
            # Fallback to Vietnamese
            return self._pos_tag_vietnamese(text)
    
    def _pos_tag_vietnamese(self, text: str) -> List[tuple]:
        """POS tagging for Vietnamese using underthesea or spaCy fallback."""
        # Try underthesea first (preferred for Vietnamese)
        if vi_pos_tag is not None:
            try:
                return vi_pos_tag(text)
            except Exception as e:
                print(f"Warning: underthesea POS tagging failed: {e}")
        
        # Fallback to spaCy Vietnamese model
        if nlp_vi is not None:
            try:
                doc = nlp_vi(text)
                return [(token.text, self._convert_spacy_to_underthesea_pos(token.pos_)) 
                       for token in doc if not token.is_space]
            except Exception as e:
                print(f"Warning: spaCy Vietnamese POS tagging failed: {e}")
        
        # Last resort: simple word splitting with unknown tags
        words = text.split()
        return [(word, 'X') for word in words]
    
    def _pos_tag_english(self, text: str) -> List[tuple]:
        """POS tagging for English using spaCy."""
        if nlp_en is not None:
            try:
                doc = nlp_en(text)
                return [(token.text, token.pos_) for token in doc if not token.is_space]
            except Exception as e:
                print(f"Warning: spaCy English POS tagging failed: {e}")
        
        # Fallback: simple word splitting with unknown tags
        words = text.split()
        return [(word, 'X') for word in words]
    
    def _convert_spacy_to_underthesea_pos(self, spacy_pos: str) -> str:
        """Convert spaCy POS tags to underthesea-compatible format for Vietnamese."""
        conversion_map = {
            'NOUN': 'N', 'VERB': 'V', 'ADJ': 'A', 'ADV': 'R',
            'PRON': 'P', 'DET': 'L', 'NUM': 'M', 'ADP': 'E',
            'CONJ': 'C', 'CCONJ': 'C', 'SCONJ': 'C',
            'INTJ': 'I', 'PART': 'T', 'PUNCT': 'CH',
            'SYM': 'CH', 'X': 'X', 'SPACE': 'CH'
        }
        return conversion_map.get(spacy_pos, 'X')

    def pos_match(self, question1: str, question2: str, language: Optional[str] = None) -> float:
        """
        Calculate POS_match score between two questions (auto-detects language).
        
        Args:
            question1: First question
            question2: Second question  
            language: Optional language override ('vi', 'en', or None for auto-detect)
            
        Returns:
            POS_match score between 0 and 1
        """
        if not question1.strip() or not question2.strip():
            return 0.0
        
        # Auto-detect language if not specified
        if language is None:
            lang1 = self.language_detector.detect_language(question1)
            lang2 = self.language_detector.detect_language(question2)
            # Use the more confident detection or Vietnamese as default
            language = lang1 if lang1 == lang2 else "vi"
        
        # Get POS tags for both questions
        pos_tags1 = self.detect_and_pos_tag(question1, language)
        pos_tags2 = self.detect_and_pos_tag(question2, language)
        
        # Extract POS tag distributions
        dist1 = self._get_pos_distribution(pos_tags1, language)
        dist2 = self._get_pos_distribution(pos_tags2, language)
        
        # Calculate Jensen-Shannon divergence
        js_divergence = self._jensen_shannon_divergence(dist1, dist2)
        
        # Convert to similarity score
        pos_match_score = 1.0 - js_divergence
        
        return max(0.0, min(1.0, pos_match_score))  # Clamp to [0, 1]

    def _get_pos_distribution(self, pos_tags: List[tuple], language: str) -> np.ndarray:
        """
        Get normalized POS tag distribution from POS tags.
        
        Args:
            pos_tags: List of (word, pos_tag) tuples
            language: Language code ('vi' or 'en')
            
        Returns:
            Normalized POS distribution vector
        """
        # Choose appropriate tag set based on language
        if language == "en":
            tag_set = self.english_pos_tags
        else:
            tag_set = self.vietnamese_pos_tags
        
        # Extract just the POS tags
        tags = [tag for word, tag in pos_tags]
        
        # Count POS tag frequencies
        tag_counts = Counter(tags)
        
        # Create distribution vector
        distribution = np.zeros(len(tag_set))
        total_tags = len(tags)
        
        if total_tags == 0:
            return distribution
        
        for i, tag in enumerate(tag_set):
            distribution[i] = tag_counts.get(tag, 0) / total_tags
        
        return distribution

    def _jensen_shannon_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        """
        Calculate Jensen-Shannon divergence between two probability distributions.
        
        Args:
            p, q: Probability distribution vectors
            
        Returns:
            Jensen-Shannon divergence value
        """
        # Add small epsilon to avoid log(0)
        epsilon = 1e-10
        p = p + epsilon
        q = q + epsilon
        
        # Normalize after adding epsilon
        p = p / np.sum(p)
        q = q / np.sum(q)
        
        # Calculate M = (P + Q) / 2
        m = (p + q) / 2
        
        # Calculate KL divergences
        kl_p_m = self._kl_divergence(p, m)
        kl_q_m = self._kl_divergence(q, m)
        
        # JS divergence = (KL(P||M) + KL(Q||M)) / 2
        js_divergence = (kl_p_m + kl_q_m) / 2
        
        return js_divergence

    def _kl_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        """Calculate KL divergence KL(P||Q)."""
        return np.sum(p * np.log(p / q))

    def analyze_pos_similarity(self, question1: str, question2: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Detailed analysis of POS similarity between two questions.
        
        Args:
            question1: First question
            question2: Second question
            language: Optional language override
            
        Returns:
            Dictionary with detailed analysis
        """
        if language is None:
            language = self.language_detector.detect_language(question1)
        
        # Get POS tags
        pos_tags1 = self.detect_and_pos_tag(question1, language)
        pos_tags2 = self.detect_and_pos_tag(question2, language)
        
        # Get distributions
        dist1 = self._get_pos_distribution(pos_tags1, language)
        dist2 = self._get_pos_distribution(pos_tags2, language)
        
        # Calculate metrics
        js_divergence = self._jensen_shannon_divergence(dist1, dist2)
        pos_match_score = 1.0 - js_divergence
        
        # Choose tag set
        tag_set = self.english_pos_tags if language == "en" else self.vietnamese_pos_tags
        
        return {
            "language": language,
            "pos_match_score": pos_match_score,
            "js_divergence": js_divergence,
            "question1_tags": pos_tags1,
            "question2_tags": pos_tags2,
            "question1_distribution": {tag: dist1[i] for i, tag in enumerate(tag_set) if dist1[i] > 0},
            "question2_distribution": {tag: dist2[i] for i, tag in enumerate(tag_set) if dist2[i] > 0},
            "tag_set_used": tag_set
        }
