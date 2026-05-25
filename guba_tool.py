#!/usr/bin/env python3
"""
东方财富股吧自动化工具 v1.0
功能: 发帖 / 回复 / 批量发帖 / 定时发帖

用法:
  # 发帖（单条）
  guba_tool.py post <stock_code> <标题> <内容>
  示例: guba_tool.py post 300750 "宁德时代后市怎么看？" "最近走势不错，大家怎么看？"

  # 回复帖子
  guba_tool.py reply <post_url> <回复内容>
  示例: guba_tool.py reply "https://guba.eastmoney.com/news,300750,1713788676.html" "长期看好！"

  # 批量发帖（从 JSON 配置文件）
  guba_tool.py batch <config.json>
  示例: guba_tool.py batch posts.json

  # 定时发帖（指定时间 + 配置文件）
  guba_tool.py schedule <config.json> <HH:MM>
  示例: guba_tool.py schedule posts.json 14:30

  # 预览帖子列表
  guba_tool.py list <stock_code> [maxCount]
  示例: guba_tool.py list 300750 10
"""

import asyncio, json, sys, time, os, websockets
from datetime import datetime, timedelta

WS_URL = "ws://localhost:9876"
TIMEOUT = 30

# ==================== WebSocket 通信 ====================

async def send_raw_cmd(action, params=None, tab_id=None, timeout=TIMEOUT):
    """发送原始命令到浏览器桥接"""
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({"type": "register", "client": "hermes", "version": "1.1.0"}))
        await asyncio.wait_for(ws.recv(), timeout=5)
        rid = f"cmd_{int(time.time() * 1000)}"
        cmd = {"type": "command", "id": rid, "action": action, "tabId": tab_id, "params": params or {}}
        await ws.send(json.dumps(cmd))
        try:
            resp_raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
            return json.loads(resp_raw)
        except asyncio.TimeoutError:
            return {"error": "timeout", "id": rid}

async def cmd_navigate(url, tab_id=None):
    """导航到URL"""
    return await send_raw_cmd("navigate", {"url": url}, tab_id, 15)

async def cmd_click(selector, tab_id=None):
    """点击元素"""
    return await send_raw_cmd("click", {"selector": selector}, tab_id, 15)

async def cmd_write_text(selector, text, tab_id=None):
    """写入文本到元素"""
    return await send_raw_cmd("write_text", {"selector": selector, "text": text}, tab_id, 15)

async def cmd_read_text(max_length=2000, tab_id=None):
    """读取页面文本"""
    return await send_raw_cmd("read_text", {"maxLength": max_length}, tab_id, 15)

async def cmd_scroll(direction="down", amount=500, tab_id=None):
    """滚动页面"""
    return await send_raw_cmd("scroll", {"direction": direction, "amount": amount}, tab_id, 15)

# ==================== 工具函数 ====================

def find_stock_tab(tabs, stock_code=None):
    """从标签列表中查找合适的股吧标签页"""
    for t in tabs:
        url = t.get("url", "")
        title = t.get("title", "")
        # 优先匹配指定股票代码
        if stock_code and stock_code in url:
            return t["id"]
        # 匹配任何股吧页面
        if "guba.eastmoney" in url or "东方财富" in title:
            return t["id"]
    return None

def extract_post_id(url):
    """从帖子URL提取 post_id"""
    # URL格式: /news,300750,1713788676.html
    import re
    m = re.search(r'news,(\d+),(\d+)\.html', url)
    if m:
        return m.group(2)
    return None

# ==================== 核心操作 ====================

async def open_post_editor(tab_id):
    """打开发帖编辑器"""
    r = await cmd_click(".fastpost_btn", tab_id)
    if "error" in r:
        return {"error": f"点击发新帖失败: {r.get('error')}"}
    await asyncio.sleep(2)
    
    # 展开标题输入
    r = await cmd_click(".add-title-box", tab_id)
    await asyncio.sleep(1)
    
    return {"success": True}

