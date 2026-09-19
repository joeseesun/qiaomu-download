# 内置视频号适配器

`qiaomu-download` 1.2.0 已把原 `qiaomu-wx-video` 的验证、在线解析、本地 feed 捕获、媒体下载、解密、编码验证和后端安装能力收入同一安装包。实现位于 `scripts/wechat/`，统一入口为 `scripts/download.py`。

## 快速路径

```bash
python3 scripts/download.py download 'https://weixin.qq.com/sph/...' --dir ~/Downloads
```

适配器先运行只读预检。若 `127.0.0.1:2022` 已有本地 API 且 `~/.local/share/qiaomu-wx-video/local-settings.json` 配置了后端、配置文件和 ffmpeg，它会请求 `/api/channels/feed/profile?url=...`。只有内层 `errCode == 0` 且 `media` 非空才算取得媒体。

页面 socket 未连接时返回 `manual_action_required`。此时由用户手动在电脑微信中重新打开并播放视频，Agent 不操作微信。随后运行：

```bash
python3 scripts/download.py download 'https://weixin.qq.com/sph/...' --wait-page 90 --dir ~/Downloads
```

获取媒体后保留完整签名参数，直接下载、按需调用锁定后端的 `decrypt` 子命令，并用 ffmpeg 完整解码验证。默认尝试取得不同真实编码的 H.264 和 H.265 文件；`--single-version` 只保留一个。

## 在线解析

包内保留两个固定解析器作为无本地连接时的可选路径。分享 URL 会离开本机，因此必须先获得用户对本次范围的明确同意：

```bash
python3 scripts/download.py download 'https://weixin.qq.com/sph/...' --wechat-online allowed
```

只发送公开分享 URL，不发送 Cookie、微信登录态、设备信息、证书、抓包或本地文件。解析器失败后停止，不循环轰炸接口。

## 首次本地设置

内置安装器只从 `ltaoo/wx_channels_download` 的锁定官方 Release 下载对应平台资产，并按 `scripts/wechat/release-lock.json` 校验 SHA-256：

```bash
python3 scripts/wechat/install_backend.py --accept-upstream-license
```

上游 v260714 使用带 Commons Clause 的 MIT 许可证；安装前需要用户确认已经审阅。安装器只写用户级数据目录，不安装证书、不启动后端、不修改代理。

若后端需要本机 CA 和代理捕获：

1. 使用本机独立生成的 CA，不使用随公开私钥分发的共享根证书。
2. 首次信任证书和首次修改系统代理分别说明影响并取得授权。
3. 修改前记录 HTTP、HTTPS、SOCKS 和网络服务快照。
4. 保留 Clash、Surge、FlClash 等现有代理；需要串联时使用后端 `upstreamProxy`。
5. 取得本批媒体地址后先恢复代理，再停止本次启动的后端。
6. 失败、中断和超时也执行同样恢复，并检查端口和联网状态。

## 固定安全规则

- 禁止用 Computer Use、Accessibility、AppleScript、浏览器自动化或任何 UI 工具操作微信。
- 用户只需要在确实缺少页面连接时手动重新打开并播放一次；不要求点击下载按钮。
- 不批量爬取账号作品，不绕过登录、权限、付费、地区或访问控制。
- 不输出签名媒体 URL、解密 key、完整 API 响应或账号标识。
- 私有元数据目录使用 `0700`，文件使用 `0600`，使用后清理本批临时凭据。
- 只停止本次启动且 PID、可执行路径都匹配的进程；不关闭用户已有后端。

## 结果状态

- `ok: true`：至少一个文件通过验证，`files` 给出绝对路径、编码、尺寸、时长和字节数。
- `manual_action_required`：后端已可用，但需要用户手动打开并播放一次。
- `wechat_setup_required`：没有可用本地后端；按首次设置流程准备，或征得同意后使用在线解析。
- `online_resolver`：固定解析器未返回可验证媒体，可转本地路径。
- `local_configuration`：本地 API 存在，但设置文件缺少后端、配置或 ffmpeg 路径。

macOS Apple Silicon 与上游 v260714 已有 H.264/HEVC 下载、解密和完整解码证据。其他系统、全部微信版本、全部清晰度和所有生成回放仍属于缺失证据。
