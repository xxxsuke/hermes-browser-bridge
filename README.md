# Hermes Browser Bridge

操控你的浏览器，两种方式任选：

- **🧠 AI Agent 模式** — 配合 Hermes Agent，说句话就让 AI 自动搜、读、配图、修网络
- **⌨️ 命令行模式** — 纯 Windows CMD，`python hermes_client.py` 手动操控

**不需要 WSL，不需要 Linux，装好 Python 就能用。**

---

## 目录

- [它能做什么](#它能做什么)
- [快速开始（3 分钟）](#快速开始3-分钟)
- [命令大全](#命令大全)
- [常见问题排查](#常见问题排查)
- [与 Hermes Agent 集成](#与-hermes-agent-集成)
- [代理自动管理（选装）](#代理自动管理选装)
- [项目文件结构](#项目文件结构)
- [开发踩坑记录](#开发踩坑记录)

---

## 它能做什么

### 🧠 AI Agent 模式（配合 Hermes Agent，推荐）

对 Hermes 说一句话，Agent 自动搞定：

```
你说的话                          Agent 做的事
─────────────────────────────────────────────────────────
"帮我搜一下今天AI圈有什么新闻"     自动搜索多平台 → 筛选相关文章 → 滚动到底读完 → 截图留存
"给这篇文章找3张配图"             自动搜头条图片 → 提取高分辨率图 → vision验证内容匹配 → 下载
"网又断了，看看怎么回事"           5层递进诊断 → 定位到Clash残留 → 自动修复 → 验证恢复
"搜一下鸿蒙最新版本的评测"         多引擎搜索 → 点进原文 → 读完 → 判断完整性 → 返回摘要
```

### ⌨️ 命令行模式（Windows CMD 直接跑）

```cmd
操作                          命令
────────────────────────────────────────────
列出所有标签页                python hermes_client.py list_tabs
搜索并打开网页                python hermes_client.py navigate "https://baidu.com/s?wd=天气"
读取页面文字                  python hermes_client.py read_text
截图                          python hermes_client.py screenshot
填写表单/发帖                 python hermes_client.py write_text "#title" "我的标题"
下载文件                      python hermes_client.py download "https://example.com/file.pdf"
新建窗口                      python hermes_client.py create_window "https://xiaohongshu.com"
Ctrl+F 搜索                   python hermes_client.py find_in_page "关键词"
```

**关键区别：** 它不是新开一个自动化浏览器，而是**操控你正在用的 Edge/Chrome 窗口**。你登录过的网站（小红书、知乎、微博）直接用，不需要再登录。配合 Hermes Agent 时，AI 自己会判断什么时候搜索、什么时候换引擎、什么时候开代理——你只需要说你要什么。

---

## 快速开始（3 分钟）

### 第一步：安装 Python（如果没有的话）

打开 [python.org](https://www.python.org/downloads/) → 下载最新版。

**⚠️ 安装时一定要勾选** `Add Python to PATH`，否则后面 `python` 命令找不到。

装完后打开 CMD（Win+R → 输入 `cmd` → 回车），验证：

```cmd
python --version
pip --version
```

两条都应该显示版本号，不报错。

### 第二步：下载项目

下载 zip 包：https://github.com/hermes-bridge/hermes-browser-bridge/archive/refs/heads/main.zip

解压到桌面或者你喜欢的目录，比如 `C:\Users\你的用户名\Desktop\hermes-browser-bridge\`

或者在 CMD 里：

```cmd
cd C:\Users\你的用户名\Desktop
git clone https://github.com/hermes-bridge/hermes-browser-bridge.git
```

（如果没有 git，去 https://git-scm.com/download/win 下载装一下）

### 第三步：安装依赖

在 CMD 里进入项目目录，运行：

```cmd
cd C:\Users\你的用户名\Desktop\hermes-browser-bridge
pip install websockets
```

看到 `Successfully installed websockets-xxx` 就成功了。

### 第四步：启动桥接服务

```cmd
python bridge.py
```

你会看到：

```
╔══════════════════════════════════════════╗
║     Hermes Browser Bridge v5             ║
║     WebSocket: ws://localhost:9876       ║
║     HTTP polling: http://localhost:9877  ║
╚══════════════════════════════════════════╝
```

**⚠️ 这个窗口不要关，保持运行。** 后面所有的操作都需要它活着。

> **防火墙弹窗？** Windows 可能会问是否允许 Python 通过防火墙 → 点「允许访问」。

### 第五步：安装 Edge/Chrome 扩展

1. 打开 Edge 浏览器
2. 地址栏输入 `edge://extensions`（Chrome 用户输入 `chrome://extensions`）
3. **打开左上角的「开发人员模式」开关**（很重要！）
4. 点击「加载解压缩的扩展」
5. 选择项目里的 `extension` 文件夹
   - 如果你解压在桌面：`C:\Users\你的用户名\Desktop\hermes-browser-bridge\extension`
6. 扩展栏会出现一个桥接图标
7. 图标上应该显示 **「已连接」** 状态

没显示「已连接」？看下方 [常见问题排查](#常见问题排查)。

### 第六步：验证

**不要关掉 bridge.py 那个 CMD 窗口。** 打开**另一个** CMD 窗口：

```cmd
cd C:\Users\你的用户名\Desktop\hermes-browser-bridge
python hermes_client.py list_tabs
```

应该返回你当前浏览器打开的标签页列表。

再试试读取当前页面的文字：

```cmd
python hermes_client.py read_text
```

返回页面内容 → 恭喜，成功了！🎉

---

## 命令大全

### 标签页管理

```cmd
python hermes_client.py list_tabs                        # 列出所有标签
python hermes_client.py activate_tab <id>                # 切换到指定标签
python hermes_client.py new_tab <url>                     # 新建标签页
python hermes_client.py close_tab <id>                    # 关闭标签
python hermes_client.py reload_tab [id]                   # 刷新（不指定 id 刷当前页）
python hermes_client.py navigate <url> [id]               # 导航到 URL
python hermes_client.py go_back [id]                      # 后退
python hermes_client.py go_forward [id]                   # 前进
python hermes_client.py duplicate_tab <id>                # 复制标签页
python hermes_client.py move_tab <id> <index>             # 移动标签位置
python hermes_client.py pin_tab <id>                      # 固定标签
```

### 页面读写

```cmd
python hermes_client.py read_text [maxLength]             # 读取页面文字
python hermes_client.py read_html                         # 读取 HTML 源码
python hermes_client.py read_element <selector>            # 读取指定元素
python hermes_client.py get_links [maxCount]              # 获取所有链接
python hermes_client.py get_images [maxCount]             # 获取所有图片
python hermes_client.py scroll [direction] [amount]       # 滚动页面（up/down）
```

### 页面操作

```cmd
python hermes_client.py click <selector>                  # 点击元素
python hermes_client.py double_click <selector>            # 双击
python hermes_client.py right_click <selector>             # 右键
python hermes_client.py hover <selector>                  # 悬停
python hermes_client.py write_text <selector> <text>       # 填写输入框
python hermes_client.py type_text <selector> <text>        # 逐字输入（模拟打字）
python hermes_client.py find_in_page <query>               # 页面内搜索
```

**选择器（selector）示例：**

| 选择器 | 匹配 | 示例 |
|--------|------|------|
| `#kw` | id="kw" 的元素 | 百度搜索框 |
| `#su` | id="su" 的按钮 | 百度搜索按钮 |
| `.title` | class="title" 的元素 | |
| `div.result` | class="result" 的 div | |
| `button` | 第一个 button | |
| `input[name="q"]` | name="q" 的 input | |

### 截图与下载

```cmd
python hermes_client.py screenshot [id]                   # 截图当前页面
python hermes_client.py download <url> [filename]          # 下载文件
python hermes_client.py list_downloads                    # 查看下载列表
```

### 书签与历史

```cmd
python hermes_client.py list_bookmarks                    # 列出书签树
python hermes_client.py create_bookmark <title> <url>     # 创建书签
python hermes_client.py remove_bookmark <id>              # 删除书签
python hermes_client.py search_bookmarks <query>          # 搜索书签
python hermes_client.py search_history <query>            # 搜索历史
```

### 窗口与系统

```cmd
python hermes_client.py create_window <url>                # 创建新窗口
python hermes_client.py list_windows                      # 列出所有窗口
python hermes_client.py get_tab_info [id]                  # 标签详情
python hermes_client.py set_zoom [id] <level>              # 设置缩放（1.0=100%）
python hermes_client.py get_zoom [id]                      # 获取缩放
python hermes_client.py clear_cache                        # 清除缓存
python hermes_client.py clear_cookies                      # 清除 Cookie
python hermes_client.py clear_data                         # 清除所有数据
```

---

## 常见问题排查

### ❌ `python` 提示"不是内部或外部命令"

**原因：** 安装 Python 时没有勾选 `Add Python to PATH`。

**解决：**
1. 重新运行 Python 安装包
2. 在第一个界面**勾选「Add Python to PATH」**
3. 点「Install Now」
4. 重启 CMD

### ❌ `pip` 提示"不是内部或外部命令"

**原因：** 同上，或 Python 版本太老。

**解决：** 重新安装 Python（3.7 以上版本），确保勾选 PATH。装好后运行：

```cmd
python -m pip install --upgrade pip
```

### ❌ `ModuleNotFoundError: No module named 'websockets'`

**原因：** 没装 websockets 库。

**解决：**

```cmd
pip install websockets
```

### ❌ 扩展图标显示「未连接」

**原因：** bridge.py 没启动，或端口被占用。

**解决：**
1. 确认 `python bridge.py` 在运行，且显示 `ws://localhost:9876`
2. 确认不是 9876 端口被其他程序占用：

```cmd
netstat -ano | findstr :9876
```

如果被占用，关掉占用程序，或者改 bridge.py 里的 PORT 为 9875 并在扩展 background.js 也改。

### ❌ 扩展加载后显示"无法加载扩展"

**原因：**
- 选错了文件夹（应该选 extension 子文件夹，不是项目根目录）
- 没打开「开发人员模式」

**解决：**
1. 确认 `edge://extensions` 页面左上角的「开发人员模式」已开启
2. 点「加载解压缩的扩展」→ 选择 `extension` 文件夹（里面有 manifest.json 的那个）

### ❌ `read_text` 返回空内容或 `"content script not ready"`

**原因：** 浏览器没有把 content.js 注入到当前页面。

**解决：**

1. **刷新页面**（F5）让 content.js 重新注入
2. 如果还是不行，重启扩展：
   - 在 `edge://extensions` 页面关掉扩展开关 → 再打开
   - 或者删除扩展 → 重新加载

### ❌ `read_text` 返回成功但内容是空的，或者 `write_text` 写不进去

**原因：** 目标页面用了 Vue/React 等现代框架，直接赋值 `el.value` 不触发响应式更新。

**解决：** 已经内置了修复——代码会自动用原生 setter + dispatchEvent。如果还有问题，试试：

```cmd
python hermes_client.py type_text <selector> <text>
```

（`type_text` 是逐字模拟键盘输入，而非直接赋值）

### ❌ 扩展显示「已连接」但不响应任何命令

**原因：** 新建的标签页需要刷新才能注入 content.js。

**解决：** 导航到新页面后，等 1-2 秒再执行操作。或者手动刷新一下页面。

### ❌ 截图返回空

**原因：** 某些受限页面（chrome://、edge://）不能截图。

**解决：** 在普通网页（如 baidu.com）上执行截图。如果还是空，试试兼容模式：

```cmd
python hermes_client.py screenshot
```

如果一直失败，可以手动截屏：Windows + Shift + S

### ❌ 桥接启动时说 `Address already in use`

**原因：** 端口 9876 被其他程序占用了。

**解决：**

```cmd
netstat -ano | findstr :9876
```

记下最后一列的 PID，然后：

```cmd
taskkill /PID <那个数字> /F
```

或者更改 bridge.py 第 7 行的 `PORT = 9876` 为其他端口（比如 9875），同步修改 `offscreen.js` 里的端口号，然后重装扩展。

### ❌ 修改了 manifest.json 后扩展不工作了

**原因：** Chromium 扩展在权限变更后必须**删除重装**，仅仅是「重新加载」不行。

**解决：**
1. 在 `edge://extensions` 上点「删除」扩展
2. 再次点击「加载解压缩的扩展」
3. 刷新所有页面

### ❌ bridge.py 提示 `os.name == 'nt'` 相关错误

**原因：** 你在 Linux/Mac 上运行了 Windows 专用代码（proxy_manager、某些 Windows 特有操作）。

**解决：** bridge.py 本身是跨平台的。只有 `proxy_manager.py` 依赖于 Windows 注册表。如果不在 Windows 上，忽略 proxy_manager 相关功能即可。

### ❌ Windows 防火墙弹出 Python 网络访问

**原因：** bridge.py 监听端口时触发了防火墙规则。

**解决：** 点击「允许访问」。这是安全的——bridge 只在 localhost（本机）监听。

---

## 与 Hermes Agent 集成

如果你在使用 [Hermes Agent](https://hermes-agent.nousresearch.com/)（本地 AI Agent 框架），项目附带了 Hermes Skill 文件（在 `skills/` 目录下）。

### 快速安装

```bash
# 将 skill 文件复制到 Hermes 的 skills 目录
cp -r skills/* ~/.hermes/skills/
```

### 统一入口：hermes-browser-control（推荐）

**日常浏览器操作只需要加载一个 skill：`hermes-browser-control`。**

它覆盖了：WS 命令封装、代理自动管理、多平台搜索、内容研究流水线、图片提取验证、网络诊断。

Hermes 里说"帮我搜一下xxx"或"找张配图"，Agent 会自动加载 browser-control。

### 底层参考：hermes-browser-bridge

仅在调试桥接本身（WS 断连、扩展不响应）时才需要加载。包含完整的架构说明、命令列表、踩坑记录。

### 调用示例

```python
from hermes_tools import terminal

# 读取页面
terminal("python3 ~/hermes-browser-bridge/hermes_client.py read_text", timeout=10)

# 点击按钮
terminal("python3 ~/hermes-browser-bridge/hermes_client.py click '#publish-btn'", timeout=10)

# 填写表单
terminal("python3 ~/hermes-browser-bridge/hermes_client.py write_text '#title' '标题'", timeout=10)

# 截图
terminal("python3 ~/hermes-browser-bridge/hermes_client.py screenshot", timeout=15)
```

---

## 代理自动管理（选装）

如果你使用 Clash Verge（翻墙工具）访问国际网站，`proxy_manager.py` 可以自动切换代理模式：

```cmd
python proxy_manager.py on     # 开启系统代理 + Clash 全局模式
python proxy_manager.py off    # 关闭系统代理 + Clash 规则模式
```

**前提条件：**
- 已安装 [Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev)
- Clash 核心端口 7897（默认）
- Clash API 端口 9090（默认），Secret 配置正确

如果不用代理/Clash，忽略这个文件就行，不影响核心功能。

---

## 项目文件结构

```
hermes-browser-bridge/
├── bridge.py              # [核心] WebSocket 桥接服务（跑在 Windows 上）
├── hermes_client.py       # [核心] 命令行客户端 50+ 命令
├── proxy_manager.py       # [选装] 代理自动开关（仅 Windows + Clash）
├── demo.py                # 演示 Python 脚本
├── gen_icons.py           # 扩展图标生成工具
├── INSTALL.md             # 安装指南（本文档）
├── README.md              # 项目介绍
├── extension/             # Chromium 浏览器扩展
│   ├── manifest.json      # MV3 扩展配置
│   ├── background.js      # Service Worker — 接收命令执行 Chrome API
│   ├── content.js         # 页面注入脚本（~460 行）
│   ├── offscreen.js       # Offscreen 文档 — 管理 WebSocket 持久连接
│   ├── offscreen.html     # Offscreen 页面
│   ├── popup.html         # 扩展弹窗界面
│   ├── popup.js           # 扩展弹窗逻辑
│   └── icons/             # 扩展图标（16/48/128）
└── skills/                # Hermes Agent Skill 文件（选装）
    ├── hermes-browser-control.md
    ├── hermes-browser-bridge.md
    └── browser-bridge-extension.md
```

---

## 开发踩坑记录

这个项目踩过的坑，直接写在这里让后人少走弯路：

### 1️⃣ MV3 Service Worker 30 秒断连

Service Worker 空闲 30 秒就会被浏览器杀掉。WebSocket 连接随之断开。

**解决：** 仅用 HTTP 轮询。扩展每 2 秒 `fetch("http://localhost:9877/poll")`，bridge 返回待处理命令。HTTP 请求本身就能唤醒 SW，不需要 WebSocket 心跳。

### 2️⃣ Content script 必须加消息监听器

如果 `content.js` 没有 `chrome.runtime.onMessage.addListener`，所有 `read_text`/`click` 都返回 "injection failed"。

**已内置修复。** 如果改过 content.js，注意检查。

### 3️⃣ 禁止 eval（CSP 策略）

`eval("return (" + code + ")")` 会被 Content Security Policy 阻止。

**已内置修复。** 改用 `new Function('return (' + code + ')')()`。

### 4️⃣ Vue/React 输入框不回显

`el.value = 'xxx'` 赋值后，Vue/React 不触发响应式更新，界面上看不出来。

**已内置修复。** 用原生 setter：

```javascript
const nativeSetter = Object.getOwnPropertyDescriptor(
  HTMLInputElement.prototype, 'value'
).set;
nativeSetter.call(el, newVal);
el.dispatchEvent(new Event('input', { bubbles: true }));
```

### 5️⃣ `captureVisibleTab` 需要用户手势

Chrome 的 `captureVisibleTab` 需要当前页面有用户交互（键盘/鼠标）。从命令行触发时经常失败。

**已内置修复。** 用 `chrome.debugger.attach` + `Page.captureScreenshot` 兜底。

### 6️⃣ 改 manifest 权限后必须重装

修改 `manifest.json` 的 permissions 后，浏览器会禁用扩展。点「重新加载」也没用。

**解决：** 删除扩展 → 重新加载 → 刷新所有已打开页面。

### 7️⃣ DNS 劫持问题

某些网络环境（校园网、酒店 WiFi、运营商）会劫持 DNS 返回广告页。

**表现：** 打开网页弹出广告、`read_text` 返回的不是目标内容。

**解决：** 在系统设置里把 DNS 改为 `114.114.114.114`。CMD 管理员：

```cmd
netsh interface ip set dns "以太网" static 114.114.114.114
ipconfig /flushdns
```

---

## License

MIT
