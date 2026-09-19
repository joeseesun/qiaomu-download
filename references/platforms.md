# Platform support

| 平台 | 路由 | 认证策略 | 说明 |
|---|---|---|---|
| YouTube | yt-dlp YouTube extractor | 公开优先，失败后浏览器 Cookie | OAuth 已不是默认方案，受限内容通常需要 Cookie |
| Bilibili / b23.tv | yt-dlp Bilibili extractor | 公开优先，高清/会员内容可用本机会话 | 不承诺付费或 DRM 内容 |
| X / Twitter | yt-dlp Twitter extractor | 公开优先，受限帖子可用本机会话 | 站点变更时先升级 yt-dlp |
| Vimeo、TikTok 等 | 对应 extractor | 同上 | 以当前 yt-dlp 实际探测为准 |
| 未知站点 | generic extractor | 同上 | 支持范围无法靠静态列表保证 |
| 微信视频号 | qiaomu-wx-video | 专用下载流程 | 禁止微信 UI 自动化 |
