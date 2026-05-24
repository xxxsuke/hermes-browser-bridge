// offscreen.js — 持久 WebSocket 连接，不会被 SW 生命周期影响
const WS = "ws://localhost:9876";
let ws = null;

function connect() {
  if (ws && ws.readyState === WebSocket.OPEN) return;
  try {
    ws = new WebSocket(WS);
    ws.onopen = () => {
      console.log("[offscreen] connected");
      ws.send(JSON.stringify({ type: "register", client: "extension" }));
    };
    ws.onmessage = async (e) => {
      const msg = JSON.parse(e.data);
      // 转发给 background.js 执行，等待回复
      try {
        const result = await chrome.runtime.sendMessage(msg);
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "reply", id: msg.id, ...result }));
        }
      } catch (err) {
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "reply", id: msg.id, error: err.message }));
        }
      }
    };
    ws.onclose = () => { ws = null; setTimeout(connect, 1000); };
    ws.onerror = () => { ws = null; setTimeout(connect, 2000); };
  } catch(e) { setTimeout(connect, 2000); }
}

connect();
// 每 30 秒 ping 保持连接
setInterval(() => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "ping" }));
  } else {
    connect();
  }
}, 30000);
