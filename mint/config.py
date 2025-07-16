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
    model_name: str = field(default="gpt-4o-mini")
    temperature: float = field(default=0.1)
    max_tokens: int = field(default=2000)
    timeout: int = field(default=30)
    
    # Dataset Settings
    dataset_path: str = field(default="dataset/ViText2SQL")
    split: str = field(default="dev")
    level: str = field(default="syllable")
    samples: int = field(default=10)
    
    # Strategy Settings
    strategy: str = field(default="zero-shot")
    template_dir: str = field(default="templates")
    template_name: str = field(default="vietnamese_nl2sql.txt")
    
    # Few-shot Settings
    few_shot_examples: int = field(default=3)
    few_shot_template: str = field(default="few_shot_vietnamese_nl2sql.txt")
    
    # Chain-of-Thought Settings
    cot_reasoning_steps: bool = field(default=True)
    cot_template: str = field(default="cot_vietnamese_nl2sql.txt")
    
    # Program-Aided Language Settings
    pal_code_execution: bool = field(default=False)
    pal_template: str = field(default="pal_vietnamese_nl2sql.txt")
    
    # Output Settings
    results_dir: str = field(default="results")
    logs_dir: str = field(default="logs")
    sqlite_dbs_dir: str = field(default="sqlite_dbs")
    
    # Evaluation Settings
    enable_execution_accuracy: bool = field(default=True)
    enable_component_analysis: bool = field(default=True)
    enable_error_analysis: bool = field(default=True)
    evaluation_timeout: int = field(default=30)
    
    # Logging Settings
    log_level: str = field(default="INFO")
    log_format: str = field(default="json")
    enable_request_logging: bool = field(default=True)
    enable_response_logging: bool = field(default=True)
    
    # Performance Settings
    batch_size: int = field(default=10)
    max_concurrent_requests: int = field(default=5)
    retry_attempts: int = field(default=3)
    retry_delay: int = field(default=1)
    
    def __post_init__(self):
        """Load configuration from environment after initialization."""
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
            'samples': 'DEFAULT_SAMPLES',
            
            # Strategy Settings
            'strategy': 'DEFAULT_STRATEGY',
            'template_dir': 'DEFAULT_TEMPLATE_DIR',
            'template_name': 'DEFAULT_TEMPLATE',
            
            # Few-shot Settings
            'few_shot_examples': 'FEW_SHOT_EXAMPLES',
            'few_shot_template': 'FEW_SHOT_TEMPLATE',
            
            # CoT Settings
            'cot_reasoning_steps': 'COT_REASONING_STEPS',
            'cot_template': 'COT_TEMPLATE',
            
            # PAL Settings
            'pal_code_execution': 'PAL_CODE_EXECUTION',
            'pal_template': 'PAL_TEMPLATE',
            
            # Output Settings
            'results_dir': 'RESULTS_DIR',
            'logs_dir': 'LOGS_DIR',
            'sqlite_dbs_dir': 'SQLITE_DBS_DIR',
            
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
        valid_strategies = ['zero-shot', 'few-shot', 'cot', 'pal']
        if self.strategy not in valid_strategies:
            raise ValueError(f"Invalid strategy: {self.strategy}. Must be one of {valid_strategies}")
        
        # Validate model name
        if not self.model_name:
            raise ValueError("Model name cannot be empty")
        
        # Validate API keys based on model
        if 'gpt' in self.model_name.lower() and not self.openai_api_key:
            raise ValueError("OpenAI API key required for GPT models")
        elif 'claude' in self.model_name.lower() and not self.anthropic_api_key:
            raise ValueError("Anthropic API key required for Claude models")
        
        # Validate dataset settings
        if self.samples < -1 or self.samples == 0:
            raise ValueError("Samples must be -1 (all) or positive integer")
        
        if self.level not in ['syllable', 'word']:
            raise ValueError("Level must be 'syllable' or 'word'")
    
    def _setup_directories(self):
        """Create necessary directories."""
        directories = [self.results_dir, self.logs_dir, self.template_dir]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @property
    def template_path(self) -> str:
        """Get full path to the template file based on strategy."""
        template_map = {
            'zero-shot': self.template_name,
            'few-shot': self.few_shot_template,
            'cot': self.cot_template,
            'pal': self.pal_template
        }
        template_file = template_map.get(self.strategy, self.template_name)
        return str(Path(self.template_dir) / template_file)
    
    @property
    def dataset_full_path(self) -> str:
        """Get full dataset path including level."""
        level_dir = f"{self.level}-level" if self.level in ["syllable", "word"] else self.level
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