"""
Data loading utilities for ViPERSQL

This module provides standardized data loading functions for ViText2SQL and BIRD datasets.
"""

import json
from pathlib import Path
from typing import Dict, List, Any


def load_dataset(dataset_name: str = "vitext2sql", split: str = "test", level: str = "std", language: str = "vi") -> List[Dict[str, Any]]:
    """
    Load dataset for Text-to-SQL evaluation.

    Args:
        dataset_name (str): Name of the dataset ('vitext2sql' or 'bird'). Default: 'vitext2sql'
        split (str): Data split to load ('test', 'train', 'dev', 'candidates')
        level (str): Level for ViText2SQL ('std', 'syllable', 'word'). Ignored for BIRD.
        language (str): Language code ('vi' for Vietnamese, 'en' for English). Only used for BIRD.

    Returns:
        List[Dict[str, Any]]: List of dataset samples

    Raises:
        FileNotFoundError: If the dataset file doesn't exist
        ValueError: If unsupported dataset name is provided
    """
    dataset_name = dataset_name.lower()

    # Get project root (assuming this is called from project root or subdirectories)
    project_root = Path(__file__).parent.parent.parent

    if dataset_name == "vitext2sql":
        # ViText2SQL dataset structure
        level_dir = f"{level}-level"

        if split == "candidates":
            file_path = project_root / "dataset" / "ViText2SQL" / level_dir / "dicl_candidates.json"
        else:
            file_path = project_root / "dataset" / "ViText2SQL" / level_dir / f"{split}.json"

    elif dataset_name == "bird":
        # BIRD dataset structure
        if split == "candidates":
            file_path = project_root / "dataset" / "BIRD" / language / "candidates.json"
        else:
            file_path = project_root / "dataset" / "BIRD" / language / f"{split}.json"

    else:
        raise ValueError(f"Unsupported dataset: {dataset_name}. Supported datasets: 'vitext2sql', 'bird'")

    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    print(f"Loading {dataset_name} {split} data from: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Loaded {len(data)} samples")
    return data


def load_tables_info(dataset_name: str = "vitext2sql", level: str = "std") -> Dict[str, Any]:
    """
    Load tables information for schema context.

    Args:
        dataset_name (str): Name of the dataset ('vitext2sql' or 'bird'). Default: 'vitext2sql'
        level (str): Level for ViText2SQL ('std', 'syllable', 'word'). Ignored for BIRD.

    Returns:
        Dict[str, Any]: Dictionary with db_id as keys and table info as values

    Raises:
        FileNotFoundError: If the tables file doesn't exist
        ValueError: If unsupported dataset name is provided
    """
    dataset_name = dataset_name.lower()

    # Get project root
    project_root = Path(__file__).parent.parent.parent

    if dataset_name == "vitext2sql":
        # ViText2SQL dataset structure
        level_dir = f"{level}-level"
        file_path = project_root / "dataset" / "ViText2SQL" / level_dir / "tables.json"

    elif dataset_name == "bird":
        # BIRD dataset structure
        file_path = project_root / "dataset" / "BIRD" / "tables.json"

    else:
        raise ValueError(f"Unsupported dataset: {dataset_name}. Supported datasets: 'vitext2sql', 'bird'")

    if not file_path.exists():
        raise FileNotFoundError(f"Tables file not found: {file_path}")

    print(f"Loading tables info from: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Convert to dict with db_id as key for easier lookup
    tables_dict = {}
    for db_info in data:
        db_id = db_info.get('db_id')
        if db_id:
            tables_dict[db_id] = db_info

    print(f"Loaded tables info for {len(tables_dict)} databases")
    return tables_dict


def load_vitext2sql_data(level: str = "std", split: str = "test") -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Convenience function to load ViText2SQL test data, candidates, and tables info in one call.

    Args:
        level (str): Level of Vietnamese text segmentation ('std', 'syllable', 'word')
        split (str): Data split to load for test data

    Returns:
        tuple: (test_data, candidates_data, tables_info)
    """
    test_data = load_dataset("vitext2sql", split, level)

    try:
        candidates_data = load_dataset("vitext2sql", "candidates", level)
    except FileNotFoundError:
        print("Warning: Candidates file not found, using train data as candidates")
        try:
            candidates_data = load_dataset("vitext2sql", "train", level)
        except FileNotFoundError:
            print("Warning: Train file not found either, using test data as candidates")
            candidates_data = test_data.copy()

    tables_info = load_tables_info("vitext2sql", level)

    return test_data, candidates_data, tables_info


def load_bird_data(language: str = "vi", split: str = "test") -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Convenience function to load BIRD test data, candidates, and tables info in one call.

    Args:
        language (str): Language code ('vi' for Vietnamese, 'en' for English)
        split (str): Data split to load for test data

    Returns:
        tuple: (test_data, candidates_data, tables_info)
    """
    test_data = load_dataset("bird", split, "std", language)

    try:
        candidates_data = load_dataset("bird", "candidates", "std", language)
    except FileNotFoundError:
        print("Warning: Candidates file not found, using test data as candidates")
        candidates_data = test_data.copy()

    tables_info = load_tables_info("bird")

    return test_data, candidates_data, tables_info
