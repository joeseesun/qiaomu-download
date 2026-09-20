# Workflow

## 路由与依赖检查

`scripts/download.py` 是所有平台的统一入口。它把 `weixin.qq.com/sph/*` 交给视频号适配器，把 `open.spotify.com/track/*` 交给 Spotify 单曲适配器，其他 URL 进入常规 yt-dlp 流程。

每个新下载任务先运行：

```bash
python3 scripts/download.py doctor --upgrade
```

`doctor` 只比较 GitHub 官方 latest stable release。检测到更新时，根据现有安装来源使用 Homebrew、pip、pipx、uv 或 `yt-dlp -U`。网络检查失败或包管理器拒绝更新时，保留已安装版本并报告失败阶段。

## 下载

```bash
python3 scripts/download.py download URL --quality best --dir ~/Downloads
```

进程输出下载进度到 stderr，最终 JSON 输出到 stdout。完成条件是 JSON 中 `ok` 为 true，且每个文件通过 ffprobe 的流、时长和大小检查。

Spotify 单曲会先读取公开页面元数据，再搜索十个 YouTube 候选。评分同时检查标题、艺人和时长，并加入频道验证、播放量和错误版本惩罚；置信度不足会返回 `match` 错误。专辑与播放列表不会自动展开。

## 故障恢复

1. `validate`：检查 HTTPS URL，不改动环境。
2. `wechat_setup_required`：视频号本地后端未连接；按 [视频号内置适配器](wechat-video.md) 准备环境，或在用户同意发送分享 URL 后使用 `--wechat-online allowed`。
3. `manual_action_required`：只让用户手动重新打开并播放一次，再用 `--wait-page 90` 继续；Agent 不操作微信。
4. `dependency`：安装缺失依赖后重试。
5. `metadata`：更新 yt-dlp；需要登录时保持浏览器已登录并允许 Cookie 回退。
6. `download`：检查网络、磁盘空间和站点可用性；同一媒体的并发任务会被锁拒绝。
7. `verify`：文件未通过 ffprobe，不宣告成功。
8. `match`：Spotify 候选相似度不足；返回候选匹配失败，不猜测或盲目下载。
