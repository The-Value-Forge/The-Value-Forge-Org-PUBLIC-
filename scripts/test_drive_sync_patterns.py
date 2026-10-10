"""Tests for drive_sync.py's pattern-register protections.

Run directly (no pytest needed):  python3 scripts/test_drive_sync_patterns.py

Covers the monotonic guards on full patterns.json replacement, the append-only
delta merge, and the reference warnings. These protect data/patterns.json —
the site's only cumulative, irreplaceable dataset — so every rule here is
load-bearing; if you change guard behaviour, change the test WITH the reasoning.
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
# googleapiclient isn't needed for the pure functions; stub the imports so the
# module loads in environments without the Drive client installed.
import types
for mod in ("google", "google.oauth2", "google.oauth2.service_account",
            "googleapiclient", "googleapiclient.discovery", "googleapiclient.http"):
    sys.modules.setdefault(mod, types.ModuleType(mod))
sys.modules["google.oauth2"].service_account = sys.modules["google.oauth2.service_account"]
for name, attr in (("googleapiclient.discovery", "build"),
                   ("googleapiclient.http", "MediaIoBaseDownload"),
                   ("google.oauth2.service_account", "Credentials")):
    setattr(sys.modules[name], attr, object)

from drive_sync import (  # noqa: E402
    merge_patterns_delta,
    reference_warnings,
    validate_patterns_full,
)

CURRENT = {
    "generated": "2026-07-11",
    "source": "Monthly Review",
    "intelligence_window": "",
    "patterns": [
        {
            "id": "VF-P1",
            "title": "Earlier specialist input → better outcomes",
            "status": "established",
            "confirmation_level": "Definitive",
            "first_appeared": "2026-06",
            "domains": ["D01", "D02"],
            "history": [
                {"date": "2026-06", "status": "established",
                 "note": "Clinical evidence (PMIDs 42100443, 41665982)."},
                {"date": "2026-07", "status": "established", "note": "Held (PMID 41911440)."},
            ],
        },
        {
            "id": "VF-P2",
            "title": "Information infrastructure",
            "status": "established",
            "first_appeared": "2026-06",
            "domains": ["D01"],
            "history": [{"date": "2026-06", "status": "established", "note": "PMID 40260522."}],
        },
    ],
}


def write_current(tmp: Path) -> Path:
    p = tmp / "patterns.json"
    p.write_text(json.dumps(CURRENT), encoding="utf-8")
    return p


def as_bytes(obj) -> bytes:
    return json.dumps(obj).encode("utf-8")


def test_full_pass():
    with tempfile.TemporaryDirectory() as d:
        cur = write_current(Path(d))
        inc = json.loads(json.dumps(CURRENT))
        inc["generated"] = "2026-08-08"
        inc["patterns"][0]["history"].append(
            {"date": "2026-08", "status": "established", "note": "New month (PMID 43000001)."})
        errors, warnings = validate_patterns_full(as_bytes(inc), cur)
        assert errors == [], errors
        assert warnings == [], warnings


def test_full_holds_on_lost_pattern():
    with tempfile.TemporaryDirectory() as d:
        cur = write_current(Path(d))
        inc = json.loads(json.dumps(CURRENT))
        inc["patterns"] = [p for p in inc["patterns"] if p["id"] != "VF-P2"]
        errors, _ = validate_patterns_full(as_bytes(inc), cur)
        assert any("VF-P2 DISAPPEARED" in e for e in errors), errors


def test_full_holds_on_lost_history():
    with tempfile.TemporaryDirectory() as d:
        cur = write_current(Path(d))
        inc = json.loads(json.dumps(CURRENT))
        inc["patterns"][0]["history"] = inc["patterns"][0]["history"][1:]  # drop 2026-06
        errors, _ = validate_patterns_full(as_bytes(inc), cur)
        assert any("LOSE history" in e and "2026-06" in e for e in errors), errors


def test_full_holds_on_first_appeared_rewrite():
    with tempfile.TemporaryDirectory() as d:
        cur = write_current(Path(d))
        inc = json.loads(json.dumps(CURRENT))
        inc["patterns"][0]["first_appeared"] = "2026-07"
        errors, _ = validate_patterns_full(as_bytes(inc), cur)
        assert any("first_appeared would change" in e for e in errors), errors


def test_full_holds_on_stale_generated():
    with tempfile.TemporaryDirectory() as d:
        cur = write_current(Path(d))
        inc = json.loads(json.dumps(CURRENT))
        inc["generated"] = "2026-06-13"
        errors, _ = validate_patterns_full(as_bytes(inc), cur)
        assert any("OLDER than current" in e for e in errors), errors


def test_full_holds_on_malformed():
    with tempfile.TemporaryDirectory() as d:
        cur = write_current(Path(d))
        errors, _ = validate_patterns_full(b"not json", cur)
        assert errors and "HELD" in errors[0], errors
        errors, _ = validate_patterns_full(as_bytes({"patterns": [{"title": "no id"}]}), cur)
        assert errors, "patterns without ids must be held"


def test_full_no_current_file_accepts():
    with tempfile.TemporaryDirectory() as d:
        errors, _ = validate_patterns_full(as_bytes(CURRENT), Path(d) / "patterns.json")
        assert errors == [], errors


def test_reference_warning_fires_only_for_new_unreferenced_entries():
    inc = json.loads(json.dumps(CURRENT))
    inc["patterns"][0]["history"].append({"date": "2026-08", "status": "established",
                                          "note": "No citation given."})
    warnings = reference_warnings(inc, CURRENT)
    assert len(warnings) == 1 and "VF-P1 history 2026-08" in warnings[0], warnings
    # structured references or supporting slugs satisfy the check
    inc["patterns"][0]["history"][-1]["supporting"] = ["2026-08-01-some-signal"]
    assert reference_warnings(inc, CURRENT) == []
    # pre-existing unreferenced entries never warn (only NEW entries are policed)
    assert reference_warnings(CURRENT, CURRENT) == []


def test_delta_appends_history_and_updates_status():
    delta = {"generated": "2026-08-08", "patterns": [{
        "id": "VF-P1", "status": "qualified",
        "history": [{"date": "2026-08", "status": "qualified",
                     "note": "Narrowed (PMID 43000001).",
                     "references": [{"pmid": "43000001"}]}],
    }]}
    merged, errors, warnings = merge_patterns_delta(CURRENT, delta)
    assert errors == [] and warnings == [], (errors, warnings)
    p1 = next(p for p in merged["patterns"] if p["id"] == "VF-P1")
    assert [h["date"] for h in p1["history"]] == ["2026-06", "2026-07", "2026-08"]
    assert p1["status"] == "qualified"
    assert merged["generated"] == "2026-08-08"
    assert CURRENT["patterns"][0]["status"] == "established", "input must not be mutated"


def test_delta_adds_new_pattern_and_is_idempotent():
    delta = {"generated": "2026-08-08", "patterns": [{
        "id": "VF-P12", "title": "New pattern", "status": "emerging",
        "first_appeared": "2026-08", "domains": ["D03"],
        "history": [{"date": "2026-08", "status": "emerging", "note": "PMID 43000002."}],
    }]}
    once, errors, _ = merge_patterns_delta(CURRENT, delta)
    assert errors == [] and any(p["id"] == "VF-P12" for p in once["patterns"])
    twice, errors2, _ = merge_patterns_delta(once, delta)
    assert errors2 == [] and twice == once, "re-applying a delta must be a no-op"


def test_delta_protects_first_appeared_and_rejects_bad_new_pattern():
    delta = {"patterns": [
        {"id": "VF-P1", "first_appeared": "2026-01", "history": []},
        {"id": "VF-P13", "history": []},  # new pattern missing first_appeared
    ]}
    merged, errors, _ = merge_patterns_delta(CURRENT, delta)
    p1 = next(p for p in merged["patterns"] if p["id"] == "VF-P1")
    assert p1["first_appeared"] == "2026-06"
    assert any("immutable" in e for e in errors), errors
    assert not any(p["id"] == "VF-P13" for p in merged["patterns"])
    assert any("VF-P13" in e for e in errors), errors


def test_compare_citation_flags_composed_title_and_wrong_year():
    from drive_sync import compare_citation
    local = {"title": "Comparison of seven geriatric assessment tools for predicting institutionalisation",
             "year": "2026", "authors": "Abbadi, et al."}
    pubmed = {"title": "Comparing geriatric assessment tools for predicting negative health outcomes in older adults",
              "year": "2026", "first_author": "Abbadi A"}
    issues = compare_citation(local, pubmed)
    assert any("title mismatch" in i for i in issues), issues
    local2 = {"title": "Comparing geriatric assessment tools for predicting negative health outcomes in older adults",
              "year": "2025", "authors": "Abbadi A, Innocenti F"}
    assert any("year" in i for i in compare_citation(local2, pubmed))
    local3 = dict(local2, year="2026")
    assert compare_citation(local3, pubmed) == []


def test_compare_citation_title_test_measured_on_the_real_corpus():
    """The three cases that re-calibrated this check on 13 September 2026.

    Run over all 124 published artefacts, the old full-title recall test flagged
    five citations of which two were innocent -- a 40% false-positive rate, in
    the guard that is supposed to stop a composed title reaching the site. A
    checker crying wolf is worse than none, because it gets switched off. Each
    string below is verbatim from the corpus and its PubMed record.
    """
    from drive_sync import compare_citation

    # MUST NOT FIRE -- a subtitle shortened. The main clause is exact.
    assert compare_citation(
        {"title": "Telehome-Based Palliative Care in Nursing Practice: An "
                  "Integrative Review"},
        {"title": "Telehome-Based Palliative Care in Nursing Practice: An "
                  "Integrative Review of Care Delivery, Caregiver Involvement "
                  "and Service Coordination."}) == []

    # MUST NOT FIRE -- an acronym, expanded from the record itself.
    assert compare_citation(
        {"title": "Exercise-based rehabilitation for depressive symptoms, "
                  "anxiety and HRQoL in rheumatoid arthritis: systematic "
                  "review and meta-analysis"},
        {"title": "Effectiveness of exercise-based rehabilitation for "
                  "depressive symptoms, anxiety, and health-related quality of "
                  "life in adults with rheumatoid arthritis: A systematic "
                  "review and meta-analysis of randomized controlled "
                  "trials."}) == []

    # MUST FIRE -- the study's stated purpose swapped for a vaguer one. The old
    # test missed this: the shared ": a meta-analysis" tail propped its
    # full-title recall above the threshold.
    issues = compare_citation(
        {"title": "Clinical Frailty Scale and outcomes in elderly heart "
                  "failure: a meta-analysis"},
        {"title": "Clinical frailty scale for risk stratification in elderly "
                  "patients with heart failure: a meta-analysis."})
    assert any("title mismatch" in i for i in issues), issues

    # MUST NOT FIRE -- the RECORD is corrupt, not the citation. PubMed strips
    # italicised genus names, and a guard that fails a correct citation on the
    # strength of a mangled record teaches its reader to ignore it.
    assert compare_citation(
        {"title": "Ceftriaxone for methicillin-susceptible Staphylococcus "
                  "aureus bloodstream infections is associated with increased "
                  "short-term mortality: a systematic review and "
                  "meta-analysis"},
        {"title": "Ceftriaxone for methicillin-susceptiblebloodstream "
                  "infections is associated with increased short-term "
                  "mortality: a systematic review and meta-analysis."}) == []


def test_compare_citation_flags_the_wrong_journal():
    """The hole in this guard, found 13 September 2026.

    compare_citation has checked title, year and first author since 10 July and
    never looked at `container:` — parse_sources did not even extract it.
    Measured that day across all 124 published artefacts, SIX citations name the
    wrong journal, every one of them with the right PMID, the right DOI and the
    right first author. So every existing check passed them, and would pass an
    identical artefact today.

    The four cases below are the real ones, verbatim. A wrong journal is not
    cosmetic: it is the field a reader uses to judge weight before opening
    anything, so a general-medicine journal presented as the field's flagship
    silently inflates the evidence.
    """
    from drive_sync import compare_citation
    real = [
        ("International Journal of Chronic Obstructive Pulmonary Disease",
         "Sensors (Basel, Switzerland)", "Sensors (Basel)", "Stoustrup AL"),
        ("BMJ Supportive & Palliative Care",
         "European urology open science", "Eur Urol Open Sci", "Carpen TP"),
        ("Journal of Antimicrobial Chemotherapy",
         "Annals of medicine", "Ann Med", "Maraolo AE"),
        ("Age and Ageing",
         "Palliative medicine", "Palliat Med", "Manson J"),
    ]
    for cited, actual, abbrev, author in real:
        issues = compare_citation(
            {"title": "t", "authors": author, "container": cited},
            {"title": "t", "first_author": author,
             "journal": actual, "journal_abbrev": abbrev})
        assert any("journal" in i for i in issues), (cited, actual, issues)

    # And it must not fire on the legitimate variants, or it becomes noise and
    # stops being read — the failure that kept slot 1 broken for eleven days.
    fine = [
        ("Clinical Psychology", "The British journal of clinical psychology",
         "Br J Clin Psychol"),                       # restyled/shortened
        ("Geriatrics & Gerontology International",
         "Geriatrics & gerontology international", "Geriatr Gerontol Int"),
        ("Health Technol Assess",                    # cited as the abbreviation
         "Health technology assessment (Winchester, England)", "Health Technol Assess"),
    ]
    for cited, actual, abbrev in fine:
        issues = compare_citation(
            {"title": "t", "authors": "X Y", "container": cited},
            {"title": "t", "first_author": "X Y",
             "journal": actual, "journal_abbrev": abbrev})
        assert not any("journal" in i for i in issues), (cited, actual, issues)

    # A missing container is not a failure — policy sources have no journal.
    assert compare_citation(
        {"title": "t", "authors": "X Y"},
        {"title": "t", "first_author": "X Y", "journal": "Whatever"}) == []


def test_sources_reader_stops_at_the_next_top_level_key():
    """The boundary is the part of a parser nobody tests, and it bit twice.

    check_sources_reachable walked out of `sources:` and straight into `tags:`,
    whose `  - frailty` items match the list-item pattern and became source
    entries carrying no identifiers at all. A clean three-source signal
    therefore reported FOUR unreachable sources that do not exist, and the
    corpus-wide count read 26 when the true number is 7. The identical bug was
    in verify_citations.py's reader on the same day.

    It was caught only by opening the file the count pointed at — which is the
    standing rule here: measure the artefact, never trust the measurement.
    """
    from drive_sync import check_sources_reachable
    doc = (b'---\n'
           b'title: "X"\n'
           b'sources:\n'
           b'  - citation: "Lim KS. Advance care planning uptake. BMC Palliat Care. 2026."\n'
           b'    doi: "10.1186/s12904-026-02133-w"\n'
           b'    pmid: "42106761"\n'
           b'tags:\n'
           b'  - palliative-care\n'
           b'  - frailty\n'
           b'  - advance-care-planning\n'
           b'---\n\nBody.\n')
    assert check_sources_reachable("signal--x.md", doc) == [], \
        check_sources_reachable("signal--x.md", doc)

    # And it must still catch the real thing: a source with no identifier at all.
    bad = (b'---\nsources:\n'
           b'  - authors: "NHS England"\n'
           b'    title: "Frailty Pathways Best Practice Guide"\n'
           b'    url: ""\n'
           b'tags:\n  - frailty\n---\n\nBody.\n')
    hits = check_sources_reachable("signal--y.md", bad)
    assert len(hits) == 1 and "Frailty Pathways" in hits[0], hits


def test_parse_sources_extracts_container():
    """parse_sources must hand compare_citation the field it now checks.

    The journal check is inert if the parser drops `container:`, and that is
    exactly the state this file was in before today: a guard whose input never
    contained the thing it was about to test.
    """
    from drive_sync import parse_sources
    got = parse_sources('---\nsources:\n  - authors: "A B"\n    title: "T"\n'
                        '    container: "J Foo"\n    pmid: "1"\n---\n')
    assert got and got[0].get("container") == "J Foo", got


def test_parse_sources_extracts_pmid_entries():
    from drive_sync import parse_sources
    text = '''---
title: "X"
sources:
 - authors: "A B, C D"
   title: "Some title"
   year: 2026
   pmid: "12345678"
 - authors: "No Pmid"
   title: "Guidance doc"
   pmid: ""
---
body'''
    entries = parse_sources(text)
    assert len(entries) == 1 and entries[0]["pmid"] == "12345678" and entries[0]["year"] == "2026", entries


# --- citation integrity (the 7 Aug 2026 referencing loss) --------------------
# The synthesis and the August flagship both shipped with `sources: []` because
# the translator's own frontmatter templates used that as the worked example.
# Signals were unaffected (their template showed a populated entry), which is
# why the loss looked like a content problem rather than a routine bug.
# Run against the live archive when changing this: it must flag exactly those
# two files and clear the other 70, including the June batches that use the
# older pre-formatted `citation:` shape rather than structured fields.

def test_integrity_flags_aggregate_with_empty_sources():
    from drive_sync import check_citation_integrity
    doc = b'---\ntitle: "X"\nsources: []\n---\n\nA review found a 42% higher risk.\n'
    errs = check_citation_integrity("synthesis--2026-08-07-week.md", doc)
    assert len(errs) == 1 and "unreachable" in errs[0], errs
    # the flagship path is the one that matters most — it is the landing hero
    assert check_citation_integrity("monthly--2026-08-theme.md", doc), "monthly must be checked too"


def test_integrity_covers_signals_with_no_crossref_escape():
    """A Signal reports one study, so it must carry its citation outright — a
    cross-reference link is not a substitute the way it is for an aggregate.
    Signals survived August only because their template happened to show a
    populated entry; the guard covers them so that stops being luck."""
    from drive_sync import check_citation_integrity
    empty = b'---\ntitle: "X"\nsources: []\n---\n\nbody\n'
    errs = check_citation_integrity("signal--2026-08-07-thing.md", empty)
    assert errs and "MUST carry its citation" in errs[0], errs
    crossref = (b'---\ntitle: "X"\nsources: []\n---\n\nsee '
                b'[other](/signal/2026-07-31-germot-case-finding-rule-frailty/)\n')
    assert check_citation_integrity("signal--2026-08-07-thing.md", crossref), \
        "a cross-reference must NOT excuse a Signal from carrying its own source"
    good = (b'---\ntitle: "X"\nsources:\n  - authors: "Dean S"\n    pmid: "42386304"\n'
            b'---\n\nbody\n')
    assert check_citation_integrity("signal--2026-08-07-thing.md", good) == []


def test_integrity_accepts_block_list_sources():
    """A populated YAML block list leaves the `sources:` line itself empty —
    reading only that line is exactly how a naive guard would false-positive on
    every correctly-referenced synthesis in the archive."""
    from drive_sync import check_citation_integrity
    doc = (b'---\ntitle: "X"\nsources:\n  - authors: "Dean S"\n    title: "SDEC outcomes"\n'
           b'    pmid: "42386304"\n---\n\nbody\n')
    assert check_citation_integrity("synthesis--2026-08-07-week.md", doc) == []


def test_integrity_accepts_crossreferences_instead_of_sources():
    """The Monthly may satisfy reachability by linking the site artefact that
    carries the citation (translator v3.6+ cross-reference discipline)."""
    from drive_sync import check_citation_integrity
    doc = (b'---\ntitle: "X"\nsources: []\n---\n\nAs found in '
           b'[this week\'s signal](/signal/2026-07-31-germot-case-finding-rule-frailty/).\n')
    assert check_citation_integrity("monthly--2026-08-theme.md", doc) == []


def test_integrity_accepts_inline_list_sources():
    from drive_sync import check_citation_integrity
    doc = b'---\ntitle: "X"\nsources: [{title: "A"}]\n---\n\nbody\n'
    assert check_citation_integrity("synthesis--2026-08-07-week.md", doc) == []


def test_integrity_flags_missing_sources_key_entirely():
    from drive_sync import check_citation_integrity
    doc = b'---\ntitle: "X"\ndate: 2026-08-07\n---\n\nA study found something.\n'
    assert check_citation_integrity("synthesis--2026-08-07-week.md", doc), "absent key is as bad as empty"


def test_full_patterns_from_drive_is_ignored_not_guarded():
    """A full patterns.json in Drive is ignored outright (10 Aug 2026).

    Four legacy copies frozen in July turned the 08:10 sync red every single
    morning: once patterns-delta-2026-08 advanced the register to generated
    2026-08-08, each of them would have dropped VF-P12 and two August history
    entries, so the monotonic guard correctly HELD them — and kept holding them,
    daily, forever. A sync that is red every morning is one nobody reads.

    Denylisting the four IDs treated a class as four instances. The filename
    rule means nothing dropped in that folder can regress the register, with no
    list to maintain. The guards themselves are NOT relaxed — this asserts both
    halves: the sync ignores the file, and validate_patterns_full still rejects
    a regressing one for the hand-reviewed PR path.
    """
    import inspect
    from drive_sync import main, validate_patterns_full
    src = inspect.getsource(main)
    assert "ignoring {name}" in src, "the sync must ignore a full patterns.json outright"
    assert "validate_patterns_full(data, PATTERNS_PATH)" not in src, \
        "the Drive path must not consume full-file replacements any more"
    # the guard itself is untouched: a regressing file is still rejected
    with tempfile.TemporaryDirectory() as d:
        cur = write_current(Path(d))
        inc = json.loads(json.dumps(CURRENT))
        inc["patterns"] = [p for p in inc["patterns"] if p["id"] != "VF-P2"]
        errors, _ = validate_patterns_full(as_bytes(inc), cur)
        assert any("VF-P2 DISAPPEARED" in e for e in errors), errors


def test_tiny_artefact_upload_is_caught_by_size_not_by_content():
    """The 24-byte placeholder from the 6 Sep 2026 flagship run is the fixture.

    That stub was the third instance of a routine's Drive upload landing a
    placeholder instead of the artefact (August edition, evidence-watch Issue
    19, the 6 Sep monthly). Each was caught in-run by the routine itself, which
    is luck dressed as process: a 24-byte file is a VALID file, so the sync's
    other guards have nothing to bite on. This asserts that specifically —
    check_citation_integrity passes the stub, and only the size floor stops it.
    """
    from drive_sync import check_artefact_size, check_citation_integrity, MIN_ARTEFACT_BYTES

    stub = b"# Monthly Review\n\nTBC\n"  # 22 bytes, the shape of the real one
    assert len(stub) < MIN_ARTEFACT_BYTES

    # The point of the thread: the existing guards do NOT catch this.
    assert check_citation_integrity("monthly--2026-09-virtual-wards.md", stub) == [], \
        "if this starts failing, the size floor may be redundant — re-check before removing it"

    # A monthly is the landing hero, so a stub there fails the run red.
    warns, errors = check_artefact_size("monthly--2026-09-virtual-wards.md", stub)
    assert not warns and len(errors) == 1, (warns, errors)
    assert "22 bytes" in errors[0] and "Fix the Drive original" in errors[0], errors

    # A signal or synthesis warns instead: losing a whole week to a hard
    # failure is worse than publishing one flagged file.
    for nm in ("signal--2026-09-04-x.md", "synthesis--2026-09-04-week-ending.md"):
        warns, errors = check_artefact_size(nm, stub)
        assert len(warns) == 1 and not errors, (nm, warns, errors)

    # The floor sits below every artefact that has actually been published —
    # smallest real signal to date is 1,384 bytes.
    real = b"x" * 1384
    assert check_artefact_size("signal--2026-08-28-opioid-safety.md", real) == ([], [])
    assert check_artefact_size("monthly--2026-09-virtual-wards.md", real) == ([], [])

    # Unrouted names are none of this guard's business.
    assert check_artefact_size("patterns-delta-2026-09.json", b"{}") == ([], [])


def test_size_guard_is_wired_into_the_sync_loop():
    """A guard nobody calls is decoration. Assert main() actually routes both
    halves — the warning list and the red-failing error list."""
    import inspect
    from drive_sync import main
    src = inspect.getsource(main)
    assert "check_artefact_size(name, data)" in src, "the size guard is not called"
    assert "integrity_errors.extend(size_errors)" in src, \
        "a stub monthly must reach the red-failing path, not the warnings block"


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted({k: v for k, v in globals().items() if k.startswith("test_")}.items()):
        try:
            fn()
            print(f"  ok    {name}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL  {name}: {e}")
    print(f"\n{'ALL PASS' if not failures else f'{failures} FAILURE(S)'}")
    sys.exit(1 if failures else 0)
