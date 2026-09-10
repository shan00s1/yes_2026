/**
 * NEXUS 2026 - High Reliability Native WebRTC Camera QR Scanner
 * Powered by local jsQR + Native BarcodeDetector (Zero external CDN dependencies)
 * Auto-starts scanning using the default available camera on load.
 */

// Global State
let videoStream = null;
let isScanning = false;
let isProcessing = false;
let isAnalyzingFrame = false;
let lastScannedCode = null;
let lastScannedTime = 0;
let audioCtx = null;
let animationFrameId = null;
let barcodeDetector = null;
let zxingReader = null;
let currentDeviceId = null;
let availableVideoDevices = [];

// Safe UserMedia Caller - Never writes to read-only navigator properties
function safeGetUserMedia(constraints) {
  if (navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function') {
    return navigator.mediaDevices.getUserMedia(constraints);
  }
  const legacy = navigator.getUserMedia ||
    navigator.webkitGetUserMedia ||
    navigator.mozGetUserMedia ||
    navigator.msGetUserMedia;

  if (legacy) {
    return new Promise((resolve, reject) => {
      legacy.call(navigator, constraints, resolve, reject);
    });
  }
  return Promise.reject(new Error('CAMERA_UNAVAILABLE'));
}

// Check if current context is secure (HTTPS or localhost)
function checkSecureContext() {
  if (typeof window.isSecureContext === 'boolean') {
    return window.isSecureContext;
  }
  const host = window.location.hostname;
  return host === 'localhost' || host === '127.0.0.1' || window.location.protocol === 'https:';
}

document.addEventListener('DOMContentLoaded', () => {
  initAudio();
  initBarcodeDetector();
  initZXing();
  initCameraControls();
  initManualInput();
  initFileUpload();
  fetchRecentCheckins();
  setInterval(fetchRecentCheckins, 10000);

  // Check for insecure context (e.g. visiting via plain HTTP on LAN IP: http://10.15.27.x:5000)
  const isSecure = checkSecureContext();
  const warningBanner = document.getElementById('origin-warning-banner');

  if (!isSecure && window.location.protocol === 'http:' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    if (warningBanner) warningBanner.style.display = 'flex';

    // If user opened on host machine via its LAN IP, test if localhost:5000 is reachable and auto-redirect
    fetch('http://localhost:5000/api/event/info', { mode: 'no-cors' })
      .then(() => {
        console.log('[Scanner] Host machine detected on LAN IP. Redirecting to http://localhost:5000/checkin for native camera support...');
        window.location.href = 'http://localhost:5000/checkin';
      })
      .catch(() => {
        // Remote device on LAN. Show insecure origin helper.
        showInsecureOriginCard();
      });
    return;
  }

  // Check if we are on standalone kiosk vs admin dashboard
  if (window.location.pathname.includes('/checkin')) {
    autoStartCameraByDefault();
  }
});

function pauseCamera() {
  stopCamera();
}

// Expose camera controls globally for admin dashboard tabs
window.startScannerCamera = autoStartCameraByDefault;
window.pauseScannerCamera = pauseCamera;

// Initialize Native BarcodeDetector if available in modern Chromium/Edge
function initBarcodeDetector() {
  if ('BarcodeDetector' in window) {
    try {
      barcodeDetector = new BarcodeDetector({ formats: ['qr_code'] });
      console.log('[Scanner] Native BarcodeDetector hardware acceleration active.');
    } catch (e) {
      barcodeDetector = null;
    }
  }
}

// Initialize Local Standalone ZXing Engine
function initZXing() {
  if (window.ZXing && typeof window.ZXing.BrowserQRCodeReader === 'function') {
    try {
      zxingReader = new window.ZXing.BrowserQRCodeReader();
      console.log('[Scanner] ZXing optical QR engine active.');
    } catch (e) {
      zxingReader = null;
    }
  }
}

// Audio Synthesis (Chime on success, Buzzer on duplicate)
function initAudio() {
  const unlock = () => {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === 'suspended') audioCtx.resume();
    document.removeEventListener('click', unlock);
    document.removeEventListener('touchstart', unlock);
  };
  document.addEventListener('click', unlock);
  document.addEventListener('touchstart', unlock);
}

