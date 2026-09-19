#!/usr/bin/env python3
"""Evaluate qiaomu-download trigger fixtures."""

import argparse
import json
from pathlib import Path

PLATFORMS = ("youtube", "youtu.be", "bilibili", "b站", "b23.tv", "x.com", "twitter", "vimeo", "tiktok", "视频", "video")
ACTIONS = ("下载", "保存", "mp3", "音频", "字幕", "download", "update yt-dlp")
NEGATIVE = ("上传", "剪辑", "总结", "分析", "电子书", "weixin.qq.com/sph", "视频号")
DESCRIPTION_TERMS = ("youtube", "bilibili", "x/twitter", "yt-dlp", "下载", "audio", "字幕", "qiaomu-wx-video")


def predicts(text: str) -> bool:
    value = text.lower()
    return any(x in value for x in PLATFORMS) and any(x in value for x in ACTIONS) and not any(x in value for x in NEGATIVE)


def description(root: Path) -> str:
    text = (root / "SKILL.md").read_text(encoding="utf-8")
    return text.split("---", 2)[1].lower() if text.startswith("---") else ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output")
    args = parser.parse_args()
    root = Path(args.skill_dir).resolve()
    fixtures = json.loads((root / "evals/trigger_cases.json").read_text(encoding="utf-8"))
    results = []
    for bucket, expected in (("should_trigger", True), ("should_not_trigger", False), ("near_neighbor", False)):
        for case in fixtures[bucket]:
            text = case["text"]
            actual = predicts(text)
            results.append({"bucket": bucket, "text": text, "expected": expected, "predicted": actual, "passed": actual == expected})
    desc = description(root)
    missing = [term for term in DESCRIPTION_TERMS if term not in desc]
    total = len(results)
    passed = sum(r["passed"] for r in results)
    payload = {"ok": passed == total and not missing, "total": total, "passed": passed,
               "summary": {"total": total, "passed": passed}, "missing_description_terms": missing,
               "results": results}
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        output = root / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    if not payload["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
