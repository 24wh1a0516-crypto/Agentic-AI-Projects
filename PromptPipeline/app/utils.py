"""Utility functions for display and file output."""

import json
import os
from datetime import datetime


def print_stage(title: str, data: dict) -> None:
    """Print a stage's output with a formatted header.

    Args:
        title: Stage label to display.
        data: Dictionary to pretty-print.
    """
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(json.dumps(data, indent=2))


def save_output(filename: str, data: dict) -> str:
    """Save a dictionary as JSON to the outputs/ directory.

    Args:
        filename: Base filename (without directory).
        data: Dictionary to save.

    Returns:
        Full path of the saved file.
    """
    os.makedirs("outputs", exist_ok=True)
    path = os.path.join("outputs", filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path
