import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for service in ("app", "consumer", "ws_api"):
    sys.path.insert(0, str(ROOT / service))
