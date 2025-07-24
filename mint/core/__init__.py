"""
ViPERSQL Core Components

This module contains the core system components including:
- LLM interface for unified model access
- Template manager for prompt engineering
- Evaluator for comprehensive assessment
"""

from .llm_interface import LLMInterface
from .template_manager import TemplateManager
from .evaluator import UnifiedEvaluator

__all__ = [
    'LLMInterface',
    'TemplateManager',
    'UnifiedEvaluator'
]
