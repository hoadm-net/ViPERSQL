"""
Configuration Management for ViPERSQL

Centralized configuration management that loads from .env files,
environment variables, and command-line arguments.
"""

import os
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv
from .constants import (
    DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, DEFAULT_TIMEOUT,
    DEFAULT_BATCH_SIZE, DEFAULT_CONCURRENT_REQUESTS,
    DEFAULT_RETRY_ATTEMPTS, DEFAULT_RETRY_DELAY,
    DEFAULT_FEW_SHOT_EXAMPLES, DEFAULT_LOG_LEVEL, DEFAULT_LOG_FORMAT,
    MIN_TEMPERATURE, MAX_TEMPERATURE, MIN_TOKENS
)


@dataclass
class ViPERConfig:
    """
    Centralized configuration for ViPERSQL system.
    
    Loads configuration from multiple sources in order of priority:
    1. Direct constructor arguments (highest priority)
    2. Environment variables
    3. .env file
    4. Default values (lowest priority)
    """
    
    # API Keys
    openai_api_key: str = field(default="")
    anthropic_api_key: str = field(default="")
    langchain_api_key: str = field(default="")
    langchain_tracing: bool = field(default=False)
    
    # Model Settings
    model_name: str = field(default="gpt-4-turbo")  # Will be overridden by DEFAULT_MODEL from .env
    temperature: float = field(default=DEFAULT_TEMPERATURE)
    max_tokens: int = field(default=DEFAULT_MAX_TOKENS)
    timeout: int = field(default=DEFAULT_TIMEOUT)

    # Dataset Settings
    dataset_path: str = field(default="dataset/ViText2SQL")
    split: str = field(default="dev")
    level: str = field(default="std")  # Default is std-level
    num_samples: Optional[int] = field(default=None)  # Number of samples to process (None = all)

    # Strategy Settings
    strategy: str = field(default="zero-shot")
    template_dir: str = field(default="templates")
    template_name: str = field(default="vietnamese_nl2sql.txt")
    
    # Few-shot Settings
    few_shot_examples: int = field(default=DEFAULT_FEW_SHOT_EXAMPLES)
    few_shot_template: str = field(default="few_shot_vietnamese_nl2sql.txt")
    example_selection_strategy: str = field(default="random")  # 'random', 'skill_knn', 'dicl', 'astres', 'vir2'

    # ViR2 Selector Settings
    vir2_candidate_pool_size: int = field(default=50)  # M parameter - Stage 1 retrieval size
    vir2_beam_size: int = field(default=5)            # B parameter - Beam search size
    vir2_diversity_weight: float = field(default=0.3)  # λ parameter - Diversity weight

    # Chain-of-Thought Settings
    cot_reasoning_steps: bool = field(default=True)
    cot_template: str = field(default="cot_vietnamese_nl2sql.txt")
    
    # Program-Aided Language Settings

    
    # Output Settings
    results_dir: str = field(default="results")

    # Evaluation Settings
    enable_execution_accuracy: bool = field(default=True)
    enable_component_analysis: bool = field(default=True)
    enable_error_analysis: bool = field(default=True)
    evaluation_timeout: int = field(default=DEFAULT_TIMEOUT)

    # Logging Settings
    log_level: str = field(default=DEFAULT_LOG_LEVEL)
    log_format: str = field(default=DEFAULT_LOG_FORMAT)
    enable_request_logging: bool = field(default=True)
    enable_response_logging: bool = field(default=True)
    
    # Performance Settings
    batch_size: int = field(default=DEFAULT_BATCH_SIZE)
    max_concurrent_requests: int = field(default=DEFAULT_CONCURRENT_REQUESTS)
    retry_attempts: int = field(default=DEFAULT_RETRY_ATTEMPTS)
    retry_delay: int = field(default=DEFAULT_RETRY_DELAY)

    def __init__(self, **kwargs):
        """Load configuration from environment after initialization."""
        # Set default level = std if not provided
        if 'level' not in kwargs:
            kwargs['level'] = 'std'
        for field_name in self.__dataclass_fields__:
            if field_name in kwargs:
                setattr(self, field_name, kwargs[field_name])
        self._load_from_env()
        self._validate_config()
        self._setup_directories()
    
    def _load_from_env(self):
        """Load configuration from environment variables and .env files."""
        # Try to load from .env files in order of preference
        env_files = [".env", "config.env", ".env.local"]
        for env_file in env_files:
            if Path(env_file).exists():
                load_dotenv(env_file, override=False)
                break
        
        # Load values from environment, keeping existing values if they were set in constructor
        env_mapping = {
            # API Keys
            'openai_api_key': 'OPENAI_API_KEY',
            'anthropic_api_key': 'ANTHROPIC_API_KEY', 
            'langchain_api_key': 'LANGCHAIN_API_KEY',
            'langchain_tracing': 'LANGCHAIN_TRACING_V2',
            
            # Model Settings
            'model_name': 'DEFAULT_MODEL',
            'temperature': 'DEFAULT_TEMPERATURE',
            'max_tokens': 'DEFAULT_MAX_TOKENS',
            'timeout': 'DEFAULT_TIMEOUT',
            
            # Dataset Settings
            'dataset_path': 'DATASET_PATH',
            'split': 'DEFAULT_SPLIT',
            'level': 'DEFAULT_LEVEL', 
            'num_samples': 'DEFAULT_SAMPLES',

            # Strategy Settings
            'strategy': 'DEFAULT_STRATEGY',
            'template_dir': 'DEFAULT_TEMPLATE_DIR',
            'template_name': 'DEFAULT_TEMPLATE',
            
            # Few-shot Settings
            'few_shot_examples': 'FEW_SHOT_EXAMPLES',
            'few_shot_template': 'FEW_SHOT_TEMPLATE',
            'example_selection_strategy': 'EXAMPLE_SELECTION_STRATEGY',

            # CoT Settings
            'cot_reasoning_steps': 'COT_REASONING_STEPS',
            'cot_template': 'COT_TEMPLATE',
            
            
            
            # Output Settings
            'results_dir': 'RESULTS_DIR',

            # Evaluation Settings
            'enable_execution_accuracy': 'ENABLE_EXECUTION_ACCURACY',
            'enable_component_analysis': 'ENABLE_COMPONENT_ANALYSIS',
            'enable_error_analysis': 'ENABLE_ERROR_ANALYSIS',
            'evaluation_timeout': 'EVALUATION_TIMEOUT',
            
            # Logging Settings
            'log_level': 'LOG_LEVEL',
            'log_format': 'LOG_FORMAT',
            'enable_request_logging': 'ENABLE_REQUEST_LOGGING',
            'enable_response_logging': 'ENABLE_RESPONSE_LOGGING',
            
            # Performance Settings
            'batch_size': 'BATCH_SIZE',
            'max_concurrent_requests': 'MAX_CONCURRENT_REQUESTS',
            'retry_attempts': 'RETRY_ATTEMPTS',
            'retry_delay': 'RETRY_DELAY'
        }
        
        for attr_name, env_name in env_mapping.items():
            # Only update if the current value is the default (not set in constructor)
            current_value = getattr(self, attr_name)
            if self._is_default_value(attr_name, current_value):
                env_value = os.getenv(env_name)
                if env_value is not None:
                    # Convert to appropriate type
                    converted_value = self._convert_env_value(env_value, type(current_value))
                    setattr(self, attr_name, converted_value)
    
    def _is_default_value(self, attr_name: str, current_value: Any) -> bool:
        """Check if current value is the default value."""
        # Get the default value from the field definition
        for field_info in self.__dataclass_fields__.values():
            if field_info.name == attr_name:
                return current_value == field_info.default
        return False
    
    def _convert_env_value(self, value: str, target_type: type) -> Any:
        """Convert environment variable string to target type."""
        if target_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif target_type == int:
            return int(value)
        elif target_type == float:
            return float(value)
        else:
            return value
    
    def _validate_config(self):
        """Validate configuration values."""
        # Validate strategy
        valid_strategies = ['zero-shot', 'few-shot', 'cot']
        if self.strategy not in valid_strategies:
            raise ValueError(f"Invalid strategy: {self.strategy}. Must be one of {valid_strategies}")
        
        # Validate level
        valid_levels = ['std', 'syllable', 'word']
        if self.level not in valid_levels:
            raise ValueError(f"Invalid level: {self.level}. Must be one of {valid_levels}")

        # Validate split
        valid_splits = ['train', 'dev', 'test']
        if self.split not in valid_splits:
            raise ValueError(f"Invalid split: {self.split}. Must be one of {valid_splits}")

        # Validate numeric values
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError(f"Temperature must be between 0 and 2, got {self.temperature}")

        if self.max_tokens <= 0:
            raise ValueError(f"Max tokens must be positive, got {self.max_tokens}")

        if self.few_shot_examples < 0:
            raise ValueError(f"Few-shot examples must be non-negative, got {self.few_shot_examples}")

    def _setup_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [self.results_dir]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @property
    def template_path(self) -> str:
        """Get template path based on strategy."""
        template_map = {
            'zero-shot': self.template_name,
            'few-shot': self.few_shot_template,
            'cot': self.cot_template

        }
        template_file = template_map.get(self.strategy, self.template_name)
        return str(Path(self.template_dir) / template_file)
    
    @property
    def dataset_full_path(self) -> str:
        """Get full dataset path including level."""
        level_dir = f"{self.level}-level" if self.level in ["syllable", "word", "std"] else self.level
        return str(Path(self.dataset_path) / level_dir)
    
    @property
    def default_strategy(self) -> str:
        """Get the default strategy name."""
        return self.strategy
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            field.name: getattr(self, field.name) 
            for field in self.__dataclass_fields__.values()
        }
    
    def update(self, **kwargs) -> 'ViPERConfig':
        """Create new config with updated values."""
        current_dict = self.to_dict()
        current_dict.update(kwargs)
        return ViPERConfig(**current_dict)
    
    def __str__(self) -> str:
        """String representation for logging."""
        return f"ViPERConfig(strategy={self.strategy}, model={self.model_name}, split={self.split})" 

    @property
    def schema_path(self) -> str:
        """Get schema path based on level."""
        level_dir = f"{self.level}-level" if self.level in ["syyllable", "word", "std"] else self.level
        return str(Path(self.dataset_path) / level_dir / "tables.json")
