#!/usr/bin/env python3
"""Prepare and verify teaching patches in a detached worktree, preserving raw evidence."""

import argparse
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import urllib.request
import uuid
import xml.etree.ElementTree as ET

from case_catalog import CASES

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parent


def git(*args, cwd=REPO):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n" if not isinstance(value, str) else value)


def command(case):
    common = ["./mvnw", "-B", "-ntp", "-Dfmt.skip=true", "-Dsurefire.failIfNoSpecifiedTests=false"]
    if case["kind"] == "unit":
        return common + ["-pl", "order-core", "-am", "-Dtest=PricingTest#"+case["test"], "test"]
    if case["kind"] == "integration":
        return common + ["-Dit.test=OrderIT#"+case["test"], "verify"]
    if case["kind"] == "static":
        return ["uvx", "semgrep", "--quiet", "--config", "policies/semgrep.yml", "--json", "--error", "order-core/src/main/java"]
    return common + ["-pl", "order-core", "dependency:tree", "-Dincludes=org.apache.logging.log4j:log4j-core"]


def prepare():
    revision = git("rev-parse", "HEAD")
    entries = []
    for case in CASES:
        file = PROJECT / case["path"]
        before = file.read_text()
        after = before
        for old, new in [(case["old"], case["new"]), *case.get("extra", [])]:
            if after.count(old) != 1:
                raise ValueError(f"{case['id']} mutation anchor changed: {old!r}")
            after = after.replace(old, new, 1)
        relative = "order-review-lab/"+case["path"]
        directory = PROJECT/"book-assets"/case["id"]
        patch = "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), "a/"+relative, "b/"+relative))
        fixed = "".join(difflib.unified_diff(after.splitlines(True), before.splitlines(True), "a/"+relative, "b/"+relative))
        write(directory/"buggy.patch", patch); write(directory/"fixed.patch", fixed)
        line = after[:after.index(case["new"])].count("\n")+1
        root = case["id"]+":"+(case["finding"] or "clean")
        findings = [] if not case["finding"] else [{"id":case["finding"], "root_cause_id":root,
            "file":case["path"], "line_start":line, "line_end":line+max(3,case["new"].count("\n")),
            "severity":"must_fix", "acceptable_fix":"Restore business contract; validate the same regression test"}]
        write(directory/"oracle.yaml", {"case_id":case["id"], "findings":findings})
        write(directory/"requirement.md", f"# {case['id']} {case['title']}\n\n依据 `order-rules-v1`。验收测试：`{case['test']}`。\n\n此补丁是教学构造，正确基线以源码与集成测试为准。评审时不得读取 Oracle 或修复补丁。\n")
        write(directory/"case.yaml", {"case_id":case["id"], "baseline_sha":revision,
            "source_sha256":hashlib.sha256(before.encode()).hexdigest(), "buggy_patch_sha256":hashlib.sha256(patch.encode()).hexdigest(),
            "command":command(case), "kind":case["kind"], "test":case["test"], "status":"prepared"})
        entries.append({"id":case["id"], "directory":"book-assets/"+case["id"], "changed_paths":[case["path"]],
                        "labels":case["labels"], "code_revision":revision+":"+hashlib.sha256(patch.encode()).hexdigest()})
    write(PROJECT/"evaluation/cases.yaml", {"version":1,"project_root":".","policy":"policies/risk-rules.yaml","cases":entries})


def capture(cmd, cwd, output):
    started = time.monotonic()
    with output.open("w") as stream:
        try:
            result = subprocess.run(cmd, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT, timeout=600, check=False)
            return {"command":cmd,"exit_code":result.returncode,"seconds":round(time.monotonic()-started,3)}
        except subprocess.TimeoutExpired:
            return {"command":cmd,"exit_code":124,"status":"timeout","seconds":600}


def assertion_failed(work, case):
    paths = list(work.glob("**/target/*-reports/TEST-*.xml"))
    for path in paths:
        for test in ET.parse(path).getroot().findall("testcase"):
            if test.attrib["name"] == case["test"] and test.find("failure") is not None:
                return True
    return False


