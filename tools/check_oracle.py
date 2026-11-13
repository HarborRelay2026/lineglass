"""Compare the compiled Fe solver with direct Python enumeration of short lines."""

import argparse
from collections import defaultdict
from itertools import groupby, product
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory


def clue_signature(line, width):
    bits = ((line >> index) & 1 for index in range(width))
    return tuple(sum(group) for bit, group in groupby(bits) if bit)


def cases_for(width):
    by_clue = defaultdict(list)
    for line in range(1 << width):
        by_clue[clue_signature(line, width)].append(line)
    for clues, candidates in by_clue.items():
        results = []
        for state in product(range(3), repeat=width):
            filled = sum(1 << i for i, cell in enumerate(state) if cell == 1)
            empty = sum(1 << i for i, cell in enumerate(state) if cell == 2)
            fits = [line for line in candidates if line & filled == filled and not line & empty]
            always = fits[0] if fits else 0
            ever = 0
            for line in fits:
                always &= line
                ever |= line
            results.append((filled, empty, len(fits), always, ever))
        yield clues, results


def fe_test(width, clues, cases, number):
    # Five six-bit fields fit a single word at widths 0–5.
    words = [a | b << 6 | count << 12 | every << 18 | some << 24
             for a, b, count, every, some in cases]
    lengths = list(clues) + [0] * (16 - len(clues))
    return f"""
#[test]
fn oracle_w{width}_{number}() {{
    let fixtures: [usize; {len(words)}] = {words}
    let clues: [usize; 16] = {lengths}
    for item in fixtures {{
        let result = solve_line(width: {width}, clues: clues, clue_count: {len(clues)},
                                filled: item & 63, empty: (item >> 6) & 63)
        assert!(result.ways == ((item >> 12) & 63))
        assert!(result.always_filled == ((item >> 18) & 63))
        assert!(result.ever_filled == (item >> 24))
    }}
}}
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fe", default="fe")
    args = parser.parse_args()
    executable = shutil.which(args.fe)
    if not executable:
        parser.error("Provide the Fe executable with --fe")
    root = Path(__file__).resolve().parents[1]
    total = 0
    tests = ["use ingot::solve_line\n"]
    for width in range(6):
        for number, (clues, cases) in enumerate(cases_for(width)):
            tests.append(fe_test(width, clues, cases, number))
            total += len(cases)
    with TemporaryDirectory(prefix="lineglass-oracle-") as temp:
        trial = Path(temp)
        shutil.copy(root / "fe.toml", trial)
        (trial / "src").mkdir()
        shutil.copy(root / "src/lib.fe", trial / "src/lib.fe")
        (trial / "src/oracle.fe").write_text("".join(tests), encoding="utf-8")
        subprocess.run([executable, "test", str(trial), "--color", "never"], check=True)
    print(f"{total} lines matched in count, forced cells and possible cells.")


if __name__ == "__main__":
    main()
