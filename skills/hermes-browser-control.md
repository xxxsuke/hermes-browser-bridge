---
name: hermes-browser-control
description: 浏览器统一控制入口 — WS 连接、代理管理、多平台搜索、内容研究、图片提取、网络诊断。一次加载覆盖所有浏览器操作，不再需要分别加载 bridge 和 operations。
version: 3.0.0
category: automation
tags: [browser, proxy, search, images, network, content-research, unified]
triggers:
  - 浏览器操作 / 打开网页 / 搜索 / 截图
  - 写文章 / 搜素材 / 配图 / 提取图片
  - 代理 / 翻墙 / 网络不通
  - 任何需要操控浏览器的任务
---

# Browser Control — 浏览器统一入口 v3

**一个 skill 覆盖所有浏览器操作。** 不再需要分别加载 `browser-bridge` 和 `browser-operations`。

底层依赖：hermes-browser-bridge（bridge.py + 扩展），深入调试时参考 `hermes-browser-bridge` skill（架构/项目结构/踩坑记录/故障排查）。

---

## 零、速查：WS 命令封装

所有浏览器操作的基础。直接复制使用：

```python
import asyncio, json, websockets

async def cmd(ws, action, params=None, tab_id=None, timeout=15):
    rid = f't_{int(__import__("time").time()*1000)}'
    await ws.send(json.dumps({'type':'command','id':rid,'action':action,'tabId':tab_id,'params':params or {}}))
    return json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))

async def main():
    async with websockets.connect('ws://localhost:9876') as ws:
        await ws.send(json.dumps({'type':'register','client':'hermes'}))
        await asyncio.wait_for(ws.recv(), timeout=5)
        # ... 你的操作 ...
```

全部命令：`list_tabs` `activate_tab` `new_tab` `close_tab` `reload_tab` `navigate` `read_text` `read_html` `click` `scroll` `screenshot` `get_images` `get_links` `type_text` `key_press` `create_window` `close_window` `list_windows`

---

## 一、铁律（违反必出事）

1. **close_window 必须用 windowId** — 从 create_window 返回值取，禁止通过 tabId 反查
2. **新标签先 reload** — navigate 后 reload_tab 等 3s，确保 content.js 注入
3. **独立窗口，用完即关** — create_window 干活，完事 close_window
4. **标签 ≤ 10 个**
5. **代理按需开关** — 默认直连，国际站自动开，用完即关
6. **NO_PROXY=localhost** — 代理排除 localhost，否则劫持 WS

---

## 二、代理自动管理

**原则：默认直连，访问国际站时自动开全局代理，用完即关。**

```python
def need_proxy(url):
    intl = ['youtube.com','tiktok.com','twitter.com','x.com',
            'github.com','google.com','openai.com','reddit.com','discord.com',
            'facebook.com','instagram.com','medium.com','wikipedia.org']
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower()
    return any(d in domain for d in intl)

# 开代理
subprocess.run(['python3','~/hermes-browser-bridge/proxy_manager.py','on'])
await asyncio.sleep(2)

# 关代理
subprocess.run(['python3','~/hermes-browser-bridge/proxy_manager.py','off'])
```

---

## 三、多平台搜索

### 国内（直连）

| 平台 | URL 模板 | 备注 |
|------|----------|------|
| 搜狗 | `sogou.com/web?query={}` | 中文最佳 |
| 头条搜索 | `so.toutiao.com/search?keyword={}` | |
| 头条图片 | `so.toutiao.com/search?keyword={}&tab=image` | **配图首选** |
| 小红书 | `xiaohongshu.com/search_result?keyword={}` | |
| 微博 | `s.weibo.com/weibo?q={}` | |
| B站 | `search.bilibili.com/all?keyword={}` | |
| 百度 | `baidu.com/s?wd={}` | ⚠️ 验证码多 |
| 知乎 | `zhihu.com/search?type=content&q={}` | ⚠️ 反爬 |

### 国际（需代理）

| 平台 | URL 模板 |
|------|----------|
| GitHub | `github.com/search?q={}&type=repositories` |
| X/Twitter | `x.com/search?q={}` |
| YouTube | `youtube.com/results?search_query={}` |

---

## 四、内容研究流水线

```
开独立窗口 → 多引擎搜索 → 筛选文章 → 点进原文 → 滚动到底 → 提取配图 → 判断完整性 → 截图取证 → 关窗
```

### 点进原文 + 滚动

