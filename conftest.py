"""Root pytest configuration.

Puts the repository root on `sys.path` so tests can import the top-level
packages (`ml`, `backend`, `data`) regardless of which directory pytest is
invoked from. The tree uses PEP 420 namespace packages (no `__init__.py`), and
pytest's default `prepend` import mode would otherwise insert only the test
file's own directory.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
