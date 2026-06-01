"""Tests derived from FEATURES.md.

Section numbers below (e.g. §3) refer to that document.
"""

import pytest

from process_sb_report import PlotScoutAdvancement


# --- §11  Construction / error paths ----------------------------------------

def test_missing_file_raises_FileNotFoundError(tmp_path):
    bogus = tmp_path / 'does_not_exist_20250101.csv'
    with pytest.raises(FileNotFoundError):
        PlotScoutAdvancement(str(bogus), obscure_names=False)


def test_filename_without_date_raises_ValueError(tmp_path):
    path = tmp_path / 'no_date_in_name.csv'
    path.write_text('placeholder')
    with pytest.raises(ValueError):
        PlotScoutAdvancement(str(path), obscure_names=False)


def test_report_date_extracted_from_filename(make_csv):
    path = make_csv(filename='something_20250908_other.csv')
    obj = PlotScoutAdvancement(str(path), obscure_names=False)
    assert obj.report_date == ('2025', '09', '08')


# --- §1, §2, §3  Parsing & normalization ------------------------------------

def test_scout_names_loaded_into_data_dict(parsed):
    assert set(parsed.data_dict.keys()) == {'Alice Smith', 'Bob Jones', 'Diana Prince'}


def test_dob_and_age_parsed(parsed):
    alice = parsed.data_dict['Alice Smith']
    assert alice['dob'] == '01/15/10'
    assert alice['age'] == '14'


def test_aged_out_scout_filtered(parsed):
    # Charlie Brown was age 18 in the CSV; §3 removes him.
    assert 'Charlie Brown' not in parsed.data_dict


def test_first_class_normalization_from_1st(make_csv, standard_csv_body):
    body = standard_csv_body.replace(
        'Current Rank,Tenderfoot,Star,Life Scout,2nd Class',
        'Current Rank,Tenderfoot,Star,Life Scout,1st Class',
    )
    obj = PlotScoutAdvancement(str(make_csv(body=body)), obscure_names=False)
    obj.read_data()
    assert obj.data_dict['Diana Prince']['rank'] == 'First Class'


def test_second_class_normalization_from_2nd(parsed):
    # Diana's current rank in the CSV is '2nd Class'.
    assert parsed.data_dict['Diana Prince']['rank'] == 'Second Class'


def test_completed_requirement_value_preserved(parsed):
    """A truthy completion value should pass through to the parsed dict unchanged."""
    bob_scout = dict(parsed.data_dict['Bob Jones']['Scout']['reqs'])
    assert bob_scout['1b'] == '11/01/21'


# --- §4  Auto-completion of earlier-rank requirements -----------------------

def test_lower_rank_reqs_auto_completed_when_current_rank_higher(parsed):
    # Alice is Tenderfoot (index 1). Her empty Scout (index 0) req should auto-complete.
    alice_scout = dict(parsed.data_dict['Alice Smith']['Scout']['reqs'])
    assert alice_scout['1a'] is True


def test_same_rank_reqs_not_auto_completed(parsed):
    # Alice is Tenderfoot; her empty Tenderfoot reqs must stay incomplete.
    alice_tf = dict(parsed.data_dict['Alice Smith']['Tenderfoot']['reqs'])
    assert alice_tf['1a'] == ''


def test_star_normalization_used_during_auto_completion(parsed):
    """Bob's current rank is bare 'Star'; auto-completion still treats him as
    Star Scout, so his empty Tenderfoot reqs (rank 1 < 4) auto-complete."""
    bob_tf = dict(parsed.data_dict['Bob Jones']['Tenderfoot']['reqs'])
    assert bob_tf['1a'] is True
    assert bob_tf['1b'] is True


# --- §1  CSV quoting (regression for fix #6) --------------------------------

def test_csv_quoted_field_with_comma_preserves_column_alignment(parsed):
    """The 1a description in the standard CSV contains an embedded comma inside
    quotes. The csv module must keep Bob's column at index 2, not slip it."""
    bob_scout = dict(parsed.data_dict['Bob Jones']['Scout']['reqs'])
    assert bob_scout['1a'] == '11/01/21'


# --- §7  Scout ordering -----------------------------------------------------

def test_scout_order_descends_by_completed_requirements(parsed):
    # Completed-req counts on the standard CSV:
    #   Bob = 8 (5 truthy in CSV + 3 auto-completed Tenderfoot/inherited)
    #   Diana = 4 (2 truthy + 2 auto-completed Tenderfoot)
    #   Alice = 2 (1 truthy Scout + 1 auto-completed Scout)
    assert parsed.scout_order == ('Bob Jones', 'Diana Prince', 'Alice Smith')


# --- §5, §6  Class-level invariants -----------------------------------------

def test_rank_progression_is_seven_ranks_in_canonical_order():
    assert PlotScoutAdvancement.rank_progression == (
        'Scout', 'Tenderfoot', 'Second Class', 'First Class',
        'Star Scout', 'Life Scout', 'Eagle Scout',
    )


def test_req_min_durations_covers_every_rank():
    assert set(PlotScoutAdvancement.req_min_durations) == \
        set(PlotScoutAdvancement.rank_progression)


def test_do_req_where_has_three_categories_each_covering_every_rank():
    assert set(PlotScoutAdvancement.do_req_where) == {
        'do at meetings', 'do as homework', 'do on outings',
    }
    for category, by_rank in PlotScoutAdvancement.do_req_where.items():
        assert set(by_rank) == set(PlotScoutAdvancement.rank_progression), \
            f'category {category!r} missing ranks'


def test_second_class_outings_contains_3d_and_4_as_separate_entries():
    """Regression for fix #2: a missing comma had concatenated '3d' '4' into '3d4'."""
    outings = PlotScoutAdvancement.do_req_where['do on outings']['Second Class']
    assert '3d' in outings
    assert '4' in outings
    assert '3d4' not in outings
