# Security and privacy

- 只接受 HTTPS，不接受 URL 用户名/密码、自定义端口、localhost 或私有 IP。
- 单视频模式固定使用 `--no-playlist`，防止一个链接意外扩张为整套内容。
- 固定使用 `--no-overwrites`，保护已有文件。
- Cookie 先不读取，公开抽取失败后才回退到本机浏览器；不复制、存储或打印 Cookie。
- 不把 Cookie、令牌或凭证放入命令参数之外的日志和结果。
- 不绕过 DRM、付费墙、地区限制或其他访问控制。
- 微信视频号由 qiaomu-wx-video 处理；禁止自动化微信客户端、点击、播放或刷新微信内嵌页面。
- 更新来源只信任 yt-dlp 官方 GitHub release；使用现有安装管理器完成升级。
- 只清理本次任务新创建、名称含当前媒体 ID 的格式分片。
