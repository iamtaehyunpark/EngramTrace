"""Keep test imports and all generated memory independent of the developer's data."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
