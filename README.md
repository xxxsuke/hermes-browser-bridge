# Hermes Browser Bridge

让 AI Agent（Hermes）直接操控你的 Edge/Chrome 浏览器——不是开一个新的自动化浏览器，而是复用你正在用的标签页，已登录的网站全部可用。

## 一句话

**像人一样操控浏览器：读页面、点按钮、填表单、截图、搜书签、管下载、切代理。**

## 架构

```
┌─────────────────────────────────────────┐
│  Edge / Chrome (你的浏览器)              │
│  └─ Extension (background + content.js) │
│      ↕ chrome.runtime.sendMessage        │
│  └─ WebSocket → ws://localhost:9876      │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  bridge.py (Python, Windows 上运行)      │
│  WebSocket Server + HTTP 轮询           │
│  端口: 9876 (WS) + 9877 (HTTP)          │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Hermes Agent (WSL/Linux)               │
│  → execute_code: hermes_client.py       │
│  → skill: browser-control v2.1          │
└─────────────────────────────────────────┘
```

## 能力清单（50+ 命令）

| 类别 | 命令 | 
|------|------|
| **标签页** | list_tabs, activate_tab, new_tab, close_tab, reload_tab, navigate, go_back, go_forward |
| **页面读** | read_text, read_html, read_element, get_links, get_images, scroll |
| **页面写** | click, double_click, right_click, hover, write_text, type_text, drag |
| **键盘** | key_press（支持 Ctrl/Shift/Alt）, find_in_page（Ctrl+F） |
| **截图** | screenshot（debugger API 兜底） |
| **书签** | list_bookmarks, create_bookmark, remove_bookmark, search_bookmarks |
| **历史** | search_history, delete_history |
| **下载** | download, list_downloads |
| **DevTools** | attach_debugger, debugger_cmd, detach_debugger |
| **窗口** | create_window, list_windows |
| **清除** | clear_cache, clear_cookies, clear_all_data |
| **代理** | proxy_on, proxy_off（自动切换系统代理 + Clash 全局/规则模式） |

## 快速开始

### 1. 启动桥接

```bash
# 安装依赖（唯一依赖）
pip install websockets

# 启动桥接服务
python3 bridge.py
```

看到 `WebSocket: ws://localhost:9876` 就成功了。

### 2. 安装扩展

1. 打开 Edge/Chrome → `edge://extensions` 或 `chrome://extensions`
2. 开启「开发人员模式」
3. 点击「加载解压缩的扩展」→ 选择 `extension/` 目录
4. 扩展图标应显示「已连接」

### 3. 测试

```bash
# 列表所有标签页
python3 hermes_client.py list_tabs

# 读取当前页面文字
python3 hermes_client.py read_text

# 搜索并点击
python3 hermes_client.py navigate https://baidu.com
python3 hermes_client.py write_text '#kw' 'Hello World'
python3 hermes_client.py click '#su'
```

## 在 Hermes Agent 中使用

```python
from hermes_tools import terminal

# 读页面
terminal("python3 ~/hermes-browser-bridge/hermes_client.py read_text", timeout=10)

# 点击按钮
terminal("python3 ~/hermes-browser-bridge/hermes_client.py click '.publish-btn'", timeout=10)

# 填表单
terminal("python3 ~/hermes-browser-bridge/hermes_client.py write_text '#title' '标题'", timeout=10)

# 截图
terminal("python3 ~/hermes-browser-bridge/hermes_client.py screenshot", timeout=15)
```

## 代理自动管理

`proxy_manager.py` 按需开关代理——访问国际网站时自动开 Clash 全局，用完即关。

```bash
# 开启代理（系统代理 + Clash 全局模式）
python3 proxy_manager.py on

# 关闭代理（直连 + Clash 规则模式）
python3 proxy_manager.py off
```

内置国际站点白名单：YouTube, Twitter/X, GitHub, Google, OpenAI, Reddit, Discord, Facebook, Instagram, TikTok, Medium, Wikipedia。

## 项目文件

```
hermes-browser-bridge/
├── bridge.py              # WebSocket + HTTP 双协议桥接
├── hermes_client.py       # 命令行客户端（50+ 命令）
├── proxy_manager.py       # 代理开关管理（Windows 注册表 + Clash API）
├── demo.py                # 演示脚本
├── gen_icons.py           # 图标生成工具
├── INSTALL.md             # 详细安装指南
├── extension/             # Chromium 扩展
│   ├── manifest.json      # MV3 配置
│   ├── background.js      # Service Worker + WebSocket
│   ├── content.js         # 页面注入脚本（~460 行）
│   ├── offscreen.js       # Offscreen 持久连接
│   ├── offscreen.html     # Offscreen 页面
│   ├── popup.html/js       # 扩展状态面板
│   └── icons/             # 扩展图标
├── skills/                # Hermes Skill 文件
│   ├── hermes-browser-control.md   # 浏览器操控整合方案
│   ├── hermes-browser-bridge.md    # Bridge 使用指南
│   └── browser-bridge-extension.md # 扩展构建与维护
└── README.md
```

## 支持的浏览器

- ✅ Microsoft Edge (Chromium)
- ✅ Google Chrome
- ✅ Brave / Opera / Vivaldi
- ✅ 所有基于 Chromium 的浏览器

## 开发踩坑记录

1. **MV3 Service Worker 断连**：SW 空闲 30 秒后被杀 → HTTP 轮询代替 WS
2. **Content Script 缺消息监听**：必须加 `chrome.runtime.onMessage.addListener`
3. **CSP 阻止 eval()**：用 `new Function()` 代替
4. **Vue/React 输入框**：用原生 setter + dispatchEvent('input')
5. **captureVisibleTab 限制**：debugger API 兜底
6. **权限变更重装**：改 manifest 权限后必须删除重新加载扩展
7. **Bridge 运行位置**：必须在 Windows 上运行（非 WSL），操控 Windows 上的浏览器
8. **WSL→Windows 桥接**：bridge.py 跑在 Windows 上，Hermes 在 WSL 中通过 `localhost:9876` 连接

## License

MIT
