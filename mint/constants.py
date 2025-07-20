"""
Constants for ViPERSQL system.

This module contains all configurable constants used throughout the system
to avoid magic numbers and improve maintainability.
"""

# Display and formatting constants
SEPARATOR_LENGTH = 60
LONG_SEPARATOR_LENGTH = 80
HEADER_SEPARATOR_LENGTH = 60

# Text truncation lengths
QUESTION_PREVIEW_LENGTH = 80
SQL_PREVIEW_LENGTH = 60

# Processing and batching constants
INTERMEDIATE_SAVE_INTERVAL = 10  # Save intermediate results every N samples
DEFAULT_BATCH_SIZE = 10
DEFAULT_CONCURRENT_REQUESTS = 5

# LLM default parameters
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_TOKENS = 2000
DEFAULT_TIMEOUT = 30

# LLM generation parameters (for method signatures)
FALLBACK_TEMPERATURE = 0.7
FALLBACK_MAX_TOKENS = 512

# Retry and performance constants
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 1

# Evaluation and reporting constants
COMPONENT_NAME_WIDTH = 15
SCORE_COLUMN_WIDTH = 10
PRECISION_COLUMN_WIDTH = 12
RECALL_COLUMN_WIDTH = 12

# Few-shot learning constants
DEFAULT_FEW_SHOT_EXAMPLES = 3

# Validation constants
MIN_TEMPERATURE = 0
MAX_TEMPERATURE = 2
MIN_TOKENS = 1

# File and directory constants
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "json"
