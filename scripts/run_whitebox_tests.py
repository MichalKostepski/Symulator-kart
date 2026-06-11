
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cmd = [
    sys.executable,
    "-m",
    "unittest",
    "discover",
    "-s",
    "tests/whitebox",
    "-p",
    "test_*.py",
    "-v",
]
print("Uruchamiam testy białoskrzynkowe...")
result = subprocess.run(cmd, cwd=ROOT)
sys.exit(result.returncode)
