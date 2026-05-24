# Hermes Browser Bridge — Hermes 端 Skill

通过 WebSocket 连接浏览器扩展，让 Hermes 直接操作你的浏览器页面。

## 安装

```bash
# 1. 启动 Python 桥接
python3 ~/hermes-browser-bridge/bridge.py &

# 2. 在 Edge 中加载扩展
# edge://extensions → 开发者模式 → 加载解压缩的扩展
# 选择: ~/hermes-browser-bridge/extension/

# 3. 确认连接
# 打开任意页面，点击扩展图标看状态
```

## 使用方式

Hermes 通过 `execute_code` 或 `terminal` 调用 WebSocket 发送命令。

Python 脚本位置: `~/hermes-browser-bridge/hermes_client.py`

```python
# 在 Hermes 的 execute_code 中:
from hermes_tools import terminal
terminal("python3 ~/hermes-browser-bridge/hermes_client.py read_text")
```

## 可用命令

| 命令 | 说明 |
|------|------|
| `read_text` | 读取当前页面文字内容 |
| `read_html` | 读取页面 HTML |
| `get_links` | 获取所有链接 |
| `get_images` | 获取所有图片 |
| `read_element <selector>` | 读取指定元素 |
| `write_text <selector> <text>` | 填写文本 |
| `click <selector>` | 点击元素 |
| `scroll [up|down] [px]` | 滚动页面 |
| `navigate <url>` | 导航到 URL |
| `list_tabs` | 列出所有标签页 |
| `eval <js_code>` | 执行 JS 代码 |
