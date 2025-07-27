"""
MINT - Modern Integration for Natural language Text-to-SQL

A comprehensive toolkit for Vietnamese Text-to-SQL conversion with support for
multiple strategies: Zero-shot, Few-shot, and Chain-of-Thought (CoT).

Core Components:
- LLM Interface: Unified interface for OpenAI and Anthropic models
- Template System: Flexible prompt template management
- Evaluation Engine: Comprehensive evaluation metrics with component-wise analysis
"""

# Core components
from .metrics.enhanced_metrics import EnhancedEvaluationMetrics

# Configuration and strategy components
from .config import ViPERConfig
from .core.llm_interface import LLMInterface
from .core.template_manager import TemplateManager
from .strategies import create_strategy

__all__ = [
    'ViPERConfig',
    'LLMInterface',
    'TemplateManager',
    'EnhancedEvaluationMetrics',
    'create_strategy',
]
