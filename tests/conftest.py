"""Shared pytest fixtures.

`process_sb_report.py` lives at the project root rather than inside a package,
so we prepend the project root to sys.path before tests import it.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import process_sb_report  # noqa: E402


# A small but feature-complete synthetic ScoutBook export. Designed so:
#
#   - Alice Smith   (Tenderfoot, age 14)  exercises auto-completion of Scout reqs
#                                         from the rank below her current rank.
#   - Bob Jones     ('Star',     age 16)  exercises the bare 'Star' -> 'Star Scout'
#                                         normalization in auto-completion (§2/§4)
#                                         and accumulates the most completed reqs.
#   - Charlie Brown (Life Scout, age 18)  is aged out and must be filtered (§3).
#   - Diana Prince  ('2nd Class',age 15)  exercises the '2nd' -> 'Second Class'
#                                         current-rank normalization (§2).
#
# The Scout 1a row uses a quoted description containing a comma to regression-test
# the switch from a hand-rolled parser to the csv module (§1).
_STANDARD_CSV_BODY = "\n".join([
    'Name,Alice Smith,Bob Jones,Charlie Brown,Diana Prince',
    'DOB,01/15/10,03/22/08,06/10/06,05/05/09',
    'Age,14,16,18,15',
    'Current Rank,Tenderfoot,Star,Life Scout,2nd Class',
    'Scout,12/01/22,11/01/21,10/01/20,11/01/22',
    'Tenderfoot,,10/15/22,09/15/21,',
    'Second Class,,09/15/22,08/15/21,',
    'First Class,,08/15/22,07/15/21,',
    'Star Scout,,07/15/22,06/15/21,',
    'Life Scout,,,05/15/21,',
    'Eagle Scout,,,,',
    'Scout v2024,1,1,1,1',
    '"1a. Discuss, with your patrol leader",,11/01/21,10/01/20,11/01/22',
    '1b. Repeat the Scout Oath,12/01/22,11/01/21,10/01/20,11/01/22',
    'Tenderfoot v2024,1,1,1,1',
    '1a. Present yourself for inspection,,,09/15/21,',
    '1b. Spend at least one night camping,,,09/15/21,',
    'Second Class v2024,1,1,1,1',
    '1a. Spend at least 7 nights camping,,09/15/22,08/15/21,',
    '2a. Demonstrate how to find directions,,09/15/22,08/15/21,',
    'First Class v2024,1,1,1,1',
    '1a. Demonstrate finding directions,,08/15/22,07/15/21,',
    'Star Scout v2024,1,1,1,1',
    '1. Serve 4 months in a leadership position,,07/15/22,06/15/21,',
    'Life Scout v2024,1,1,1,1',
    '1. Serve 6 months in a leadership position,,,05/15/21,',
    'Eagle Scout v2024,1,1,1,1',
    '1. Be active for at least 6 months,,,,',
]) + "\n"


@pytest.fixture
def standard_csv_body():
    return _STANDARD_CSV_BODY


@pytest.fixture
def make_csv(tmp_path, standard_csv_body):
    """Write a CSV (defaulting to the standard scenario) and return its Path.

    Tests can pass a custom body string to vary the scenario.
    """
    def _make(body=None, filename='ReportBuilder_TEST_20250101.csv'):
        path = tmp_path / filename
        path.write_text(body if body is not None else standard_csv_body)
        return path
    return _make


@pytest.fixture
def parsed(make_csv):
    """A PlotScoutAdvancement instance with read_data() already run on the standard CSV."""
    obj = process_sb_report.PlotScoutAdvancement(str(make_csv()), obscure_names=False)
    obj.read_data()
    return obj
