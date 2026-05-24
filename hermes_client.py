#!/usr/bin/env python3
"""
Hermes Browser Bridge Client v1.1 — 完整浏览器控制

用法:
  # 标签页
  hermes_client.py list_tabs
  hermes_client.py activate_tab <tabId>
  hermes_client.py reload_tab [tabId]
  hermes_client.py close_tab <tabId>
  hermes_client.py new_tab <url>
  hermes_client.py duplicate_tab <tabId>
  hermes_client.py move_tab <tabId> <index>
  hermes_client.py pin_tab <tabId>
  hermes_client.py go_back [tabId]
  hermes_client.py go_forward [tabId]

  # 页面读写
  hermes_client.py read_text [maxLength]
  hermes_client.py read_html
  hermes_client.py get_links [maxCount]
  hermes_client.py get_images [maxCount]
  hermes_client.py read_element <selector>
  hermes_client.py write_text <selector> <text>
  hermes_client.py click <selector>
  hermes_client.py scroll [direction] [amount]
  hermes_client.py navigate <url> [tabId]

  # 窗口
  hermes_client.py create_window <url>
  hermes_client.py list_windows

  # 书签
  hermes_client.py list_bookmarks
  hermes_client.py create_bookmark <title> <url>
  hermes_client.py remove_bookmark <bookmarkId>
  hermes_client.py search_bookmarks <query>

  # 历史
  hermes_client.py search_history <query> [maxResults]
  hermes_client.py delete_history all|range|url <arg>

  # 下载
  hermes_client.py download <url> [filename]
  hermes_client.py list_downloads

  # DevTools
  hermes_client.py attach_debugger <tabId>
  hermes_client.py debugger_cmd <tabId> <method> [params_json]
  hermes_client.py detach_debugger <tabId>

  # 截图/缩放/打印
  hermes_client.py screenshot
  hermes_client.py set_zoom <zoom> [tabId]
  hermes_client.py get_zoom [tabId]
  hermes_client.py print_page

  # 清除数据
  hermes_client.py clear_cache
  hermes_client.py clear_cookies
  hermes_client.py clear_all_data

  # 信息
  hermes_client.py get_tab_info [tabId]
"""

import asyncio, json, sys, time, websockets

WS_URL = "ws://localhost:9876"
TIMEOUT = 30

