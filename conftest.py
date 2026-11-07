"""
Pytest configuration hook ensuring project root is in sys.path.
"""
import os
import sys
from pathlib import Path

# Set default deterministic test mode if not explicitly overridden
os.environ.setdefault("LLM_PROVIDER", "deterministic")

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
