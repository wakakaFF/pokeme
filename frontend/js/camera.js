// 摄像头控制模块
const CameraModule = (() => {
  let stream = null;
  const video = document.getElementById('camera-video');

  async function start() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
      });
      video.srcObject = stream;
      await video.play();
    } catch (err) {
      console.error('摄像头启动失败:', err);
      alert('无法访问摄像头，请检查权限设置。\n也可以点击下方「上传图片」使用本地图片。');
    }
  }

  function captureFrame() {
    return new Promise((resolve) => {
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      canvas.getContext('2d').drawImage(video, 0, 0);
      canvas.toBlob(resolve, 'image/jpeg', 0.85);
    });
  }

  return { start, captureFrame };
})();
