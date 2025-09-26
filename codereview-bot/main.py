#!/usr/bin/env python3
"""Main entry point for CodeReview Bot."""
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.bot.app import main

if __name__ == "__main__":
    main()