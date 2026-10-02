"""Run with: python -m unittest discover -s tests -v"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import yaml  # noqa: E402

import canary  # noqa: E402
import validate  # noqa: E402,F401  (import must succeed)
from sgcards_lib import card_files, load_sources, load_yaml, method_for  # noqa: E402


def run_validate(cards_dir=None, extra=()):
    cmd = [sys.executable, str(ROOT / "scripts" / "validate.py"), "--json", *extra]
    if cards_dir:
        cmd += ["--cards-dir", str(cards_dir)]
    out = subprocess.run(cmd, capture_output=True, text=True)
    return out.returncode, json.loads(out.stdout)


class TestData(unittest.TestCase):
    def test_repo_validates(self):
        rc, res = run_validate()
        self.assertEqual(rc, 0, res["errors"])

    def test_canary(self):
        self.assertEqual(canary.run(), [])

    def test_fetch_rules(self):
        s = load_sources()
        self.assertEqual(method_for("https://www.maybank2u.com.sg/en/x.page", s), "manual")
        self.assertEqual(method_for("https://www.dbs.com.sg/personal/cards/credit-cards/vantage", s), "headless")
        self.assertEqual(method_for("https://www.uob.com.sg/x", s), "static")


class TestValidatorRejects(unittest.TestCase):
    """A number without a quote, or an expired pending change, must fail the build."""

    def _mutated(self, mutate):
        d = Path(tempfile.mkdtemp())
        src = card_files()[0]
        doc = load_yaml(src)
        mutate(doc)
        (d / src.name).write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))
        return d

    def test_number_without_quote_fails(self):
        def m(doc):
            f = doc["facts"]["fees"]["annual_fee_sgd"]
            f.clear()
            f.update({"value": 123.45, "source_url": "https://example.invalid", "last_verified": "2026-10-01",
                      "source_type": "issuer"})
        rc, _ = run_validate(self._mutated(m))
        self.assertNotEqual(rc, 0)

    def test_guessed_number_without_source_fails(self):
        def m(doc):
            doc["facts"]["min_income_sgd"] = {"value": 30000}
        rc, _ = run_validate(self._mutated(m))
        self.assertNotEqual(rc, 0)

    def test_expired_pending_change_fails(self):
        def m(doc):
            pc = copy.deepcopy(load_yaml(ROOT / "data/cards/dbs-vantage.yaml")["pending_changes"][0])
            pc["effective_date"] = "2026-01-01"
            doc["pending_changes"] = [pc]
        rc, _ = run_validate(self._mutated(m))
        self.assertNotEqual(rc, 0)


class TestScan(unittest.TestCase):
    def test_repo_scan_clean(self):
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "scan_repo.py")], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout)


class TestEvalSet(unittest.TestCase):
    def test_eval_set_shape(self):
        ev = yaml.safe_load((ROOT / "tests" / "eval_set.yaml").read_text())
        ids = set()
        for q in ev["cases"]:
            for k in ("id", "question", "expected", "source_url", "category"):
                self.assertIn(k, q, q.get("id"))
            self.assertNotIn(q["id"], ids)
            ids.add(q["id"])
        self.assertGreaterEqual(len(ev["cases"]), 45)


if __name__ == "__main__":
    unittest.main()
