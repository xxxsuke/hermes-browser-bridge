#!/usr/bin/env python3
"""Hermes Browser Bridge v5 — 正确路由"""
import asyncio, json
import websockets
from websockets.asyncio.server import serve

PORT = 9876
ext_ws = None
pending = {}

async def handler(ws):
    global ext_ws
    client = "?"
    
    async for message in ws:
        msg = json.loads(message)
        
        if msg.get("type") == "register":
            client = msg.get("client", "?")
            if client == "extension":
                ext_ws = ws
            print(f"[+] {client}")
            await ws.send(json.dumps({"type": "registered"}))
            continue
        
        # Hermes → Extension: 转发命令
        if client == "hermes" and msg.get("type") == "command":
            if ext_ws and ext_ws.state.name == "OPEN":
                rid = msg["id"]
                fut = asyncio.get_running_loop().create_future()
                pending[rid] = fut
                await ext_ws.send(json.dumps(msg))
                try:
                    result = await asyncio.wait_for(fut, timeout=30)
                    await ws.send(json.dumps(result))
                except asyncio.TimeoutError:
                    pending.pop(rid, None)
                    try: await ws.send(json.dumps({"error": "timeout", "id": rid}))
                    except: pass
            else:
                await ws.send(json.dumps({"error": "no extension", "id": msg.get("id")}))
            continue
        
        # Extension → Hermes: 命令结果
        if client == "extension" and msg.get("type") == "reply":
            rid = msg.get("id")
            if rid and rid in pending:
                pending[rid].set_result(msg)
                del pending[rid]
            continue
    
    if client == "extension":
        ext_ws = None
    print(f"[-] {client}")

async def main():
    print(f"Bridge v5: ws://localhost:{PORT}")
    async with serve(handler, "127.0.0.1", PORT):
        await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())