function playSuccessChime() {
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const now = audioCtx.currentTime;
    
    // First high note (880Hz - A5)
    const osc1 = audioCtx.createOscillator();
    const gain1 = audioCtx.createGain();
    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(880, now);
    gain1.gain.setValueAtTime(0.3, now);
    gain1.gain.exponentialRampToValueAtTime(0.01, now + 0.2);
    osc1.connect(gain1);
    gain1.connect(audioCtx.destination);
    osc1.start(now);
    osc1.stop(now + 0.2);

    // Second celebratory note (1320Hz - E6)
    const osc2 = audioCtx.createOscillator();
    const gain2 = audioCtx.createGain();
    osc2.type = 'sine';
    osc2.frequency.setValueAtTime(1320, now + 0.1);
    gain2.gain.setValueAtTime(0.35, now + 0.1);
    gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.45);
    osc2.connect(gain2);
    gain2.connect(audioCtx.destination);
    osc2.start(now + 0.1);
    osc2.stop(now + 0.45);
  } catch (e) {}
}

function playDuplicateAlert() {
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const now = audioCtx.currentTime;
    [0, 0.18].forEach(offset => {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(240, now + offset);
      osc.frequency.linearRampToValueAtTime(150, now + offset + 0.14);
      gain.gain.setValueAtTime(0.4, now + offset);
      gain.gain.exponentialRampToValueAtTime(0.01, now + offset + 0.14);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start(now + offset);
      osc.stop(now + offset + 0.14);
    });
  } catch (e) {}
}

// Update floating camera status pill badge
function updateStatusBadge(state, label) {
  const dot = document.getElementById('cam-status-dot');
  const text = document.getElementById('cam-status-text');
  if (!dot || !text) return;

  dot.className = 'cam-dot';
  if (state === 'active') {
    dot.classList.add('active');
    text.textContent = label || 'Camera Live • Scanning';
  } else if (state === 'error') {
    dot.classList.add('error');
    text.textContent = label || 'Camera Offline';
  } else if (state === 'paused') {
    text.textContent = label || 'Camera Paused';
  } else {
    text.textContent = label || 'Connecting to Camera...';
  }
}

// Auto-start camera on page load by default
function autoStartCameraByDefault() {
  updateStatusBadge('connecting', 'Auto-Starting Default Camera...');
  setTimeout(() => {
    startCamera(null);
  }, 200);
}

// Camera Controls & Native WebRTC Stream
function initCameraControls() {
  const startBtnOverlay = document.getElementById('btn-start-camera-overlay');
  const toggleBtn = document.getElementById('btn-toggle-camera');
  const cameraSelect = document.getElementById('camera-select');
  const switchBtn = document.getElementById('btn-switch-camera');

  if (startBtnOverlay) {
    startBtnOverlay.addEventListener('click', () => startCamera(currentDeviceId));
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      if (isScanning) {
        stopCamera();
      } else {
        startCamera(currentDeviceId);
      }
    });
  }

  if (cameraSelect) {
    cameraSelect.addEventListener('change', (e) => {
      currentDeviceId = e.target.value;
      startCamera(currentDeviceId);
    });
  }

  if (switchBtn) {
    switchBtn.addEventListener('click', () => {
      if (availableVideoDevices.length > 1) {
        const currentIndex = availableVideoDevices.findIndex(d => d.deviceId === currentDeviceId);
        const nextIndex = (currentIndex + 1) % availableVideoDevices.length;
        currentDeviceId = availableVideoDevices[nextIndex].deviceId;
        if (cameraSelect) cameraSelect.value = currentDeviceId;
        startCamera(currentDeviceId);
      }
    });
  }

  if (navigator.mediaDevices && typeof navigator.mediaDevices.enumerateDevices === 'function') {
    populateCameraDevices();
  }
}

// Populate available cameras in dropdown
async function populateCameraDevices() {
  try {
    if (!navigator.mediaDevices || typeof navigator.mediaDevices.enumerateDevices !== 'function') return;
    const devices = await navigator.mediaDevices.enumerateDevices();
    availableVideoDevices = devices.filter(d => d.kind === 'videoinput');
    const select = document.getElementById('camera-select');
    const switchBtn = document.getElementById('btn-switch-camera');

    if (select && availableVideoDevices.length > 0) {
      select.innerHTML = availableVideoDevices.map((d, idx) => {
        const label = d.label || `Camera ${idx + 1} (${d.deviceId.substring(0, 6)}...)`;
        return `<option value="${d.deviceId}">${label}</option>`;
      }).join('');

      if (currentDeviceId) {
        select.value = currentDeviceId;
      }
      select.style.display = 'inline-block';

      if (switchBtn && availableVideoDevices.length > 1) {
        switchBtn.style.display = 'inline-flex';
      }
    }
  } catch (e) {
    console.log('[Scanner] Device enumeration notice:', e);
  }
}

