"""
Utility modules for ViPERSQL multi-language support.
"""

from .language_detector import LanguageDetector
from .multilang_embedder import MultiLanguageEmbedder

__all__ = [
    'LanguageDetector',
    'MultiLanguageEmbedder'
]
