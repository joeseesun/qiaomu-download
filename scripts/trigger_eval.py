#!/usr/bin/env python3
"""Evaluate qiaomu-download trigger fixtures."""

import argparse
import json
import re
from pathlib import Path

URL_RE = re.compile(r"https://[^\s<>\]\[)]+", re.I)
PLATFORMS = ("youtube", "youtu.be", "bilibili", "b站", "b23.tv", "x.com", "twitter", "vimeo", "tiktok", "douyin", "抖音", "xiaohongshu", "小红书", "instagram", "facebook", "twitch", "reddit", "weibo", "微博", "acfun", "视频", "video")
ACTIONS = ("下载", "保存", "存下来", "mp3", "音频", "字幕", "download", "save this", "update yt-dlp")
NEGATIVE = ("上传", "剪辑", "总结", "分析", "电子书", "weixin.qq.com/sph", "视频号", "pdf", "图片", "image", "网页")
DESCRIPTION_TERMS = ("https url", "youtube", "bilibili", "x/twitter", "douyin", "tiktok", "xiaohongshu", "yt-dlp", "下载这个", "audio", "字幕", "qiaomu-wx-video")


def predicts(text: str) -> bool:
    value = text.lower()
    has_target = bool(URL_RE.search(value)) or any(x in value for x in PLATFORMS)
    return has_target and any(x in value for x in ACTIONS) and not any(x in value for x in NEGATIVE)


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
