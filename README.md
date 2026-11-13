# Lineglass

Lineglass answers a question a nonogram player can act on. Given the lengths of the runs in a row and any cells already marked, which moves follow from the clues? It counts all legal completions and returns every cell that must be filled or empty. Puzzle authors can use the same result to measure ambiguity.

## Try a hint

Install [Fe 26.6.0](https://github.com/argotorg/fe/releases/tag/v26.6.0). The command-line demonstration also requires Python 3.10 or newer. Run these commands from the project directory.

```sh
python tools/hint.py '.????' 3
```

```text
2 completion(s)
.?##?
```

A single run of three must fit after the leading empty cell. Its two possible placements share the middle two cells. Here `#` means filled, `.` empty and `?` undecided. Try `python tools/hint.py '?#?' 1 1` for a contradiction. Both examples run the compiled Fe implementation in the local test EVM. The Python front end parses the input and displays the returned masks.

## Build and verify

```sh
fe --version
fe check
fe test
fe build
python tools/check_oracle.py
```

The tested release reports `fe 26.6.0 (5b3f96a)`. Both Python commands accept `--fe PATH`. The project uses the compiler's bundled libraries and Python's standard library. Build and test work offline once the compiler is installed.

## API and algorithm

`solve_line` in `src/lib.fe` takes the line width, sixteen clue slots, the number of active clues, and two masks for cells already filled or empty. Bit zero denotes the leftmost cell. The returned `ways` is the exact count. In a feasible line, `always_filled` is the intersection of all completions and `ever_filled` is their union. Cells inside the line outside that union are forced empty. Zero ways means there is no answer compatible with the inputs, and both masks are zero.

The algorithm stores prefixes by length. With no runs, each prefix is feasible if all its cells can be empty. For each new run, a prefix either ends in an empty cell or ends exactly at the right end of the run. In the latter case it checks the run's span and the separator before it. These two sets of completions are disjoint. Adding their counts and intersecting or uniting their masks gives the exact result without visiting each completion. The algorithm uses two rows of at most 33 summaries, and O(width × (clue count + 1)) steps.

`src/reader.fe` exposes a stateless EVM function that takes the same information in standard ABI types. It returns a tuple of three unsigned integers. The example in `src/tests.fe` makes an actual message call through this interface in the local EVM.

## Scope and evidence

Lines can contain up to 32 cells and 16 positive clues. Overlapping marks, bits outside the line, excessive dimensions and unsatisfiable clues return zero ways. Unused clue slots are ignored. This library reasons about one line at a time. A whole puzzle may require alternating between rows and columns, or considering several lines together.

The six focused Fe tests cover an overlapping run, a mandatory separator, the 32nd cell, sixteen runs, invalid input and the ABI example. The Python oracle independently enumerates binary strings and groups them by the lengths of their runs. It checks the compiled Fe solver against every realizable clue list and every combination of filled, empty and unknown marks at widths zero through five. Across 3,976 inputs it checks the count and both masks. At width 32 a test checks the exact count of 1,081,575 placements of eight isolated cells.

## Authorship

HarbourRelay developed this entry using OpenAI Codex for design, source, tests and documentation. All project-specific implementation work began November 12, 2026. The Fe compiler and its standard library are upstream tools. No game-jam code, music, purchased assets or third-party puzzle data are included. The project is released under the MIT license, to the extent copyright subsists.
