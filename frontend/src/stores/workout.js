import { defineStore } from 'pinia'
import { ref, watch, computed } from 'vue'
import { workoutsAPI, exercisesAPI } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { sendRestNotification, playTimerChime, triggerVibration } from '@/utils/notifications'

export function normalizeExerciseName(name) {
  if (!name) return ''
  return name
    .replace(/[\(（].*?[\)）]/g, '')
    .replace(/[\s\-_·/]+/g, '')
    .trim()
    .toLowerCase()
}

/**
 * Determines whether a set in an active exercise should be counted & saved.
 * - If the user checked ✅ (is_completed) on at least one set in this exercise,
 *   ONLY the checked sets are counted/saved (ignoring unchecked pre-filled sets).
 * - Otherwise, if the user didn't check any boxes for this exercise, count sets
 *   where the user actually entered weight_kg > 0 or manually edited the set.
 */
export function isSetEffective(ex, s) {
  if (!ex || !s) return false
  const hasAnyCheckedInEx = Array.isArray(ex.sets) && ex.sets.some((st) => st.is_completed)
  if (hasAnyCheckedInEx) {
    return Boolean(s.is_completed)
  }
  return Number(s.weight_kg) > 0 || Boolean(s.user_edited && Number(s.reps) > 0)
}

const EXERCISE_ALIAS_MAP = {
  '槓鈴深蹲': '槓鈴頸後深蹲',
  '頸後深蹲': '槓鈴頸後深蹲',
  '自由深蹲': '槓鈴頸後深蹲',
  '深蹲': '槓鈴頸後深蹲',
  '機械腿推': '機械斜板腿推 (倒蹬機)',
  '斜板腿推': '機械斜板腿推 (倒蹬機)',
  '倒蹬機': '機械斜板腿推 (倒蹬機)',
  '腿推': '機械斜板腿推 (倒蹬機)',
  '坐姿腿屈伸': '坐姿機械腿屈伸 (練股四頭)',
  '機械腿屈伸': '坐姿機械腿屈伸 (練股四頭)',
  '腿屈伸': '坐姿機械腿屈伸 (練股四頭)',
  '俯臥腿彎舉': '俯臥機械腿彎舉 (練腿後側)',
  '坐姿腿彎舉': '俯臥機械腿彎舉 (練腿後側)',
  '機械腿彎舉': '俯臥機械腿彎舉 (練腿後側)',
  '腿彎舉': '俯臥機械腿彎舉 (練腿後側)',
  '站姿提踵': '站姿槓鈴提踵 (練小腿)',
  '槓鈴提踵': '站姿槓鈴提踵 (練小腿)',
  '提踵': '站姿槓鈴提踵 (練小腿)',
  '羅馬尼亞硬舉': '羅馬尼亞硬舉 (RDL)',
  'rdl': '羅馬尼亞硬舉 (RDL)',
  '傳統硬舉': '傳統槓鈴硬舉',
  '槓鈴硬舉': '傳統槓鈴硬舉',
  '分腿蹲': '保加利亞分腿蹲',
  '臀推': '槓鈴臀推 (Hip Thrust)',
  '槓鈴臀推': '槓鈴臀推 (Hip Thrust)',
  '哈克深蹲': '哈克深蹲 (Hack Squat)',
  '槓鈴臥推': '槓鈴平板臥推',
  '平板臥推': '槓鈴平板臥推',
  '啞鈴臥推': '啞鈴平板臥推',
  '繩索夾胸': '繩索夾胸 (滑輪飛鳥)',
  '滑輪飛鳥': '繩索夾胸 (滑輪飛鳥)',
  '高位下拉': '滑輪高位下拉',
  '槓鈴划船': '槓鈴俯身划船',
  '俯身划船': '槓鈴俯身划船',
  '站姿肩推': '槓鈴站姿肩推 (OHP)',
  '槓鈴肩推': '槓鈴站姿肩推 (OHP)',
  '啞鈴側平舉': '站姿啞鈴側平舉',
  '側平舉': '站姿啞鈴側平舉',
  '繩索面拉': '繩索面拉 (Face Pull)',
  '面拉': '繩索面拉 (Face Pull)'
}

