
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cmd = [
    sys.executable,
    "-m",
    "unittest",
    "tests/unit/poker_unittest.py",
    "tests/unit/makao_unittest.py",
]
print("Uruchamiam testy jednostkowe...")
result = subprocess.run(cmd, cwd=ROOT)
sys.exit(result.returncode)
