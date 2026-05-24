// background.js v6 — offscreen 持久连接架构
// 只负责执行 chrome API，WebSocket 由 offscreen.js 管理

// 启动 offscreen 页面
async function ensureOffscreen() {
  const has = await chrome.offscreen?.hasDocument?.().catch(() => false);
  if (!has) {
    await chrome.offscreen.createDocument({
      url: "offscreen.html",
      reasons: ["DOM_PARSER"],
      justification: "Persistent WebSocket for Hermes Bridge"
    });
  }
}
ensureOffscreen();

// 处理来自 offscreen 的命令
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  const { id, action, tabId, params } = msg;
  const p = params || {};

  // 找目标标签
  const getTab = async () => {
    if (tabId) return tabId;
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    return tabs[0]?.id;
  };

  (async () => {
    let tid = tabId;
    if (!tid) tid = await getTab();

    if (action === "list_tabs") {
      chrome.tabs.query({}, tabs => sendResponse({
        tabs: tabs.map(t => ({ id: t.id, title: t.title || "", url: t.url || "", active: t.active }))
      }));
      return;
    }
    if (action === "new_tab") {
      chrome.tabs.create({ url: p.url || "about:blank" }, tab =>
        sendResponse({ tabId: tab.id, title: tab.title, url: tab.url }));
      return;
    }
    if (action === "close_tab") {
      chrome.tabs.remove(tid, () => {
        sendResponse({ closed: !chrome.runtime.lastError,
          error: chrome.runtime.lastError?.message });
      });
      return;
    }
    if (action === "close_window") {
      chrome.tabs.get(tid, tab => {
        if (chrome.runtime.lastError) { sendResponse({ error: chrome.runtime.lastError.message }); return; }
        chrome.windows.remove(tab.windowId, () => {
          sendResponse({ closed: !chrome.runtime.lastError,
            error: chrome.runtime.lastError?.message });
        });
      });
      return;
    }
    if (action === "activate_tab") {
      chrome.tabs.update(tid, { active: true }, () => sendResponse({ ok: true }));
      return;
    }
    if (action === "reload_tab") {
      chrome.tabs.reload(tid, {}, () => sendResponse({ ok: true }));
      return;
    }
    if (action === "navigate") {
      chrome.tabs.update(tid, { url: p.url }, () => sendResponse({ ok: true }));
      return;
    }
    if (action === "create_window") {
      chrome.windows.create({ url: p.url || "about:blank" }, win =>
        sendResponse({ windowId: win.id, tabId: win.tabs?.[0]?.id }));
      return;
    }
    if (action === "search_history") {
      chrome.history.search({ text: p.query || "", maxResults: p.maxResults || 20 }, r =>
        sendResponse({ results: r.map(h => ({ title: h.title, url: h.url })) }));
      return;
    }
    if (action === "list_bookmarks") {
      chrome.bookmarks.getTree(tree => sendResponse({ tree }));
      return;
    }
    if (action === "list_windows") {
      chrome.windows.getAll({ populate: true }, wins => sendResponse({
        windows: wins.map(w => ({ id: w.id, focused: w.focused, tabs: w.tabs?.length }))
      }));
      return;
    }
    if (action === "get_tab_info") {
      chrome.tabs.get(tid, tab => sendResponse({
        id: tab.id, title: tab.title || "", url: tab.url || "", status: tab.status,
        favIconUrl: tab.favIconUrl, audible: tab.audible, incognito: tab.incognito
      }));
      return;
    }
    if (action === "screenshot") {
      chrome.debugger.attach({ tabId: tid }, "1.3", () => {
        chrome.debugger.sendCommand({ tabId: tid }, "Page.captureScreenshot", { format: "png" }, r => {
          chrome.debugger.detach({ tabId: tid });
          sendResponse({ dataUrl: "data:image/png;base64," + (r?.data || "") });
        });
      });
      return;
    }
    // ── 下载 ──
    if (action === "download") {
      chrome.downloads.download({ url: p.url, filename: p.filename || "", saveAs: p.saveAs || false }, id =>
        sendResponse({ downloadId: id, error: chrome.runtime.lastError?.message }));
      return;
    }
    if (action === "list_downloads") {
      chrome.downloads.search({ limit: p.limit || 20 }, results =>
        sendResponse({ downloads: results.map(d => ({ id: d.id, filename: d.filename, url: d.url, state: d.state })) }));
      return;
    }
    // ── 导航 ──
    if (action === "go_back") { chrome.tabs.goBack(tid, () => sendResponse({ ok: true })); return; }
    if (action === "go_forward") { chrome.tabs.goForward(tid, () => sendResponse({ ok: true })); return; }
    // ── 缩放 ──
    if (action === "set_zoom") { chrome.tabs.setZoom(tid, p.zoom || 1.0, () => sendResponse({ ok: true })); return; }
    if (action === "get_zoom") { chrome.tabs.getZoom(tid, z => sendResponse({ zoom: z })); return; }
    // ── 打印 ──
    if (action === "print") { chrome.tabs.print(); sendResponse({ ok: true }); return; }
    // ── 书签操作 ──
    if (action === "create_bookmark") {
      chrome.bookmarks.create({ title: p.title || "", url: p.url }, bm => sendResponse({ id: bm.id, title: bm.title }));
      return;
    }
    if (action === "remove_bookmark") {
      chrome.bookmarks.remove(p.bookmarkId, () => sendResponse({ ok: true }));
      return;
    }
    if (action === "search_bookmarks") {
      chrome.bookmarks.search(p.query || "", results =>
        sendResponse({ results: results.map(b => ({ id: b.id, title: b.title, url: b.url })) }));
      return;
    }
    // ── 清除数据 ──
    if (action === "clear_data") {
      let opts = { since: p.since || 0 };
      if (p.cache) opts = { ...opts, cache: true };
      if (p.cookies) opts = { ...opts, cookies: true };
      if (p.history) opts = { ...opts, history: true };
      chrome.browsingData.remove(opts, () => sendResponse({ ok: true }));
      return;
    }
    // content script ops — 更健壮的注入
    chrome.tabs.sendMessage(tid, { action, params }, resp => {
      if (!chrome.runtime.lastError) {
        sendResponse(resp);
        return;
      }
      // 注入 content.js
      chrome.scripting.executeScript({ target: { tabId: tid }, files: ["content.js"] }, () => {
        if (chrome.runtime.lastError) {
          sendResponse({ error: "inject: " + chrome.runtime.lastError.message });
          return;
        }
        // 等脚本初始化
        setTimeout(() => {
          chrome.tabs.sendMessage(tid, { action, params }, retry => {
            if (chrome.runtime.lastError) {
              sendResponse({ error: "retry: " + chrome.runtime.lastError.message });
            } else {
              sendResponse(retry);
            }
          });
        }, 800);
      });
    });
  })();

  return true; // 保持异步通道
});
