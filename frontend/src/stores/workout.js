import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { workoutsAPI } from '@/api/client'

export const useWorkoutStore = defineStore('workout', () => {
  // 1. Active In-Gym Workout Session State
  const isWorkoutActive = ref(false)
  const sessionName = ref('今日自訂訓練')
  const routineId = ref(null)
  const startTime = ref(null)
  const activeExercises = ref([]) // List of { exercise_id, name, target_muscle_group, sets: [{ set_number, weight_kg, reps, rpe, is_completed, prev_weight, prev_reps }] }

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
      activeExercises.value = data.activeExercises || []
    } catch (e) {
      console.error('Failed to parse active workout cache:', e)
    }
  }

  // Save active workout to localStorage whenever it changes
  watch(
    [isWorkoutActive, sessionName, routineId, startTime, activeExercises],
    () => {
      if (isWorkoutActive.value) {
        localStorage.setItem(
          'fitpulse_active_workout',
          JSON.stringify({
            isWorkoutActive: isWorkoutActive.value,
            sessionName: sessionName.value,
            routineId: routineId.value,
            startTime: startTime.value,
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
    activeExercises.value = []

    if (routine && routine.exercises) {
      routine.exercises.forEach((re) => {
        const sets = []
        for (let i = 1; i <= re.target_sets; i++) {
          sets.push({
            set_number: i,
            weight_kg: 0,
            reps: re.target_reps || 10,
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

  // Finish Workout Session
  async function finishWorkout() {
    const allSets = []
    let totalVol = 0

    activeExercises.value.forEach((ex) => {
      ex.sets.forEach((s) => {
        if (s.is_completed) {
          totalVol += s.weight_kg * s.reps
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

    const endTime = new Date()
    const duration = startTime.value
      ? Math.max(1, Math.round((endTime - new Date(startTime.value)) / 60000))
      : 30

    const sessionPayload = {
      routine_id: routineId.value,
      session_name: sessionName.value,
      start_time: startTime.value ? new Date(startTime.value).toISOString() : new Date().toISOString(),
      end_time: endTime.toISOString(),
      duration_minutes: duration,
      sets: allSets
    }

    try {
      const res = await workoutsAPI.createSession(sessionPayload)
      // Reset state
      isWorkoutActive.value = false
      stopRestTimer()
      localStorage.removeItem('fitpulse_active_workout')
      return res.data
    } catch (err) {
      throw err
    }
  }

  function cancelWorkout() {
    isWorkoutActive.value = false
    stopRestTimer()
    localStorage.removeItem('fitpulse_active_workout')
  }

  return {
    isWorkoutActive,
    sessionName,
    routineId,
    startTime,
    activeExercises,
    isTimerActive,
    timerTotalSeconds,
    timerRemainingSeconds,
    startWorkout,
    addExerciseToActive,
    addSet,
    removeSet,
    removeExercise,
    toggleSetComplete,
    startRestTimer,
    stopRestTimer,
    addTimerSeconds,
    finishWorkout,
    cancelWorkout
  }
})