// Main camera initialization routine with automatic constraint fallback ladder
async function startCamera(deviceId = null) {
  const video = document.getElementById('qr-video');
  const placeholder = document.getElementById('camera-placeholder');
  const overlay = document.getElementById('scanner-overlay');
  const errorBanner = document.getElementById('camera-error-banner');
  const toggleBtn = document.getElementById('btn-toggle-camera');

  if (errorBanner) errorBanner.style.display = 'none';
  updateStatusBadge('connecting', 'Opening Camera Feed...');

  // Check if WebRTC getUserMedia is available
  if (!navigator.mediaDevices && !navigator.getUserMedia && !navigator.webkitGetUserMedia) {
    handleCameraFailure({ name: 'InsecureOriginError', message: 'Camera access requires localhost or HTTPS.' });
    return;
  }

  // Stop any existing stream before opening new device
  if (videoStream) {
    videoStream.getTracks().forEach(track => track.stop());
    videoStream = null;
  }

  let stream = null;

  // Progressive camera constraints ladder (Prioritizing high resolution & sharp optics)
  const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
  const constraintLadder = [];

  if (deviceId) {
    constraintLadder.push(
      { video: { deviceId: { exact: deviceId }, width: { ideal: 1920, min: 1280 }, height: { ideal: 1080, min: 720 } }, audio: false },
      { video: { deviceId: { exact: deviceId }, width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false },
      { video: { deviceId: { exact: deviceId } }, audio: false }
    );
  } else if (isMobile) {
    constraintLadder.push(
      { video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920, min: 1280 }, height: { ideal: 1080, min: 720 } }, audio: false },
      { video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false },
      { video: { facingMode: { ideal: 'environment' } }, audio: false }
    );
  }

  // Desktop webcam ladder (1080p -> 720p -> 480p -> minimal)
  constraintLadder.push(
    { video: { width: { ideal: 1920, min: 1280 }, height: { ideal: 1080, min: 720 } }, audio: false },
    { video: { width: { ideal: 1280, min: 960 }, height: { ideal: 720, min: 540 } }, audio: false },
    { video: { width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false },
    { video: { width: { ideal: 640 }, height: { ideal: 480 } }, audio: false },
    { video: true, audio: false }
  );

  for (const c of constraintLadder) {
    try {
      stream = await safeGetUserMedia(c);
      if (stream) break;
    } catch (e) {
      // Continue down the ladder
    }
  }

  if (!stream) {
    handleCameraFailure(new Error('All camera constraints failed'));
    return;
  }

  // Step 5: Bind stream to video element
  try {
    videoStream = stream;
    video.srcObject = videoStream;
    video.setAttribute('playsinline', 'true');
    video.setAttribute('autoplay', 'true');
    video.muted = true;

    // Retrieve active deviceId and label from active track
    const videoTrack = stream.getVideoTracks()[0];
    if (videoTrack) {
      const settings = videoTrack.getSettings ? videoTrack.getSettings() : {};
      if (settings.deviceId) currentDeviceId = settings.deviceId;

      // Enable continuous hardware autofocus and exposure if supported
      try {
        if (videoTrack.getCapabilities) {
          const caps = videoTrack.getCapabilities();
          const adv = {};
          if (caps.focusMode && caps.focusMode.includes('continuous')) adv.focusMode = 'continuous';
          if (caps.exposureMode && caps.exposureMode.includes('continuous')) adv.exposureMode = 'continuous';
          if (caps.whiteBalanceMode && caps.whiteBalanceMode.includes('continuous')) adv.whiteBalanceMode = 'continuous';
          if (Object.keys(adv).length > 0 && videoTrack.applyConstraints) {
            videoTrack.applyConstraints({ advanced: [adv] }).catch(() => {});
          }
        }
      } catch (focusErr) {}
    }

    await video.play();

    isScanning = true;
    if (placeholder) placeholder.style.display = 'none';
    if (overlay) overlay.style.display = 'flex';

    if (toggleBtn) {
      toggleBtn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/></svg> Pause Camera`;
      toggleBtn.className = 'btn btn-secondary btn-sm';
    }

    const cameraLabel = videoTrack && videoTrack.label ? videoTrack.label : 'Default Cam';
    updateStatusBadge('active', `Live: ${cameraLabel}`);

    // Populate camera options list now that permission is granted
    populateCameraDevices();

    // Start continuous frame analysis
    if (animationFrameId) cancelAnimationFrame(animationFrameId);
    animationFrameId = requestAnimationFrame(scanVideoFrame);

  } catch (playErr) {
    console.error('[Scanner] Video playback error:', playErr);
    handleCameraFailure(playErr);
  }
}

// Graceful camera failure handling with actionable recovery
function handleCameraFailure(err) {
  isScanning = false;
  updateStatusBadge('error', 'Camera Unavailable');

  const placeholder = document.getElementById('camera-placeholder');
  const title = document.getElementById('cam-placeholder-title');
  const desc = document.getElementById('cam-placeholder-desc');
  const actions = document.getElementById('cam-placeholder-actions');
  const errorBanner = document.getElementById('camera-error-banner');
  const pulseIndicator = document.getElementById('cam-pulse-indicator');

  if (placeholder) placeholder.style.display = 'flex';
  if (pulseIndicator) pulseIndicator.style.display = 'none';
  if (actions) actions.style.display = 'block';

  const isSecure = checkSecureContext();

  if (!isSecure || err.name === 'InsecureOriginError' || (err.message && err.message.includes('getUserMedia'))) {
    showInsecureOriginCard();
    return;
  }

  if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
    if (title) title.textContent = 'Camera Permission Blocked';
    if (desc) desc.innerHTML = 'Please click the <strong>lock/camera icon</strong> in your browser address bar, set Camera to <strong>Allow</strong>, then click retry.';
    if (errorBanner) {
      errorBanner.innerHTML = `
        <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid var(--danger); border-radius: var(--radius-sm); padding: 12px; font-size: 12px; color: #fca5a5;">
          <strong>Permission Required:</strong> Access to the webcam was denied.
          <div style="margin-top: 8px;">
            <button class="btn btn-primary btn-sm" onclick="startCamera()">Retry Camera</button>
          </div>
        </div>
      `;
      errorBanner.style.display = 'block';
    }
  } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
    if (title) title.textContent = 'No Camera Detected';
    if (desc) desc.textContent = 'No webcam or video device found on this system. You can scan badges using the options below.';
    if (errorBanner) {
      errorBanner.innerHTML = `
        <div style="background: rgba(245, 158, 11, 0.15); border: 1px solid var(--warning); border-radius: var(--radius-sm); padding: 12px; font-size: 12px; color: #fde68a;">
          <strong>No Webcam Found.</strong> Use <strong>Take Photo & Scan</strong> or <strong>Manual ID Input</strong> below.
        </div>
      `;
      errorBanner.style.display = 'block';
    }
  } else {
    if (title) title.textContent = 'Camera Initialization Notice';
    if (desc) desc.textContent = 'Could not establish video stream: ' + (err.message || err.name);
    if (errorBanner) {
      errorBanner.innerHTML = `
        <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid var(--danger); border-radius: var(--radius-sm); padding: 12px; font-size: 12px; color: #fca5a5;">
          <strong>Camera Notice:</strong> ${err.message || err.name}<br>
          <div style="margin-top: 8px; display: flex; gap: 8px; justify-content: center;">
            <button class="btn btn-primary btn-sm" onclick="startCamera()">Try Default Camera Again</button>
          </div>
        </div>
      `;
      errorBanner.style.display = 'block';
    }
  }
}

// Insecure Origin (HTTP IP) Resolution Card
function showInsecureOriginCard() {
  const placeholder = document.getElementById('camera-placeholder');
  if (!placeholder) return;

  const lanIp = document.body.getAttribute('data-lan-ip') || window.location.hostname;

  placeholder.innerHTML = `
    <div style="background: rgba(239, 68, 68, 0.12); border: 2px solid var(--danger); border-radius: 14px; padding: 22px; text-align: center; max-width: 440px;">
      <div style="margin-bottom: 8px;">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
      </div>
      <h3 style="font-size: 17px; margin-bottom: 6px; color: #fca5a5;">Live Camera Requires Secure Context</h3>
      <p style="font-size: 12px; color: #e2e8f0; line-height: 1.5; margin-bottom: 16px;">
        Web browsers strictly restrict live webcam streaming to <strong>localhost</strong> or <strong>HTTPS</strong>. 
        You are currently visiting via: <code>${window.location.host}</code>
      </p>

      <div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 14px;">
        <a href="http://localhost:5000/checkin" class="btn btn-primary btn-sm">
          Open on http://localhost:5000/checkin
        </a>
        <a href="https://${lanIp}:5443/checkin" class="btn btn-secondary btn-sm">
          Open via Secure HTTPS (Port 5443)
        </a>
      </div>

      <div style="border-top: 1px dashed rgba(255,255,255,0.15); padding-top: 12px;">
        <label class="btn btn-outline-cyan btn-sm" style="cursor: pointer; width: 100%;">
          Snap Photo with Device Camera
          <input type="file" accept="image/*" capture="environment" style="display: none;" onchange="handleDirectCapture(this)">
        </label>
      </div>
    </div>
  `;
}

// Stop / Pause camera stream
function stopCamera() {
  if (videoStream) {
    videoStream.getTracks().forEach(track => track.stop());
    videoStream = null;
  }
  isScanning = false;
  updateStatusBadge('paused', 'Camera Paused');

  const placeholder = document.getElementById('camera-placeholder');
  const overlay = document.getElementById('scanner-overlay');
  const toggleBtn = document.getElementById('btn-toggle-camera');
  const title = document.getElementById('cam-placeholder-title');
  const desc = document.getElementById('cam-placeholder-desc');
  const actions = document.getElementById('cam-placeholder-actions');
  const pulseIndicator = document.getElementById('cam-pulse-indicator');

  if (placeholder) {
    placeholder.style.display = 'flex';
    if (pulseIndicator) pulseIndicator.style.display = 'none';
    if (title) title.textContent = 'Camera Paused';
    if (desc) desc.textContent = 'Click below to resume live QR code scanning.';
    if (actions) actions.style.display = 'block';
  }
  if (overlay) overlay.style.display = 'none';

  if (toggleBtn) {
    toggleBtn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Resume Camera`;
    toggleBtn.className = 'btn btn-primary btn-sm';
  }

  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
  }
}

