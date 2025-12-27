import subprocess
import sys
from pathlib import Path


def test_smart_router_script_runs():
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "tests" / "test_smart_router.py"
    assert script.exists(), f"Missing script: {script}"

    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )

    if proc.returncode != 0:
        # stdout/stderr'i assertion mesajına göm
        raise AssertionError(
            "tests/test_smart_router.py failed\n"
            f"exit_code={proc.returncode}\n"
            "----- STDOUT -----\n"
            f"{proc.stdout}\n"
            "----- STDERR -----\n"
            f"{proc.stderr}\n"
        )