def verify(selected):
    manifest = json.loads((PROJECT/"evaluation/cases.yaml").read_text())
    entries = {case["id"]:case for case in manifest["cases"]}
    baseline = json.loads((PROJECT/"book-assets"/selected[0]["id"]/"case.yaml").read_text())["baseline_sha"]
    scratch = Path(tempfile.mkdtemp(prefix="order-cases-"))
    worktree = scratch/"repo"
    subprocess.run(["git","worktree","add","--detach",str(worktree),baseline],cwd=REPO,check=True)
    try:
        for case in selected:
            subprocess.run(["git","checkout","--detach",baseline],cwd=worktree,check=True,stdout=subprocess.DEVNULL)
            directory = PROJECT/entries[case["id"]]["directory"]
            raw = directory/"tool-evidence/raw"; raw.mkdir(parents=True,exist_ok=True)
            work = worktree/"order-review-lab"
            subprocess.run(["git","apply","--check",str(directory/"buggy.patch")],cwd=worktree,check=True)
            subprocess.run(["git","apply",str(directory/"buggy.patch")],cwd=worktree,check=True)
            buggy_diff = git("diff", "--binary", cwd=worktree)
            buggy_sha = hashlib.sha256(buggy_diff.encode()).hexdigest()
            subprocess.run(["git","add","-u"],cwd=worktree,check=True)
            subprocess.run(["git","commit","-qm",case["id"]+" teaching mutation"],cwd=worktree,check=True)
            changed_sha=git("rev-parse","HEAD",cwd=worktree)
            entries[case["id"]]["code_revision"]=changed_sha
            subprocess.run(["git","update-ref","refs/heads/case/order/"+case["id"],changed_sha],cwd=REPO,check=True)
            write(raw/"buggy-source.txt",(work/case["path"]).read_text())
            observed = {"case_id":case["id"],"baseline_sha":baseline,"change_sha":changed_sha,"buggy_diff_sha256":buggy_sha,"kind":"executed-teaching-case","runs":[]}
            run = capture(command(case),work,raw/"buggy.txt"); observed["runs"].append(run)
            if case["kind"] == "dependency":
                request=urllib.request.Request("https://api.osv.dev/v1/query",data=json.dumps({"package":{"ecosystem":"Maven","name":"org.apache.logging.log4j:log4j-core"},"version":"2.14.1"}).encode(),headers={"Content-Type":"application/json"})
                response=json.loads(urllib.request.urlopen(request,timeout=30).read())
                write(raw/"osv.json",response)
                assert run["exit_code"]==0 and "log4j-core:jar:2.14.1" in (raw/"buggy.txt").read_text()
                assert any("CVE-2021-44228" in vuln.get("aliases",[]) or vuln["id"]=="CVE-2021-44228" for vuln in response.get("vulns",[]))
            elif case["kind"] == "static":
                data=json.loads((raw/"buggy.txt").read_text())
                assert run["exit_code"]==1 and any(item["check_id"].endswith(case["test"]) for item in data["results"])
            elif case["finding"]:
                assert run["exit_code"]!=0 and assertion_failed(work,case), f"{case['id']}: expected business assertion was not observed"
            else:
                assert run["exit_code"]==0
            subprocess.run(["git","apply",str(directory/"fixed.patch")],cwd=worktree,check=True)
            assert not git("diff",baseline,cwd=worktree), "Fix must restore exact baseline"
            subprocess.run(["git","add","-u"],cwd=worktree,check=True)
            subprocess.run(["git","commit","-qm",case["id"]+" restore correct baseline"],cwd=worktree,check=True)
            fixed_sha=git("rev-parse","HEAD",cwd=worktree)
            subprocess.run(["git","update-ref","refs/heads/fix/order/"+case["id"],fixed_sha],cwd=REPO,check=True)
            observed["fix_sha"]=fixed_sha
            fixed=capture(command(case),work,raw/"fixed.txt"); observed["runs"].append(fixed)
            assert fixed["exit_code"]==0, f"{case['id']}: corrected baseline failed"
            observed["status"]="verified"
            write(directory/"tool-evidence/observed.yaml",observed)
            evidence_files=[]
            for file in sorted(raw.iterdir()):
                if file.name=="fixed.txt": continue
                evidence_files.append({"path":str(file.relative_to(PROJECT)),"sha256":hashlib.sha256(file.read_bytes()).hexdigest()})
            write(directory/"tool-evidence/manifest.json",{"run_id":str(uuid.uuid4()),"case_id":case["id"],"code_revision":entries[case["id"]]["code_revision"],"files":evidence_files})
            expected=json.loads((directory/"oracle.yaml").read_text())["findings"]
            agents={name:[] for name in ["general-review","correctness","test","security","impact"]}
            if expected:
                item=expected[0]
                for role in ["correctness","test"]:
                    agents[role]=[{"schema_version":2,"finding_id":case["finding"],"root_cause_id":item["root_cause_id"],
                        "invariant":"order-rules-v1","source":role,"category":"correctness","severity":"must_fix","confidence":0.95,
                        "file":item["file"],"line_start":item["line_start"],"claim":case["title"],
                        "evidence":[{"type":"dependency_scan" if case["kind"]=="dependency" else "static_analysis" if case["kind"]=="static" else "test","ref":str((raw/("osv.json" if case["kind"]=="dependency" else "buggy.txt")).relative_to(PROJECT))}],
                        "suggested_fix":"Restore the frozen business contract and rerun the regression", "blocking":True,"needs_human":True}]
            write(directory/"runs/recorded-agents.json",agents)
            write(directory/"human-verdict.yaml",{"case_id":case["id"],"status":"pending-human-review","required":bool(expected),"note":"No human approval has been fabricated; recorded fixture only."})
            metadata=json.loads((directory/"case.yaml").read_text())
            metadata.update(change_sha=changed_sha,fix_sha=fixed_sha,status="verified")
            write(directory/"case.yaml",metadata)
            write(PROJECT/"evaluation/cases.yaml",manifest)
            print(case["id"],"verified",flush=True)
    finally:
        subprocess.run(["git","worktree","remove","--force",str(worktree)],cwd=REPO,check=True)
        shutil.rmtree(scratch)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=["prepare","verify"])
    parser.add_argument("--case",action="append",dest="cases")
    args=parser.parse_args()
    if args.action=="prepare": prepare()
    else:
        chosen=[case for case in CASES if not args.cases or case["id"] in args.cases]
        if not chosen: parser.error("No matching case")
        verify(chosen)