export function normalizeMuscleGroupCode(rawMg, itemName = '') {
  const combined = `${rawMg || ''} ${itemName || ''}`.toUpperCase()
  const exact = (rawMg || '').trim().toUpperCase()
  if (['CHEST', 'BACK', 'LEGS', 'SHOULDERS', 'ARMS', 'CORE', 'CARDIO'].includes(exact)) {
    return exact
  }
  if (/LEG|QUAD|GLUTE|HAMSTRING|CALF|LOWER|腿|臀|股|膕|小腿|下肢|深蹲|硬舉|RDL|提踵|倒蹬/.test(combined)) return 'LEGS'
  if (/BACK|LAT|PULL|ROW|背|闊背|斜方|划船|引體|下拉/.test(combined)) return 'BACK'
  if (/SHOULDER|DELT|肩|三角肌|側平舉|面拉|後束/.test(combined)) return 'SHOULDERS'
  if (/ARM|BICEP|TRICEP|手|二頭|三頭|彎舉|下壓|臂/.test(combined)) return 'ARMS'
  if (/CORE|ABS|核|腹|棒式|捲腹/.test(combined)) return 'CORE'
  if (/CARDIO|HIIT|有氧|心肺|燃脂|跑步|飛輪|戰繩|波比/.test(combined)) return 'CARDIO'
  return 'CHEST'
}

export async function matchOrCreateExercise(itemName, targetMuscleGroup, allExercises, knownExerciseId = null) {
  const cleanName = (itemName || '').trim()
  const resolvedMg = normalizeMuscleGroupCode(targetMuscleGroup, cleanName)

  // 0. If backend already resolved and provided exercise_id, check it first
  if (knownExerciseId) {
    const byId = allExercises.find((e) => e.id === knownExerciseId)
    if (byId && (!cleanName || byId.name === cleanName || normalizeExerciseName(byId.name) === normalizeExerciseName(cleanName))) {
      return byId
    }
  }

  if (!cleanName) {
    return allExercises.find((e) => e.target_muscle_group === resolvedMg) || allExercises[0] || { id: null, name: '自訂動作', target_muscle_group: resolvedMg }
  }

  const normTarget = normalizeExerciseName(cleanName)
  const aliasCanonical = EXERCISE_ALIAS_MAP[cleanName.toLowerCase()] || EXERCISE_ALIAS_MAP[normTarget]

  // 1. Exact or alias match
  let match = allExercises.find(
    (e) => e.name.trim().toLowerCase() === cleanName.toLowerCase() || (aliasCanonical && e.name.trim() === aliasCanonical)
  )
  if (match) return match

  // 2. Normalized match (ignoring parenthetical suffixes like (RDL), (練股四頭), (OHP))
  if (normTarget) {
    match = allExercises.find((e) => normalizeExerciseName(e.name) === normTarget)
    if (match) return match

    // 3. Substring match on normalized name (at least 3 chars)
    match = allExercises.find((e) => {
      const normEx = normalizeExerciseName(e.name)
      return normEx.length >= 3 && normTarget.length >= 3 && (normEx.includes(normTarget) || normTarget.includes(normEx))
    })
    if (match) return match
  }

  // 4. Not in library -> Create custom exercise in DB so it never falls back to a wrong exercise!
  try {
    const res = await exercisesAPI.create({
      name: cleanName,
      target_muscle_group: resolvedMg,
      equipment: 'BARBELL'
    })
    const created = res.data
    allExercises.push(created)
    return created
  } catch (err) {
    return {
      id: knownExerciseId || null,
      name: cleanName,
      target_muscle_group: resolvedMg
    }
  }
}

