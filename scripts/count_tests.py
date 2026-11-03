"""Print the real test total (never hard-code it in the README)."""

import subprocess
import sys

if __name__ == "__main__":
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        capture_output=True,
        text=True,
        cwd=str(__file__ and __import__("pathlib").Path(__file__).resolve().parent.parent),
    )
    for line in out.stdout.splitlines():
        if "test" in line and ("collected" in line or "selected" in line):
            print(line)
