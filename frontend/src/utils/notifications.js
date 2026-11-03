/**
 * FitPulse Native Web Notifications & Sound/Vibration Helper
 */

export async function requestNotificationPermission() {
  if (!('Notification' in window)) {
    return 'unsupported'
  }
  try {
    const permission = await Notification.requestPermission()
    return permission
  } catch (e) {
    console.error('Error requesting notification permission:', e)
    return 'denied'
  }
}

export function isNotificationSupported() {
  return 'Notification' in window
}

export function getNotificationPermission() {
  if (!('Notification' in window)) return 'unsupported'
  return Notification.permission
}

export function playTimerChime() {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext
    if (!AudioCtx) return
    const ctx = new AudioCtx()
    
    // Play a dual-tone ascending athletic chime (C5 -> E5 -> G5)
    const tones = [523.25, 659.25, 783.99]
    tones.forEach((freq, idx) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      const startTime = ctx.currentTime + idx * 0.12
      
      osc.type = 'sine'
      osc.frequency.setValueAtTime(freq, startTime)
      gain.gain.setValueAtTime(0.3, startTime)
      gain.gain.exponentialRampToValueAtTime(0.001, startTime + 0.35)
      
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.start(startTime)
      osc.stop(startTime + 0.35)
    })
  } catch (e) {
    console.log('Audio chime played with error/restriction:', e)
  }
}

export function triggerVibration(pattern = [200, 100, 200, 100, 300]) {
  if ('vibrate' in navigator) {
    try {
      navigator.vibrate(pattern)
    } catch (e) {
      console.log('Vibration error:', e)
    }
  }
}

/**
 * High-Five Crisp Acoustic Slap + Victory Chime Synthesizer
 */
export function playHighFiveSound() {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext
    if (!AudioCtx) return
    const ctx = new AudioCtx()
    const now = ctx.currentTime

    // 1. Crisp handclap noise snap (20ms fast burst)
    const bufferSize = Math.floor(ctx.sampleRate * 0.08)
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate)
    const data = buffer.getChannelData(0)
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * Math.exp(-i / (ctx.sampleRate * 0.018))
    }
    const noise = ctx.createBufferSource()
    noise.buffer = buffer
    const noiseFilter = ctx.createBiquadFilter()
    noiseFilter.type = 'bandpass'
    noiseFilter.frequency.setValueAtTime(1200, now)
    noiseFilter.Q.setValueAtTime(1.8, now)
    const noiseGain = ctx.createGain()
    noiseGain.gain.setValueAtTime(0.85, now)
    noiseGain.gain.exponentialRampToValueAtTime(0.005, now + 0.08)
    noise.connect(noiseFilter)
    noiseFilter.connect(noiseGain)
    noiseGain.connect(ctx.destination)
    noise.start(now)

    // 2. Resonant palm body impact thud (160Hz -> 50Hz)
    const thud = ctx.createOscillator()
    const thudGain = ctx.createGain()
    thud.type = 'sine'
    thud.frequency.setValueAtTime(160, now)
    thud.frequency.exponentialRampToValueAtTime(50, now + 0.11)
    thudGain.gain.setValueAtTime(0.65, now)
    thudGain.gain.exponentialRampToValueAtTime(0.001, now + 0.11)
    thud.connect(thudGain)
    thudGain.connect(ctx.destination)
    thud.start(now)
    thud.stop(now + 0.12)

    // 3. Ascending victory fanfare chime (C5 -> E5 -> G5 -> C6)
    const fanfareTones = [523.25, 659.25, 783.99, 1046.50]
    fanfareTones.forEach((freq, idx) => {
      const osc = ctx.createOscillator()
      const g = ctx.createGain()
      const startTime = now + 0.12 + idx * 0.08
      osc.type = 'triangle'
      osc.frequency.setValueAtTime(freq, startTime)
      g.gain.setValueAtTime(0.3, startTime)
      g.gain.exponentialRampToValueAtTime(0.001, startTime + 0.45)
      osc.connect(g)
      g.connect(ctx.destination)
      osc.start(startTime)
      osc.stop(startTime + 0.45)
    })
  } catch (e) {
    console.log('High-five audio played with error:', e)
  }
}

/**
 * Native Web Speech API Audio Cheer
 */
export function speakCheer(text = '太棒了！今日挑戰達成，為你的堅持喝采！') {
  if (!('speechSynthesis' in window)) return
  try {
    window.speechSynthesis.cancel()
    const utter = new SpeechSynthesisUtterance(text)
    utter.lang = 'zh-TW'
    utter.rate = 1.05
    utter.pitch = 1.15
    window.speechSynthesis.speak(utter)
  } catch (e) {
    console.log('Speech synthesis error:', e)
  }
}

export async function sendRestNotification(title = '🔔 休息時間到！', body = '準備進行下一組動作，保持專注 💪') {
  playTimerChime()
  triggerVibration()

  if (!('Notification' in window) || Notification.permission !== 'granted') {
    return
  }

  const options = {
    body,
    icon: '/pwa-192x192.png',
    badge: '/apple-touch-icon.png',
    tag: 'fitpulse-rest-alert',
    renotify: true,
    silent: false,
    vibrate: [200, 100, 200, 100, 300]
  }

  try {
    // Try service worker notification first (supports background/screen lock)
    if ('serviceWorker' in navigator) {
      const reg = await navigator.serviceWorker.ready
      if (reg && reg.showNotification) {
        await reg.showNotification(title, options)
        return
      }
    }
    // Fallback to standard window Notification
    new Notification(title, options)
  } catch (e) {
    console.log('Notification dispatch fallback:', e)
    try {
      new Notification(title, options)
    } catch (err) {}
  }
}