// Continuous Real-Time Frame Analysis Loop
let lastScanTimestamp = 0;

// Adaptive contrast & histogram equalizer for smartphone screens & low-light badges
function enhanceContrastForPhoneScreen(data) {
  const len = data.length;
  let minLum = 255;
  let maxLum = 0;
  // Sample pixels to compute dynamic range
  const step = Math.max(4, Math.floor(len / 600) * 4);
  for (let i = 0; i < len; i += step) {
    const lum = (data[i] * 299 + data[i + 1] * 587 + data[i + 2] * 114) / 1000;
    if (lum < minLum) minLum = lum;
    if (lum > maxLum) maxLum = lum;
  }

  const range = maxLum - minLum;
  if (range < 25) return; // Insufficient dynamic range to equalize

  const invRange = 255 / range;
  for (let i = 0; i < len; i += 4) {
    const lum = (data[i] * 299 + data[i + 1] * 587 + data[i + 2] * 114) / 1000;
    let stretched = (lum - minLum) * invRange;
    // S-curve contrast boost
    stretched = stretched < 128 
      ? (stretched * stretched) / 128 
      : 255 - ((255 - stretched) * (255 - stretched)) / 128;
    data[i] = stretched;
    data[i + 1] = stretched;
    data[i + 2] = stretched;
  }
}

