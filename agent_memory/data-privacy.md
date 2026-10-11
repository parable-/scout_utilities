# data-privacy

## Never commit

- `ReportBuilder_*.csv` — real scout names, dates of birth, ages.
- `event_checklist.png`, `scout_advancement.png` — real names unless
  generated with `--obscure`.

These files are routinely present in the working tree because the user
runs the script in-place. Always check `git status` before any `git add`,
and double-check contents of anything staged, even if the filename looks
innocuous.

## No .gitignore enforcing this

The repo has no `.gitignore` yet — user declined adding one when offered.
That means **nothing automated prevents a commit** of these files; the
"never commit" rule above is enforced only by discipline. Always run
`git status` before any `git add`, prefer naming specific files to
`git add .`, and audit staged contents before committing.

## What is safe in source

- The committed source and tests contain no real scout names.
- The script has an `--obscure` flag that anonymizes outputs as
  `SCOUT NAME N` with ages shown as `##`. Use it before sharing any
  rendered PNG outside the troop.
- Test fixtures use fictional names (Alice/Bob/Charlie/Diana) in a
  synthetic CSV built in `tests/conftest.py`.
