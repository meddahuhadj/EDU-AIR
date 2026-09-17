"""Test fixture: make the project root importable for both edu_air and
hadj_no_touch.

Run from the project root:
    py -3.12 -m pytest tests_edu_air -q
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))