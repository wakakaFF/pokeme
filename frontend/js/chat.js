marked.setOptions({ breaks: true });

const messagesEl = document.getElementById('chat-messages');
const inputEl    = document.getElementById('chat-input');
const sendBtn    = document.getElementById('chat-send-btn');

const history = [];

function appendBubble(role) {
  const div = document.createElement('div');
  div.className = `chat-bubble ${role}`;
  const content = document.createElement('div');
  content.className = 'bubble-content';
  div.appendChild(content);
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return content;
}

function setLoading(on) {
  sendBtn.disabled = on;
  inputEl.disabled = on;
  sendBtn.textContent = on ? '…' : '➤';
}

async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text) return;

  inputEl.value = '';

  // 用户气泡
  const userBubble = appendBubble('user');
  userBubble.textContent = text;
  history.push({ role: 'user', content: text });

  // 助手气泡（流式填充）
  const aiBubble = appendBubble('assistant');
  aiBubble.innerHTML = '<span class="typing-dot">●</span>';

  setLoading(true);

  let fullText = '';

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: history }),
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';
    let finished = false;

    while (!finished) {
      const { done, value } = await reader.read();
      if (done) break;

      buf += decoder.decode(value, { stream: true });

      // 逐行消费，保留不完整的最后一行
      let nl;
      while ((nl = buf.indexOf('\n')) !== -1) {
        const line = buf.slice(0, nl).replace(/\r$/, '');
        buf = buf.slice(nl + 1);

        if (!line.startsWith('data: ')) continue;
        const payload = line.slice(6);
        if (payload === '[DONE]') { finished = true; break; }

        let obj;
        try { obj = JSON.parse(payload); } catch (_) { continue; }
        if (obj.error) throw new Error(obj.error);
        if (obj.text) {
          fullText += obj.text;
          aiBubble.innerHTML = marked.parse(fullText);
          messagesEl.scrollTop = messagesEl.scrollHeight;
        }
      }
    }

    if (!fullText) fullText = '（无回复）';
    aiBubble.innerHTML = marked.parse(fullText);
    history.push({ role: 'assistant', content: fullText });

  } catch (e) {
    aiBubble.textContent = `❌ 出错了：${e.message}`;
  } finally {
    setLoading(false);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    inputEl.focus();
  }
}

sendBtn.addEventListener('click', sendMessage);
inputEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// ── 语音输入 ──────────────────────────────────────────────────
const micBtn = document.getElementById('chat-mic-btn');

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
  micBtn.title = '浏览器不支持语音输入';
  micBtn.style.opacity = '0.4';
  micBtn.disabled = true;
} else {
  const recognition = new SpeechRecognition();
  recognition.lang = 'zh-CN';
  recognition.interimResults = true;
  recognition.maxAlternatives = 1;

  let isRecording = false;

  recognition.onstart = () => {
    isRecording = true;
    micBtn.classList.add('recording');
    inputEl.placeholder = '正在听…';
  };

  recognition.onresult = (e) => {
    const transcript = Array.from(e.results)
      .map(r => r[0].transcript)
      .join('');
    inputEl.value = transcript;
    // 如果是最终结果，自动发送
    if (e.results[e.results.length - 1].isFinal) {
      recognition.stop();
      if (inputEl.value.trim()) sendMessage();
    }
  };

  recognition.onerror = (e) => {
    console.warn('语音识别错误:', e.error);
  };

  recognition.onend = () => {
    isRecording = false;
    micBtn.classList.remove('recording');
    inputEl.placeholder = '问问图图…';
  };

  micBtn.addEventListener('click', () => {
    if (isRecording) {
      recognition.stop();
    } else {
      inputEl.value = '';
      recognition.start();
    }
  });
}
