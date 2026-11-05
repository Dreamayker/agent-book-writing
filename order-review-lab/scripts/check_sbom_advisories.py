"""Cross-check Java SBOM versions against OSV's API, with a vulnerable control."""

import datetime
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SENTINEL = "pkg:maven/org.apache.commons/commons-compress@1.24.0"
SENTINEL_ADVISORY = "GHSA-4265-ccf5-phj5"


def assess(components, results, assessments, today, source_sha256=None):
    """Return unexpected advisories; exceptions bind ID, package and version."""
    if len(results) != len(components) + 1:
        raise ValueError("OSV response length does not match queries")
    if SENTINEL_ADVISORY not in {v["id"] for v in results[-1].get("vulns", [])}:
        raise ValueError("OSV vulnerable control was not detected")
    unexpected = []
    for component, result in zip(components, results[:-1]):
        for vuln in result.get("vulns", []):
            matching = [
                a for a in assessments
                if a["id"] == vuln["id"] and a["purl"] == component["purl"]
                and datetime.date.fromisoformat(a["review_by"]) >= today
                and a.get("status") == "not_affected" and a.get("reason")
                and (source_sha256 is None or a.get("source_sha256") == source_sha256)
            ]
            if not matching:
                unexpected.append({"purl": component["purl"], "id": vuln["id"]})
    return unexpected


def main():
    components = [
        c for c in json.loads((ROOT / "target/bom.json").read_text())["components"]
        if c.get("purl", "").startswith("pkg:maven/")
        and not c["purl"].startswith("pkg:maven/com.xinghe/")
    ]
    if not components:
        raise ValueError("SBOM contains no external Maven dependencies")
    assessments = json.loads((ROOT / "docs/dependency-assessments.json").read_text())
    source_hash = hashlib.sha256()
    for path in sorted(ROOT.glob("order-*/src/main/**/*")):
        if path.is_file():
            source_hash.update(str(path.relative_to(ROOT)).encode() + b"\0")
            source_hash.update(path.read_bytes() + b"\0")
    source_sha256 = source_hash.hexdigest()
    queries = [{"package": {"purl": c["purl"]}} for c in components]
    queries.append({"package": {"purl": SENTINEL}})
    request = urllib.request.Request(
        "https://api.osv.dev/v1/querybatch",
        data=json.dumps({"queries": queries}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        raw = json.load(response)
    today = datetime.datetime.now(datetime.timezone.utc).date()
    report = {"checked_at": today.isoformat(), "queries": queries,
              "raw_response": raw, "assessments": assessments,
              "source_sha256": source_sha256}
    output = ROOT / "target/osv-api-results.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    unexpected = assess(components, raw["results"], assessments, today, source_sha256)
    if unexpected:
        print(json.dumps(unexpected, indent=2), file=sys.stderr)
        return 1
    print(f"OSV API checked {len(components)} Java packages; vulnerable control detected; "
          "all returned advisories have current, exact-version applicability assessments.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
