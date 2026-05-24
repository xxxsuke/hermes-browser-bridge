# Hermes Browser Bridge — 安装指南

## 架构

```
┌──────────────────────────────────────────────────┐
│  Edge / Chrome 浏览器 (Windows)                   │
│  ┌────────────────────────────────────────────┐  │
│  │  任意页面 (小红书/GitHub/...)               │  │
│  │  └─ content.js (读写页面)                  │  │
│  │       ↕ chrome.runtime.sendMessage          │  │
│  │  └─ background.js (WebSocket client)        │  │
│  └──────────────┬─────────────────────────────┘  │
└─────────────────┼────────────────────────────────┘
                  │ ws://localhost:9876
┌─────────────────┼────────────────────────────────┐
│  WSL / Linux    │                                │
│  ┌──────────────▼──────────────────────────┐     │
│  │  bridge.py (WebSocket Server + Router)   │     │
│  └──────────────┬──────────────────────────┘     │
│                 │ ws://localhost:9876             │
│  ┌──────────────▼──────────────────────────┐     │
│  │  Hermes Agent                            │     │
│  │  → execute_code: hermes_client.py       │     │
│  └──────────────────────────────────────────┘     │
└──────────────────────────────────────────────────┘
```

## 安装（3 步）

### 步骤 1：启动 Python 桥接（在 WSL 终端）

```bash
# 安装依赖
pip install websockets

# 启动桥接（前台运行，保持终端开着）
python3 ~/hermes-browser-bridge/bridge.py
```

看到:
```
╔══════════════════════════════════════════╗
║     Hermes Browser Bridge v1.0          ║
║     WebSocket: ws://localhost:9876      ║
╚══════════════════════════════════════════╝
```
就成功了。保持这个终端不要关。

### 步骤 2：安装浏览器扩展

**如果扩展目录在 WSL 中：**
1. 打开 Edge 浏览器
2. 地址栏输入: `edge://extensions`
3. 打开「开发人员模式」（左下角开关）
4. 点击「加载解压缩的扩展」
5. 在地址栏输入: `\\wsl.localhost\Ubuntu\home\suke\hermes-browser-bridge\extension`
6. 回车 → 选择文件夹

**如果 WSL 路径打不开：复制到 Windows：**

在 WSL 终端执行:
```bash
cp -r ~/hermes-browser-bridge/extension /mnt/c/Users/10737/Desktop/hermes-extension/
```

然后在 Edge 中:
1. `edge://extensions` → 开发人员模式
2. 加载解压缩的扩展 → 选择 `C:\Users\10737\Desktop\hermes-extension\`

### 步骤 3：验证连接

1. 打开任意网页（如 baidu.com）
2. 点击扩展图标 → 应显示「已连接」
3. 在 WSL 终端运行:
```bash
python3 ~/hermes-browser-bridge/hermes_client.py read_text
```
4. 看到页面文字内容 → 成功！

## 在 Hermes 中使用

通过 execute_code 调用:

```python
from hermes_tools import terminal

# 读取当前页面
terminal("python3 ~/hermes-browser-bridge/hermes_client.py read_text", timeout=10)

# 点击按钮
terminal("python3 ~/hermes-browser-bridge/hermes_client.py click '.publish-btn'", timeout=10)

# 填写表单
terminal("python3 ~/hermes-browser-bridge/hermes_client.py write_text '#title' '我的标题'", timeout=10)

# 导航
terminal("python3 ~/hermes-browser-bridge/hermes_client.py navigate 'https://xiaohongshu.com'", timeout=15)
```

## 开机自启（可选）

```bash
# 在 WSL 中设置 systemd 服务
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
systemctl --user status hermes-bridge.service
```

## 支持的浏览器

- ✅ Microsoft Edge (Chromium)
- ✅ Google Chrome
- ✅ Brave
- ✅ Opera
- ✅ Vivaldi
- ✅ 所有基于 Chromium 的浏览器

## 故障排查

| 问题 | 解决 |
|------|------|
| 扩展显示「未连接」 | 确认 bridge.py 正在运行 |
| 连接超时 | 检查防火墙是否拦截 9876 端口 |
| content script not ready | 刷新页面 |
| WSL 路径打不开 | 复制到 Windows 桌面 |
