"""
Language Detection Utility for ViPERSQL

Automatically detects the language of input questions to determine
appropriate models and processing strategies.
"""

import re
from typing import Optional
from ..constants import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE


class LanguageDetector:
    """
    Simple language detector for Vietnamese and English text.
    
    Uses character-based and keyword-based heuristics to detect language.
    """
    
    def __init__(self):
        """Initialize language detector with language patterns."""
        # Vietnamese-specific patterns
        self.vietnamese_chars = set("àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ")
        
        # Vietnamese common words
        self.vietnamese_words = {
            "là", "của", "có", "được", "những", "các", "một", "này", "đó", "để", 
            "với", "trong", "và", "cho", "từ", "về", "như", "theo", "khi", "nếu",
            "tại", "bao", "nhiều", "gì", "nào", "ai", "đâu", "bao", "thế", "sao"
        }
        
        # English common words 
        self.english_words = {
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
            "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
            "this", "but", "his", "by", "from", "they", "she", "or", "an", "will",
            "what", "who", "where", "when", "how", "which", "many", "some", "all"
        }
    
    def detect_language(self, text: str) -> str:
        """
        Detect language of input text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Language code ('vi' or 'en')
        """
        if not text or not text.strip():
            return DEFAULT_LANGUAGE
            
        text = text.lower().strip()
        
        # Check for Vietnamese characters
        vietnamese_char_count = sum(1 for char in text if char in self.vietnamese_chars)
        
        # Check for Vietnamese words
        words = re.findall(r'\b\w+\b', text)
        vietnamese_word_count = sum(1 for word in words if word in self.vietnamese_words)
        english_word_count = sum(1 for word in words if word in self.english_words)
        
        # Decision logic
        if vietnamese_char_count > 0:
            return "vi"
        elif vietnamese_word_count > english_word_count:
            return "vi"
        elif english_word_count > 0 and len(words) > 0:
            return "en"
        else:
            # Default fallback
            return DEFAULT_LANGUAGE
    
    def is_supported_language(self, lang_code: str) -> bool:
        """Check if language is supported."""
        return lang_code in SUPPORTED_LANGUAGES
    
    def get_language_info(self, text: str) -> dict:
        """
        Get detailed language information for debugging.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with language detection details
        """
        detected_lang = self.detect_language(text)
        
        words = re.findall(r'\b\w+\b', text.lower())
        vietnamese_chars = sum(1 for char in text if char in self.vietnamese_chars)
        vietnamese_words = sum(1 for word in words if word in self.vietnamese_words)
        english_words = sum(1 for word in words if word in self.english_words)
        
        return {
            "detected_language": detected_lang,
            "text_length": len(text),
            "word_count": len(words),
            "vietnamese_chars": vietnamese_chars,
            "vietnamese_words": vietnamese_words,
            "english_words": english_words,
            "confidence": self._calculate_confidence(text, detected_lang)
        }
    
    def _calculate_confidence(self, text: str, detected_lang: str) -> float:
        """Calculate confidence score for language detection."""
        words = re.findall(r'\b\w+\b', text.lower())
        
        if not words:
            return 0.5
            
        vietnamese_chars = sum(1 for char in text if char in self.vietnamese_chars)
        vietnamese_words = sum(1 for word in words if word in self.vietnamese_words)
        english_words = sum(1 for word in words if word in self.english_words)
        
        if detected_lang == "vi":
            if vietnamese_chars > 0:
                return 0.9
            elif vietnamese_words > english_words:
                return 0.7
            else:
                return 0.6
        else:  # English
            if english_words > vietnamese_words and vietnamese_chars == 0:
                return 0.8
            else:
                return 0.6