```python
await cmd(ws, 'click', {'selector': '.result h3 a'}, tab)
await asyncio.sleep(5)
r = await cmd(ws, 'list_tabs')
art_tab = r['tabs'][-1]['id']

for i in range(25):
    rr = await cmd(ws, 'scroll', {'direction':'down','amount':800}, art_tab)
    if rr.get('scrollY',0) >= rr.get('maxScroll',99999)-100:
        break

r = await cmd(ws, 'read_text', {'maxLength': 20000}, art_tab)
```

### 完整性判断（检查最后 300 字）

| 标识 | 判断 |
|------|------|
| `举报` `版权` `免责声明` `界面新闻` `转载` `作者` | ✅ 完整 |
| 广告推荐 / 相关阅读 / 热搜榜 | ⚠️ 截断 |
| `展开全文` `阅读更多` | ❌ 需点击展开 |

### 引用铁律

- 真实来源，不编造
- 所有数据、排名、事实必须来自打开过的原文
- 每篇文章至少截 2 张图留存

---

## 五、图片提取与配图

### 图片源优先级

| 优先级 | 来源 | 可靠性 |
|--------|------|:---:|
| **1** | 头条图片搜索 (`so.toutiao.com?tab=image`) | ✅ |
| 2 | 非 SPA 新闻站原文 | ✅ |
| 3 | Pollinations AI 生成 | ⚠️ 15% 成功率 |
| 4 | HTML 卡片（1200x800 截图） | ✅ 兜底 |

### 千万别做的事

- ❌ 点进头条文章详情页提取图片（SPA，get_images 返回空）
- ❌ 用 Bing 图片（只有缩略图 200-346px）
- ❌ 用百度图片（验证码地狱）

### 头条图片搜索流程

```python
from urllib.parse import quote
url = f"https://so.toutiao.com/search?keyword={quote(keyword)}&tab=image"
# 用 Hermes 内置 browser_navigate + browser_get_images
# Python 端手动过滤：尺寸≥200 + 黑名单域名
# 下载到 D:\Download\article-images\
```

### 图片验证铁律

1. **必须用 vision_analyze 验证** — 不能用标题/alt 猜测
2. **不匹配果断换源**

---

## 六、网络诊断（5 层递进）

用户说"网不通"时按顺序走：

```bash
# Layer 1: 网络存活？
ping -c 2 -W 2 192.168.31.1
nslookup baidu.com

# Layer 2: 直连可达？
env -u http_proxy -u https_proxy curl -sI --connect-timeout 5 https://www.baidu.com

# Layer 3: 代理端口？
ss -tlnp | grep 7897

# Layer 4: Windows 系统代理
powershell.exe -Command "Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' | Select-Object ProxyEnable,ProxyServer | Format-List"

# Layer 5: WSL2 环境变量
env | grep -iE "http_proxy|https_proxy|all_proxy"
```

### 常见修复

**Clash Verge ProxyServer 残留**（关闭代理后仍无法上网）：
```bash
powershell.exe -Command "Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -Name ProxyServer -Value ''"
```
然后完全退出浏览器重开。

**MiWiFi 劫持**（跳到 miwifi.com）：
```bash
sudo bash -c 'echo "nameserver 114.114.114.114" > /etc/resolv.conf'
powershell.exe -Command "ipconfig /flushdns"
```

---

## 七、独立窗口模板

```python
# 开窗
r = await cmd(ws, 'create_window', {'url': 'https://目标'})
wid = r['windowId']
tid = r['tabId']

# 干活...
await cmd(ws, 'reload_tab', {}, tid)
await asyncio.sleep(3)

# 关窗（必须用 windowId！）
await cmd(ws, 'close_window', {'windowId': wid})
```

---

## 八、故障速查

| 问题 | 处理 |
|------|------|
| 桥接挂了 | 重启 Windows bridge.py |
| `injection failed` / 0字 | reload_tab + 等 3s |
| 截图失败 | debugger API 自动兜底 |
| WS 连接失败 | bridge.py 未运行，检查 `ss -tlnp \| grep 9876` |
| 搜索结果不显示 | 换搜索引擎 |
| 劫持/WLAN | 立即停止，DNS→114 |
| 验证码 | 截图通知用户，不硬闯 |
| 图片全被过滤 | 换头条图片搜索 |
| SPA 页面返回空 | 不要 reload，换非 SPA 站 |
| vision_analyze 说配图不匹配 | 换源 |

---

## 九、与旧 skill 的关系

- **hermes-browser-bridge** → 底层参考（安装/架构/踩坑记录），日常不需要加载
- **本 skill（hermes-browser-control）** → 日常唯一入口，覆盖所有浏览器操作