// Visual reticle green flash on successful detection
function flashScanReticle() {
  const targetFrame = document.querySelector('.target-frame');
  if (targetFrame) {
    targetFrame.classList.add('scan-detected');
    setTimeout(() => {
      targetFrame.classList.remove('scan-detected');
    }, 800);
  }
}

// Triple-Engine Multi-Pass QR Decoder (Native BarcodeDetector + jsQR + ZXing)
async function scanFrameForQRCode(video, canvas, ctx) {
  // ENGINE 1: Hardware-Accelerated Native BarcodeDetector (instant on modern Chromium/Edge)
  if (barcodeDetector) {
    try {
      const barcodes = await barcodeDetector.detect(video);
      if (barcodes && barcodes.length > 0 && barcodes[0].rawValue) {
        return barcodes[0].rawValue;
      }
    } catch (e) {}
  }

  const vw = video.videoWidth;
  const vh = video.videoHeight;
  if (!vw || !vh) return null;

  // PASS A: 1:1 Natural Reticle Crop (Highest module sharpness, NO downsampling blur)
  const cropSize = Math.round(Math.min(vw, vh) * 0.72);
  const sx = Math.round((vw - cropSize) / 2);
  const sy = Math.round((vh - cropSize) / 2);

  if (canvas.width !== cropSize || canvas.height !== cropSize) {
    canvas.width = cropSize;
    canvas.height = cropSize;
  }
  ctx.drawImage(video, sx, sy, cropSize, cropSize, 0, 0, cropSize, cropSize);

  // ENGINE 2 (Pass A): jsQR at 1:1 Pixel Fidelity
  if (typeof jsQR === 'function') {
    const imgData = ctx.getImageData(0, 0, cropSize, cropSize);
    let code = jsQR(imgData.data, cropSize, cropSize, { inversionAttempts: 'attemptBoth' });
    if (code && code.data) return code.data;

    // Pass A2: Phone backlight glare & contrast equalization
    enhanceContrastForPhoneScreen(imgData.data);
    code = jsQR(imgData.data, cropSize, cropSize, { inversionAttempts: 'dontInvert' });
    if (code && code.data) return code.data;
  }

  // ENGINE 3 (Pass A): Local Standalone ZXing Engine on 1:1 Reticle Crop
  if (zxingReader) {
    try {
      const zres = zxingReader.decode(canvas);
      if (zres && zres.getText && zres.getText()) return zres.getText();
    } catch (e) {}
  }

  // PASS B: Full-Frame High-Resolution Scan (for badges held off-center or distant)
  const maxDim = 1280;
  const scale = Math.min(1, maxDim / Math.max(vw, vh));
  const fw = Math.round(vw * scale);
  const fh = Math.round(vh * scale);

  if (canvas.width !== fw || canvas.height !== fh) {
    canvas.width = fw;
    canvas.height = fh;
  }
  ctx.drawImage(video, 0, 0, fw, fh);

  // ENGINE 2 (Pass B): jsQR on Full Frame
  if (typeof jsQR === 'function') {
    const fullImgData = ctx.getImageData(0, 0, fw, fh);
    let code = jsQR(fullImgData.data, fw, fh, { inversionAttempts: 'attemptBoth' });
    if (code && code.data) return code.data;

    enhanceContrastForPhoneScreen(fullImgData.data);
    code = jsQR(fullImgData.data, fw, fh, { inversionAttempts: 'dontInvert' });
    if (code && code.data) return code.data;
  }

  // ENGINE 3 (Pass B): ZXing on Full Frame
  if (zxingReader) {
    try {
      const zres = zxingReader.decode(canvas);
      if (zres && zres.getText && zres.getText()) return zres.getText();
    } catch (e) {}
  }

  return null;
}

