# qiaomu-download

> 对 Agent 说一句 **“下载这个：URL”**，它会识别页面里的视频、更新下载引擎、保存最高可用画质，并验证文件真的能播放。

[![Release](https://img.shields.io/github/v/release/joeseesun/qiaomu-download?style=flat-square)](https://github.com/joeseesun/qiaomu-download/releases)
[![License](https://img.shields.io/github/license/joeseesun/qiaomu-download?style=flat-square)](LICENSE)
[![Powered by yt-dlp](https://img.shields.io/badge/powered%20by-yt--dlp-red?style=flat-square)](https://github.com/yt-dlp/yt-dlp)

不记命令，不找解析网站，不手动挑音视频流。复制链接，说“下载这个”，剩下的交给 Skill。

```text
你：下载这个：https://x.com/vista8/status/2100589909136523770

Agent：下载完成
文件：~/Downloads/向阳乔木 - 多模态强还是不错的 […].mp4
画面：1728 × 1080 · H.264
音频：AAC
时长：39.38 秒
验证：ffprobe 通过
```

## 为什么值得安装

- **一句话触发**：只需“下载这个 + URL”，不用特意说明它是视频。
- **多平台统一入口**：微信视频号、YouTube、B站、X、抖音、TikTok、小红书等使用同一种表达。
- **自动跟进 yt-dlp**：每个新任务检查官方 stable release，仅在有新版时按现有包管理器升级。
- **公开访问优先**：先匿名解析；只有公开提取失败时才按需使用本机浏览器 Cookie。
- **下载后验真**：用 `ffprobe` 检查视频流、音频流、时长、分辨率和文件大小。
- **保护已有文件**：默认单链接、禁止播放列表扩张、禁止覆盖、重复任务加锁。
- **进度可见**：持续显示下载、合并和验证进度，完成后返回可点击的绝对路径。
- **视频号完整内置**：同一个安装包包含视频号预检、在线解析、本地捕获、下载、解密、编码验证和后端安装器，不需要另装 Skill。
- **微信和小红书更克制**：不使用 Computer Use 或 UI 自动化操作微信、小红书客户端及其内嵌页面。
- **风控平台先提醒**：遇到小红书、抖音、TikTok、Instagram、Facebook、微博等平台，先说明只做链接解析；登录、验证码和安全验证始终由用户手动完成。

## 支持哪些平台

平台能力来自当前安装的 `yt-dlp` extractor。站点会改版，因此“存在 extractor”代表可以动态探测，不代表任何链接永久可用。

| 平台 | 状态 | 能力与限制 |
|---|---|---|
| YouTube / YouTube Shorts | ✅ 已验证 | 视频、MP3、字幕、元数据；受限内容可能需要浏览器 Cookie |
| B站 / Bilibili / b23.tv | ✅ 已验证 | 普通视频、番剧等；高清、会员或登录内容受账号权限约束 |
| X / Twitter | ✅ 已验证下载 | 普通帖子视频；已完成真实下载与 `ffprobe` 验证 |
| 抖音 / Douyin | ✅ extractor | 支持分享短链探测；页面限制时可能需要本机会话 |
| TikTok | ✅ extractor | 普通视频为主要目标；直播和部分集合能力取决于当前 extractor |
| 小红书 / Xiaohongshu | ✅ extractor | 仅使用链接解析与命令行下载；不自动点击、刷新或操作小红书 UI |
| Instagram | ✅ extractor | Posts、Reels、Stories；私密内容需要用户已有会话 |
| Facebook | ✅ extractor | 普通视频与 Reels；登录可见内容受账号权限约束 |
| Vimeo | ✅ extractor | 普通视频、频道、活动；付费与 DRM 内容不绕过 |
| Twitch | ✅ extractor | Clips、VOD、直播 |
| Reddit | ✅ extractor | 帖子内视频 |
| 微博 / Weibo | ✅ extractor | 普通视频与用户视频 |
| AcFun | ✅ extractor | 普通视频与番剧 |
| Pinterest | ✅ extractor | 视频 Pin 与合集 |
| LinkedIn | ✅ extractor | 普通视频、活动、课程；部分内容需要登录 |
| SoundCloud | ✅ extractor | 音频、歌单、用户页面 |
| Dailymotion / VK | ✅ extractor | 普通视频与部分集合 |
| 其他 HTTPS 页面 | 🔎 动态探测 | yt-dlp 能识别媒体就下载，否则返回准确错误 |
| 微信视频号 | ✅ 内置适配器 | 本地连接优先；必要时只让用户手动播放一次；在线解析需先同意发送分享 URL |
| 快手 | ⚠️ 暂不承诺 | 当前未发现明确稳定的 Kuaishou extractor |

## 微信视频号和小红书的安全边界

用户担心客户端自动化导致风控或封号，因此本项目明确执行以下规则：

- 不使用 Computer Use、Accessibility、AppleScript 或其他 UI 自动化点击微信、小红书。
- 下载小红书等容易触发风控验证的平台前，先向用户说明本次仅使用 URL/yt-dlp 解析，不操作客户端或网页 UI；提醒后直接继续，不重复索要确认。
- 不替用户输入账号、密码、短信验证码或 2FA。
- 小红书优先直接解析分享 URL；公开解析失败时，只能按需读取用户本机已有浏览器 Cookie。
- 微信视频号由当前包内置适配器处理。若必须打开或播放微信页面，由用户手动完成，Agent 只处理本地接口和下载结果。
- 未经明确同意，不把视频号分享 URL 发送给第三方解析器；即使同意，也不发送 Cookie、微信登录态、设备信息或抓包。
- 首次使用本地视频号后端时，证书信任和系统代理修改分别说明影响并授权，任务结束恢复原代理快照。
- 不绕过 DRM、付费墙、会员权限、地区限制或其他访问控制。
- 公开解析失败后最多尝试一次浏览器 Cookie 回退；仍失败就停止，避免高频请求增加账号风险。

## 安装

```bash
npx skills add joeseesun/qiaomu-download
```

系统依赖：Python 3.10+、[yt-dlp](https://github.com/yt-dlp/yt-dlp)、`ffmpeg` 和 `ffprobe`。视频号脚本已随 Skill 安装；需要本地捕获时才按需安装并校验锁定的上游后端。

macOS：

```bash
brew install yt-dlp ffmpeg
```

Ubuntu / Debian：

```bash
sudo apt update
sudo apt install ffmpeg
python3 -m pip install --user --upgrade yt-dlp
```

### 前置条件检查

- [ ] Python 3.10 或更高版本可用
- [ ] `yt-dlp --version` 可以正常运行
- [ ] `ffmpeg -version` 与 `ffprobe -version` 可以正常运行
- [ ] 目标链接是你有权访问和保存的内容

## 你可以直接这样说

### 下载视频

```text
下载这个：https://v.douyin.com/...
保存这个 https://www.xiaohongshu.com/explore/...
download this https://www.tiktok.com/@user/video/...
把这个 B 站视频下载成 1080p：https://www.bilibili.com/video/...
```

### 提取音频

```text
把这个 YouTube 视频提取成 MP3：https://youtu.be/...
```

### 下载字幕

```text
下载这个视频的中英文字幕：https://youtube.com/watch?v=...
```

### 查看信息但不下载

```text
查看这个视频的信息：https://vimeo.com/...
```

## 如何判断是否触发

| 用户表达 | 处理方式 |
|---|---|
| “下载这个：URL” | 触发，先探测媒体，再下载 |
| “保存这个 URL” | 触发，先探测媒体，再下载 |
| 只粘贴一个 URL | 不擅自下载 |
| “总结这个 YouTube 视频” | 不触发下载 Skill |
| “下载这张图片 / PDF / 网页” | 不触发视频下载 Skill |
| “下载这个视频号：URL” | 触发内置视频号适配器 |

## 自动更新机制

Skill 在每个新下载任务开始时运行：

```bash
python3 scripts/download.py doctor --upgrade
```

它会读取 yt-dlp 官方 GitHub stable release，并识别当前安装来源：

- Homebrew → `brew upgrade yt-dlp`
- pip 虚拟环境 → `python -m pip install --upgrade yt-dlp`
- pipx → `pipx upgrade yt-dlp`
- uv tool → `uv tool upgrade yt-dlp`
- 官方独立版 → `yt-dlp -U`

没有新版时不会重复安装。更新失败时保留原版本，并给出具体失败阶段。

## Cookie 与隐私

默认策略是 `public first`：

1. 先不用 Cookie 读取媒体信息。
2. 公开提取失败时，才尝试本机 Chrome、Edge、Firefox 或 Safari Cookie。
3. 不复制、不保存、不打印 Cookie 内容。
4. 可明确禁用 Cookie：

```bash
python3 scripts/download.py download URL --cookies-from-browser none
```

## 命令行

Agent 通常会自动调用，也可以直接运行：

```bash
# 检查并更新 yt-dlp
python3 scripts/download.py doctor --upgrade

# 读取媒体信息
python3 scripts/download.py info 'https://x.com/...'

# 下载最高可用画质
python3 scripts/download.py download 'https://www.bilibili.com/video/...'

# 下载微信视频号（内置能力）
python3 scripts/download.py download 'https://weixin.qq.com/sph/...'

# 限制清晰度
python3 scripts/download.py download URL --quality 1080p

# 提取 MP3
python3 scripts/download.py audio 'https://youtu.be/...'

# 下载字幕
python3 scripts/download.py subtitles URL --langs 'zh.*,en.*'
```

默认保存到 `~/Downloads`。使用 `--dir` 或 `QIAOMU_DOWNLOAD_OUTPUT` 可以指定目录。

## 下载完成的标准

Skill 不会因为 `yt-dlp` 进程返回 0 就直接宣布成功。视频或音频必须继续通过 `ffprobe`：

- 文件存在且大小大于 0
- 存在预期的视频流或音频流
- 时长有效
- 返回容器、编码、分辨率、时长和绝对路径

中断或失败时，只清理本次任务新产生的格式分片，不删除已有文件。

## Troubleshooting

### `yt-dlp not found`

安装 yt-dlp 后运行：

```bash
python3 scripts/download.py doctor
```

### `ffmpeg not found` 或 `ffprobe not found`

安装 `ffmpeg`。多数包管理器会同时提供 `ffprobe`。

### X、抖音、TikTok 或小红书突然解析失败

这些平台经常调整页面和接口。先运行：

```bash
python3 scripts/download.py doctor --upgrade
```

如果公开解析仍失败，保持浏览器已登录并让 Skill 使用 `auto` Cookie 模式。它不会操作网站 UI。

### B站高清画质不可用

画质可能与登录状态、会员权限和视频本身有关。Skill 可以读取已有浏览器会话，但不会绕过权限。

### 微信视频号链接

直接使用同一个入口：

```bash
python3 scripts/download.py download 'https://weixin.qq.com/sph/...'
```

已有本地连接时会自动下载。返回 `manual_action_required` 时，由用户手动重新打开并播放一次，然后 Agent 用 `--wait-page 90` 继续。Agent 永远不点击、播放或刷新微信。若用户明确同意把本次公开分享 URL 发给固定解析器，可以添加 `--wechat-online allowed`。完整首次设置和恢复规则见 [`references/wechat-video.md`](references/wechat-video.md)。

## 验证与发布质量

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/trigger_eval.py .
python3 scripts/validate_skill.py .
```

当前发布流程包含：单元测试、触发边界评测、包结构校验、秘密扫描、真实平台证据、PR 合并、GitHub Release 和全新环境安装验证。

通用下载基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp)，视频号本地后端适配源自 [ltaoo/wx_channels_download](https://github.com/ltaoo/wx_channels_download)。后者的锁定版本使用带 Commons Clause 的 MIT 许可证，安装前请自行审阅。请只下载你有权访问和保存的内容，并遵守目标平台条款与当地法律。

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
