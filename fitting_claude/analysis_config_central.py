"""
Centralized configuration for analysis settings.

This module provides a single source of truth for selections and era combinations
that are used throughout the workflow. It reads default values from user_config.py,
which is the file users should edit.
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class SelectionsConfig:
    """
    Configuration for channel selections and era combinations.
    
    This is the SINGLE SOURCE OF TRUTH for what selections and eras
    should be combined throughout the analysis pipeline.
    
    By default, reads from user_config.py - users should edit that file
    to customize their analysis.
    """
    
    # Channel selection combinations
    # Key: Name of combined selection
    # Value: List of channel names to combine
    SELECTIONS: Dict[str, List[str]] = None
    
    # Era combinations
    # Key: Name of combined era period
    # Value: List of era names to combine
    ERAS_TO_COMBINE: Dict[str, List[str]] = None
    
    def __post_init__(self):
        """Set default values from user_config if not provided."""
        if self.SELECTIONS is None or self.ERAS_TO_COMBINE is None:
            # Import user config
            try:
                from user_config import SELECTIONS, ERAS_TO_COMBINE
                if self.SELECTIONS is None:
                    self.SELECTIONS = SELECTIONS
                if self.ERAS_TO_COMBINE is None:
                    self.ERAS_TO_COMBINE = ERAS_TO_COMBINE
            except ImportError:
                # Fallback to hardcoded defaults if user_config doesn't exist
                if self.SELECTIONS is None:
                    self.SELECTIONS = {
                        '3j_4j': ['SL_3j_resolved', 'SL_4j_resolved'],
                        '3j1b_3j2b_4j1b_4j2b': [
                            'SL_res_3j_1b', 'SL_res_3j_2b',
                            'SL_res_4j_1b', 'SL_res_4j_2b'
                        ],
                    }
                
                if self.ERAS_TO_COMBINE is None:
                    self.ERAS_TO_COMBINE = {
                        'eras_22': ['2022', '2022EE'],
                        'eras_23': ['2023', '2023BPix'],
                        'eras_all': ['2022', '2022EE', '2023', '2023BPix'],
                    }
    
    @classmethod
    def default(cls) -> 'SelectionsConfig':
        """Create configuration with default values."""
        return cls()
    
    @classmethod
    def custom(
        cls,
        selections: Dict[str, List[str]] = None,
        eras_to_combine: Dict[str, List[str]] = None
    ) -> 'SelectionsConfig':
        """
        Create configuration with custom values.
        
        Args:
            selections: Custom selection combinations (None = use defaults)
            eras_to_combine: Custom era combinations (None = use defaults)
            
        Returns:
            SelectionsConfig with specified values
        """
        return cls(
            SELECTIONS=selections,
            ERAS_TO_COMBINE=eras_to_combine
        )


# Global default configuration instance
# This can be imported and used throughout the package
DEFAULT_CONFIG = SelectionsConfig.default()


def get_selections() -> Dict[str, List[str]]:
    """
    Get the current selection combinations.
    
    Returns:
        Dictionary mapping selection names to channel lists
    """
    return DEFAULT_CONFIG.SELECTIONS


def get_eras_to_combine() -> Dict[str, List[str]]:
    """
    Get the current era combinations.
    
    Returns:
        Dictionary mapping era period names to era lists
    """
    return DEFAULT_CONFIG.ERAS_TO_COMBINE


def set_selections(selections: Dict[str, List[str]]) -> None:
    """
    Set custom selection combinations.
    
    Args:
        selections: Dictionary mapping selection names to channel lists
    """
    DEFAULT_CONFIG.SELECTIONS = selections


def set_eras_to_combine(eras_to_combine: Dict[str, List[str]]) -> None:
    """
    Set custom era combinations.
    
    Args:
        eras_to_combine: Dictionary mapping era period names to era lists
    """
    DEFAULT_CONFIG.ERAS_TO_COMBINE = eras_to_combine


# Convenience function to update both at once
def configure_analysis(
    selections: Dict[str, List[str]] = None,
    eras_to_combine: Dict[str, List[str]] = None
) -> None:
    """
    Configure the analysis with custom selections and era combinations.
    
    Args:
        selections: Custom selection combinations (None = keep current)
        eras_to_combine: Custom era combinations (None = keep current)
    
    Example:
        >>> from analysis_config_central import configure_analysis
        >>> configure_analysis(
        ...     selections={'my_selection': ['channel1', 'channel2']},
        ...     eras_to_combine={'my_era': ['2022', '2023']}
        ... )
    """
    if selections is not None:
        set_selections(selections)
    if eras_to_combine is not None:
        set_eras_to_combine(eras_to_combine)