// Continuous Frame Scan Loop with strict re-entrancy protection
async function scanVideoFrame(timestamp) {
  if (!isScanning) return;

  const video = document.getElementById('qr-video');

  if (video && video.readyState >= 2 && video.videoWidth > 0 && !isProcessing) {
    if (!isAnalyzingFrame && (timestamp - lastScanTimestamp > 35)) {
      lastScanTimestamp = timestamp;
      isAnalyzingFrame = true;

      try {
        const canvas = document.getElementById('qr-canvas');
        if (canvas) {
          const ctx = canvas.getContext('2d', { willReadFrequently: true });
          const detectedCode = await scanFrameForQRCode(video, canvas, ctx);

          if (detectedCode) {
            const cleanCode = extractRegistrationId(detectedCode);
            const now = Date.now();
            // Cooldown: prevent duplicate re-scan of same code within 3.5 seconds
            if (cleanCode && (cleanCode !== lastScannedCode || (now - lastScannedTime) > 3500)) {
              lastScannedCode = cleanCode;
              lastScannedTime = now;
              flashScanReticle();
              processScan(cleanCode);
            }
          }
        }
      } catch (err) {
        console.warn('[Scanner] Frame decode warning:', err);
      } finally {
        isAnalyzingFrame = false;
      }
    }
  }

  if (isScanning) {
    animationFrameId = requestAnimationFrame(scanVideoFrame);
  }
}

// Robust Registration ID Extractor (Handles raw codes, URLs, and query parameters)
function extractRegistrationId(raw) {
  if (!raw) return '';
  raw = String(raw).trim();
  const match = raw.match(/YES26-[A-Z]{3}-[A-Z0-9]{4,8}/i);
  if (match) return match[0].toUpperCase();
  try {
    const url = new URL(raw);
    const codeParam = url.searchParams.get('code') || url.searchParams.get('reg_id') || url.searchParams.get('id');
    if (codeParam) return codeParam.toUpperCase().trim();
  } catch (e) {}
  return raw.toUpperCase();
}

// Verification API Call
async function processScan(codeText) {
  const cleanCode = extractRegistrationId(codeText);
  if (!cleanCode) return;
  isProcessing = true;
  showScanFeedback('loading', { message: 'Validating Pass...' });

  const stationName = document.getElementById('kiosk-station-name')?.value || 'Main Gate Kiosk 1';

  try {
    const resp = await fetch('/api/checkin/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: cleanCode, station: stationName })
    });

    const res = await resp.json();

    if (res.success) {
      playSuccessChime();
      showScanFeedback('success', res);
      fetchRecentCheckins();

      // Open Category-Specific Lanyard ID Card modal
      setTimeout(() => {
        if (window.BadgeManager && res.attendee) {
          BadgeManager.openModal(res.attendee);
        }
      }, 400);

      // Auto-refresh admin tables if active
      if (typeof window.loadAdminStats === 'function') window.loadAdminStats();
      if (typeof window.loadRegistrations === 'function') window.loadRegistrations();

    } else if (res.error_type === 'DUPLICATE') {
      playDuplicateAlert();
      showScanFeedback('duplicate', res);

    } else {
      showScanFeedback('notfound', res);
    }
  } catch (err) {
    showScanFeedback('notfound', { message: 'Network / server error: ' + err.message });
  } finally {
    setTimeout(() => {
      isProcessing = false;
    }, 1200);
  }
}

