#!/usr/bin/env python3
"""Preserved search command; venue discovery now uses the unified settings."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from daily_pipeline import discovery_cli


if __name__ == '__main__':
    raise SystemExit(discovery_cli())