async def send_command(action, params=None, tab_id=None, timeout=TIMEOUT):
    request_id = f"cmd_{int(time.time() * 1000)}"
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({"type": "register", "client": "hermes", "version": "1.1.0"}))
        await asyncio.wait_for(ws.recv(), timeout=5)
        cmd = {"type": "command", "id": request_id, "action": action, "tabId": tab_id, "params": params or {}}
        await ws.send(json.dumps(cmd))
        try:
            resp_raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
            resp = json.loads(resp_raw)
            print(json.dumps(resp, ensure_ascii=False, indent=2))
        except asyncio.TimeoutError:
            print(json.dumps({"error": "timeout", "id": request_id}, ensure_ascii=False))

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    action = sys.argv[1]
    args = sys.argv[2:]
    params = {}

    # 标签页
    if action == "list_tabs": pass
    elif action == "activate_tab": tab_id = int(args[0]) if args else None; asyncio.run(send_command("activate_tab", {}, tab_id)); return
    elif action == "reload_tab": tab_id = int(args[0]) if args else None; asyncio.run(send_command("reload_tab", {}, tab_id)); return
    elif action == "close_tab": tab_id = int(args[0]); asyncio.run(send_command("close_tab", {}, tab_id)); return
    elif action == "new_tab": params = {"url": args[0] if args else "about:blank"}; asyncio.run(send_command("new_tab", params)); return
    elif action == "duplicate_tab": tab_id = int(args[0]); asyncio.run(send_command("duplicate_tab", {}, tab_id)); return
    elif action == "move_tab": tab_id = int(args[0]); params = {"index": int(args[1]) if len(args) > 1 else 0}; asyncio.run(send_command("move_tab", params, tab_id)); return
    elif action == "pin_tab": tab_id = int(args[0]); asyncio.run(send_command("pin_tab", {}, tab_id)); return
    elif action == "go_back": tab_id = int(args[0]) if args else None; asyncio.run(send_command("go_back", {}, tab_id)); return
    elif action == "go_forward": tab_id = int(args[0]) if args else None; asyncio.run(send_command("go_forward", {}, tab_id)); return

    # 页面读写
    elif action == "read_text": params = {"maxLength": int(args[0]) if args else 10000}
    elif action == "read_html": params = {"maxLength": int(args[0]) if args else 50000}
    elif action == "get_links": params = {"maxCount": int(args[0]) if args else 50}
    elif action == "get_images": params = {"maxCount": int(args[0]) if args else 50}
    elif action == "read_element": params = {"selector": args[0] if args else "body"}
    elif action == "write_text": params = {"selector": args[0] if args else "", "text": " ".join(args[1:]) if len(args) > 1 else ""}
    elif action == "click": params = {"selector": args[0] if args else ""}
    elif action == "scroll": params = {"direction": args[0] if args else "down", "amount": int(args[1]) if len(args) > 1 else None}
    elif action == "navigate": tab_id = int(args[1]) if len(args) > 1 else None; params = {"url": args[0]}; asyncio.run(send_command("navigate", params, tab_id)); return

    # 窗口
    elif action == "create_window": params = {"url": args[0] if args else "about:blank"}; asyncio.run(send_command("create_window", params)); return
    elif action == "list_windows": asyncio.run(send_command("list_windows")); return

    # 书签
    elif action == "list_bookmarks": asyncio.run(send_command("list_bookmarks")); return
    elif action == "create_bookmark": params = {"title": args[0] if args else "Bookmark", "url": args[1] if len(args) > 1 else ""}
    elif action == "remove_bookmark": params = {"bookmarkId": args[0]}
    elif action == "search_bookmarks": params = {"query": " ".join(args)}

    # 历史
    elif action == "search_history": params = {"query": args[0] if args else "", "maxResults": int(args[1]) if len(args) > 1 else 50}
    elif action == "delete_history":
        if args and args[0] == "all": params = {"all": True}
        elif args and args[0] == "url" and len(args) > 1: params = {"historyId": args[1]}
        else: print("用法: delete_history all|url <url>"); return

    # 下载
    elif action == "download": params = {"url": args[0] if args else "", "filename": args[1] if len(args) > 1 else None}
    elif action == "list_downloads": params = {"limit": int(args[0]) if args else 20}

    # DevTools
    elif action == "attach_debugger": tab_id = int(args[0]); asyncio.run(send_command("attach_debugger", {}, tab_id)); return
    elif action == "detach_debugger": tab_id = int(args[0]); asyncio.run(send_command("detach_debugger", {}, tab_id)); return
    elif action == "debugger_cmd":
        tab_id = int(args[0]); method = args[1] if len(args) > 1 else "Page.getResourceTree"
        cmd_params = json.loads(args[2]) if len(args) > 2 else {}
        asyncio.run(send_command("debugger_cmd", {"method": method, "commandParams": cmd_params}, tab_id)); return

    # 截图/缩放/打印
    elif action == "screenshot": asyncio.run(send_command("screenshot")); return
    elif action == "set_zoom": tab_id = int(args[1]) if len(args) > 1 else None; params = {"zoom": float(args[0])}; asyncio.run(send_command("set_zoom", params, tab_id)); return
    elif action == "get_zoom": tab_id = int(args[0]) if args else None; asyncio.run(send_command("get_zoom", {}, tab_id)); return
    elif action == "print_page": asyncio.run(send_command("print")); return

    # 清除数据
    elif action == "clear_cache": params = {"cache": True}
    elif action == "clear_cookies": params = {"cookies": True}
    elif action == "clear_all_data": params = {"cache": True, "cookies": True, "history": True, "downloads": True}

    # 信息
    elif action == "get_tab_info": tab_id = int(args[0]) if args else None; asyncio.run(send_command("get_tab_info", {}, tab_id)); return

    else:
        print(json.dumps({"error": f"unknown action: {action}", "help": "python3 hermes_client.py (no args)"}, ensure_ascii=False))
        return

    asyncio.run(send_command(action, params))

if __name__ == "__main__":
    main()
