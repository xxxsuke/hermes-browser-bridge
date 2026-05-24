---
name: browser-bridge-extension
description: Build and maintain a Chromium browser extension that lets Hermes Agent directly read/write/control any web page the user is browsing. Covers architecture (WS+HTTP dual-protocol bridge), MV3 Service Worker pitfalls, content script injection, and full browser API access (tabs, bookmarks, history, downloads, screenshots, DevTools).
version: 1.0.0
triggers:
  - browser extension for Hermes
  - browser bridge
  - control browser from Hermes
  - extension read write page
  - Edge Chrome extension AI agent
  - 浏览器扩展 控制 页面
  - 让 Hermes 操作浏览器
---

# Browser Bridge Extension

让 Hermes 通过浏览器扩展直接读/写/操控用户正在浏览的任何页面。

## 架构

```
Hermes Agent ←→ ws://localhost:9876 ←→ bridge.py ←→ http://localhost:9877 ←→ Edge/Chrome Extension
                                              (WS)                      (HTTP polling)
```

- **Hermes 侧**: WebSocket 连 bridge，发 JSON 命令
- **bridge.py**: 纯 Python asyncio，零外部依赖，双协议
- **扩展侧**: HTTP 轮询（每 2 秒 fetch），避 MV3 SW WebSocket 断连问题
- **content.js**: 注入页面，提供读/写/点/搜/键能力

## 安装

1. 启动桥接: `python3 ~/hermes-browser-bridge/bridge.py`
2. Edge → `edge://extensions` → 开发者模式 → 加载 `~/hermes-browser-bridge/extension/`
3. 验证: `python3 ~/hermes-browser-bridge/hermes_client.py list_tabs`

## 能力清单

| 类别 | 命令 | 说明 |
|------|------|------|
| 标签页 | `list_tabs` `activate_tab` `new_tab` `close_tab` `reload_tab` `duplicate_tab` `move_tab` `pin_tab` `go_back` `go_forward` `navigate` | 完整标签管理 |
| 页面读 | `read_text` `read_html` `read_element` `get_links` `get_images` | 读取页面内容 |
| 页面写 | `write_text` `click` `double_click` `right_click` `hover` `mouse_down` `mouse_up` `drag` | 鼠标操作 |
| 键盘 | `key_press` `type_text` | 按键/逐字输入 |
| 搜索 | `find_in_page` | Ctrl+F 页面搜索 |
| 截图 | `screenshot` | debugger API 兜底 |
| 书签 | `list_bookmarks` `create_bookmark` `remove_bookmark` `search_bookmarks` | |
| 历史 | `search_history` `delete_history` | |
| 下载 | `download` `list_downloads` `cancel_download` | |
| DevTools | `attach_debugger` `debugger_cmd` `detach_debugger` | |
| 缩放 | `set_zoom` `get_zoom` | |
| 清除 | `clear_cache` `clear_cookies` `clear_all_data` | |

## 关键陷阱和解决方案

### 1. MV3 Service Worker WebSocket 断连 ⚠️

**现象**: 扩展连上 WS 后 30 秒自动断开。

**根因**: MV3 Service Worker 空闲 30 秒后被浏览器终止。WS 连接随之断开。

**失败方案**: `chrome.alarms` 心跳——即使设 3 秒，SW 被完全 kill 后 `setTimeout` 不执行，alarm 唤醒有时序问题。

**最终方案**: HTTP 轮询。扩展每 2 秒 `fetch("http://localhost:9877/poll")`，bridge 返回待处理命令。HTTP 请求本身就能唤醒 SW，无需 alarm。

### 2. Content Script 缺少消息监听器 ⚠️

**现象**: 所有 `read_text`/`click` 等操作返回 "injection failed"。

**根因**: `content.js` 有 `window.__hermesBridgeExec` 函数但没有 `chrome.runtime.onMessage.addListener`，background 的 `sendMessage` 无人接收。

**修复**: 在 content.js 末尾加:
```javascript
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action) {
    sendResponse(window.__hermesBridgeExec(msg.action, msg.params));
  }
  return true;
});
```

### 3. CSP `eval()` 被阻止 ⚠️

**现象**: `eval_js` 返回 "Evaluating a string as JavaScript violates CSP"。

**修复**: 用 `new Function()` 代替 `eval()`:
```javascript
const fn = new Function('"use strict"; return (' + code + ')');
const result = fn();
```

### 4. Vue/React 输入框写不进去 ⚠️

**现象**: `write_text` 成功但 `read_element` 回来 value 为空。

**根因**: Vue/React 劫持了 `value` 属性的 getter/setter，直接 `el.value = '...'` 不触发响应式更新。

**修复**: 用原生 setter:
```javascript
const nativeSetter = Object.getOwnPropertyDescriptor(
  HTMLInputElement.prototype, 'value'
).set;
nativeSetter.call(el, newVal);
el.dispatchEvent(new Event('input', { bubbles: true }));
```

### 5. `captureVisibleTab` 需要 activeTab 权限 ⚠️

**现象**: `The 'activeTab' permission is not in effect`。

**修复**: debugger API 兜底:
```javascript
chrome.debugger.attach({ tabId: tid }, "1.3", () => {
  chrome.debugger.sendCommand({ tabId: tid }, "Page.captureScreenshot", ...);
});
```

### 6. 权限变更后必须重装扩展 ⚠️

**现象**: 更新 manifest.json 添加权限后，扩展功能部分失效。

**根因**: 权限变更时浏览器禁用扩展，"重新启用"可能缓存旧代码。

**修复**: 删除扩展 → 重新加载 → 刷新所有已打开页面。

## 文件位置

- 项目目录: `~/hermes-browser-bridge/`
  - `bridge.py` — 双协议桥接 (WS:9876 + HTTP:9877)
  - `extension/` — Chromium 扩展 (Edge/Chrome 通用)
  - `hermes_client.py` — Hermes 端命令行客户端
  - `INSTALL.md` — 安装指南

## 在 Hermes 中使用

```python
# execute_code 或 terminal 中调用:
terminal("python3 ~/hermes-browser-bridge/hermes_client.py read_text")
terminal("python3 ~/hermes-browser-bridge/hermes_client.py click '.publish-btn'")
terminal("python3 ~/hermes-browser-bridge/hermes_client.py screenshot")
```

## 开机自启

```bash
cat > ~/.config/systemd/user/hermes-bridge.service << 'EOF'
[Unit]
Description=Hermes Browser Bridge
After=network.target
[Service]
ExecStart=/usr/bin/python3 /home/suke/hermes-browser-bridge/bridge.py
Restart=always
RestartSec=5
[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now hermes-bridge.service
```
