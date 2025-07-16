"""
Template Manager for ViPERSQL

Manages loading and formatting of prompt templates for different strategies.
"""

from pathlib import Path
from typing import Dict, Any
from langchain.prompts import PromptTemplate
from .config import ViPERConfig


class TemplateManager:
    """Manages prompt templates for different strategies."""
    
    def __init__(self, config: ViPERConfig):
        """Initialize template manager with configuration."""
        self.config = config
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all available templates."""
        template_mapping = {
            'zero-shot': self.config.template_name,
            'few-shot': self.config.few_shot_template,
            'cot': self.config.cot_template,
            'pal': self.config.pal_template
        }
        
        for strategy, template_file in template_mapping.items():
            template_path = Path(self.config.template_dir) / template_file
            self.templates[strategy] = self._load_single_template(template_path, strategy)
    
    def _load_single_template(self, template_path: Path, strategy: str) -> PromptTemplate:
        """Load a single template file."""
        try:
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
                
                # Define input variables based on strategy
                input_variables = self._get_input_variables(strategy)
                
                return PromptTemplate(
                    template=template_content,
                    input_variables=input_variables
                )
            else:
                # Return default template if file not found
                return self._get_default_template(strategy)
                
        except Exception as e:
            print(f"Warning: Failed to load template {template_path}: {e}")
            return self._get_default_template(strategy)
    
    def _get_input_variables(self, strategy: str) -> list:
        """Get input variables for a strategy."""
        base_variables = ['tables', 'columns', 'foreign_keys', 'primary_keys', 'question']
        
        if strategy in ['few-shot', 'cot', 'pal']:
            base_variables.append('examples')
        
        return base_variables
    
    def _get_default_template(self, strategy: str) -> PromptTemplate:
        """Get default template for a strategy."""
        if strategy == 'zero-shot':
            template_content = """You are an expert in converting Vietnamese natural language questions to SQL queries.

Database Schema:
Tables: {tables}
Columns: {columns}
Foreign Keys: {foreign_keys}
Primary Keys: {primary_keys}

Vietnamese Question: {question}

SQL Query:"""
        
        elif strategy == 'few-shot':
            template_content = """You are an expert in converting Vietnamese natural language questions to SQL queries.

Database Schema:
Tables: {tables}
Columns: {columns}
Foreign Keys: {foreign_keys}
Primary Keys: {primary_keys}

Examples:
{examples}

Vietnamese Question: {question}

SQL Query:"""
        
        else:  # cot, pal
            template_content = """You are an expert in converting Vietnamese natural language questions to SQL queries.

Database Schema:
Tables: {tables}
Columns: {columns}
Foreign Keys: {foreign_keys}
Primary Keys: {primary_keys}

Think step by step:
{examples}

Vietnamese Question: {question}

SQL Query:"""
        
        return PromptTemplate(
            template=template_content,
            input_variables=self._get_input_variables(strategy)
        )
    
    def get_template(self, strategy: str) -> PromptTemplate:
        """Get template for a specific strategy."""
        if strategy not in self.templates:
            raise ValueError(f"Unknown strategy: {strategy}")
        return self.templates[strategy]
    
    def format_template(self, strategy: str, **kwargs) -> str:
        """Format template with variables."""
        template = self.get_template(strategy)
        return template.format(**kwargs) 