// Render Feedback UI Cards
function showScanFeedback(state, data) {
  const target = document.getElementById('scan-feedback-container');
  if (!target) return;

  if (state === 'loading') {
    target.innerHTML = `
      <div class="feedback-card state-idle">
        <div class="spinner" style="margin: 0 auto 12px;"></div>
        <p style="font-size: 14px; color: #cbd5e1;">Verifying credentials against database...</p>
      </div>
    `;
    return;
  }

  if (state === 'success') {
    const a = data.attendee;
    window.currentScannedAttendee = a;
    target.innerHTML = `
      <div class="feedback-card state-success">
        <div class="alert-banner banner-success">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          <div>
            <div style="font-size: 15px; font-weight: 700;">CHECK-IN CONFIRMED</div>
            <div style="font-size: 12px; font-weight: 500; opacity: 0.9;">Welcome to YES 2026!</div>
          </div>
        </div>

        <div class="scanned-profile-card">
          <div class="scanned-avatar">${window.BadgeManager ? BadgeManager.getInitials(a.full_name) : 'YES'}</div>
          <div class="scanned-info">
            <span class="pill-cat pill-cat-${a.category}">${a.category.toUpperCase()} PASS</span>
            <h3 style="margin-top: 4px;">${a.full_name}</h3>
            <div class="org">${a.designation || 'Attendee'} • ${a.organization}</div>
          </div>
        </div>

        <div class="scanned-meta-grid">
          <div class="meta-box">
            <span class="lbl">Registration ID</span>
            <span class="val">${a.registration_id}</span>
          </div>
          <div class="meta-box">
            <span class="lbl">Check-in Time</span>
            <span class="val">${a.check_in_time}</span>
          </div>
        </div>

        <div style="display: flex; gap: 10px; margin-top: 14px;">
          <button class="btn btn-primary" id="btn-print-lanyard" style="flex: 1;" onclick="BadgeManager.openModal(window.currentScannedAttendee || '${a.registration_id}')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9V2h12v7M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><path d="M6 14h12v8H6z"/></svg>
            Print Lanyard ID Badge
          </button>
        </div>
      </div>
    `;
  } else if (state === 'duplicate') {
    const a = data.attendee || {};
    window.currentScannedAttendee = a;
    target.innerHTML = `
      <div class="feedback-card state-duplicate">
        <div class="alert-banner banner-duplicate">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          <div>
            <div style="font-size: 16px; font-weight: 700;">DUPLICATE CHECK-IN PREVENTED</div>
            <div style="font-size: 12px; font-weight: 500;">This pass has already been used to check in!</div>
          </div>
        </div>

        <div class="scanned-profile-card">
          <div class="scanned-avatar">${window.BadgeManager ? BadgeManager.getInitials(a.full_name) : 'YES'}</div>
          <div class="scanned-info">
            <span class="pill-cat pill-cat-${a.category || 'participant'}">${(a.category || 'ATTENDEE').toUpperCase()}</span>
            <h3 style="margin-top: 4px;">${a.full_name || 'Registered Attendee'}</h3>
            <div class="org">${a.organization || 'Organization'}</div>
          </div>
        </div>

        <div class="scanned-meta-grid">
          <div class="meta-box" style="border-color: rgba(239, 68, 68, 0.4);">
            <span class="lbl" style="color: #fca5a5;">Initial Check-in Time</span>
            <span class="val" style="color: #ef4444;">${data.check_in_time || 'Earlier Today'}</span>
          </div>
          <div class="meta-box" style="border-color: rgba(239, 68, 68, 0.4);">
            <span class="lbl" style="color: #fca5a5;">Check-in Station</span>
            <span class="val" style="color: #ef4444;">${data.check_in_station || 'Main Kiosk'}</span>
          </div>
        </div>

        <div style="display: flex; gap: 10px; margin-top: 14px;">
          <button class="btn btn-primary" id="btn-reprint-lanyard" style="flex: 1;" onclick="BadgeManager.openModal(window.currentScannedAttendee || '${a.registration_id}')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9V2h12v7M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><path d="M6 14h12v8H6z"/></svg>
            Print Lanyard ID Badge
          </button>
        </div>
      </div>
    `;
  } else {
    target.innerHTML = `
      <div class="feedback-card state-notfound">
        <div class="alert-banner banner-notfound">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
          <div>
            <div style="font-size: 15px; font-weight: 700;">UNRECOGNIZED PASS</div>
            <div style="font-size: 12px; font-weight: 500;">${data.message || 'Registration ID not found in database.'}</div>
          </div>
        </div>
        <p style="font-size: 13px; color: var(--text-muted);">
          Please check the code or perform a manual search by email/name in the Admin Dashboard.
        </p>
      </div>
    `;
  }
}

