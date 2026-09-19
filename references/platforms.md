# Platform support

| 平台 | 路由 | 认证策略 | 说明 |
|---|---|---|---|
| YouTube | yt-dlp YouTube extractor | 公开优先，失败后浏览器 Cookie | OAuth 已不是默认方案，受限内容通常需要 Cookie |
| Bilibili / b23.tv | yt-dlp Bilibili extractor | 公开优先，高清/会员内容可用本机会话 | 不承诺付费或 DRM 内容 |
| X / Twitter | yt-dlp Twitter extractor | 公开优先，受限帖子可用本机会话 | 站点变更时先升级 yt-dlp |
| 抖音 / Douyin | yt-dlp Douyin extractor | 下载前提醒；公开优先，最多一次 Cookie 回退 | 分享短链允许重定向；不操作 UI，验证由用户手动完成 |
| TikTok | yt-dlp TikTok extractor | 下载前提醒；公开优先，最多一次 Cookie 回退 | 普通视频是主要目标；不操作 UI，验证由用户手动完成 |
| 小红书 / Xiaohongshu | yt-dlp XiaoHongShu extractor | 下载前提醒；公开优先，最多一次 Cookie 回退 | 不点击、刷新、登录或处理验证页面，避免账号风控 |
| Instagram / Facebook | 对应 extractor | 公开优先，私密内容需本机会话 | 支持普通视频、Reels；不绕过访问控制 |
| Vimeo / Twitch / Reddit | 对应 extractor | 同上 | 以当前 yt-dlp 实际探测为准 |
| 微博 / AcFun | 对应 extractor | 同上 | 以当前 yt-dlp 实际探测为准 |
| 未知站点 | generic extractor | 同上 | 支持范围无法靠静态列表保证 |
| 微信视频号 | 内置 `scripts/wechat_adapter.py` | 本地连接优先；在线解析需先取得分享 URL 授权 | 完整内置，不依赖其他 Skill；禁止微信 UI 自动化 |
