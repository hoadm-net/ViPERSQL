"""
Example selectors for few-shot learning.
"""

from .base_selector import BaseSelector
from .random_selector import RandomSelector
from .skill_knn_selector import SkillKNNSelector
from .dicl_selector import DICLSelector
from .astres_selector import ASTRESSelector
from .vir2_selector import ViR2Selector

__all__ = [
    'BaseSelector',
    'RandomSelector',
    'SkillKNNSelector',
    'DICLSelector',
    'ASTRESSelector',
    'ViR2Selector'
]
