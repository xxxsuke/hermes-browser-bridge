---
name: hermes-browser-bridge
description: [底层参考] Hermes 浏览器桥接 — WS 协议/扩展通信/安装部署/架构/踩坑记录。日常操作请用 hermes-browser-control 统一入口，本 skill 仅调试桥接本身时加载。
version: 1.3.0
category: automation
platforms: [windows, wsl, linux]
metadata:
  hermes:
    tags: [browser, extension, websocket, bridge, automation]
    related_skills: [hermes-browser-setup, hermes-agent]
triggers:
  - 浏览器截图
  - 小红书操作
  - 操控浏览器页面
  - 浏览器自动化
  - browser bridge
  - edge extension
  - chrome extension
---

# Hermes Browser Bridge v1.1

让 Hermes 直接操控你正在浏览的页面——不是独立 Chromium，而是你用的 Edge/Chrome 标签页。

**项目位置:** `~/hermes-browser-bridge/`
**扩展桌面副本:** `C:\Users\10737\Desktop\hermes-extension\`

## 架构

```
Edge/Chrome Extension (content.js + background.js)
    ↕ chrome.runtime.sendMessage
background.js ↔ ws://localhost:9876 ↔ bridge.py ↔ Hermes Agent
```

## 快速开始

```bash
# 1. 启动桥接
python3 ~/hermes-browser-bridge/bridge.py &

# 2. 加载扩展（edge://extensions → 开发人员模式 → 加载桌面文件夹）

# 3. 测试
python3 ~/hermes-browser-bridge/hermes_client.py list_tabs
python3 ~/hermes-browser-bridge/hermes_client.py read_text
```

## 全部命令

### 标签页
`list_tabs` `activate_tab` `reload_tab` `close_tab` `new_tab` `duplicate_tab`
`move_tab` `pin_tab` `navigate` `go_back` `go_forward`

### 页面读写
`read_text` `read_html` `read_element` `write_text`
`click` `double_click` `right_click` `hover` `mouse_down` `mouse_up` `drag`
`scroll` `get_links` `get_images`

### 键盘 & 搜索
`key_press` (支持 Ctrl/Shift/Alt) `type_text`
`find_in_page` (Ctrl+F 页面搜索)

### 书签、历史、下载
`list_bookmarks` `create_bookmark` `remove_bookmark` `search_bookmarks`
`search_history` `delete_history`
`download` `list_downloads`

### DevTools、截图、缩放
`attach_debugger` `debugger_cmd` `detach_debugger`
`screenshot` `set_zoom` `get_zoom` `print_page`

### 窗口、清除数据
`list_windows` `create_window`
`clear_cache` `clear_cookies` `clear_all_data`

## 在 Hermes 中使用

```python
from hermes_tools import terminal

# 读取页面
terminal("python3 ~/hermes-browser-bridge/hermes_client.py read_text", timeout=10)

# 点击 + 填写
terminal("python3 ~/hermes-browser-bridge/hermes_client.py click '#search-btn'", timeout=10)
terminal("python3 ~/hermes-browser-bridge/hermes_client.py write_text '#q' '搜索词'", timeout=10)

# 截图
terminal("python3 ~/hermes-browser-bridge/hermes_client.py screenshot", timeout=15)
```

## 开发踩坑记录（12条）

### 1. Manifest 权限变更 → 必须重装扩展
添加/删除 permissions 后 Edge 禁用。必须**删除后重新加载**，只刷新不够。

### 2. content.js 缺少消息监听器
`chrome.tabs.sendMessage` 需要 content.js 有 `chrome.runtime.onMessage.addListener`。缺失导致所有页面操作 "injection failed"。

### 3. Bridge 路由循环 (v4→v5)
v4 bridge 单一 handler 将转发给扩展的命令再次吞噬。v5 修复：按 `client` 来源路由——hermes 发命令转发给扩展，extension 发 reply 解析 future。

### 4. 扩展回复缺 `type:"reply"`
`send()` 必须含 `{type:"reply", ...data}`，否则 bridge 不识别。

### 5. SW 休眠 (MV3)
三重防御：alarm 3秒 + setInterval 2秒 ping + onclose 1秒重连。

### 6. WS CONNECTING 竞态
connecting 锁 + readyState 双重检查。

### 7. Vue/React 输入
原生 setter: `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el,val)`

### 8. 截图 fallback
captureVisibleTab → debugger Page.captureScreenshot

### 9. CSP 阻止 eval → new Function()

### 10. 页面搜索 → window.find()

### 11. Bridge 必须运行在 Windows（非 WSL），Startup 自启

### 12. 调试：bridge.log / SW 控制台 / Get-NetTCPConnection

## 项目文件

| 文件 | 说明 |
|------|------|
| `bridge.py` | Python WebSocket 桥接服务 |
| `hermes_client.py` | Hermes 端命令行客户端 |
| `extension/manifest.json` | Manifest V3 |
| `extension/background.js` | SW + WebSocket + 消息路由 |
| `extension/content.js` | 页面注入（~460行） |
| `extension/popup.html/js` | 扩展状态面板 |
| `INSTALL.md` | 安装指南 + systemd 自启 |

## 操作铁律

见 `references/operation-rules.md` — 标签管控、滚动到底、点进原文、网络劫持停、DNS 修复。

## 支持浏览器

Edge / Chrome / Brave / Opera / Vivaldi / 所有 Chromium
