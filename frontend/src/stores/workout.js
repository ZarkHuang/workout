import { defineStore } from 'pinia'
import { ref, watch, computed } from 'vue'
import { workoutsAPI } from '@/api/client'
import { sendRestNotification, playTimerChime, triggerVibration } from '@/utils/notifications'

export const useWorkoutStore = defineStore('workout', () => {
  // 1. Workout Session State (Flexible post-workout or in-gym logging)
  const isWorkoutActive = ref(false)
  const sessionName = ref('今日自訂訓練')
  const routineId = ref(null)
  const startTime = ref(null)
  const sessionDate = ref(new Date().toISOString().substring(0, 10))
  const durationMinutes = ref(45)
  const activeExercises = ref([]) 

  // Timestamp-based Session Stopwatch State
  const sessionTimerStart = ref(null) // timestamp ms
  const sessionAccumulatedSeconds = ref(0)
  const sessionTimerRunning = ref(false)

  // 2. Timestamp-based Rest Timer State
  const defaultRestSeconds = ref(parseInt(localStorage.getItem('fitpulse_default_rest_seconds') || '90', 10))
  const isTimerActive = ref(false)
  const restTimerEndTime = ref(null) // timestamp ms
  const timerTotalSeconds = ref(90)
  const timerRemainingSeconds = ref(90)
  let timerInterval = null

  // Restore active workout from localStorage on startup
  const savedSession = localStorage.getItem('fitpulse_active_workout')
  if (savedSession) {
    try {
      const data = JSON.parse(savedSession)
      isWorkoutActive.value = data.isWorkoutActive || false
      sessionName.value = data.sessionName || '今日訓練'
      routineId.value = data.routineId || null
      startTime.value = data.startTime ? new Date(data.startTime) : null
      sessionDate.value = data.sessionDate || new Date().toISOString().substring(0, 10)
      durationMinutes.value = data.durationMinutes || 45
      activeExercises.value = data.activeExercises || []
      sessionTimerStart.value = data.sessionTimerStart || null
      sessionAccumulatedSeconds.value = data.sessionAccumulatedSeconds || 0
      sessionTimerRunning.value = data.sessionTimerRunning || false
    } catch (e) {
      console.error('Failed to parse active workout cache:', e)
    }
  }

  // Restore active rest timer if exists
  const savedRestEnd = localStorage.getItem('fitpulse_rest_timer_end')
  if (savedRestEnd) {
    const endMs = parseInt(savedRestEnd, 10)
    const totalSecs = parseInt(localStorage.getItem('fitpulse_rest_timer_total') || '90', 10)
    const now = Date.now()
    if (endMs > now) {
      isTimerActive.value = true
      restTimerEndTime.value = endMs
      timerTotalSeconds.value = totalSecs
      timerRemainingSeconds.value = Math.ceil((endMs - now) / 1000)
      startRestTicker()
    } else {
      localStorage.removeItem('fitpulse_rest_timer_end')
      localStorage.removeItem('fitpulse_rest_timer_total')
    }
  }

  // Save active workout to localStorage whenever it changes
  watch(
    [isWorkoutActive, sessionName, routineId, startTime, sessionDate, durationMinutes, activeExercises, sessionTimerStart, sessionAccumulatedSeconds, sessionTimerRunning],
    () => {
      if (isWorkoutActive.value) {
        localStorage.setItem(
          'fitpulse_active_workout',
          JSON.stringify({
            isWorkoutActive: isWorkoutActive.value,
            sessionName: sessionName.value,
            routineId: routineId.value,
            startTime: startTime.value,
            sessionDate: sessionDate.value,
            durationMinutes: durationMinutes.value,
            activeExercises: activeExercises.value,
            sessionTimerStart: sessionTimerStart.value,
            sessionAccumulatedSeconds: sessionAccumulatedSeconds.value,
            sessionTimerRunning: sessionTimerRunning.value
          })
        )
      } else {
        localStorage.removeItem('fitpulse_active_workout')
      }
    },
    { deep: true }
  )

  // Start new workout session
  function startWorkout(name = '今日自訂訓練', routine = null) {
    isWorkoutActive.value = true
    sessionName.value = name
    routineId.value = routine?.id || null
    startTime.value = new Date()
    sessionDate.value = new Date().toISOString().substring(0, 10)
    durationMinutes.value = 45
    activeExercises.value = []
    sessionTimerStart.value = null
    sessionAccumulatedSeconds.value = 0
    sessionTimerRunning.value = false

    if (routine && routine.exercises) {
      routine.exercises.forEach((re) => {
        const sets = []
        const numSets = Number(re.target_sets) || 3
        const numReps = parseInt(re.target_reps) || 10
        for (let i = 1; i <= numSets; i++) {
          sets.push({
            set_number: i,
            weight_kg: 0,
            reps: numReps,
            rpe: 8.0,
            is_completed: false,
            prev_weight: null,
            prev_reps: null
          })
        }
        activeExercises.value.push({
          exercise_id: re.exercise_id,
          name: re.exercise?.name || '未知動作',
          target_muscle_group: re.exercise?.target_muscle_group || 'CHEST',
          timerStatus: 'IDLE',
          elapsedSeconds: 0,
          startTimestamp: null,
          accumulatedSeconds: 0,
          sets
        })
      })
    }
  }

  // Add an exercise to active workout
  function addExerciseToActive(exercise) {
    const existing = activeExercises.value.find((e) => e.exercise_id === exercise.id)
    if (existing) return

    activeExercises.value.push({
      exercise_id: exercise.id,
      name: exercise.name,
      target_muscle_group: exercise.target_muscle_group,
      timerStatus: 'IDLE',
      elapsedSeconds: 0,
      startTimestamp: null,
      accumulatedSeconds: 0,
      sets: [
        {
          set_number: 1,
          weight_kg: 0,
          reps: 10,
          rpe: 8.0,
          is_completed: false,
          prev_weight: null,
          prev_reps: null
        }
      ]
    })
  }

  function addSet(exerciseIndex) {
    const ex = activeExercises.value[exerciseIndex]
    if (!ex) return
    const nextSetNum = ex.sets.length + 1
    const lastSet = ex.sets[ex.sets.length - 1]
    ex.sets.push({
      set_number: nextSetNum,
      weight_kg: lastSet ? lastSet.weight_kg : 0,
      reps: lastSet ? lastSet.reps : 10,
      rpe: 8.0,
      is_completed: false,
      prev_weight: lastSet?.prev_weight || null,
      prev_reps: lastSet?.prev_reps || null
    })
  }

  function removeSet(exerciseIndex, setIndex) {
    const ex = activeExercises.value[exerciseIndex]
    if (!ex || ex.sets.length <= 1) return
    ex.sets.splice(setIndex, 1)
    ex.sets.forEach((s, idx) => {
      s.set_number = idx + 1
    })
  }

  function removeExercise(exerciseIndex) {
    activeExercises.value.splice(exerciseIndex, 1)
  }

  // --- Timestamp-Based Session Stopwatch Controls ---
  function startSessionTimer() {
    if (!sessionTimerRunning.value) {
      sessionTimerRunning.value = true
      sessionTimerStart.value = Date.now()
      if (!startTime.value) startTime.value = new Date()
    }
  }

  function pauseSessionTimer() {
    if (sessionTimerRunning.value) {
      if (sessionTimerStart.value) {
        sessionAccumulatedSeconds.value += Math.floor((Date.now() - sessionTimerStart.value) / 1000)
      }
      sessionTimerStart.value = null
      sessionTimerRunning.value = false
    }
  }

  function toggleSessionTimer() {
    if (sessionTimerRunning.value) {
      pauseSessionTimer()
    } else {
      startSessionTimer()
    }
  }

  function getSessionElapsedSeconds() {
    if (sessionTimerRunning.value && sessionTimerStart.value) {
      return sessionAccumulatedSeconds.value + Math.floor((Date.now() - sessionTimerStart.value) / 1000)
    }
    return sessionAccumulatedSeconds.value
  }

  // --- Timestamp-Based Single Exercise Stopwatch ---
  function toggleExerciseTimer(exerciseIndex) {
    const ex = activeExercises.value[exerciseIndex]
    if (!ex) return

    // Ensure main session timer is running
    if (!sessionTimerRunning.value) {
      startSessionTimer()
    }

    if (ex.timerStatus === 'RUNNING') {
      ex.timerStatus = 'PAUSED'
      if (ex.startTimestamp) {
        ex.accumulatedSeconds = (ex.accumulatedSeconds || 0) + Math.floor((Date.now() - ex.startTimestamp) / 1000)
      }
      ex.startTimestamp = null
      ex.elapsedSeconds = ex.accumulatedSeconds || 0
    } else {
      ex.timerStatus = 'RUNNING'
      ex.startTimestamp = Date.now()
    }
  }

  function resetExerciseTimer(exerciseIndex) {
    const ex = activeExercises.value[exerciseIndex]
    if (!ex) return
    ex.timerStatus = 'IDLE'
    ex.elapsedSeconds = 0
    ex.startTimestamp = null
    ex.accumulatedSeconds = 0
  }

  function syncExerciseTimers() {
    activeExercises.value.forEach((ex) => {
      if (ex.timerStatus === 'RUNNING' && ex.startTimestamp) {
        ex.elapsedSeconds = (ex.accumulatedSeconds || 0) + Math.floor((Date.now() - ex.startTimestamp) / 1000)
      }
    })
  }

  // --- Timestamp-Based Rest Timer Controls ---
  function startRestTimer(seconds = 90, exName = '', setNum = 1) {
    clearInterval(timerInterval)
    const now = Date.now()
    restTimerEndTime.value = now + seconds * 1000
    timerTotalSeconds.value = seconds
    timerRemainingSeconds.value = seconds
    isTimerActive.value = true

    localStorage.setItem('fitpulse_rest_timer_end', restTimerEndTime.value.toString())
    localStorage.setItem('fitpulse_rest_timer_total', seconds.toString())

    startRestTicker(exName, setNum)
  }

  function startRestTicker(exName = '', setNum = 1) {
    clearInterval(timerInterval)
    timerInterval = setInterval(() => {
      syncRestTimerTick(exName, setNum)
    }, 500)
  }

  function syncRestTimerTick(exName = '', setNum = 1) {
    if (!isTimerActive.value || !restTimerEndTime.value) return
    const now = Date.now()
    const diff = Math.ceil((restTimerEndTime.value - now) / 1000)

    if (diff > 0) {
      timerRemainingSeconds.value = diff
    } else {
      timerRemainingSeconds.value = 0
      clearInterval(timerInterval)
      isTimerActive.value = false
      restTimerEndTime.value = null
      localStorage.removeItem('fitpulse_rest_timer_end')
      localStorage.removeItem('fitpulse_rest_timer_total')

      sendRestNotification(
        '🔔 FitPulse 休息時間結束！',
        exName ? `第 ${setNum + 1} 組 ${exName} 準備開練！深呼吸，保持專注 💪` : '組間休息已結束，準備進行下一組動作！💪'
      )
    }
  }

  function stopRestTimer() {
    clearInterval(timerInterval)
    isTimerActive.value = false
    restTimerEndTime.value = null
    localStorage.removeItem('fitpulse_rest_timer_end')
    localStorage.removeItem('fitpulse_rest_timer_total')
  }

  function addTimerSeconds(seconds = 30) {
    if (!restTimerEndTime.value) {
      startRestTimer(seconds)
      return
    }
    restTimerEndTime.value += seconds * 1000
    timerTotalSeconds.value += seconds
    timerRemainingSeconds.value += seconds
    localStorage.setItem('fitpulse_rest_timer_end', restTimerEndTime.value.toString())
    localStorage.setItem('fitpulse_rest_timer_total', timerTotalSeconds.value.toString())
  }

  function setDefaultRestSeconds(secs) {
    defaultRestSeconds.value = Number(secs) || 90
    localStorage.setItem('fitpulse_default_rest_seconds', defaultRestSeconds.value.toString())
  }

  function setRestTimerDuration(secs) {
    const s = Math.max(5, Number(secs) || 90)
    startRestTimer(s)
  }

  // Toggle set completion and trigger rest timer
  function toggleSetComplete(exerciseIndex, setIndex, customRestSeconds = null) {
    const ex = activeExercises.value[exerciseIndex]
    const set = ex?.sets[setIndex]
    if (!set) return
    
    // Auto-start session timer if not running
    if (!sessionTimerRunning.value) {
      startSessionTimer()
    }

    set.is_completed = !set.is_completed
    if (set.is_completed) {
      const restSecs = customRestSeconds || ex?.rest_seconds || defaultRestSeconds.value || 90
      startRestTimer(restSecs, ex?.name, set.set_number)
    }
  }

  // Lifecycle listeners for seamless tab switching / phone locking
  if (typeof window !== 'undefined') {
    window.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        syncRestTimerTick()
        syncExerciseTimers()
      }
    })
    window.addEventListener('focus', () => {
      syncRestTimerTick()
      syncExerciseTimers()
    })
  }

  // Finish and submit workout session to backend
  async function finishWorkout(customDuration = null, customDateStr = null) {
    const allSets = []
    let totalVol = 0

    activeExercises.value.forEach((ex) => {
      ex.sets.forEach((s) => {
        if (s.is_completed || s.weight_kg > 0 || s.reps > 0) {
          totalVol += (Number(s.weight_kg) || 0) * (Number(s.reps) || 0)
          allSets.push({
            exercise_id: ex.exercise_id,
            set_number: s.set_number,
            weight_kg: Number(s.weight_kg) || 0,
            reps: Number(s.reps) || 0,
            rpe: Number(s.rpe) || 8.0,
            is_completed: true
          })
        }
      })
    })

    if (allSets.length === 0) {
      throw new Error('請至少填寫 1 組動作的重量或次數！')
    }

    const calculatedElapsedMins = Math.max(1, Math.round(getSessionElapsedSeconds() / 60))
    const duration = customDuration !== null ? Number(customDuration) : calculatedElapsedMins
    const targetDate = customDateStr ? new Date(customDateStr) : (startTime.value ? new Date(startTime.value) : new Date())

    const sessionPayload = {
      routine_id: routineId.value,
      session_name: sessionName.value || '今日訓練紀錄',
      start_time: targetDate.toISOString(),
      end_time: new Date(targetDate.getTime() + duration * 60000).toISOString(),
      duration_minutes: duration,
      sets: allSets
    }

    try {
      const res = await workoutsAPI.createSession(sessionPayload)
      // Reset state completely
      isWorkoutActive.value = false
      activeExercises.value = []
      routineId.value = null
      startTime.value = null
      sessionTimerStart.value = null
      sessionAccumulatedSeconds.value = 0
      sessionTimerRunning.value = false
      stopRestTimer()
      localStorage.removeItem('fitpulse_active_workout')
      return res.data
    } catch (err) {
      throw err
    }
  }

  function cancelWorkout() {
    isWorkoutActive.value = false
    activeExercises.value = []
    routineId.value = null
    startTime.value = null
    sessionTimerStart.value = null
    sessionAccumulatedSeconds.value = 0
    sessionTimerRunning.value = false
    stopRestTimer()
    localStorage.removeItem('fitpulse_active_workout')
  }

  return {
    isWorkoutActive,
    sessionName,
    routineId,
    startTime,
    sessionDate,
    durationMinutes,
    activeExercises,
    sessionTimerRunning,
    sessionAccumulatedSeconds,
    sessionTimerStart,
    defaultRestSeconds,
    isTimerActive,
    timerTotalSeconds,
    timerRemainingSeconds,
    restTimerEndTime,
    setDefaultRestSeconds,
    setRestTimerDuration,
    startWorkout,
    addExerciseToActive,
    addSet,
    removeSet,
    removeExercise,
    toggleExerciseTimer,
    resetExerciseTimer,
    syncExerciseTimers,
    startSessionTimer,
    pauseSessionTimer,
    toggleSessionTimer,
    getSessionElapsedSeconds,
    toggleSetComplete,
    startRestTimer,
    stopRestTimer,
    addTimerSeconds,
    finishWorkout,
    cancelWorkout
  }
})
