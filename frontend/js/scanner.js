// 扫描逻辑 + 卡片渲染
const Scanner = (() => {
  const loading   = document.getElementById('loading-overlay');
  const cardOverlay = document.getElementById('card-overlay');
  const card      = document.getElementById('pokedex-card');

  // ── 发送图片到后端 ────────────────────────────────────────
  async function identify(blob) {
    showLoading(true);
    try {
      const form = new FormData();
      form.append('file', blob, 'scan.jpg');

      const res = await fetch('/api/identify', { method: 'POST', body: form });
      const data = await res.json();

      if (data.is_animal === false) {
        alert(data.message);
        return;
      }

      renderCard(data.entry, data.is_new);
    } catch (err) {
      alert('识别失败，请重试');
      console.error(err);
    } finally {
      showLoading(false);
    }
  }

  // ── 渲染图鉴卡片 ─────────────────────────────────────────
  function renderCard(entry, isNew) {
    // 稀有度样式
    card.className = `pokedex-card rarity-${entry.rarity || '普通'}`;

    // 首次发现横幅
    const banner = document.getElementById('new-discovery-banner');
    banner.classList.toggle('show', !!isNew);

    // 照片
    const photo = document.getElementById('card-photo');
    photo.src = entry.photo_url || '/static/img/placeholder.png';
    photo.alt = entry.name;

    // 基本信息
    setText('card-number', `#${entry.number}`);
    setText('rarity-badge', entry.rarity || '普通');

    // 动物名 + 朗读按钮
    const nameEl = document.getElementById('card-name');
    nameEl.innerHTML = '';
    nameEl.appendChild(document.createTextNode(entry.name || ''));
    if (entry.name) {
      const btn = makeSpeakBtn(() => Narration.speakName(entry.name, btn));
      nameEl.appendChild(btn);
    }

    // 学名 + 朗读按钮
    const sciEl = document.getElementById('card-scientific');
    sciEl.innerHTML = '';
    sciEl.appendChild(document.createTextNode(entry.scientific_name || ''));
    if (entry.scientific_name) {
      const btn = makeSpeakBtn(() => Narration.speakScientific(entry.scientific_name, btn));
      sciEl.appendChild(btn);
    }
    setText('stat-height',     entry.height || '—');
    setText('stat-weight',     entry.weight || '—');
    setText('stat-habitat',    entry.habitat || '—');
    setText('stat-diet',       entry.diet || '—');
    setText('stat-predator',   entry.predator || '—');
    setText('stat-conservation', entry.conservation || '—');

    // 描述打字机效果
    typewriter('card-description', entry.description || '');

    // 属性标签
    const attrsEl = document.getElementById('card-attributes');
    attrsEl.innerHTML = '';
    (entry.attributes || []).forEach(attr => {
      const span = document.createElement('span');
      span.className = 'attr-tag';
      span.textContent = attr;
      attrsEl.appendChild(span);
    });

    // 语音播报
    setupNarration(entry.narration || entry.description || '');

    // 显示卡片
    cardOverlay.classList.add('active');
    requestAnimationFrame(() => {
      requestAnimationFrame(() => card.classList.add('slide-in'));
    });
  }

  function closeCard() {
    stopNarration();
    card.classList.remove('slide-in');
    setTimeout(() => cardOverlay.classList.remove('active'), 400);
  }

  // ── 工具函数 ─────────────────────────────────────────────
  function showLoading(show) {
    loading.classList.toggle('active', show);
  }

  function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  function makeSpeakBtn(onClick) {
    const btn = document.createElement('button');
    btn.className = 'speak-btn';
    btn.textContent = '🔊';
    btn.title = '点击朗读';
    btn.addEventListener('click', (e) => { e.stopPropagation(); onClick(btn); });
    return btn;
  }

  function typewriter(id, text, speed = 30) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = '';
    let i = 0;
    const timer = setInterval(() => {
      el.textContent += text[i++];
      if (i >= text.length) clearInterval(timer);
    }, speed);
  }

  // ── 语音播报 ─────────────────────────────────────────────
  function setupNarration(text) {
    const btn = document.getElementById('narration-btn');
    if (!btn) return;
    btn.classList.remove('playing');
    btn.onclick = () => Narration.play(text, btn);
  }

  function stopNarration() {
    const btn = document.getElementById('narration-btn');
    Narration.stop(btn);
  }

  return { identify, closeCard };
})();

// ── 事件绑定 ────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  await CameraModule.start();

  // 快门按钮
  document.getElementById('shutter-btn').addEventListener('click', async () => {
    const blob = await CameraModule.captureFrame();
    await Scanner.identify(blob);
  });

  // 上传本地图片
  document.getElementById('file-input').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (file) await Scanner.identify(file);
    e.target.value = '';
  });

  // 关闭卡片
  document.getElementById('close-card-btn').addEventListener('click', Scanner.closeCard);
  document.getElementById('card-overlay').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) Scanner.closeCard();
  });
});
