#!/usr/bin/env python3
"""Validate qiaomu-download package and governed safety contract."""

import argparse
import json
import re
from pathlib import Path

REQUIRED = [
    "SKILL.md", "README.md", "LICENSE", "manifest.json", "agents/interface.yaml",
    "references/workflow.md", "references/security.md", "references/platforms.md",
    "evals/trigger_cases.json", "evals/output/cases.json", "reports/prior-art-candidates.json",
    "reports/prior-art-research.md", "reports/output_quality_scorecard.md", "reports/trust-report.md",
    "scripts/download.py", "scripts/test_download.py", "scripts/trigger_eval.py",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_dir", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.skill_dir).resolve()
    failures = [f"missing: {path}" for path in REQUIRED if not (root / path).is_file()]
    skill = (root / "SKILL.md").read_text(encoding="utf-8") if (root / "SKILL.md").exists() else ""
    script = (root / "scripts/download.py").read_text(encoding="utf-8") if (root / "scripts/download.py").exists() else ""
    if not skill.startswith("---\n") or "name: qiaomu-download" not in skill:
        failures.append("invalid SKILL.md frontmatter")
    for term in ("Trust boundary", "Rollback boundary", "qiaomu-wx-video", "不得使用 Computer Use"):
        if term not in skill:
            failures.append(f"SKILL.md missing contract: {term}")
    for term in ("--no-playlist", "--no-overwrites", "--cookies-from-browser", "ffprobe",
                 "YT_DLP_RELEASE_API", "doctor", "download_lock", "normalize_url"):
        if term not in script:
            failures.append(f"download.py missing safety term: {term}")
    if re.search(r"(?:API_KEY|TOKEN|COOKIE)\s*=\s*['\"][^'\"]+['\"]", script):
        failures.append("hard-coded credential-like value")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8")) if (root / "manifest.json").exists() else {}
    if manifest.get("name") != "qiaomu-download" or manifest.get("version") != "1.0.0":
        failures.append("manifest identity mismatch")
    artifacts = [str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()
                 and "__pycache__" not in p.parts and p.suffix in {".pyc", ".part", ".ytdl"}]
    if artifacts:
        failures.append(f"generated artifacts present: {artifacts}")
    print(json.dumps({"ok": not failures, "root": str(root), "failures": failures}, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
