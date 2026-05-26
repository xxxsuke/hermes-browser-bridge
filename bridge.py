#!/usr/bin/env python3
"""Hermes Browser Bridge v6 — 心跳保活 + 内存清理"""
import asyncio, json, time
import websockets
from websockets.asyncio.server import serve

PORT = 9876
ext_ws = None
ext_last_seen = 0
pending = {}
MAX_PENDING = 200

async def heartbeat():
    """每30秒心跳 + 内存清理"""
    global ext_ws, ext_last_seen
    while True:
        await asyncio.sleep(30)
        now = time.time()
        
        # 清理超时 pending
        stale = [rid for rid, fut in pending.items() if fut.done() or (now - getattr(fut, '_created', now)) > 60]
        for rid in stale:
            pending.pop(rid, None)
        if stale:
            print(f"[HB] Cleaned {len(stale)} stale futures, {len(pending)} remaining")
        
        # 心跳检测扩展
        if ext_ws and ext_ws.state.name == "OPEN":
            try:
                await asyncio.wait_for(ext_ws.send(json.dumps({"type":"ping"})), timeout=5)
                ext_last_seen = now
            except:
                print("[HB] Extension ping failed, disconnecting")
                try: await ext_ws.close()
                except: pass
                ext_ws = None
        elif ext_ws:
            # 状态不是 OPEN，清理
            ext_ws = None

async def handler(ws):
    global ext_ws, ext_last_seen
    client = "?"
    
    async for message in ws:
        try:
            msg = json.loads(message)
        except:
            continue
        
        if msg.get("type") == "register":
            client = msg.get("client", "?")
            if client == "extension":
                ext_ws = ws
                ext_last_seen = time.time()
            print(f"[+] {client}")
            await ws.send(json.dumps({"type": "registered"}))
            continue
        
        if msg.get("type") == "pong":
            # 扩展心跳回复
            continue
        
        # Hermes → Extension: 转发命令
        if client == "hermes" and msg.get("type") == "command":
            if ext_ws and ext_ws.state.name == "OPEN":
                rid = msg["id"]
                # 内存保护：超过上限拒绝
                if len(pending) >= MAX_PENDING:
                    await ws.send(json.dumps({"error": "too many pending", "id": rid}))
                    continue
                
                fut = asyncio.get_running_loop().create_future()
                fut._created = time.time()
                pending[rid] = fut
                
                try:
                    await ext_ws.send(json.dumps(msg))
                    result = await asyncio.wait_for(fut, timeout=30)
                    await ws.send(json.dumps(result))
                except asyncio.TimeoutError:
                    pending.pop(rid, None)
                    try: await ws.send(json.dumps({"error": "timeout", "id": rid}))
                    except: pass
                except Exception as e:
                    pending.pop(rid, None)
                    try: await ws.send(json.dumps({"error": str(e), "id": rid}))
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
        print(f"[-] Extension disconnected")
    print(f"[-] {client}")

async def main():
    print(f"Bridge v6: ws://localhost:{PORT}")
    asyncio.create_task(heartbeat())
    async with serve(handler, "127.0.0.1", PORT):
        await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())
