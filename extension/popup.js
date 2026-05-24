// popup.js
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  if (tabs.length > 0) {
    document.getElementById('currentPage').textContent = 
      tabs[0].title.substring(0, 40) || tabs[0].url?.substring(0, 40);
  }
});

// 定期检查连接状态
setInterval(() => {
  chrome.runtime.sendMessage({ type: "ping" }, (resp) => {
    const dot = document.getElementById('statusDot');
    const conn = document.getElementById('connection');
    if (chrome.runtime.lastError) {
      dot.className = "dot off";
      conn.textContent = "未连接";
    } else {
      dot.className = "dot on";
      conn.textContent = "已连接";
    }
  });
}, 3000);
