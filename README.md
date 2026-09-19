# qiaomu-download

给 Codex/Agent 使用的通用视频下载 Skill：一句“下载这个链接”，自动检查最新版 `yt-dlp`，下载单个视频，并用 `ffprobe` 验证文件确实可播放。

## 支持什么

- YouTube、B站、X/Twitter 为一级目标
- Vimeo、TikTok、Instagram、Facebook、Twitch、Reddit，以及 yt-dlp extractor 能处理的公开页面
- 视频、MP3、字幕、元数据
- `best`、1080p、720p、480p
- 匿名优先，失败后才按需读取本机浏览器 Cookie
- 自动检查 yt-dlp 官方 stable release，并根据 Homebrew、pip、pipx、uv 或官方独立版选择升级方式

微信视频号使用独立的 `qiaomu-wx-video`，本 Skill 不会操作微信客户端或微信内嵌页面。

## 安装

```bash
npx skills add joeseesun/qiaomu-download
```

系统依赖：Python 3.10+、[yt-dlp](https://github.com/yt-dlp/yt-dlp)、`ffmpeg`/`ffprobe`。macOS 可使用：

```bash
brew install yt-dlp ffmpeg
```

如果 Homebrew 提示 Xcode license，请先在终端执行 Apple 给出的许可命令，再重试安装。

### 前置条件检查

- [ ] Python 3.10 或更高版本可用
- [ ] `yt-dlp --version` 可以正常运行
- [ ] `ffmpeg -version` 与 `ffprobe -version` 可以正常运行
- [ ] 目标链接是你有权访问和保存的内容

## Agent 用法

你可以直接这样说：

- `下载这个 https://x.com/...`
- `把这个 B 站视频下载成 1080p：https://www.bilibili.com/video/...`
- `提取这个 YouTube 视频的 MP3：https://youtu.be/...`
- `下载这个视频的中英文字幕：https://youtube.com/watch?v=...`

## 命令行

```bash
python3 scripts/download.py doctor --upgrade
python3 scripts/download.py info 'https://x.com/...'
python3 scripts/download.py download 'https://www.bilibili.com/video/...' --quality 1080p
python3 scripts/download.py audio 'https://youtu.be/...'
python3 scripts/download.py subtitles 'https://youtube.com/watch?v=...' --langs 'zh.*,en.*'
```

默认输出到 `~/Downloads`。可用 `--dir` 指定目录，或设置 `QIAOMU_DOWNLOAD_OUTPUT`。

## Cookie 与隐私

默认 `--cookies-from-browser auto` 先做公开访问；只有失败后才尝试本机浏览器 Cookie。可以明确禁用：

```bash
python3 scripts/download.py download URL --cookies-from-browser none
```

Skill 不保存或打印 Cookie，不绕过 DRM、付费墙或访问控制。请只下载你有权访问和保存的内容。

## 常见问题

## Troubleshooting

**提示 `yt-dlp not found`**：运行 `python3 scripts/download.py doctor`，按输出安装 yt-dlp。

**提示 `ffmpeg not found`**：安装 ffmpeg；`ffprobe` 会随 ffmpeg 一起安装。

**B站高清或登录内容失败**：保持浏览器已登录，重试 `auto`，或明确指定 `--cookies-from-browser chrome`。

**X 链接抽取失败**：先执行 `doctor --upgrade`，站点改版通常需要新版 yt-dlp extractor。

**视频号链接**：交给 `qiaomu-wx-video`；本 Skill 不自动化微信 UI。

## 验证

```bash
python3 scripts/test_download.py
python3 scripts/trigger_eval.py .
python3 scripts/validate_skill.py .
```

核心运行时来自 [yt-dlp](https://github.com/yt-dlp/yt-dlp)，平台支持以当前 extractor 的实际探测结果为准。

## 设计与验证

技能包含单元测试、触发评测、包结构校验、真实平台探测报告和安全审计材料，详见 `reports/`。

<!-- qiaomu-profile:start -->
## 关于向阳乔木

向阳乔木（乔向阳 / Joe）是一位实践型 AI 产品与内容创作者，长期把前沿 AI 变化转译成可复用的工作流、产品判断、AI 编程实践、AI 搜索实践和 GEO/AI 营销方法。

- 个人网站: https://qiaomu.ai
- 博客: https://blog.qiaomu.ai
- X: https://x.com/vista8
- GitHub: https://github.com/joeseesun/
- 微信公众号: 向阳乔木推荐看

### 支持与关注

| 打赏支持 | 微信公众号 |
|---|---|
| <img src="assets/qiaomu-profile/qiaomu_reward_qr.png" alt="向阳乔木打赏二维码" width="180" /> | <img src="assets/qiaomu-profile/qiaomu_wechat_public_account_qr.jpg" alt="向阳乔木推荐看公众号二维码" width="180" /> |
| 感谢支持乔木持续分享 AI 实践 | 扫码关注「向阳乔木推荐看」 |

<!-- qiaomu-profile:end -->

## License

MIT
