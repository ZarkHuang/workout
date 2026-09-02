import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { workoutsAPI } from '@/api/client'

export const useWorkoutStore = defineStore('workout', () => {
  // 1. Workout Session State (Flexible post-workout or in-gym logging)
  const isWorkoutActive = ref(false)
  const sessionName = ref('今日自訂訓練')
  const routineId = ref(null)
  const startTime = ref(null)
  const sessionDate = ref(new Date().toISOString().substring(0, 10))
  const durationMinutes = ref(45)
  const activeExercises = ref([]) // List of { exercise_id, name, target_muscle_group, timerStatus: 'IDLE'|'RUNNING'|'PAUSED', elapsedSeconds: 0, sets: [{ set_number, weight_kg, reps, rpe, is_completed, prev_weight, prev_reps }] }

  // 2. Rest Timer State
  const isTimerActive = ref(false)
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
    } catch (e) {
      console.error('Failed to parse active workout cache:', e)
    }
  }

  // Save active workout to localStorage whenever it changes
  watch(
    [isWorkoutActive, sessionName, routineId, startTime, sessionDate, durationMinutes, activeExercises],
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
            activeExercises: activeExercises.value
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
    // Re-index sets
    ex.sets.forEach((s, idx) => {
      s.set_number = idx + 1
    })
  }

  function removeExercise(exerciseIndex) {
    activeExercises.value.splice(exerciseIndex, 1)
  }

  // Toggle exercise-specific timer (Start / Pause / Resume)
  function toggleExerciseTimer(exerciseIndex) {
    const ex = activeExercises.value[exerciseIndex]
    if (!ex) return
    if (ex.timerStatus === 'RUNNING') {
      ex.timerStatus = 'PAUSED'
    } else {
      ex.timerStatus = 'RUNNING'
    }
  }

  function resetExerciseTimer(exerciseIndex) {
    const ex = activeExercises.value[exerciseIndex]
    if (!ex) return
    ex.timerStatus = 'IDLE'
    ex.elapsedSeconds = 0
  }

  // Toggle set completion and trigger rest timer
  function toggleSetComplete(exerciseIndex, setIndex, defaultRestSeconds = 90) {
    const set = activeExercises.value[exerciseIndex]?.sets[setIndex]
    if (!set) return
    set.is_completed = !set.is_completed
    if (set.is_completed) {
      startRestTimer(defaultRestSeconds)
    }
  }

  // Rest Timer Controls with Web Audio synthesis & Vibration
  function playBeepSound() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext
      if (!AudioCtx) return
      const ctx = new AudioCtx()
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = 'sine'
      osc.frequency.setValueAtTime(880, ctx.currentTime) // A5 note
      gain.gain.setValueAtTime(0.3, ctx.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5)
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.start()
      osc.stop(ctx.currentTime + 0.5)
    } catch (e) {
      console.log('Audio alert not supported or blocked by user gesture:', e)
    }
  }

  function triggerVibration() {
    if ('vibrate' in navigator) {
      navigator.vibrate([200, 100, 200])
    }
  }

  function startRestTimer(seconds = 90) {
    clearInterval(timerInterval)
    timerTotalSeconds.value = seconds
    timerRemainingSeconds.value = seconds
    isTimerActive.value = true

    timerInterval = setInterval(() => {
      if (timerRemainingSeconds.value > 0) {
        timerRemainingSeconds.value--
      } else {
        clearInterval(timerInterval)
        isTimerActive.value = false
        playBeepSound()
        triggerVibration()
      }
    }, 1000)
  }

  function stopRestTimer() {
    clearInterval(timerInterval)
    isTimerActive.value = false
  }

  function addTimerSeconds(seconds = 30) {
    timerRemainingSeconds.value += seconds
    timerTotalSeconds.value += seconds
  }

  // Finish and submit workout session to backend
  async function finishWorkout(customDuration = null, customDateStr = null) {
    const allSets = []
    let totalVol = 0

    activeExercises.value.forEach((ex) => {
      ex.sets.forEach((s) => {
        // If weight > 0 or reps > 0 or marked completed, we include it
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

    const targetDate = customDateStr ? new Date(customDateStr) : (startTime.value ? new Date(startTime.value) : new Date())
    const duration = customDuration !== null ? Number(customDuration) : (durationMinutes.value || 45)

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
      sessionName.value = '今日自訂訓練'
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
    sessionName.value = '今日自訂訓練'
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
    isTimerActive,
    timerTotalSeconds,
    timerRemainingSeconds,
    startWorkout,
    addExerciseToActive,
    addSet,
    removeSet,
    removeExercise,
    toggleExerciseTimer,
    resetExerciseTimer,
    toggleSetComplete,
    startRestTimer,
    stopRestTimer,
    addTimerSeconds,
    finishWorkout,
    cancelWorkout
  }
})
