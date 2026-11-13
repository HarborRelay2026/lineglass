"""Print the cells a single nonogram line logically forces, using the Fe code."""

import argparse
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("line", help="Use ? for unknown, # for filled, and . for empty.")
    parser.add_argument("clues", type=int, nargs="*", help="Positive run lengths, left to right.")
    parser.add_argument("--fe", default="fe", help="Path to Fe 26.6.0.")
    args = parser.parse_args()
    if not 0 <= len(args.line) <= 32 or any(cell not in "?#." for cell in args.line):
        parser.error("Use up to 32 cells drawn from ?, # and .")
    if len(args.clues) > 16 or any(not 1 <= value <= 32 for value in args.clues):
        parser.error("Supply up to 16 run lengths in the range 1–32.")
    executable = shutil.which(args.fe)
    if not executable:
        parser.error("Provide the Fe executable with --fe")
    filled = sum(1 << i for i, cell in enumerate(args.line) if cell == "#")
    empty = sum(1 << i for i, cell in enumerate(args.line) if cell == ".")
    lengths = args.clues + [0] * (16 - len(args.clues))
    # Only validated integers enter the fixture. All deductions run in Fe.
    fixture = f"""
use ingot::solve_line
#[event]
struct Hint {{ ways: u256, always: u256, ever: u256 }}
#[test]
fn probe() uses (log: mut Log) {{
    let result = solve_line(width: {len(args.line)}, clues: {lengths},
                            clue_count: {len(args.clues)}, filled: {filled}, empty: {empty})
    log.emit(Hint {{ ways: result.ways as u256, always: result.always_filled as u256,
                    ever: result.ever_filled as u256 }})
}}
"""
    root = Path(__file__).resolve().parents[1]
    with TemporaryDirectory(prefix="lineglass-hint-") as temp:
        trial = Path(temp)
        shutil.copy(root / "fe.toml", trial)
        (trial / "src").mkdir()
        shutil.copy(root / "src/lib.fe", trial / "src/lib.fe")
        (trial / "src/hint.fe").write_text(fixture, encoding="utf-8")
        run = subprocess.run([executable, "test", str(trial), "--show-logs", "--color", "never"],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if run.returncode:
        raise SystemExit(run.stdout)
    words = re.findall(r"data: 0x([0-9a-fA-F]{192})\b", run.stdout)
    if len(words) != 1:
        raise SystemExit("Fe did not return the three expected event values.")
    ways, always, ever = (int(words[0][start:start + 64], 16) for start in (0, 64, 128))
    print(f"{ways} completion(s)")
    if ways:
        print("".join("#" if (always >> i) & 1 else "?" if (ever >> i) & 1 else "."
                      for i in range(len(args.line))))


if __name__ == "__main__":
    main()
