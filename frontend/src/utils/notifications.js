/**
 * FitPulse Native Web Notifications, Background Rest Timer & Sound/Vibration Helper
 */

let sharedAudioCtx = null
let scheduledAudioNodes = []
let keepAliveSource = null
let restWorker = null
let lastNotifiedEndTime = 0

function getOrCreateAudioContext() {
  const AudioCtx = window.AudioContext || window.webkitAudioContext
  if (!AudioCtx) return null
  if (!sharedAudioCtx || sharedAudioCtx.state === 'closed') {
    sharedAudioCtx = new AudioCtx()
  }
  if (sharedAudioCtx.state === 'suspended') {
    sharedAudioCtx.resume().catch(() => {})
  }
  return sharedAudioCtx
}

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

export function stopScheduledAudioKeepAlive() {
  scheduledAudioNodes.forEach((node) => {
    try {
      node.stop()
      node.disconnect()
    } catch (e) {}
  })
  scheduledAudioNodes = []

  if (keepAliveSource) {
    try {
      keepAliveSource.stop()
      keepAliveSource.disconnect()
    } catch (e) {}
    keepAliveSource = null
  }
}

/**
 * Schedules a hardware-clock Web Audio chime at `delaySeconds` in the future
 * plus a sub-audible keep-alive buffer so iOS PWA does not suspend the timer
 * when the user switches to another app during rest.
 */
export function scheduleAudioChimeInSeconds(delaySeconds) {
  try {
    stopScheduledAudioKeepAlive()
    const ctx = getOrCreateAudioContext()
    if (!ctx) return

    const safeDelay = Math.max(0.5, Number(delaySeconds) || 0)
    const now = ctx.currentTime
    const chimeStart = now + safeDelay

    // 1. Sub-audible keep-alive buffer during the countdown window
    const bufferRate = 8000
    const buffer = ctx.createBuffer(1, bufferRate, bufferRate)
    const chan = buffer.getChannelData(0)
    for (let i = 0; i < bufferRate; i++) {
      chan[i] = (i % 2 === 0 ? 1 : -1) * 0.00002
    }
    const silentLoop = ctx.createBufferSource()
    silentLoop.buffer = buffer
    silentLoop.loop = true
    const silentGain = ctx.createGain()
    silentGain.gain.setValueAtTime(0.0001, now)
    silentLoop.connect(silentGain)
    silentGain.connect(ctx.destination)
    silentLoop.start(now)
    silentLoop.stop(chimeStart + 1.5)
    keepAliveSource = silentLoop

    // 2. Hardware-scheduled ascending athletic chime at exact rest completion
    const tones = [523.25, 659.25, 783.99, 1046.5]
    tones.forEach((freq, idx) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      const startTime = chimeStart + idx * 0.14

      osc.type = 'sine'
      osc.frequency.setValueAtTime(freq, startTime)
      gain.gain.setValueAtTime(0.0001, now)
      gain.gain.setValueAtTime(0.35, startTime)
      gain.gain.exponentialRampToValueAtTime(0.001, startTime + 0.38)

      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.start(startTime)
      osc.stop(startTime + 0.4)
      scheduledAudioNodes.push(osc)
    })
  } catch (e) {
    console.log('Scheduled audio keep-alive fallback:', e)
  }
}

export function playTimerChime() {
  try {
    const ctx = getOrCreateAudioContext()
    if (!ctx) return

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
    const ctx = getOrCreateAudioContext()
    if (!ctx) return
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

async function postToServiceWorker(message) {
  if (!('serviceWorker' in navigator)) return
  try {
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage(message)
      return
    }
    const reg = await navigator.serviceWorker.ready
    if (reg && reg.active) {
      reg.active.postMessage(message)
    }
  } catch (e) {}
}

if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
  navigator.serviceWorker.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'REST_NOTIFICATION_FIRED') {
      if (event.data.endTime) {
        lastNotifiedEndTime = Number(event.data.endTime)
      }
    }
  })
}

export function scheduleBackgroundRestAlert(endTimeMs, title = '休息時間結束', body = '組間休息已結束，準備進行下一組動作', onWorkerReachedZero = null) {
  const now = Date.now()
  const delayMs = Math.max(0, endTimeMs - now)
  const delaySecs = delayMs / 1000

  // Auto-request permission on user gesture if not yet granted/denied
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission().catch(() => {})
  }

  // 1. Hardware Web Audio scheduled chime + background keep-alive
  scheduleAudioChimeInSeconds(delaySecs)

  // 2. Service Worker background notification schedule
  postToServiceWorker({
    type: 'SCHEDULE_REST_NOTIFICATION',
    endTime: endTimeMs,
    delayMs,
    title,
    body
  })

  // 3. Dedicated Web Worker timer (less throttled than main-thread setInterval)
  if (restWorker) {
    try {
      restWorker.terminate()
    } catch (e) {}
    restWorker = null
  }
  try {
    const workerCode = `
      let timer = setTimeout(() => {
        self.postMessage({ type: 'EXPIRED', endTime: ${endTimeMs} });
      }, ${delayMs});
      self.onmessage = (e) => {
        if (e.data === 'STOP') clearTimeout(timer);
      };
    `
    const blob = new Blob([workerCode], { type: 'application/javascript' })
    const url = URL.createObjectURL(blob)
    restWorker = new Worker(url)
    restWorker.onmessage = (e) => {
      if (e.data && e.data.type === 'EXPIRED') {
        if (typeof onWorkerReachedZero === 'function') {
          onWorkerReachedZero()
        }
      }
      URL.revokeObjectURL(url)
    }
  } catch (e) {}
}

export function cancelBackgroundRestAlert() {
  stopScheduledAudioKeepAlive()
  postToServiceWorker({ type: 'CANCEL_REST_NOTIFICATION' })
  if (restWorker) {
    try {
      restWorker.postMessage('STOP')
      restWorker.terminate()
    } catch (e) {}
    restWorker = null
  }
}

export function hasEndTimeAlreadyNotified(endTimeMs) {
  return Boolean(endTimeMs && lastNotifiedEndTime === Number(endTimeMs))
}

export async function sendRestNotification(
  title = '休息時間結束',
  body = '組間休息已結束，準備進行下一組動作',
  endTimeMs = null
) {
  if (endTimeMs && lastNotifiedEndTime === Number(endTimeMs)) {
    return
  }
  if (endTimeMs) {
    lastNotifiedEndTime = Number(endTimeMs)
  }

  stopScheduledAudioKeepAlive()
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
    if ('serviceWorker' in navigator) {
      const reg = await navigator.serviceWorker.ready
      if (reg && reg.showNotification) {
        await reg.showNotification(title, options)
        return
      }
    }
    new Notification(title, options)
  } catch (e) {
    try {
      new Notification(title, options)
    } catch (err) {}
  }
}
