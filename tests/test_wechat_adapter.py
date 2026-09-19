#!/usr/bin/env python3
"""Unit tests for the embedded WeChat Channels dispatcher."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "wechat_adapter.py"
SPEC = importlib.util.spec_from_file_location("qiaomu_wechat_adapter", MODULE_PATH)
assert SPEC and SPEC.loader
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)


class WeChatAdapterTests(unittest.TestCase):
    def test_doctor_finds_all_embedded_components(self) -> None:
        result = adapter.doctor()
        self.assertTrue(result["ok"])
        self.assertEqual(result["ui_automation"], "forbidden")

    def test_no_connection_requires_setup_without_online_consent(self) -> None:
        check = {"ok": True, "local_api_2022_listening": False}
        with tempfile.TemporaryDirectory() as temp, patch.object(adapter, "preflight", return_value=check):
            result = adapter.download(
                "https://weixin.qq.com/sph/abc", Path(temp), "never", 0, 30, False
            )
        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "wechat_setup_required")
        self.assertTrue(result["online_resolver_requires_explicit_share_url_consent"])
        self.assertFalse(result["ui_automation_used"])

    def test_explicit_online_consent_uses_embedded_resolver(self) -> None:
        check = {"ok": True, "local_api_2022_listening": False}
        expected = {"ok": True, "adapter": "embedded-wechat-online", "files": [{"path": "/tmp/a.mp4"}]}
        with tempfile.TemporaryDirectory() as temp, patch.object(adapter, "preflight", return_value=check), patch.object(
            adapter, "try_online", return_value=expected
        ) as online:
            result = adapter.download(
                "https://weixin.qq.com/sph/abc", Path(temp), "allowed", 0, 30, False
            )
        self.assertEqual(result, expected)
        online.assert_called_once()

    def test_local_manual_action_is_returned_without_ui_automation(self) -> None:
        check = {"ok": True, "local_api_2022_listening": True}
        expected = {
            "ok": False, "stage": "manual_action_required",
            "manual_action": "请手动刷新一个视频号页面并播放一次",
            "ui_automation_used": False,
        }
        with tempfile.TemporaryDirectory() as temp, patch.object(adapter, "preflight", return_value=check), patch.object(
            adapter, "try_local", return_value=expected
        ):
            result = adapter.download(
                "https://weixin.qq.com/sph/abc", Path(temp), "never", 0, 30, False
            )
        self.assertEqual(result, expected)

    def test_online_result_normalizes_verified_files(self) -> None:
        raw = {
            "ok": True, "worker": "upstream", "title": "demo", "fallbacks": [],
            "files": [{"path": "/tmp/demo.mp4", "bytes": 3, "codec": "h264",
                       "width": 720, "height": 1280, "duration_seconds": 5,
                       "kind": "h264", "verification": "ffprobe"}],
        }
        completed = adapter.subprocess.CompletedProcess([], 0, json.dumps(raw), "")
        with patch.object(adapter, "run_component", return_value=completed):
            result = adapter.try_online(
                "https://weixin.qq.com/sph/abc", Path("/tmp"), 30, False
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["files"][0]["video_codec"], "h264")
        self.assertFalse(result["ui_automation_used"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
