// 图鉴收藏页逻辑
document.addEventListener('DOMContentLoaded', async () => {
  let currentCategory = null;

  await loadStats();
  await loadCollection();

  // 分类筛选按钮
  document.getElementById('filter-bar').addEventListener('click', async (e) => {
    const btn = e.target.closest('.filter-btn');
    if (!btn) return;

    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentCategory = btn.dataset.category || null;
    await loadCollection(currentCategory);
  });

  async function loadStats() {
    try {
      const res = await fetch('/api/stats');
      const stats = await res.json();
      document.getElementById('total-count').textContent = `已发现 ${stats.total} 种动物`;
    } catch (e) {
      console.error(e);
    }
  }

  async function loadCollection(category = null) {
    const grid = document.getElementById('collection-grid');
    grid.innerHTML = '<div style="color:#666;padding:20px">加载中...</div>';

    try {
      const url = category
        ? `/api/collection?category=${encodeURIComponent(category)}`
        : '/api/collection';
      const res = await fetch(url);
      const data = await res.json();

      if (data.entries.length === 0) {
        grid.innerHTML = `
          <div class="empty-state" style="grid-column:1/-1">
            <div class="icon">🔍</div>
            <div>还没有发现动物</div>
            <div style="font-size:12px;margin-top:4px">去扫描页扫描你的第一只动物吧！</div>
          </div>`;
        return;
      }

      grid.innerHTML = data.entries.map(entry => `
        <div class="grid-card rarity-${entry.rarity || '普通'}" onclick="showDetail(${entry.id})">
          <img
            src="${entry.photo_url || ''}"
            alt="${entry.name}"
            onerror="this.style.background='#1a1a2e'"
          />
          <div class="grid-card-info">
            <div class="grid-card-number">#${entry.number || '????'}</div>
            <div class="grid-card-name">${entry.name}</div>
            <div class="grid-card-rarity" style="color:${rarityColor(entry.rarity)}">${entry.rarity || ''}</div>
          </div>
        </div>
      `).join('');
    } catch (e) {
      grid.innerHTML = '<div style="color:#f66;padding:20px">加载失败，请刷新重试</div>';
      console.error(e);
    }
  }

  function rarityColor(rarity) {
    const map = { '传说': '#ffd700', '极稀有': '#9b59b6', '稀有': '#3498db', '普通': '#888' };
    return map[rarity] || '#888';
  }
});

function makeSpeakBtn(onClick) {
  const btn = document.createElement('button');
  btn.className = 'speak-btn';
  btn.textContent = '🔊';
  btn.title = '点击朗读';
  btn.addEventListener('click', (e) => { e.stopPropagation(); onClick(btn); });
  return btn;
}

async function showDetail(id) {
  try {
    const res = await fetch(`/api/collection/${id}`);
    const entry = await res.json();

    const overlay = document.getElementById('card-overlay');
    const card    = document.getElementById('pokedex-card');

    // 填充内容
    document.getElementById('card-photo').src        = entry.photo_url || '';
    document.getElementById('card-photo').alt        = entry.name;
    document.getElementById('card-number').textContent = `#${entry.number || '????'}`;

    // 动物名 + 朗读按钮
    const nameEl = document.getElementById('card-name');
    nameEl.innerHTML = '';
    nameEl.appendChild(document.createTextNode(entry.name || '—'));
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
    document.getElementById('rarity-badge').textContent   = entry.rarity || '普通';
    document.getElementById('stat-height').textContent    = entry.height || '—';
    document.getElementById('stat-weight').textContent    = entry.weight || '—';
    document.getElementById('stat-habitat').textContent   = entry.habitat || '—';
    document.getElementById('stat-diet').textContent      = entry.diet || '—';
    document.getElementById('stat-predator').textContent  = entry.predator || '—';
    document.getElementById('stat-conservation').textContent = entry.conservation || '—';
    document.getElementById('card-description').textContent = entry.description || '';

    // 属性标签
    const attrsEl = document.getElementById('card-attributes');
    attrsEl.innerHTML = (entry.attributes || [])
      .map(a => `<span class="attr-tag">${a}</span>`).join('');

    // 稀有度样式
    const rarityClass = `rarity-${entry.rarity || '普通'}`;
    card.className = `pokedex-card ${rarityClass}`;

    // 语音播报按钮
    const narrationText = entry.narration || entry.description || '';
    const narrationBtn = document.getElementById('narration-btn');
    if (narrationBtn) {
      narrationBtn.classList.remove('playing');
      narrationBtn.onclick = () => Narration.play(narrationText, narrationBtn);
    }

    // 显示卡片
    overlay.classList.add('active');
    setTimeout(() => card.classList.add('slide-in'), 10);
  } catch (e) {
    console.error(e);
  }
}

// 关闭卡片
document.addEventListener('DOMContentLoaded', () => {
  const overlay = document.getElementById('card-overlay');
  const card    = document.getElementById('pokedex-card');

  function closeCard() {
    Narration.stop(document.getElementById('narration-btn'));
    card.classList.remove('slide-in');
    setTimeout(() => overlay.classList.remove('active'), 400);
  }

  document.getElementById('close-card-btn').addEventListener('click', closeCard);
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeCard();
  });
});
