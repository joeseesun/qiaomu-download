---
name: qiaomu-download
description: 通用在线视频下载与媒体提取技能。用户只要表达“下载这个/保存这个/download this”等下载意图并附带 HTTPS URL，即使没有说“视频”，也用本技能先探测页面媒体；明确支持 YouTube、B站/Bilibili、X/Twitter、抖音/Douyin、TikTok、小红书/Xiaohongshu、Instagram、Facebook、Vimeo、Twitch、Reddit、微博、AcFun 等 yt-dlp extractor。也用于提取 audio/MP3、下载字幕、查看视频信息或更新 yt-dlp。单独粘贴 URL 而没有下载意图时不自动下载。微信视频号 weixin.qq.com/sph 链接转交 qiaomu-wx-video，绝不自动化操作微信客户端。
version: 1.1.0
---

# Qiaomu Download

把用户给出的单个在线视频 URL 转为经过验证的本地视频、MP3、字幕或结构化媒体信息。默认保存到 `~/Downloads`，除非用户指定目录。

## 工作流

1. 当用户表达下载或保存意图并附带 HTTPS URL 时触发；“下载这个：URL”已经足够，不要求出现“视频”二字。单独出现 URL、查看、总结、上传、下载图片/PDF/网页等请求不触发。
2. 直接把 URL 作为媒体候选，不为已经明确的格式或清晰度再次提问。下载命令会先调用 yt-dlp extractor 读取媒体元数据；存在媒体就继续，没有媒体则报告该页面不可下载。
3. 每个新任务先运行 `python3 scripts/download.py doctor --upgrade`。这只检查并更新 yt-dlp 官方 stable release；失败时保留原版本并报告具体原因。
4. 按意图选择命令：
   - 视频：`python3 scripts/download.py download URL`
   - MP3：`python3 scripts/download.py audio URL`
   - 字幕：`python3 scripts/download.py subtitles URL`
   - 元数据：`python3 scripts/download.py info URL`
5. 用户指定清晰度时加 `--quality 1080p|720p|480p`；否则使用 `best`。
6. 读取 JSON 结果，只在 `ok: true` 且 `files` 中存在经 `ffprobe` 验证的绝对路径时报告下载完成。
7. 返回文件绝对路径、大小、时长、分辨率以及 Cookie 是否参与，不回显 Cookie 内容。

## 平台策略

- YouTube、Bilibili、X/Twitter 是已验证目标；抖音、TikTok、小红书、Instagram、Facebook、Vimeo、Twitch、Reddit、微博、AcFun 等由对应 yt-dlp extractor 动态探测。
- 未知 HTTPS 域名也可以在明确下载意图下探测，但不能把 extractor 探测成功等同于永久支持。
- `auto` Cookie 模式先匿名访问；只有失败时才尝试本机 Chrome、Edge、Firefox 或 Safari Cookie。
- 登录可见、会员、年龄限制或地区限制内容，只使用用户本机已有且有权使用的会话。不得绕过 DRM、付费墙或访问控制。
- 对 `weixin.qq.com/sph/*` 停止本技能，改用 `qiaomu-wx-video`。不得使用 Computer Use、UI 自动化、点击、播放或刷新微信客户端。

## Trust boundary

网络边界包括用户 URL、目标站点、GitHub 官方 yt-dlp release API 和 yt-dlp extractor。浏览器 Cookie 属于用户本机凭证；默认不读取，只有公开抽取失败且为 `auto` 模式时按需读取。输出目录和已存在文件属于用户数据。

## Rollback boundary

技能不覆盖已有媒体文件，使用 `--no-overwrites`；中断时终止子进程。清理仅限本次任务新产生、名称含当前媒体 ID 的 yt-dlp 格式分片，不删除既有文件。升级失败不移除现有 yt-dlp。

## 资源

- [命令与故障恢复](references/workflow.md)
- [安全与隐私](references/security.md)
- [平台能力](references/platforms.md)