async def post_to_board(stock_code, title, content, tab_id=None):
    """
    发帖到指定股票吧
    stock_code: 股票代码，如 "300750"
    title: 帖子标题
    content: 帖子内容
    """
    board_url = f"https://guba.eastmoney.com/list,{stock_code}.html"
    
    # 1. 导航到股票吧页面
    r = await cmd_navigate(board_url, tab_id)
    if "ok" not in r:
        # 可能 tab_id 错了，尝试找新标签
        r2 = await send_raw_cmd("list_tabs")
        tabs = r2.get("tabs", [])
        for t in tabs:
            if stock_code in t.get("url", ""):
                tab_id = t["id"]
                break
        await cmd_navigate(board_url, tab_id)
    
    await asyncio.sleep(4)
    
    # 2. 打开编辑器
    r = await open_post_editor(tab_id)
    if "error" in r:
        return r
    
    # 3. 写入标题
    r = await cmd_write_text(".xeditor_title", title, tab_id)
    await asyncio.sleep(0.5)
    
    # 4. 写入内容到 Jodit 编辑器
    r = await cmd_write_text(".jodit-wysiwyg", content, tab_id)
    await asyncio.sleep(0.5)
    
    # 5. 点击发布
    r = await cmd_click(".submit_btn", tab_id)
    await asyncio.sleep(3)
    
    # 6. 验证
    r = await cmd_read_text(500, tab_id)
    text = r.get("text", "")
    
    if content[:15] in text:
        return {"success": True, "message": f"✅ 帖子已发布到 {stock_code}吧", "stock_code": stock_code}
    else:
        return {"success": False, "message": f"⚠️ 可能发布成功，但未在页面找到内容确认", "stock_code": stock_code}

async def reply_to_post(post_url, content, tab_id=None):
    """
    回复帖子
    post_url: 帖子完整 URL
    content: 回复内容
    """
    # 1. 导航到帖子详情页
    r = await cmd_navigate(post_url, tab_id)
    await asyncio.sleep(4)
    
    # 查找当前标签
    if tab_id is None:
        r = await send_raw_cmd("list_tabs")
        tabs = r.get("tabs", [])
        for t in tabs:
            url = t.get("url", "")
            if "news," in url:
                tab_id = t["id"]
                break
    
    # 2. 写入回复内容到文本框
    r = await cmd_write_text("textarea.gb_textarea", content, tab_id)
    await asyncio.sleep(0.5)
    
    # 3. 点击发布按钮
    r = await cmd_click(".rebtns.resubmit", tab_id)
    await asyncio.sleep(3)
    
    # 4. 验证
    r = await cmd_read_text(500, tab_id)
    text = r.get("text", "")
    
    if content[:15] in text:
        return {"success": True, "message": "✅ 回复已发布！"}
    else:
        return {"success": False, "message": "⚠️ 回复可能已发布，但未确认到内容"}

async def batch_post(config_file):
    """
    批量发帖
    config_file: JSON 配置文件路径
    """
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    posts = config.get("posts", [])
    if not posts:
        return {"error": "配置文件中没有帖子(posts)数据"}
    
    results = []
    for i, post in enumerate(posts):
        print(f"\n[{i+1}/{len(posts)}] 发帖到 {post.get('stock_code')}...")
        r = await post_to_board(
            post["stock_code"],
            post["title"],
            post["content"]
        )
        print(f"  {r.get('message', '')}")
        results.append(r)
        
        if i < len(posts) - 1:
            delay = config.get("interval", 10)
            print(f"  等待 {delay} 秒...")
            await asyncio.sleep(delay)
    
    success = sum(1 for r in results if r.get("success"))
    return {
        "success": success,
        "total": len(posts),
        "results": results,
        "message": f"批量发帖完成: {success}/{len(posts)} 成功"
    }

async def scheduled_post(config_file, schedule_time):
    """
    定时发帖
    config_file: JSON 配置文件
    schedule_time: 定时时间 "HH:MM" 格式
    """
    now = datetime.now()
    target = datetime.strptime(schedule_time, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day
    )
    
    if target < now:
        target += timedelta(days=1)
    
    wait_seconds = (target - now).total_seconds()
    print(f"⏰ 计划在 {target.strftime('%Y-%m-%d %H:%M')} 发帖")
    print(f"   还需等待 {int(wait_seconds)} 秒 ({wait_seconds/60:.1f} 分钟)")
    
    # 等待
    await asyncio.sleep(wait_seconds)
    
    print(f"\n🚀 时间到！开始发帖...")
    return await batch_post(config_file)