export const useWorkoutStore = defineStore('workout', () => {
  // 1. Workout Session State (Flexible post-workout or in-gym logging)
  const ownerUserId = ref(null)
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
      ownerUserId.value = data.ownerUserId || null
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
    [ownerUserId, isWorkoutActive, sessionName, routineId, startTime, sessionDate, durationMinutes, activeExercises, sessionTimerStart, sessionAccumulatedSeconds, sessionTimerRunning],
    () => {
      if (isWorkoutActive.value) {
        localStorage.setItem(
          'fitpulse_active_workout',
          JSON.stringify({
            ownerUserId: ownerUserId.value,
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

  function syncUserOwnership(userId) {
    if (!userId) return
    if (isWorkoutActive.value && ownerUserId.value !== userId) {
      // Unsaved workout draft was created by a different account or has invalid owner -> purge it!
      cancelWorkout()
    }
    ownerUserId.value = userId
  }

  // Start new workout session
  function startWorkout(name = '今日自訂訓練', routine = null) {
    const authStore = useAuthStore()
    ownerUserId.value = authStore.user?.id || null
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
    const existingIdx = activeExercises.value.findIndex(
      (e) => e.name === exercise.name || (exercise.id && e.exercise_id === exercise.id && e.name === exercise.name)
    )
    if (existingIdx > -1) {
      addSet(existingIdx)
      return
    }

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

  // Move exercise up (-1) or down (+1) in active workout
  function moveExercise(exerciseIndex, direction) {
    const targetIdx = exerciseIndex + direction
    if (targetIdx < 0 || targetIdx >= activeExercises.value.length) return
    const temp = activeExercises.value[exerciseIndex]
    activeExercises.value[exerciseIndex] = activeExercises.value[targetIdx]
    activeExercises.value[targetIdx] = temp
  }

  // Replace an exercise in-place (when gym equipment is occupied)
  function replaceExerciseInActive(exerciseIndex, newExercise) {
    const ex = activeExercises.value[exerciseIndex]
    if (!ex || !newExercise) return
    ex.exercise_id = newExercise.id
    ex.name = newExercise.name
    ex.target_muscle_group = newExercise.target_muscle_group || ex.target_muscle_group
    ex.sets.forEach((s) => {
      s.is_completed = false
      s.user_edited = false
      s.weight_kg = 0
    })
  }

  // Cycle set type tag: NORMAL (1,2,3) -> WARMUP (W) -> DROP (D) -> FAILURE (F)
  function cycleSetType(exerciseIndex, setIndex) {
    const ex = activeExercises.value[exerciseIndex]
    const set = ex?.sets[setIndex]
    if (!set) return
    const order = ['NORMAL', 'WARMUP', 'DROP', 'FAILURE']
    const current = set.set_type || 'NORMAL'
    const next = order[(order.indexOf(current) + 1) % order.length]
    set.set_type = next
  }

  // Start workout directly from a past history session (1-click Repeat Session with actual weights & reps!)
  function startWorkoutFromHistorySession(historySession) {
    if (!historySession) return
    const authStore = useAuthStore()
    ownerUserId.value = authStore.user?.id || null
    isWorkoutActive.value = true
    sessionName.value = historySession.session_name || '歷史菜單重練'
    routineId.value = historySession.routine_id || null
    startTime.value = new Date()
    sessionDate.value = new Date().toISOString().substring(0, 10)
    durationMinutes.value = historySession.duration_minutes || 45
    activeExercises.value = []
    sessionTimerStart.value = null
    sessionAccumulatedSeconds.value = 0
    sessionTimerRunning.value = false

    const grouped = []
    const mapByKey = {}
    ;(historySession.sets || []).forEach((st) => {
      const key = `${st.exercise_id || ''}-${st.exercise_name || ''}`
      if (!mapByKey[key]) {
        mapByKey[key] = {
          exercise_id: st.exercise_id || null,
          name: st.exercise_name || '訓練動作',
          target_muscle_group: normalizeMuscleGroupCode(st.target_muscle_group, st.exercise_name),
          timerStatus: 'IDLE',
          elapsedSeconds: 0,
          startTimestamp: null,
          accumulatedSeconds: 0,
          sets: []
        }
        grouped.push(mapByKey[key])
      }
      mapByKey[key].sets.push({
        set_number: mapByKey[key].sets.length + 1,
        set_type: 'NORMAL',
        weight_kg: Number(st.weight_kg) || 0,
        reps: Number(st.reps) || 10,
        rpe: Number(st.rpe) || 8.0,
        is_completed: false,
        user_edited: true,
        prev_weight: Number(st.weight_kg) || null,
        prev_reps: Number(st.reps) || null
      })
    })

    activeExercises.value = grouped
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
      let recordedSetNum = 0
      ex.sets.forEach((s) => {
        if (isSetEffective(ex, s)) {
          recordedSetNum += 1
          totalVol += (Number(s.weight_kg) || 0) * (Number(s.reps) || 0)
          allSets.push({
            exercise_id: ex.exercise_id || null,
            exercise_name: ex.name || '自訂動作',
            target_muscle_group: ex.target_muscle_group || 'CHEST',
            set_number: recordedSetNum,
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
    ownerUserId,
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
    syncUserOwnership,
    setDefaultRestSeconds,
    setRestTimerDuration,
    startWorkout,
    startWorkoutFromHistorySession,
    addExerciseToActive,
    addSet,
    removeSet,
    removeExercise,
    moveExercise,
    replaceExerciseInActive,
    cycleSetType,
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