// Manual Registration ID Lookup Input
function initManualInput() {
  const form = document.getElementById('manual-search-form');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const input = document.getElementById('manual-reg-id');
    const code = input?.value?.trim();
    if (!code) return;

    processScan(code);
    input.value = '';
  });
}

// Direct Native Camera Snapshot Capture (Works on HTTP IP and all devices)
function handleDirectCapture(fileInput) {
  if (!fileInput || !fileInput.files || fileInput.files.length === 0) return;
  const file = fileInput.files[0];
  decodeQRFromFile(file);
}

// File Upload QR Code Scanning
function initFileUpload() {
  const fileInput = document.getElementById('qr-file-input');
  if (!fileInput) return;

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length === 0) return;
    const file = e.target.files[0];
    decodeQRFromFile(file);
  });
}

function decodeQRFromFile(file) {
  const reader = new FileReader();
  reader.onload = (event) => {
    const img = new Image();
    img.onload = async () => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d', { willReadFrequently: true });
      // Proportional downscale for high-megapixel mobile photos (4000x3000 down to max 1400px)
      const maxDim = 1400;
      let w = img.width;
      let h = img.height;
      if (w > maxDim || h > maxDim) {
        if (w > h) {
          h = Math.round((h * maxDim) / w);
          w = maxDim;
        } else {
          w = Math.round((w * maxDim) / h);
          h = maxDim;
        }
      }
      canvas.width = w;
      canvas.height = h;
      ctx.drawImage(img, 0, 0, w, h);

      let decoded = null;

      // 1. BarcodeDetector
      if (barcodeDetector) {
        try {
          const bcs = await barcodeDetector.detect(canvas);
          if (bcs && bcs.length > 0 && bcs[0].rawValue) decoded = bcs[0].rawValue;
        } catch (e) {}
      }

      // 2. jsQR (original + contrast-stretched)
      if (!decoded && typeof jsQR === 'function') {
        const imgData = ctx.getImageData(0, 0, w, h);
        let code = jsQR(imgData.data, w, h, { inversionAttempts: 'attemptBoth' });
        if (code && code.data) {
          decoded = code.data;
        } else {
          enhanceContrastForPhoneScreen(imgData.data);
          code = jsQR(imgData.data, w, h, { inversionAttempts: 'dontInvert' });
          if (code && code.data) decoded = code.data;
        }
      }

      // 3. ZXing
      if (!decoded && zxingReader) {
        try {
          const zres = zxingReader.decode(canvas);
          if (zres && zres.getText && zres.getText()) decoded = zres.getText();
        } catch (e) {}
      }

      if (decoded) {
        flashScanReticle();
        processScan(decoded);
      } else {
        showScanFeedback('notfound', { message: 'Could not decode QR code from the captured image. Please ensure the QR code is clear, well-lit, and unblurred.' });
      }
    };
    img.src = event.target.result;
  };
  reader.readAsDataURL(file);
}

// Live Recent Check-ins Ticker
async function fetchRecentCheckins() {
  try {
    const resp = await fetch('/api/checkin/recent');
    const data = await resp.json();

    if (data.success) {
      const elChecked = document.getElementById('kiosk-stat-checked');
      const elTotal = document.getElementById('kiosk-stat-total');
      const elRate = document.getElementById('kiosk-stat-rate');

      if (elChecked) elChecked.textContent = data.total_checked_in;
      if (elTotal) elTotal.textContent = data.total_registered;

      const rate = data.total_registered > 0 
        ? Math.round((data.total_checked_in / data.total_registered) * 100) 
        : 0;
      if (elRate) elRate.textContent = rate + '%';

      renderRecentStream(data.recent_checkins);
    }
  } catch (e) {}
}

function renderRecentStream(list) {
  const streamEl = document.getElementById('recent-stream-list');
  if (!streamEl) return;

  if (!list || list.length === 0) {
    streamEl.innerHTML = `<div style="text-align: center; color: var(--text-dim); padding: 20px; font-size: 13px;">No check-ins yet. Ready for scans.</div>`;
    return;
  }

  streamEl.innerHTML = list.map(item => `
    <div class="recent-item">
      <div>
        <strong style="color: #f1f5f9;">${item.full_name}</strong>
        <span class="pill-cat pill-cat-${item.category}" style="font-size: 10px; padding: 1px 6px; margin-left: 6px;">${item.category.toUpperCase()}</span>
        <div style="font-size: 11px; color: var(--text-dim);">${item.organization || ''}</div>
      </div>
      <div style="text-align: right; font-family: var(--font-mono); font-size: 11px; color: var(--secondary);">
        ${item.check_in_time ? item.check_in_time.split(' ')[1] : ''}
      </div>
    </div>
  `).join('');
}

window.handleDirectCapture = handleDirectCapture;
window.startCamera = startCamera;