async def list_posts(stock_code, max_count=20):
    """列出帖子列表"""
    r = await send_raw_cmd("list_tabs")
    tabs = r.get("tabs", [])
    
    tab_id = find_stock_tab(tabs, stock_code)
    
    if not tab_id:
        # 导航到股票吧
        board_url = f"https://guba.eastmoney.com/list,{stock_code}.html"
        r = await send_raw_cmd("new_tab", {"url": board_url})
        tab_id = r.get("tabId")
        await asyncio.sleep(4)
    
    # 激活标签
    await send_raw_cmd("activate_tab", {}, tab_id)
    await asyncio.sleep(1)
    
    # 读取页面内容
    r = await cmd_read_text(5000, tab_id)
    text = r.get("text", "")
    
    # 解析帖子列表
    lines = text.split("\n")
    posts = []
    for i, line in enumerate(lines):
        if line.strip() and len(line) > 10 and i > 0:
            posts.append(line.strip())
    
    # 查找帖子标题行
    # 东方财富股吧的帖子列表格式:
    # 阅读 评论 标题 作者 最后更新
    # 1 0 帖子标题 作者 时间
    print(f"\n=== {stock_code}吧 最新帖子 ===")
    print("-" * 60)
    
    # 简单解析：找到"最新发帖"后的内容
    idx = text.find("最新发帖")
    if idx >= 0:
        post_section = text[idx:]
        lines = post_section.split("\n")
        count = 0
        for i, line in enumerate(lines):
            if i >= 2:  # 跳过表头
                line = line.strip()
                if line and len(line) > 5 and not line.startswith("阅读"):
                    print(f"  {line[:80]}")
                    count += 1
                    if count >= max_count:
                        break
    
    return {"success": True, "count": len(posts)}

# ==================== 配置模板 ====================

def generate_config_template():
    """生成批量发帖配置文件模板"""
    template = {
        "interval": 10,  # 发帖间隔（秒）
        "posts": [
            {
                "stock_code": "300750",
                "title": "宁德时代后市怎么看？",
                "content": "宁德时代最近走势不错，大家怎么看后市？感觉新能源有回暖迹象。"
            },
            {
                "stock_code": "000001",
                "title": "平安银行最近表现",
                "content": "平安银行最近表现不错，大家觉得呢？"
            }
        ]
    }
    return template

# ==================== 主入口 ====================

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    action = sys.argv[1]
    args = sys.argv[2:]
    
    if action == "post":
        if len(args) < 3:
            print("用法: guba_tool.py post <stock_code> <标题> <内容>")
            return
        stock_code = args[0]
        title = args[1]
        content = " ".join(args[2:]) if len(args) > 2 else ""
        result = asyncio.run(post_to_board(stock_code, title, content))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif action == "reply":
        if len(args) < 2:
            print("用法: guba_tool.py reply <post_url> <回复内容>")
            return
        post_url = args[0]
        content = " ".join(args[1:])
        result = asyncio.run(reply_to_post(post_url, content))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif action == "batch":
        if len(args) < 1:
            print("用法: guba_tool.py batch <config.json>")
            return
        result = asyncio.run(batch_post(args[0]))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif action == "schedule":
        if len(args) < 2:
            print("用法: guba_tool.py schedule <config.json> <HH:MM>")
            return
        result = asyncio.run(scheduled_post(args[0], args[1]))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif action == "list":
        stock_code = args[0] if args else "300750"
        max_count = int(args[1]) if len(args) > 1 else 10
        asyncio.run(list_posts(stock_code, max_count))
    
    elif action == "template":
        template = generate_config_template()
        print(json.dumps(template, ensure_ascii=False, indent=2))
    
    else:
        print(f"未知命令: {action}")
        print(__doc__)

if __name__ == "__main__":
    main()
