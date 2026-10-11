# known-issues

Findings from a code review. Several were fixed in commit `11eeca1`;
others remain as the natural next-pass candidates.

## Unfixed

- **`--plot` is a no-op.** Parsed by argparse but never consulted; the
  two PNGs are generated unconditionally.
- **macOS-only fonts.** `ImageFont.truetype(...)` calls hardcode
  `/System/Library/Fonts/Supplemental/*`. Script won't run on Linux
  or Windows without edits. Add candidate-list fallback for portability.
- **`req_check` is dead code.** Built in `read_data()` but only consumed
  by a commented-out block in `dump_data()`. Delete or revive the dump.
- **`current_rank = None`** in `read_data()` is a dead local.
- **`{}` vs `set()` inconsistency.** `do_req_where['do on outings']` uses
  `{}` (empty dict) for Star/Life/Eagle Scout where every other entry
  uses `set()`. Works by accident because `x in {}` returns False, but
  it's a land mine.
- **Two-digit year assumption.** `dob_list[2] += 2000 + 18` silently
  assumes any 2-digit year is 20xx.

## Latent parser bug (not reproduced in practice)

If any scout's cell is empty in a version-line row (e.g.
`Scout v2024,,1,1`), that scout's `data_dict[name][rank]` never gets
its `'reqs'` list initialized. The scout_order aggregation later does
`['reqs']` lookup and will raise `KeyError`. Real-world ScoutBook
exports appear to always populate version cells, so this never
triggers in practice. Test fixtures mirror the real-world shape.

## Fixed — don't re-report these

Commit `11eeca1` resolved:

- `--obscure` crashed `plot_trip_template` with KeyError because the
  obscured display name was then used as a dict lookup key
- Missing comma in `do_req_where`: `'3d' '4'` concatenated to `'3d4'`
- `plot_rank_col` indexed the unsorted reqs list using the sorted
  iteration index; swap to `req_spec[1]`
- `assert`-based file / date validation replaced with `FileNotFoundError`
  and `ValueError`
- Hand-rolled CSV parser (`line.strip().split(',')`) replaced with
  Python's `csv` module — handles quoted fields with commas
- Four regex literals missing `r''` prefix (DeprecationWarning on 3.12+)
