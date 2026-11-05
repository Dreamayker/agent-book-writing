import datetime
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "sbom_check", Path(__file__).parents[1] / "check_sbom_advisories.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AdvisoryGateTests(unittest.TestCase):
    def test_empty_or_partial_backend_cannot_pass(self):
        with self.assertRaises(ValueError):
            module.assess([], [{}], [], datetime.date(2026, 11, 5))
        with self.assertRaises(ValueError):
            module.assess([], [], [], datetime.date(2026, 11, 5))

    def test_expired_or_different_version_assessment_does_not_hide_vulnerability(self):
        component = {"purl": "pkg:maven/example/lib@1.0"}
        results = [{"vulns": [{"id": "GHSA-example"}]},
                   {"vulns": [{"id": module.SENTINEL_ADVISORY}]}]
        assessment = {"id": "GHSA-example", "purl": component["purl"],
                      "status": "not_affected", "reason": "unreachable feature",
                      "review_by": "2026-11-04"}
        today = datetime.date(2026, 11, 5)
        self.assertTrue(module.assess([component], results, [assessment], today))
        assessment["review_by"] = "2026-12-05"
        assessment["purl"] = "pkg:maven/example/lib@2.0"
        self.assertTrue(module.assess([component], results, [assessment], today))
        assessment["purl"] = component["purl"]
        self.assertEqual(module.assess([component], results, [assessment], today), [])
        assessment["source_sha256"] = "old-source"
        self.assertTrue(module.assess([component], results, [assessment], today, "new-source"))


if __name__ == "__main__":
    unittest.main()
