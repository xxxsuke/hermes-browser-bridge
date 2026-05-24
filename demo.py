import asyncio, json, websockets, base64, os, shutil
from urllib.parse import quote

async def cmd(ws, action, params=None, tab_id=None, timeout=12):
    rid = f't_{int(__import__("time").time()*1000)}'
    await ws.send(json.dumps({'type':'command','id':rid,'action':action,'tabId':tab_id,'params':params or {}}))
    try: return json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))
    except: return {'error':'timeout'}

async def scroll_bottom(ws, tab, steps=25):
    for i in range(steps):
        r = await cmd(ws, 'scroll', {'direction':'down','amount':800}, tab)
        await asyncio.sleep(0.2)
        if r.get('scrollY',0) >= r.get('maxScroll',99999)-100: return True
    return False

async def main():
    async with websockets.connect('ws://localhost:9876') as ws:
        await ws.send(json.dumps({'type':'register','client':'hermes'}))
        await asyncio.wait_for(ws.recv(), timeout=5)

        print('=== 1. 多平台搜索 ===')
        keyword = quote('小红书 RedSkill 红技能 内测')
        r = await cmd(ws, 'create_window', {'url': f'https://www.baidu.com/s?wd={keyword}'})
        tab = r.get('tabId')
        print(f'百度搜索: tab {tab}')
        await asyncio.sleep(4)

        r2 = await cmd(ws, 'read_text', {'maxLength': 500}, tab)
        print(f'结果: {r2.get("length",0)}字')

        print('\n=== 2. 点进原文 ===')
        r3 = await cmd(ws, 'click', {'selector': '.result.c-container h3 a'}, tab)
        print(f'click: {r3.get("text","?")[:50]}')
        await asyncio.sleep(5)

        r4 = await cmd(ws, 'list_tabs')
        art_tab = tab
        for t in r4.get('tabs',[]):
            if t['id'] != tab and ('红技能' in t.get('title','') or 'RedSkill' in t.get('title','') or 'jiemian' in t.get('title','')):
                art_tab = t['id']
                break
        print(f'文章标签: [{art_tab}]')

        print('\n=== 3. 滚动阅读 ===')
        await cmd(ws, 'activate_tab', {}, art_tab)
        await asyncio.sleep(1)
        await scroll_bottom(ws, art_tab)
        r5 = await cmd(ws, 'read_text', {'maxLength': 5000}, art_tab)
        print(f'全文: {r5.get("length",0)}字')

        print('\n=== 4. 提取配图 ===')
        r6 = await cmd(ws, 'get_images', {'maxCount': 20}, art_tab)
        imgs = r6.get('images',[])
        big = [i for i in imgs if i.get('width',0)>200 and i.get('height',0)>100]
        print(f'配图: {len(big)}张 / 共{len(imgs)}张')

        print('\n=== 5. 截图 ===')
        await cmd(ws, 'scroll', {'direction':'up','amount':99999}, art_tab)
        await asyncio.sleep(1)
        r7 = await cmd(ws, 'screenshot', {}, art_tab, 15)
        if 'dataUrl' in r7:
            path = '/home/suke/articles/demo_final.png'
            with open(path,'wb') as f: f.write(base64.b64decode(r7['dataUrl'].split(',')[1]))
            shutil.copy(path, '/mnt/c/Users/10737/Desktop/demo_截图.png')
            print(f'📸 {os.path.getsize(path)//1024}KB')

        print('\n=== 6. 关窗 ===')
        r8 = await cmd(ws, 'close_window', {}, art_tab)
        print(f'closed={r8.get("closed")}')

        print('\n✅ 演示完成')

asyncio.run(main())
