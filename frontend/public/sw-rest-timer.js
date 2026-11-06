// FitPulse Background Rest Timer Service Worker Extension
let activeRestTimerId = null
let activeResolve = null

function clearPendingTimer() {
  if (activeRestTimerId !== null) {
    clearTimeout(activeRestTimerId)
    activeRestTimerId = null
  }
  if (activeResolve) {
    activeResolve()
    activeResolve = null
  }
}

self.addEventListener('message', (event) => {
  const data = event.data
  if (!data || !data.type) return

  if (data.type === 'SCHEDULE_REST_NOTIFICATION') {
    clearPendingTimer()

    const now = Date.now()
    const targetEndTime = Number(data.endTime) || (now + (Number(data.delayMs) || 0))
    const delayMs = Math.max(0, targetEndTime - now)
    const title = data.title || '休息時間結束'
    const body = data.body || '組間休息已結束，準備進行下一組動作'

    const timerPromise = new Promise((resolve) => {
      activeResolve = resolve
      activeRestTimerId = setTimeout(async () => {
        activeRestTimerId = null
        activeResolve = null
        try {
          if (self.registration && self.registration.showNotification) {
            await self.registration.showNotification(title, {
              body,
              icon: '/pwa-192x192.png',
              badge: '/apple-touch-icon.png',
              tag: 'fitpulse-rest-alert',
              renotify: true,
              silent: false,
              vibrate: [200, 100, 200, 100, 300],
              data: { url: '/active-workout', endTime: targetEndTime }
            })
          }
          const clientsList = await self.clients.matchAll({ type: 'window', includeUncontrolled: true })
          for (const client of clientsList) {
            client.postMessage({
              type: 'REST_NOTIFICATION_FIRED',
              endTime: targetEndTime
            })
          }
        } catch (err) {
          // Ignore errors in background notification dispatch
        } finally {
          resolve()
        }
      }, delayMs)
    })

    if (event.waitUntil) {
      event.waitUntil(timerPromise)
    }
  } else if (data.type === 'CANCEL_REST_NOTIFICATION') {
    clearPendingTimer()
  }
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if ('focus' in client) {
          return client.focus()
        }
      }
      if (self.clients.openWindow) {
        return self.clients.openWindow('/active-workout')
      }
    })
  )
})

