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
