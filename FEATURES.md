# scout_utilities — Detailed Feature Reference

This document describes everything `process_sb_report.py` does to a ScoutBook
Rank Requirements CSV. See [README.md](README.md) for install and basic usage.

## 1. Input format

The script consumes a CSV exported from ScoutBook Report Builder. The filename
must contain a `YYYYMMDD` date — the matched value is shown on the advancement
PNG as the report date.

Row-by-row layout the parser expects:

| Row(s)       | First column                                                        | Subsequent columns                                  |
|--------------|---------------------------------------------------------------------|-----------------------------------------------------|
| 1            | (anything — ignored)                                                | Scout full names                                    |
| 2            | `DOB`                                                               | Per-scout date of birth (`mm/dd/yy`)                |
| 3            | `Age`                                                               | Per-scout age in years (integer)                    |
| 4            | `Current Rank`                                                      | Per-scout current rank                              |
| 5–11         | One of the seven rank names (`Scout` … `Eagle Scout`)               | Date awarded (`mm/dd/yy`) or empty                  |
| version line | e.g. `Scout v2024`, `Second Class v2024`                            | Truthy cell = version applies to that scout         |
| req line     | e.g. `1a. Discuss with your patrol leader…`                         | Truthy cell = requirement completed for that scout  |

CSV fields containing commas must be properly quoted; the parser uses Python's
standard `csv` module, so quoted commas inside descriptions are handled.

## 2. Normalizations applied during parsing

- **Scout names** are re-capitalized: first letter uppercase, subsequent
  letters lowercase if preceded by a letter, otherwise uppercase. So `mcDONALD`
  becomes `Mcdonald`, `o'brien` becomes `O'Brien`.
- **Current Rank cells** beginning with `1st` are rewritten to `First Class`;
  cells beginning with `2nd` are rewritten to `Second Class`.
- For the auto-completion logic only (§4), bare `Star` / `Life` / `Eagle`
  current-rank values are treated as `Star Scout` / `Life Scout` / `Eagle Scout`.

## 3. Aged-out scout filtering

Any scout whose `Age` cell is ≥ 18 is removed from `data_dict` before any
output is generated. The remaining scouts are the report's audience.

## 4. Auto-completion of earlier-rank requirements

If a scout's current rank is higher than rank R, then any of their R-level
requirements that appear incomplete in the CSV are silently marked complete in
memory. Rationale: once ScoutBook records a scout as having advanced past R,
all R requirements must have been satisfied, even if the per-requirement entry
is blank in the export.

This only applies to ranks *below* the scout's current rank — requirements at
or above the current rank are left as-is.

## 5. Rank progression and time-gated requirements

The seven ranks in canonical order:

> Scout → Tenderfoot → Second Class → First Class → Star Scout → Life Scout → Eagle Scout

A subset of requirements have minimum durations (in days) before they can be
considered complete:

| Rank         | Requirement | Minimum days |
|--------------|-------------|--------------|
| Tenderfoot   | 1b          | 2            |
| Tenderfoot   | 6c          | 30           |
| Second Class | 1a          | 7            |
| Second Class | 7a          | 30           |
| First Class  | 1a          | 13           |
| Star Scout   | 1           | 122          |
| Life Scout   | 1           | 183          |
| Eagle Scout  | 1           | 183          |

Time-gated requirements are drawn with a red outline on
`scout_advancement.png`.

## 6. Requirement categorization (where it gets done)

Each requirement is tagged with at most one category for color-coding:

| Category       | Fill color (PIL name) | Approximate hue |
|----------------|-----------------------|------------------|
| At meetings    | `azure`               | pale blue        |
| As homework    | `cornsilk`            | pale yellow      |
| On outings     | `lavenderblush`       | pale pink        |

Completed requirements are always drawn in `palegreen`, overriding the category
color. Categorization is hardcoded in `do_req_where` in the source.

## 7. Scout ordering

On `scout_advancement.png`, scouts are sorted by total completed requirements
(across all ranks), descending. Tie-break is alphabetical (dict insertion order
from `sorted(data_dict)`).

## 8. "Eagle is Impossible Unless…" deadline

For each scout the script sums the minimum-duration days for all of their
*incomplete* time-gated requirements, *excluding* the rank they're currently
working on. That sum is subtracted from their 18th birthday, producing a date
by which the scout must complete those requirements or Eagle becomes
mathematically impossible before they age out.

For scouts already at Life Scout the deadline label changes from `Advance` to
`Complete`, and the remaining-days count is computed against today's date
instead of the time-requirement sum.

## 9. Outputs

### `scout_advancement.png`

- Title bar showing the report date (extracted from the input filename).
- Three horizontal blocks, each repeating the scout list:
  1. Scout & Tenderfoot ranks
  2. Second Class & First Class ranks
  3. Star Scout, Life Scout, Eagle Scout ranks, plus the
     "Eagle is Impossible Unless" column
- Each requirement is rendered as a small box, filled per §6 and outlined per §5.
- Color legend in the lower-right corner.

### `event_checklist.png`

A printable troop roster checklist:

| Column                | Type                  |
|-----------------------|-----------------------|
| Scout Name            | text                  |
| Interest Y/N          | checkbox              |
| Commit Y/N            | checkbox              |
| Medical A/B C         | two checkboxes        |
| Paid                  | checkbox              |
| Consent Form          | checkbox              |
| Other Form(s)         | checkbox              |
| Age                   | text                  |
| Tent # Assignment     | blank line            |
| Cleanup Assignment    | blank line            |
| Equipment Returned    | checkbox              |

Four blank rows are appended below the scouts for leaders to sign in.

## 10. `--obscure` mode

When `--obscure` is passed on the command line:

- Scout names are replaced with `SCOUT NAME 0`, `SCOUT NAME 1`, … in both PNGs.
- Ages on `event_checklist.png` are replaced with `##`.

Use this when sharing screenshots outside the troop.

## 11. Errors

| Condition                                               | Exception           |
|---------------------------------------------------------|---------------------|
| `--file` path doesn't exist                             | `FileNotFoundError` |
| `--file` filename doesn't contain a `YYYYMMDD` date     | `ValueError`        |

## 12. Fonts

The script loads fonts by absolute path from
`/System/Library/Fonts/Supplemental/` (macOS-only). To run elsewhere, edit the
`ImageFont.truetype(...)` calls in `plot_advancement` and `plot_trip_template`
to point at locally available monospace fonts.
