"""
Multi-language Embedding Generator for ViPERSQL

Supports both Vietnamese (PhoBERT) and English (BERT) embeddings
with automatic language detection and appropriate model selection.
"""

import numpy as np
import torch
from typing import List, Dict, Optional, Union
from transformers import AutoTokenizer, AutoModel
from ..utils.language_detector import LanguageDetector
from ..constants import LANGUAGE_MODELS


class MultiLanguageEmbedder:
    """
    Multi-language embedding generator that automatically selects
    appropriate models based on input language.
    
    - Vietnamese: PhoBERT-base-v2 (vinai/phobert-base-v2)
    - English: BERT-base-uncased (google-bert/bert-base-uncased)
    """

    def __init__(self, cache_models: bool = True):
        """
        Initialize multi-language embedder.
        
        Args:
            cache_models: Whether to pre-load and cache models (uses more memory)
        """
        self.language_detector = LanguageDetector()
        self.cache_models = cache_models
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Model caches
        self._models = {}
        self._tokenizers = {}
        
        if cache_models:
            self._preload_models()

    def _preload_models(self):
        """Pre-load all language models for faster inference."""
        print(f"[MultiLanguageEmbedder] Pre-loading models on device: {self.device}")
        
        for lang, model_config in LANGUAGE_MODELS.items():
            try:
                model_name = model_config["embedding_model"]
                print(f"[MultiLanguageEmbedder] Loading {lang} model: {model_name}")
                
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModel.from_pretrained(model_name).to(self.device)
                model.eval()
                
                self._tokenizers[lang] = tokenizer
                self._models[lang] = model
                
                print(f"[MultiLanguageEmbedder] Successfully loaded {lang} model")
                
            except Exception as e:
                print(f"[MultiLanguageEmbedder] Failed to load {lang} model: {e}")

    def _get_model_and_tokenizer(self, language: str):
        """Get model and tokenizer for specified language."""
        if language not in LANGUAGE_MODELS:
            raise ValueError(f"Unsupported language: {language}")
        
        # Return cached models if available
        if language in self._models and language in self._tokenizers:
            return self._models[language], self._tokenizers[language]
        
        # Load model on-demand
        model_name = LANGUAGE_MODELS[language]["embedding_model"]
        print(f"[MultiLanguageEmbedder] Loading {language} model on-demand: {model_name}")
        
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModel.from_pretrained(model_name).to(self.device)
            model.eval()
            
            # Cache if enabled
            if self.cache_models:
                self._tokenizers[language] = tokenizer
                self._models[language] = model
            
            return model, tokenizer
            
        except Exception as e:
            raise RuntimeError(f"Failed to load {language} model {model_name}: {e}")

    def encode(self, text: str, language: Optional[str] = None) -> np.ndarray:
        """
        Generate embedding for input text.
        
        Args:
            text: Input text to encode
            language: Optional language override ('vi' or 'en')
            
        Returns:
            Embedding vector as numpy array
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return np.zeros(768)  # Standard BERT/PhoBERT dimension
        
        # Auto-detect language if not specified
        if language is None:
            language = self.language_detector.detect_language(text)
        
        # Get appropriate model and tokenizer
        model, tokenizer = self._get_model_and_tokenizer(language)
        
        try:
            # Tokenize and encode
            inputs = tokenizer(
                text,
                return_tensors="pt",
                max_length=512,
                truncation=True,
                padding=True
            ).to(self.device)
            
            # Generate embeddings
            with torch.no_grad():
                outputs = model(**inputs)
                # Use mean pooling of last hidden state
                embeddings = outputs.last_hidden_state.mean(dim=1)
            
            # Convert to numpy array and move to CPU
            return embeddings.cpu().numpy().flatten()
            
        except Exception as e:
            print(f"[MultiLanguageEmbedder] Error encoding text '{text[:50]}...': {e}")
            # Return zero vector as fallback
            return np.zeros(768)

    def encode_batch(self, texts: List[str], language: Optional[str] = None, batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to encode
            language: Optional language override
            batch_size: Batch size for processing
            
        Returns:
            2D numpy array of embeddings
        """
        if not texts:
            return np.array([])
        
        # Auto-detect language from first non-empty text if not specified
        if language is None:
            for text in texts:
                if text and text.strip():
                    language = self.language_detector.detect_language(text)
                    break
            else:
                language = "vi"  # Default fallback
        
        # Get appropriate model and tokenizer
        model, tokenizer = self._get_model_and_tokenizer(language)
        
        embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            try:
                # Filter out empty texts and keep track of indices
                non_empty_texts = []
                non_empty_indices = []
                
                for j, text in enumerate(batch_texts):
                    if text and text.strip():
                        non_empty_texts.append(text)
                        non_empty_indices.append(j)
                
                if not non_empty_texts:
                    # All texts empty, add zero vectors
                    batch_embeddings = np.zeros((len(batch_texts), 768))
                else:
                    # Tokenize batch
                    inputs = tokenizer(
                        non_empty_texts,
                        return_tensors="pt",
                        max_length=512,
                        truncation=True,
                        padding=True
                    ).to(self.device)
                    
                    # Generate embeddings
                    with torch.no_grad():
                        outputs = model(**inputs)
                        # Use mean pooling
                        batch_embeddings_tensor = outputs.last_hidden_state.mean(dim=1)
                        batch_embeddings_np = batch_embeddings_tensor.cpu().numpy()
                    
                    # Create full batch array with zero vectors for empty texts
                    batch_embeddings = np.zeros((len(batch_texts), 768))
                    for k, idx in enumerate(non_empty_indices):
                        batch_embeddings[idx] = batch_embeddings_np[k]
                
                embeddings.append(batch_embeddings)
                
            except Exception as e:
                print(f"[MultiLanguageEmbedder] Error processing batch {i//batch_size + 1}: {e}")
                # Add zero vectors for failed batch
                batch_embeddings = np.zeros((len(batch_texts), 768))
                embeddings.append(batch_embeddings)
        
        return np.vstack(embeddings)

    def get_model_info(self, language: str) -> Dict[str, str]:
        """Get information about the model used for a specific language."""
        if language not in LANGUAGE_MODELS:
            raise ValueError(f"Unsupported language: {language}")
        
        model_config = LANGUAGE_MODELS[language]
        return {
            "language": language,
            "embedding_model": model_config["embedding_model"],
            "tokenizer_model": model_config.get("tokenizer_model", model_config["embedding_model"]),
            "is_loaded": language in self._models
        }

    def clear_cache(self):
        """Clear model cache to free memory."""
        print("[MultiLanguageEmbedder] Clearing model cache")
        
        # Move models to CPU and clear cache
        for model in self._models.values():
            if hasattr(model, 'cpu'):
                model.cpu()
        
        self._models.clear()
        self._tokenizers.clear()
        
        # Clear CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(LANGUAGE_MODELS.keys())

    def detect_language(self, text: str) -> str:
        """Detect language of input text."""
        return self.language_detector.detect_language(text)

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings (768 for both BERT and PhoBERT)."""
        return 768
