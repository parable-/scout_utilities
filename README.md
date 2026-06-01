# scout_utilities

Scripts for Scoutmasters and committee members to summarize troop advancement
and generate event paperwork from ScoutBook Report Builder exports.

`process_sb_report.py` consumes a Rank Requirements CSV exported from ScoutBook
and emits two PNGs:

- **`scout_advancement.png`** — an at-a-glance grid of every active scout's
  rank progress, color-coded by where each requirement gets done (meetings /
  homework / outings) and with a per-scout "Eagle is Impossible Unless..."
  deadline.
- **`event_checklist.png`** — a printable troop roster checklist for an event
  (interest / commit / medical / paid / etc. checkboxes per scout, plus blank
  rows for leaders).

See [FEATURES.md](FEATURES.md) for a detailed description of parsing rules,
color coding, the Eagle deadline calculation, and the two output layouts.

## Install

Requires Python 3.8+ and [Pillow](https://pillow.readthedocs.io/):

```bash
pip install pillow
```

The script currently loads fonts by absolute path from
`/System/Library/Fonts/Supplemental/` (Andale Mono, Courier New Bold). To run on
Linux or Windows you'll need to edit the `ImageFont.truetype(...)` calls in
`process_sb_report.py` to point at locally available monospace fonts.

## Exporting the input CSV from ScoutBook

1. In ScoutBook, open **Report Builder**.
2. Select the scouts you want to include.
3. For each **Scout Rank**, check **Rank Status** and the **<rank> Requirements** boxes.
4. Under **Settings**, enable:
   - Show Dates
   - Show Requirement Descriptions
   - Show Empty Requirements
   - Show Current Rank
   - Show DOB
   - Show Age
5. Run the report and download the CSV.

The exported filename must contain a date in `YYYYMMDD` form (anywhere in the
name) — the script uses it as the report's "as of" date on the output PNG.

## Run

```bash
python3 process_sb_report.py \
    --file ReportBuilder_Troop0318B_Rank_Requirements_20250908.csv
```

Both PNGs (`scout_advancement.png`, `event_checklist.png`) are written to the
current working directory.

### Flags

| Flag        | Purpose                                                                 |
|-------------|-------------------------------------------------------------------------|
| `--file`    | **Required.** Path to the ScoutBook Rank Requirements CSV.              |
| `--dump`    | Also print a text-mode dump of all parsed data to stdout.               |
| `--obscure` | Anonymize names (`SCOUT NAME N`) and ages (`##`) in both PNGs.          |
| `--plot`    | Accepted for backwards compatibility; PNGs are always generated.        |

Use `--obscure` when sharing screenshots outside the troop.

## Tests

```bash
pip install pytest
pytest
```

Tests live under `tests/` and exercise the parser against synthetic CSVs built
in-memory (no real scout data ever touches disk).
