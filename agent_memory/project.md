# project

A single Python script, `process_sb_report.py`, that reads a ScoutBook
Report Builder CSV export and emits two PNGs:

- `scout_advancement.png` — rank-progress grid with "Eagle Impossible" deadlines
- `event_checklist.png` — printable event roster with checkboxes

See the repo-root `README.md` and `FEATURES.md` for the authoritative,
user-facing descriptions. This note just covers conventions a new agent
won't learn from those.

## Running the script

Requires Python 3.7+ and Pillow. Fonts are hardcoded macOS paths under
`/System/Library/Fonts/Supplemental/*` — portability requires editing
the `ImageFont.truetype(...)` calls.

## Running the tests

**Use `python3.11 -m pytest tests/ -v`** on this machine. The system
`python3` is 3.7 and does not have pytest. Pillow + pytest are both
installed under python3.11.

Tests live under `tests/` and build synthetic CSVs in-memory via the
fixtures in `tests/conftest.py`. No real scout data touches disk during
testing.

## Code style preferences

- Default to no comments; only write one when the WHY is non-obvious.
- Prefer editing existing files over creating new ones.
- Don't create docs or README files unless explicitly asked.
