#!/usr/bin/env python3
"""Check line coverage from actual JaCoCo XML, including MySQL integration runs."""

import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(__file__).resolve().parents[1]
for report, threshold in [
    ("order-core/target/site/jacoco/jacoco.xml", 0.90),
    ("order-test/target/site/jacoco-aggregate/jacoco.xml", 0.80),
]:
    counter = next(
        c
        for c in ET.parse(root / report).getroot().findall("counter")
        if c.attrib["type"] == "LINE"
    )
    covered, missed = int(counter.attrib["covered"]), int(counter.attrib["missed"])
    ratio = covered / (covered + missed)
    print(
        f"{report}: {covered}/{covered + missed} = {ratio:.2%}; required {threshold:.0%}"
    )
    if ratio < threshold:
        raise SystemExit(1)
