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

export function triggerVibration() {
  if ('vibrate' in navigator) {
    try {
      navigator.vibrate([200, 100, 200, 100, 300])
    } catch (e) {
      console.log('Vibration error:', e)
    }
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
