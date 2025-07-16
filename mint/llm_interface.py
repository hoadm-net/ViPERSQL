"""
LLM Interface for ViPERSQL

Provides unified interface for different LLM providers (OpenAI, Anthropic).
"""

import time
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from .config import ViPERConfig


class LLMInterface:
    """Unified interface for LLM providers."""
    
    def __init__(self, config: ViPERConfig):
        """Initialize LLM interface with configuration."""
        self.config = config
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the appropriate LLM based on model name."""
        model_name = self.config.model_name.lower()
        
        if 'gpt' in model_name:
            return ChatOpenAI(
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                openai_api_key=self.config.openai_api_key
            )
        elif 'claude' in model_name:
            return ChatAnthropic(
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                anthropic_api_key=self.config.anthropic_api_key
            )
        else:
            raise ValueError(f"Unsupported model: {self.config.model_name}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from LLM."""
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {str(e)}")
    
    def generate_with_metadata(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response with timing and metadata."""
        start_time = time.time()
        
        try:
            response = self.llm.invoke(prompt)
            latency = time.time() - start_time
            
            return {
                'content': response.content,
                'latency': latency,
                'model': self.config.model_name,
                'prompt_length': len(prompt),
                'response_length': len(response.content)
            }
        except Exception as e:
            latency = time.time() - start_time
            return {
                'content': f"ERROR: {str(e)}",
                'latency': latency,
                'model': self.config.model_name,
                'error': str(e)
            } 