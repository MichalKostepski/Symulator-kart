
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
steps = [
    [sys.executable, str(ROOT / "scripts" / "run_unit_tests.py")],
    [sys.executable, str(ROOT / "scripts" / "run_whitebox_tests.py")],
    [sys.executable, str(ROOT / "scripts" / "run_blackbox_poker.py")],
]
for cmd in steps:
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        sys.exit(result.returncode)
sys.exit(0)
