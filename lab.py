#!/usr/bin/env python3
"""Compare search hypotheses on synthetic inputs; does not run REA or a target app."""

import argparse
import json
import sys
import unicodedata
import unittest


def literal(title, query):
    return query in title


def lower(title, query):
    return query.lower() in title.lower()


def folded(title, query):
    normalize = lambda s: unicodedata.normalize("NFKC", s).casefold()
    return normalize(query) in normalize(title)


HYPOTHESES = {"literal": literal, "lower": lower, "nfkc_casefold": folded}
CASES = [
    {"id": "control", "title": "alpha notes", "query": "alpha"},
    {"id": "case", "title": "Alpha notes", "query": "alpha"},
    {"id": "sharp_s", "title": "Straße", "query": "STRASSE"},
    {"id": "composed", "title": "caf\u00e9", "query": "cafe\u0301"},
    {"id": "fullwidth", "title": "\uff23\uff30\uff35 manual", "query": "CPU"},
    {"id": "accent", "title": "caf\u00e9", "query": "cafe"},
    {"id": "space", "title": "alpha  notes", "query": "alpha notes"},
    {"id": "empty", "title": "alpha notes", "query": ""},
]


def validate(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError("Expected a non-empty JSON array of cases")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Each case must be an object")
        if any(not isinstance(row.get(k), str) for k in ("id", "title", "query")):
            raise ValueError("Each case needs string id, title, query")
        if not row["id"] or row["id"] in seen:
            raise ValueError("Case IDs must be non-empty and unique")
        seen.add(row["id"])
        if "observed" in row and type(row["observed"]) is not bool:
            raise ValueError("observed must be true/false, or omitted if unknown")
    return rows


def compare(rows):
    rows = validate(rows)
    results = []
    remaining = set(HYPOTHESES)
    observed_count = 0
    for row in rows:
        predictions = {name: fn(row["title"], row["query"]) for name, fn in HYPOTHESES.items()}
        observed = row.get("observed")
        if observed is not None:
            observed_count += 1
            remaining &= {name for name, value in predictions.items() if value == observed}
        results.append({**row, "observed": observed, "predictions": predictions})
    return {
        "scope": "Synthetic hypothesis comparison; no REA engine or application was run",
        "python": sys.version.split()[0],
        "unicode_version": unicodedata.unidata_version,
        "observed_cases": observed_count,
        "not_falsified": sorted(remaining),
        "limitation": "Agreement on supplied cases does not prove an implementation or general equivalence",
        "cases": results,
    }


class Tests(unittest.TestCase):
    def test_discriminating_cases(self):
        predictions = {row["id"]: row["predictions"] for row in compare(CASES)["cases"]}
        self.assertEqual(predictions["case"], {"literal": False, "lower": True, "nfkc_casefold": True})
        self.assertEqual(predictions["sharp_s"], {"literal": False, "lower": False, "nfkc_casefold": True})
        self.assertTrue(predictions["composed"]["nfkc_casefold"])
        self.assertTrue(predictions["fullwidth"]["nfkc_casefold"])
        self.assertFalse(any(predictions["accent"].values()))
        self.assertFalse(any(predictions["space"].values()))
        self.assertTrue(all(predictions["empty"].values()))

    def test_unknown_is_not_false(self):
        report = compare(CASES)
        self.assertEqual(report["observed_cases"], 0)
        self.assertEqual(report["not_falsified"], sorted(HYPOTHESES))
        self.assertIsNone(report["cases"][0]["observed"])

    def test_single_observation_does_not_prove_a_winner(self):
        report = compare([{**CASES[1], "observed": True}])
        self.assertEqual(report["not_falsified"], ["lower", "nfkc_casefold"])

    def test_conflicting_observations_can_falsify_all(self):
        report = compare([{**CASES[0], "observed": False}])
        self.assertEqual(report["not_falsified"], [])

    def test_reject_ambiguous_inputs(self):
        for bad in ([], {}, [CASES[0], CASES[0]], [{**CASES[0], "observed": "false"}],
                    [{**CASES[0], "observed": 0}], [{**CASES[0], "observed": None}],
                    [{**CASES[0], "title": None}], [{**CASES[0], "id": ""}]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                compare(bad)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="JSON case array; omitted = synthetic demo")
    parser.add_argument("--self-test", action="store_true", help="Run the included local tests")
    args = parser.parse_args()
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    try:
        if args.input:
            with open(args.input, encoding="utf-8") as handle:
                rows = json.load(handle)
        else:
            rows = CASES
        print(json.dumps(compare(rows), ensure_ascii=False, indent=2))
    except (ValueError, OSError) as error:
        print(f"Input error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
