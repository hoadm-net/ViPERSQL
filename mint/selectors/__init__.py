"""
Example selectors for few-shot learning.
"""

from .base_selector import BaseSelector
from .random_selector import RandomSelector
from .dicl_selector import DICLSelector
from .skill_knn_selector import SkillKNNSelector
from .astres_selector import ASTRESSelector
from .vir2_selector import ViR2Selector
from .vir2_no_pos_selector import ViR2NoPOSSelector
from .vir2_no_diversity_selector import ViR2NoDiversitySelector
from .vir2_no_beam_search_selector import ViR2NoBeamSearchSelector

__all__ = [
    'BaseSelector',
    'RandomSelector',
    'SkillKNNSelector',
    'DICLSelector',
    'ASTRESSelector',
    'ViR2Selector',
    'ViR2NoPOSSelector',
    'ViR2NoDiversitySelector',
    'ViR2NoBeamSearchSelector'
]
