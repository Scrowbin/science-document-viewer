#!/usr/bin/env python3
"""
Phase 1 Extraction Evaluation runner.
Delegates to evaluate_extraction_ohr.py for the full OHR-Bench benchmark evaluation.
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from evaluate_extraction_ohr import main

if __name__ == "__main__":
    main()
