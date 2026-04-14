// 图鉴语音播报 — 宝可梦图鉴风格
const Narration = (() => {
  let audioCtx = null;
  let currentSource = null;

  function getCtx() {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    return audioCtx;
  }

  async function play(text, btn) {
    // 如果正在播放，停止
    if (currentSource) {
      stop(btn);
      return;
    }

    btn.classList.add('playing');

    try {
      const res = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error('TTS 请求失败');

      const arrayBuffer = await res.arrayBuffer();
      const ctx = getCtx();
      const audioBuffer = await ctx.decodeAudioData(arrayBuffer);

      // ── 音效链：模拟图鉴小喇叭的电子感 ──────────────────
      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;

      // 带通滤波器：过滤高低频，保留中频，像从小喇叭出来
      const bandpass = ctx.createBiquadFilter();
      bandpass.type = 'bandpass';
      bandpass.frequency.value = 1800;
      bandpass.Q.value = 0.8;

      // 轻微失真（电子感）
      const waveshaper = ctx.createWaveShaper();
      waveshaper.curve = makeDistortionCurve(12);
      waveshaper.oversample = '2x';

      // 压缩器：让声音更有力
      const compressor = ctx.createDynamicsCompressor();
      compressor.threshold.value = -20;
      compressor.ratio.value = 4;

      // 增益补偿
      const gain = ctx.createGain();
      gain.gain.value = 1.8;

      // 连接链路
      source.connect(bandpass);
      bandpass.connect(waveshaper);
      waveshaper.connect(compressor);
      compressor.connect(gain);
      gain.connect(ctx.destination);

      currentSource = source;
      source.start();
      source.onended = () => {
        currentSource = null;
        btn.classList.remove('playing');
      };
    } catch (e) {
      console.warn('TTS error:', e);
      btn.classList.remove('playing');
    }
  }

  function stop(btn) {
    if (currentSource) {
      try { currentSource.stop(); } catch (_) {}
      currentSource = null;
    }
    if (btn) btn.classList.remove('playing');
  }

  // 生成失真曲线
  function makeDistortionCurve(amount) {
    const n = 256;
    const curve = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      const x = (i * 2) / n - 1;
      curve[i] = ((Math.PI + amount) * x) / (Math.PI + amount * Math.abs(x));
    }
    return curve;
  }

  // 朗读中文名（走 TTS API）
  async function speakName(text, btn) {
    if (btn.classList.contains('speaking')) return;
    btn.classList.add('speaking');
    try {
      const res = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      const arrayBuffer = await res.arrayBuffer();
      const ctx = getCtx();
      const audioBuffer = await ctx.decodeAudioData(arrayBuffer);
      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(ctx.destination);
      source.start();
      source.onended = () => btn.classList.remove('speaking');
    } catch (e) {
      console.warn('speakName error:', e);
      btn.classList.remove('speaking');
    }
  }

  // 朗读拉丁学名（用浏览器英语语音）
  function speakScientific(text, btn) {
    if (btn.classList.contains('speaking')) return;
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = 'en-US';
    utter.rate = 0.85;
    btn.classList.add('speaking');
    utter.onend = utter.onerror = () => btn.classList.remove('speaking');
    speechSynthesis.speak(utter);
  }

  return { play, stop, speakName, speakScientific };
})();
