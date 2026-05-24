---
name: hermes-browser-control
description: 像人一样操控 Edge/Chrome。独立窗口、多平台搜索、自动登录、下载、提取图片、代理自动管理、视频帧分析。
version: 2.1.0
triggers:
  - 浏览器控制
  - 打开网页
  - 搜索
  - 下载
  - 登录
  - 提取图片
  - 代理
  - 翻墙
---

# Hermes Browser Control Skill v2.1

像人一样操控浏览器：搜索、登录、下载、提取、截图、关窗。**自动代理管理：选节点、开系统代理、用完即关。**

## 架构

```
Hermes (WSL) → ws://localhost:9876 → bridge.py (Windows) → offscreen.js → background.js → Edge
                                     ↕ Clash API (9090) + 注册表代理开关
```

## 核心原则

1. **单窗口** — 用完关，再开新
2. **≤10 标签**
3. **网络问题先诊断**
4. **代理按需开关** — 访问国际站时开系统代理，用完关。Clash 后台一直跑。

---

## 一、代理自动管理（按需开关）

**原则：默认直连，访问国际站时自动开全局代理，用完即关。**

### 判断是否需要代理

```python
def need_proxy(url):
    intl = ['youtube.com','tiktok.com','twitter.com','x.com',
            'github.com','google.com','openai.com','reddit.com','discord.com',
            'facebook.com','instagram.com','medium.com','wikipedia.org']
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower()
    return any(d in domain for d in intl)
```

### 自动开关

```bash
# 开 — 系统代理 + Clash 全局模式
python3 ~/hermes-browser-bridge/proxy_manager.py on

# 关 — 直连 + Clash 规则模式
python3 ~/hermes-browser-bridge/proxy_manager.py off
```

### 使用流程

```python
if need_proxy(target_url):
    subprocess.run(['python3','~/hermes-browser-bridge/proxy_manager.py','on'])
    await asyncio.sleep(2)

# ... 访问网站 ...

if need_proxy(target_url):
    subprocess.run(['python3','~/hermes-browser-bridge/proxy_manager.py','off'])
```

**不做手动开关，不做常开。**

---

## 二、多平台搜索

| 平台 | 搜索 URL | 需要代理 |
|------|----------|----------|
| 百度 | `baidu.com/s?wd=` | ❌ |
| 搜狗 | `sogou.com/web?query=` | ❌ |
| 小红书 | `xiaohongshu.com/search_result?keyword=` | ❌ |
| 微博 | `s.weibo.com/weibo?q=` | ❌ |
| 抖音 | `douyin.com/search/` | ❌ |
| 知乎 | `zhihu.com/search?type=content&q=` | ❌ |
| B站 | `search.bilibili.com/all?keyword=` | ❌ |
| GitHub | `github.com/search?q=` | ⚠️ 可能需要 |
| X/Twitter | `x.com/search?q=` | ✅ |
| TikTok | `tiktok.com/search?q=` | ✅ |
| YouTube | `youtube.com/results?search_query=` | ✅ |

---

## 三、登录流程

填表→点击→检测验证码→截图通知用户。遇到人机验证立即通知，不硬闯。

## 四、图片提取与文件下载

get_images → 过滤 avatar/icon → download 保存。支持 PDF/文档 URL 下载。

## 五、视频帧分析

打开视频页 → 每 N 秒截图 → vision_analyze 逐帧识别 → 拼成故事板。YouTube 可配合 transcript API 拿字幕。

## 六、命令速查

### 窗口标签
create_window / close_window / close_tab / list_tabs / new_tab / activate_tab / reload_tab / navigate

### 页面读写
read_text / read_html / read_element / get_links / get_images / scroll

### 鼠标键盘
click / double_click / right_click / hover / drag / write_text / key_press / type_text / find_in_page

### 导航工具
go_back / go_forward / set_zoom / get_zoom / print

### 下载书签
download / list_downloads / create_bookmark / remove_bookmark / search_bookmarks

### 数据
screenshot / search_history / list_bookmarks / list_windows / get_tab_info / clear_data

## 七、网络诊断

| 问题 | 修复 |
|------|------|
| MiWiFi劫持 | DNS→114 + flushdns |
| SSL错误 | ntpdate 同步时间 |
| 桥接挂了 | 重启 Windows bridge.py |
| 代理不可用 | 检查 Clash:9090 |
| Edge 打不开 | 检查系统代理设置 |
