"""
Unified Logger for ViPERSQL

Provides centralized logging functionality for all components.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from .config import ViPERConfig


class ViPERLogger:
    """Unified logger for ViPERSQL system."""
    
    def __init__(self, config: ViPERConfig):
        """Initialize logger with configuration."""
        self.config = config
        self.log_file = Path(config.logs_dir) / "vipersql_logs.json"
        
        # Create logs directory
        Path(config.logs_dir).mkdir(parents=True, exist_ok=True)
        
        # Setup standard logger
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup standard Python logger."""
        logger = logging.getLogger('vipersql')
        logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        if self.config.log_format == 'json':
            file_handler = logging.FileHandler(
                Path(self.config.logs_dir) / "vipersql.log"
            )
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _write_log_entry(self, entry: Dict[str, Any]):
        """Write log entry to JSON file."""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False, default=str) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write log entry: {e}")
    
    def log_request(
        self,
        request_id: str,
        strategy: str,
        question: str,
        db_id: str,
        result: str,
        reasoning: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a request with all details."""
        if not self.config.enable_request_logging:
            return
        
        entry = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "type": "REQUEST",
            "strategy": strategy,
            "question": question,
            "db_id": db_id,
            "result": result,
            "reasoning": reasoning,
            "metadata": metadata or {}
        }
        
        self._write_log_entry(entry)
        self.logger.info(f"Request {request_id}: {strategy} strategy for {db_id}")
    
    def log_llm_response(
        self,
        request_id: str,
        model: str,
        prompt: str,
        response: str,
        latency: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log LLM response details."""
        if not self.config.enable_response_logging:
            return
        
        entry = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "type": "LLM_RESPONSE",
            "model": model,
            "prompt_length": len(prompt),
            "response": response,
            "response_length": len(response),
            "latency": latency,
            "metadata": metadata or {}
        }
        
        self._write_log_entry(entry)
        self.logger.info(f"Request {request_id}: LLM response from {model} in {latency:.2f}s")
    
    def log_evaluation(
        self,
        request_id: str,
        metrics: Dict[str, Any]
    ):
        """Log evaluation metrics."""
        entry = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "type": "EVALUATION",
            "metrics": metrics
        }
        
        self._write_log_entry(entry)
        self.logger.info(f"Request {request_id}: Evaluation completed")
    
    def log_info(self, message: str):
        """Log info message."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "INFO",
            "message": message
        }
        self._write_log_entry(entry)
        self.logger.info(message)
    
    def log_warning(self, message: str):
        """Log warning message."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "WARNING", 
            "message": message
        }
        self._write_log_entry(entry)
        self.logger.warning(message)
    
    def log_error(self, message: str):
        """Log error message."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "ERROR",
            "message": message
        }
        self._write_log_entry(entry)
        self.logger.error(message) 