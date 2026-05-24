"""代理管理：按需开关系统代理 + Clash 全局模式"""
import subprocess, urllib.request, json

SECRET = "set-your-secret"
CLASH = "http://127.0.0.1:9090"

def clash(path, method="GET", data=None):
    url = f"{CLASH}{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {SECRET}")
    if data:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode()
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read()) if resp.status == 200 else {}

def proxy_on():
    """开系统代理 + Clash 全局模式"""
    # Windows 系统代理
    subprocess.run(['powershell.exe','-Command',
        "Set-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings' -Name ProxyEnable -Value 1 -Force;"
        "Set-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings' -Name ProxyServer -Value '127.0.0.1:7897' -Force"],
        capture_output=True)
    # Clash 全局模式
    clash("/configs", "PATCH", {"mode": "global"})
    print("[proxy] ON — 系统代理+全局模式")

def proxy_off():
    """关系统代理 + Clash 规则模式"""
    subprocess.run(['powershell.exe','-Command',
        "Set-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings' -Name ProxyEnable -Value 0 -Force"],
        capture_output=True)
    clash("/configs", "PATCH", {"mode": "rule"})
    print("[proxy] OFF — 直连+规则模式")

def need_proxy(url):
    """判断 URL 是否需要代理"""
    intl_domains = [
        'youtube.com', 'ytimg.com', 'googlevideo.com',
        'tiktok.com', 'twitter.com', 'x.com',
        'github.com', 'githubusercontent.com',
        'google.com', 'googleapis.com', 'gstatic.com',
        'openai.com', 'anthropic.com',
        'reddit.com', 'discord.com', 'telegram.org',
        'facebook.com', 'instagram.com',
        'medium.com', 'substack.com',
        'wikipedia.org',
    ]
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower()
    return any(d in domain for d in intl_domains)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "on": proxy_on()
        elif sys.argv[1] == "off": proxy_off()
        elif sys.argv[1] == "check":
            url = sys.argv[2] if len(sys.argv) > 2 else ""
            print(f"need_proxy({url}) = {need_proxy(url)}")
    else:
        print("proxy_manager.py on|off|check <url>")
