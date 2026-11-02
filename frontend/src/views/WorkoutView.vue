<template>
  <div class="pb-24 pt-4 px-4 max-w-lg mx-auto space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-black text-slate-900">訓練中樞</h1>
        <p class="text-xs text-slate-400">課表管理、黃金動作庫與歷史日誌</p>
      </div>
      <button
        @click="startBlankWorkout"
        class="py-2 px-3.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white text-xs font-black shadow-md shadow-brand-500/20 active:scale-95 transition-all flex items-center gap-1.5"
      >
        <Plus class="w-4 h-4" />
        <span>記錄今日訓練</span>
      </button>
    </div>

    <!-- Active Draft Banner (if active) -->
    <div
      v-if="workoutStore.activeExercises.length > 0"
      @click="$router.push('/active-workout')"
      class="p-3.5 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-700 text-white flex items-center justify-between cursor-pointer active:scale-[0.98] transition-all shadow-float"
    >
      <div class="flex items-center gap-2.5 flex-1 min-w-0 pr-2">
        <Flame class="w-5 h-5 text-white flex-shrink-0" />
        <span class="text-xs font-bold truncate">{{ workoutStore.sessionName }} ({{ workoutStore.activeExercises.length }} 個動作)</span>
      </div>
      <span class="text-xs font-black bg-white/25 hover:bg-white/35 px-3 py-1.5 rounded-xl whitespace-nowrap flex-shrink-0 shadow-2xs">
        繼續填寫
      </span>
    </div>

    <!-- Navigation Tabs -->
    <div class="flex bg-slate-200/70 p-1 rounded-xl">
      <button
        @click="activeTab = 'routines'"
        class="flex-1 py-1.5 text-xs font-bold rounded-lg transition-all"
        :class="activeTab === 'routines' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'"
      >
        我的課表
      </button>
      <button
        @click="activeTab = 'library'"
        class="flex-1 py-1.5 text-xs font-bold rounded-lg transition-all"
        :class="activeTab === 'library' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'"
      >
        黃金動作庫
      </button>
      <button
        @click="activeTab = 'history'"
        class="flex-1 py-1.5 text-xs font-bold rounded-lg transition-all"
        :class="activeTab === 'history' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'"
      >
        歷史日誌
      </button>
    </div>

    <!-- TAB 1: Routines -->
    <div v-if="activeTab === 'routines'" class="space-y-3">
      <div class="flex items-center justify-between">
        <span class="text-xs font-bold text-slate-500">已儲存課表 ({{ routines.length }})</span>
        <button
          @click="openCreateRoutineModal"
          class="text-xs font-bold text-brand-600 hover:text-brand-700 flex items-center gap-1"
        >
          <Plus class="w-3.5 h-3.5" />
          <span>建立自訂課表</span>
        </button>
      </div>

      <div v-if="routines.length === 0" class="card-apple text-center py-8">
        <Dumbbell class="w-8 h-8 text-slate-300 mx-auto mb-2" />
        <div class="text-xs font-bold text-slate-700 mb-1">尚未建立任何課表</div>
        <div class="text-[11px] text-slate-400 mb-3">可以自訂推拉腿或全身體態課表！</div>
        <button
          @click="openCreateRoutineModal"
          class="py-2 px-4 rounded-xl bg-brand-50 text-brand-700 font-bold text-xs border border-brand-200"
        >
          立即建立第一套課表
        </button>
      </div>

      <div
        v-for="r in routines"
        :key="r.id"
        class="card-apple space-y-3"
      >
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center gap-2">
              <h3 class="text-sm font-bold text-slate-900">{{ r.title }}</h3>
              <span class="badge-emerald text-[10px]">{{ r.target_split }}</span>
            </div>
            <p v-if="r.description" class="text-xs text-slate-500 mt-0.5">{{ r.description }}</p>
          </div>
          <div class="flex items-center gap-1">
            <button
              @click="openEditRoutineModal(r)"
              class="text-slate-400 hover:text-brand-600 p-1 rounded-lg hover:bg-slate-100 text-xs font-bold"
              title="編輯課表"
            >
              編輯
            </button>
            <button
              @click="deleteRoutine(r.id)"
              class="text-slate-300 hover:text-rose-500 p-1"
              title="刪除課表"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Exercise preview list -->
        <div class="space-y-1.5 pt-1">
          <div
            v-for="(re, idx) in r.exercises"
            :key="re.id"
            class="text-xs text-slate-600 flex items-center justify-between bg-slate-50 px-2.5 py-1.5 rounded-lg"
          >
            <span>{{ idx + 1 }}. {{ re.exercise?.name || '動作' }}</span>
            <span class="text-[10px] font-bold text-slate-400">{{ re.target_sets }} 組 × {{ re.target_reps }} 次</span>
          </div>
        </div>

        <button
          @click="startRoutine(r)"
          class="w-full py-2.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-bold text-xs shadow-sm active:scale-95 transition-all flex items-center justify-center gap-1.5"
        >
          <Play class="w-3.5 h-3.5" />
          <span>開始此課表訓練</span>
        </button>
      </div>
    </div>

    <!-- TAB 2: Exercise Library -->
    <div v-if="activeTab === 'library'" class="space-y-3">
      <!-- Search & Filters -->
      <div class="space-y-2">
        <div class="flex items-center gap-2">
          <div class="relative flex-1">
            <Search class="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜尋動作名稱（例如：臥推、深蹲）..."
              class="w-full pl-9 pr-4 py-2 bg-white rounded-xl border border-slate-200 text-xs focus:outline-none focus:border-brand-500"
            />
          </div>
          <button
            @click="openCreateCustomExerciseModal"
            class="py-2 px-3 rounded-xl bg-brand-50 text-brand-700 border border-brand-200 font-bold text-xs whitespace-nowrap hover:bg-brand-100 active:scale-95 flex items-center gap-1"
          >
            <Plus class="w-3.5 h-3.5" />
            <span>自訂動作</span>
          </button>
        </div>

        <!-- Muscle filter pills -->
        <div class="flex gap-1.5 overflow-x-auto pb-1 no-scrollbar">
          <button
            v-for="f in muscleFilters"
            :key="f.key"
            @click="selectedMuscleFilter = f.key"
            class="px-3 py-1 rounded-full text-xs font-bold whitespace-nowrap transition-all"
            :class="selectedMuscleFilter === f.key ? 'bg-slate-900 text-white shadow-sm' : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'"
          >
            {{ f.label }}
          </button>
        </div>
      </div>

      <!-- Exercise Items -->
      <div class="space-y-2">
        <div
          v-for="ex in filteredExercises"
          :key="ex.id"
          class="card-apple space-y-2"
        >
          <div class="flex items-start justify-between">
            <div>
              <div class="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                {{ ex.name }}
                <span v-if="ex.name_en" class="text-[10px] font-normal text-slate-400">({{ ex.name_en }})</span>
              </div>
              <div class="flex items-center gap-1.5 mt-1">
                <span class="badge-emerald text-[10px]">{{ ex.target_muscle_group }}</span>
                <span class="badge-gray text-[10px]">{{ ex.equipment }}</span>
                <span v-if="ex.is_custom" class="text-[10px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 font-bold">自訂</span>
              </div>
            </div>
            <div class="flex items-center gap-1.5">
              <button
                v-if="ex.is_custom"
                @click="deleteCustomExercise(ex.id)"
                class="text-slate-300 hover:text-rose-500 p-1"
                title="刪除自訂動作"
              >
                <Trash2 class="w-3.5 h-3.5" />
              </button>
              <button
                v-if="workoutStore.isWorkoutActive"
                @click="addExerciseToActive(ex)"
                class="px-2.5 py-1 rounded-lg bg-brand-50 text-brand-700 font-bold text-xs hover:bg-brand-100 active:scale-95"
              >
                + 加入訓練
              </button>
            </div>
          </div>
          <p v-if="ex.instructions" class="text-[11px] text-slate-500 bg-slate-50 p-2 rounded-lg leading-relaxed">
            💡 {{ ex.instructions }}
          </p>
        </div>
      </div>
    </div>

    <!-- TAB 3: History Logs & Weekly Comparison -->
    <div v-if="activeTab === 'history'" class="space-y-3.5">
      <!-- Weekly Comparison Highlight Banner -->
      <div v-if="weeklyStats" class="card-apple bg-gradient-to-br from-slate-900 to-slate-800 text-white border-0 shadow-lg p-4 space-y-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-sm font-black text-white">📊 本週 vs 上週訓練對比</span>
          </div>
          <span
            class="text-[10px] font-black px-2 py-0.5 rounded-full"
            :class="weeklyStats.volume_change_pct >= 0 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'"
          >
            容量 {{ weeklyStats.volume_change_pct >= 0 ? `+${weeklyStats.volume_change_pct}% 🔥` : `${weeklyStats.volume_change_pct}% 📉` }}
          </span>
        </div>

        <div class="grid grid-cols-2 gap-2 pt-1">
          <div class="bg-white/10 rounded-xl p-2.5">
            <div class="text-[10px] text-slate-400 font-medium">本週 ({{ weeklyStats.this_week.start_date }} 起)</div>
            <div class="text-base font-black text-emerald-400 mt-0.5">
              {{ weeklyStats.this_week.volume_kg.toLocaleString() }} <span class="text-[10px] font-normal text-slate-400">kg</span>
            </div>
            <div class="text-[10px] text-slate-300 mt-0.5">
              練 {{ weeklyStats.this_week.sessions_count }} 天 · {{ weeklyStats.this_week.duration_minutes }} 分鐘
            </div>
          </div>

          <div class="bg-white/10 rounded-xl p-2.5">
            <div class="text-[10px] text-slate-400 font-medium">上週 ({{ weeklyStats.last_week.start_date }} 起)</div>
            <div class="text-base font-black text-slate-300 mt-0.5">
              {{ weeklyStats.last_week.volume_kg.toLocaleString() }} <span class="text-[10px] font-normal text-slate-400">kg</span>
            </div>
            <div class="text-[10px] text-slate-300 mt-0.5">
              練 {{ weeklyStats.last_week.sessions_count }} 天 · {{ weeklyStats.last_week.duration_minutes }} 分鐘
            </div>
          </div>
        </div>
      </div>

      <div v-if="historySessions.length === 0" class="card-apple text-center py-8 text-slate-400 text-xs">
        尚無訓練歷史紀錄，點擊上方按鈕開始第一堂訓練！
      </div>

      <div
        v-for="s in historySessions"
        :key="s.id"
        class="card-apple space-y-2.5"
      >
        <div class="flex items-start justify-between">
          <div>
            <h3 class="text-xs font-bold text-slate-900">{{ s.session_name }}</h3>
            <div class="text-[10px] text-slate-400">{{ formatFullDate(s.created_at) }} · {{ s.duration_minutes }} 分鐘</div>
          </div>
          <div class="flex items-center gap-2">
            <div class="text-right">
              <div class="text-xs font-black text-brand-700">總容量 {{ s.total_volume_kg }} kg</div>
              <div class="text-[10px] text-slate-400">{{ s.sets?.length || 0 }} 組動作</div>
            </div>
            <button
              @click="openEditSessionModal(s)"
              class="text-slate-400 hover:text-brand-600 p-1 rounded-lg hover:bg-slate-100 text-xs font-bold"
              title="編輯此筆日誌"
            >
              編輯
            </button>
            <button
              @click="handleDeleteSession(s.id)"
              class="text-slate-300 hover:text-rose-500 p-1 rounded-lg hover:bg-rose-50 transition-colors"
              title="刪除此筆日誌"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Sets breakdown -->
        <div class="bg-slate-50 rounded-xl p-2.5 space-y-1.5">
          <div
            v-for="(st, idx) in s.sets"
            :key="st.id"
            class="text-[11px] text-slate-700 flex items-center justify-between border-b border-slate-200/50 pb-1 last:border-0 last:pb-0"
          >
            <span>{{ st.exercise_name }} (第 {{ st.set_number }} 組)</span>
            <span class="font-bold text-slate-900">
              {{ st.weight_kg }}kg × {{ st.reps }}次
              <span v-if="st.estimated_1rm" class="text-[10px] text-brand-600 font-semibold ml-1">(1RM: {{ st.estimated_1rm }}kg)</span>
            </span>
          </div>
        </div>

        <!-- Quick Actions: Repeat Session or Save as Routine -->
        <div class="flex items-center gap-2 pt-1">
          <button
            @click="repeatHistorySession(s)"
            class="flex-1 py-2 px-3 rounded-xl bg-brand-50 hover:bg-brand-100 text-brand-700 font-bold text-xs border border-brand-200/70 active:scale-95 transition-all flex items-center justify-center gap-1"
          >
            <Play class="w-3.5 h-3.5" />
            <span>🔄 再練一次此菜單 (帶入當時重量)</span>
          </button>
          <button
            @click="saveHistorySessionAsRoutine(s)"
            class="py-2 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs active:scale-95 transition-all whitespace-nowrap"
          >
            📌 存為課表
          </button>
        </div>
      </div>

      <!-- 90-Day Rolling Cleanup Banner -->
      <div class="p-3 rounded-2xl bg-slate-100/80 border border-slate-200/60 flex items-center justify-between mt-2">
        <div class="text-[11px] text-slate-500">
          <span class="font-bold text-slate-700">90 天滾動歸檔：</span>
          保留近 3 個月完整組數，1RM 永久保留。
        </div>
        <button
          @click="handle90dCleanup"
          class="px-2.5 py-1 rounded-lg bg-white hover:bg-slate-200 text-slate-700 text-[10px] font-bold border border-slate-200 shadow-2xs active:scale-95 whitespace-nowrap"
        >
          清理舊日誌
        </button>
      </div>
    </div>

    <!-- Create / Edit Routine Modal -->
    <div
      v-if="showCreateRoutineModal"
      class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4"
    >
      <div class="bg-white w-full max-w-lg rounded-t-3xl sm:rounded-3xl p-5 max-h-[85vh] overflow-y-auto space-y-4 shadow-2xl">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <h3 class="font-black text-slate-900 text-base">{{ editingRoutineId ? '編輯課表' : '建立新課表' }}</h3>
          <button @click="showCreateRoutineModal = false" class="p-1 rounded-full text-slate-400 hover:bg-slate-100">
            <X class="w-5 h-5" />
          </button>
        </div>

        <div class="space-y-3">
          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">課表名稱</label>
            <input
              v-model="newRoutineTitle"
              type="text"
              placeholder="例如：週一推胸課表 / PPL-Push"
              class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">分化類型</label>
            <select
              v-model="newRoutineSplit"
              class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-brand-500"
            >
              <option value="PUSH">推日 (PUSH - 胸/肩/三頭)</option>
              <option value="PULL">拉日 (PULL - 背/二頭)</option>
              <option value="LEGS">腿日 (LEGS - 腿/臀/小腿)</option>
              <option value="CHEST">胸部專攻 (CHEST)</option>
              <option value="BACK">背部專攻 (BACK)</option>
              <option value="SHOULDERS">肩部專攻 (SHOULDERS)</option>
              <option value="CARDIO">有氧日 (CARDIO - 心肺/HIIT/燃脂)</option>
              <option value="UPPER">上半身 (UPPER)</option>
              <option value="LOWER">下半身 (LOWER)</option>
              <option value="FULL_BODY">全身綜合 (FULL BODY)</option>
            </select>
          </div>

          <!-- Select Exercises for routine (with Search & Muscle Filter) -->
          <div class="space-y-2">
            <label class="block text-xs font-bold text-slate-700">選擇包含動作 (已選 {{ selectedRoutineExercises.length }} 個)</label>
            <input
              v-model="routineExerciseSearch"
              type="text"
              placeholder="🔍 搜尋動作名稱（如：深蹲、臥推、下拉）..."
              class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-brand-500"
            />
            <div class="flex gap-1 overflow-x-auto pb-1 no-scrollbar">
              <button
                v-for="f in muscleFilters"
                :key="f.key"
                type="button"
                @click="routineMuscleFilter = f.key"
                class="px-2.5 py-1 rounded-full text-[11px] font-bold whitespace-nowrap transition-all"
                :class="routineMuscleFilter === f.key ? 'bg-slate-900 text-white shadow-xs' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
              >
                {{ f.label }}
              </button>
            </div>
            <div class="max-h-48 overflow-y-auto space-y-1.5 border border-slate-200 rounded-xl p-2 bg-slate-50">
              <div
                v-for="ex in filteredRoutinePickerExercises"
                :key="ex.id"
                @click="toggleExerciseForRoutine(ex)"
                class="p-2 rounded-lg text-xs cursor-pointer flex items-center justify-between transition-colors"
                :class="isExerciseInNewRoutine(ex.id) ? 'bg-brand-500 text-white font-bold' : 'bg-white text-slate-700 hover:bg-slate-100'"
              >
                <span>{{ ex.name }}</span>
                <span class="text-[10px]" :class="isExerciseInNewRoutine(ex.id) ? 'text-white' : 'text-slate-400'">{{ ex.target_muscle_group }}</span>
              </div>
            </div>
          </div>

          <!-- Configure sets, reps & order for selected exercises -->
          <div v-if="selectedRoutineExercises.length > 0" class="space-y-1.5">
            <label class="block text-xs font-bold text-slate-700">設定目標組數、次數與順序</label>
            <div
              v-for="(reItem, idx) in selectedRoutineExercises"
              :key="reItem.exercise_id"
              class="flex items-center justify-between bg-slate-50 p-2 rounded-xl border border-slate-200 text-xs gap-1.5"
            >
              <span class="font-bold text-slate-800 truncate flex-1">{{ idx + 1 }}. {{ reItem.exercise_name }}</span>
              <div class="flex items-center gap-1">
                <button
                  v-if="idx > 0"
                  type="button"
                  @click="moveRoutineExercise(idx, -1)"
                  class="px-1.5 py-0.5 rounded bg-white border border-slate-200 text-slate-500 hover:text-slate-800 text-[10px] font-bold"
                  title="上移"
                >
                  ↑
                </button>
                <button
                  v-if="idx < selectedRoutineExercises.length - 1"
                  type="button"
                  @click="moveRoutineExercise(idx, 1)"
                  class="px-1.5 py-0.5 rounded bg-white border border-slate-200 text-slate-500 hover:text-slate-800 text-[10px] font-bold"
                  title="下移"
                >
                  ↓
                </button>
                <input
                  v-model.number="reItem.target_sets"
                  type="number"
                  min="1"
                  class="w-11 text-center py-1 bg-white border border-slate-200 rounded-lg text-xs font-bold"
                />
                <span class="text-[10px] text-slate-500">組×</span>
                <input
                  v-model.number="reItem.target_reps"
                  type="number"
                  min="1"
                  class="w-11 text-center py-1 bg-white border border-slate-200 rounded-lg text-xs font-bold"
                />
                <span class="text-[10px] text-slate-500">次</span>
              </div>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2 pt-2">
          <button
            @click="submitCreateRoutine"
            class="flex-1 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white text-xs font-extrabold shadow-sm active:scale-95"
          >
            {{ editingRoutineId ? '儲存課表修改' : '確定儲存課表' }}
          </button>
          <button
            @click="showCreateRoutineModal = false"
            class="py-2.5 px-4 rounded-xl bg-slate-100 text-slate-600 text-xs font-bold hover:bg-slate-200 active:scale-95"
          >
            取消
          </button>
        </div>
      </div>
    </div>

    <!-- Create Custom Exercise Modal -->
    <div
      v-if="showCustomExerciseModal"
      class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4"
    >
      <div class="bg-white w-full max-w-lg rounded-t-3xl sm:rounded-3xl p-5 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <h3 class="font-black text-slate-900 text-base">新增自訂訓練動作</h3>
          <button @click="showCustomExerciseModal = false" class="p-1 rounded-full text-slate-400 hover:bg-slate-100">
            <X class="w-5 h-5" />
          </button>
        </div>

        <div class="space-y-3">
          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">動作名稱</label>
            <input
              v-model="customExForm.name"
              type="text"
              placeholder="例如：史密斯分腿蹲、單臂滑輪側平舉"
              class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-brand-500"
            />
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-1">目標肌群</label>
              <select
                v-model="customExForm.target_muscle_group"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs"
              >
                <option value="CHEST">胸部 (CHEST)</option>
                <option value="BACK">背部 (BACK)</option>
                <option value="LEGS">腿部 (LEGS)</option>
                <option value="SHOULDERS">肩部 (SHOULDERS)</option>
                <option value="ARMS">手臂 (ARMS)</option>
                <option value="CORE">核心 (CORE)</option>
                <option value="CARDIO">有氧 (CARDIO)</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-1">器材類型</label>
              <select
                v-model="customExForm.equipment"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs"
              >
                <option value="BARBELL">槓鈴 (BARBELL)</option>
                <option value="DUMBBELL">啞鈴 (DUMBBELL)</option>
                <option value="MACHINE">固定器械 (MACHINE)</option>
                <option value="CABLE">滑輪繩索 (CABLE)</option>
                <option value="BODYWEIGHT">自重 (BODYWEIGHT)</option>
              </select>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2 pt-2">
          <button
            @click="submitCustomExercise"
            class="flex-1 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white text-xs font-extrabold shadow-sm active:scale-95"
          >
            儲存自訂動作
          </button>
          <button
            @click="showCustomExerciseModal = false"
            class="py-2.5 px-4 rounded-xl bg-slate-100 text-slate-600 text-xs font-bold hover:bg-slate-200 active:scale-95"
          >
            取消
          </button>
        </div>
      </div>
    </div>

    <!-- Edit Session History Modal -->
    <div
      v-if="showEditSessionModal && editingSession"
      class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4"
    >
      <div class="bg-white w-full max-w-lg rounded-t-3xl sm:rounded-3xl p-5 max-h-[85vh] overflow-y-auto space-y-4 shadow-2xl">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <h3 class="font-black text-slate-900 text-base">編輯訓練歷史紀錄</h3>
          <button @click="showEditSessionModal = false" class="p-1 rounded-full text-slate-400 hover:bg-slate-100">
            <X class="w-5 h-5" />
          </button>
        </div>

        <div class="space-y-3">
          <div class="grid grid-cols-3 gap-2">
            <div class="col-span-2">
              <label class="block text-xs font-bold text-slate-700 mb-1">訓練名稱</label>
              <input
                v-model="editingSession.session_name"
                type="text"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold"
              />
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-1">時長 (分鐘)</label>
              <input
                v-model.number="editingSession.duration_minutes"
                type="number"
                min="1"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-center"
              />
            </div>
          </div>

          <div class="space-y-2 max-h-60 overflow-y-auto bg-slate-50 p-2.5 rounded-2xl border border-slate-200">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-700">動作與組數明細 ({{ editingSession.sets.length }} 組)</span>
              <button
                @click="addSetToEditingSession"
                class="text-[11px] font-bold text-brand-600 hover:text-brand-700"
              >
                + 新增一組
              </button>
            </div>
            <div
              v-for="(st, idx) in editingSession.sets"
              :key="idx"
              class="grid grid-cols-12 gap-1.5 items-center bg-white p-2 rounded-xl border border-slate-100 text-xs"
            >
              <div class="col-span-5">
                <select
                  v-model="st.exercise_id"
                  @change="onEditSetExerciseChange(st)"
                  class="w-full py-1 px-1.5 bg-slate-50 border border-slate-200 rounded-lg text-[11px] font-bold"
                >
                  <option v-for="ex in allExercises" :key="ex.id" :value="ex.id">{{ ex.name }}</option>
                </select>
              </div>
              <div class="col-span-3 flex items-center gap-0.5">
                <input
                  v-model.number="st.weight_kg"
                  type="number"
                  step="0.5"
                  class="w-full text-center py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs font-bold"
                />
                <span class="text-[10px] text-slate-400">kg</span>
              </div>
              <div class="col-span-3 flex items-center gap-0.5">
                <input
                  v-model.number="st.reps"
                  type="number"
                  class="w-full text-center py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs font-bold"
                />
                <span class="text-[10px] text-slate-400">次</span>
              </div>
              <div class="col-span-1 flex justify-end">
                <button
                  v-if="editingSession.sets.length > 1"
                  @click="editingSession.sets.splice(idx, 1)"
                  class="text-slate-300 hover:text-rose-500"
                >
                  <X class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2 pt-2">
          <button
            @click="submitEditSession"
            class="flex-1 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white text-xs font-extrabold shadow-sm active:scale-95"
          >
            儲存紀錄修改
          </button>
          <button
            @click="showEditSessionModal = false"
            class="py-2.5 px-4 rounded-xl bg-slate-100 text-slate-600 text-xs font-bold hover:bg-slate-200 active:scale-95"
          >
            取消
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  Plus, Dumbbell, Flame, Play, Trash2, Search, X
} from 'lucide-vue-next'
import { useWorkoutStore } from '@/stores/workout'
import { workoutsAPI, exercisesAPI } from '@/api/client'

const router = useRouter()
const route = useRoute()
const workoutStore = useWorkoutStore()

const activeTab = ref(route.query.tab === 'history' ? 'history' : (route.query.tab === 'library' ? 'library' : 'routines'))
const routines = ref([])
const allExercises = ref([])
const historySessions = ref([])
const weeklyStats = ref(null)

const searchQuery = ref('')
const selectedMuscleFilter = ref('ALL')

const showCreateRoutineModal = ref(false)
const editingRoutineId = ref(null)
const newRoutineTitle = ref('')
const newRoutineSplit = ref('PUSH')
const selectedRoutineExercises = ref([])
const routineExerciseSearch = ref('')
const routineMuscleFilter = ref('ALL')

const showCustomExerciseModal = ref(false)
const customExForm = reactive({
  name: '',
  target_muscle_group: 'CHEST',
  equipment: 'BARBELL'
})

const showEditSessionModal = ref(false)
const editingSession = ref(null)

const muscleFilters = [
  { key: 'ALL', label: '全部' },
  { key: 'CHEST', label: '胸部' },
  { key: 'BACK', label: '背部' },
  { key: 'LEGS', label: '腿部' },
  { key: 'SHOULDERS', label: '肩部' },
  { key: 'ARMS', label: '手臂' },
  { key: 'CORE', label: '核心' },
  { key: 'CARDIO', label: '有氧' }
]

const filteredExercises = computed(() => {
  return allExercises.value.filter(e => {
    const matchMuscle = selectedMuscleFilter.value === 'ALL' || e.target_muscle_group === selectedMuscleFilter.value
    const matchQuery = !searchQuery.value || e.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || (e.name_en && e.name_en.toLowerCase().includes(searchQuery.value.toLowerCase()))
    return matchMuscle && matchQuery
  })
})

const filteredRoutinePickerExercises = computed(() => {
  return allExercises.value.filter(e => {
    const matchMuscle = routineMuscleFilter.value === 'ALL' || e.target_muscle_group === routineMuscleFilter.value
    const matchQuery = !routineExerciseSearch.value || e.name.toLowerCase().includes(routineExerciseSearch.value.toLowerCase()) || (e.name_en && e.name_en.toLowerCase().includes(routineExerciseSearch.value.toLowerCase()))
    return matchMuscle && matchQuery
  })
})

function formatFullDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

async function fetchRoutines() {
  try {
    const res = await workoutsAPI.getRoutines()
    routines.value = res.data
  } catch (err) {
    console.error('Failed to fetch routines:', err)
  }
}

async function fetchExercises() {
  try {
    const res = await exercisesAPI.list()
    allExercises.value = res.data
  } catch (err) {
    console.error('Failed to fetch exercises:', err)
  }
}

async function fetchHistory() {
  try {
    const res = await workoutsAPI.getSessions({ limit: 100 })
    historySessions.value = res.data
  } catch (err) {
    console.error('Failed to fetch history:', err)
  }
}

function openCreateRoutineModal() {
  editingRoutineId.value = null
  newRoutineTitle.value = ''
  newRoutineSplit.value = 'PUSH'
  selectedRoutineExercises.value = []
  routineExerciseSearch.value = ''
  routineMuscleFilter.value = 'ALL'
  showCreateRoutineModal.value = true
}

function openEditRoutineModal(routine) {
  editingRoutineId.value = routine.id
  newRoutineTitle.value = routine.title
  newRoutineSplit.value = routine.target_split || 'PUSH'
  routineExerciseSearch.value = ''
  routineMuscleFilter.value = 'ALL'
  selectedRoutineExercises.value = (routine.exercises || []).map(re => ({
    exercise_id: re.exercise_id,
    exercise_name: re.exercise?.name || '動作',
    target_sets: re.target_sets || 3,
    target_reps: re.target_reps || 10
  }))
  showCreateRoutineModal.value = true
}

function moveRoutineExercise(idx, dir) {
  const target = idx + dir
  if (target < 0 || target >= selectedRoutineExercises.value.length) return
  const tmp = selectedRoutineExercises.value[idx]
  selectedRoutineExercises.value[idx] = selectedRoutineExercises.value[target]
  selectedRoutineExercises.value[target] = tmp
}

function repeatHistorySession(session) {
  workoutStore.startWorkoutFromHistorySession(session)
  router.push('/active-workout')
}

async function saveHistorySessionAsRoutine(session) {
  if (!session || !session.sets || session.sets.length === 0) return
  const grouped = []
  const mapById = {}
  session.sets.forEach(st => {
    const key = `${st.exercise_id}-${st.exercise_name}`
    if (!mapById[key]) {
      mapById[key] = {
        exercise_id: st.exercise_id,
        exercise_name: st.exercise_name,
        target_sets: 0,
        target_reps: Number(st.reps) || 10
      }
      grouped.push(mapById[key])
    }
    mapById[key].target_sets += 1
    if ((Number(st.reps) || 0) > mapById[key].target_reps) {
      mapById[key].target_reps = Number(st.reps)
    }
  })

  try {
    await workoutsAPI.createRoutine({
      title: `${session.session_name} (歷史轉存)`,
      target_split: 'FULL_BODY',
      description: `由 ${formatFullDate(session.created_at)} 訓練紀錄轉存`,
      exercises: grouped
    })
    await fetchRoutines()
    alert('🎉 已將該次訓練菜單存為「我的課表」！')
  } catch (err) {
    alert('轉存課表失敗，請稍後重試')
  }
}

function openCreateCustomExerciseModal() {
  customExForm.name = ''
  customExForm.target_muscle_group = selectedMuscleFilter.value === 'ALL' ? 'CHEST' : selectedMuscleFilter.value
  customExForm.equipment = 'BARBELL'
  showCustomExerciseModal.value = true
}

async function submitCustomExercise() {
  if (!customExForm.name.trim()) {
    alert('請輸入動作名稱')
    return
  }
  try {
    await exercisesAPI.create({
      name: customExForm.name.trim(),
      target_muscle_group: customExForm.target_muscle_group,
      equipment: customExForm.equipment
    })
    showCustomExerciseModal.value = false
    await fetchExercises()
  } catch (err) {
    alert('新增自訂動作失敗')
  }
}

async function deleteCustomExercise(id) {
  if (!confirm('確定要刪除此自訂動作嗎？')) return
  try {
    await exercisesAPI.delete(id)
    await fetchExercises()
  } catch (err) {
    alert('刪除失敗')
  }
}

function openEditSessionModal(session) {
  editingSession.value = {
    id: session.id,
    routine_id: session.routine_id,
    session_name: session.session_name,
    duration_minutes: session.duration_minutes,
    start_time: session.start_time,
    end_time: session.end_time,
    sets: (session.sets || []).map(st => ({
      exercise_id: st.exercise_id,
      exercise_name: st.exercise_name,
      set_number: st.set_number,
      weight_kg: st.weight_kg,
      reps: st.reps,
      rpe: st.rpe || 8.0,
      is_completed: true
    }))
  }
  showEditSessionModal.value = true
}

function onEditSetExerciseChange(st) {
  const found = allExercises.value.find(e => e.id === st.exercise_id)
  if (found) {
    st.exercise_name = found.name
  }
}

function addSetToEditingSession() {
  if (!editingSession.value) return
  const last = editingSession.value.sets[editingSession.value.sets.length - 1]
  const defaultEx = allExercises.value[0]
  editingSession.value.sets.push({
    exercise_id: last ? last.exercise_id : (defaultEx?.id || 1),
    exercise_name: last ? last.exercise_name : (defaultEx?.name || '動作'),
    set_number: editingSession.value.sets.length + 1,
    weight_kg: last ? last.weight_kg : 20,
    reps: last ? last.reps : 10,
    rpe: 8.0,
    is_completed: true
  })
}

async function submitEditSession() {
  if (!editingSession.value) return
  try {
    // Recalculate per-exercise set_number sequence
    const counts = {}
    const payloadSets = editingSession.value.sets.map(st => {
      const exId = st.exercise_id
      counts[exId] = (counts[exId] || 0) + 1
      const found = allExercises.value.find(e => e.id === exId)
      return {
        exercise_id: exId,
        exercise_name: found ? found.name : st.exercise_name,
        set_number: counts[exId],
        weight_kg: Number(st.weight_kg) || 0,
        reps: Number(st.reps) || 0,
        rpe: Number(st.rpe) || 8.0,
        is_completed: true
      }
    })

    await workoutsAPI.updateSession(editingSession.value.id, {
      routine_id: editingSession.value.routine_id,
      session_name: editingSession.value.session_name,
      start_time: editingSession.value.start_time,
      end_time: editingSession.value.end_time,
      duration_minutes: Number(editingSession.value.duration_minutes) || 45,
      sets: payloadSets
    })
    showEditSessionModal.value = false
    editingSession.value = null
    await fetchHistory()
    await fetchWeeklyStats()
  } catch (err) {
    alert('更新訓練紀錄失敗，請稍後重試')
  }
}

async function handleDeleteSession(id) {
  if (!confirm('確定要刪除這筆訓練紀錄嗎？刪除後無法復原。')) return
  try {
    await workoutsAPI.deleteSession(id)
    alert('已成功刪除該筆紀錄！')
    await fetchHistory()
    await fetchWeeklyStats()
  } catch (err) {
    alert('刪除失敗，請稍後重試')
  }
}

function startBlankWorkout() {
  workoutStore.startWorkout('今日自由訓練')
  router.push('/active-workout')
}

function startRoutine(routine) {
  workoutStore.startWorkout(routine.title, routine)
  router.push('/active-workout')
}

async function deleteRoutine(id) {
  if (!confirm('確定要刪除此課表嗎？')) return
  try {
    await workoutsAPI.deleteRoutine(id)
    await fetchRoutines()
  } catch (err) {
    alert('刪除失敗')
  }
}

function isExerciseInNewRoutine(id) {
  return selectedRoutineExercises.value.some(e => e.exercise_id === id)
}

function toggleExerciseForRoutine(ex) {
  const idx = selectedRoutineExercises.value.findIndex(e => e.exercise_id === ex.id)
  if (idx > -1) {
    selectedRoutineExercises.value.splice(idx, 1)
  } else {
    selectedRoutineExercises.value.push({
      exercise_id: ex.id,
      exercise_name: ex.name,
      target_sets: 3,
      target_reps: 10
    })
  }
}

async function submitCreateRoutine() {
  if (!newRoutineTitle.value.trim()) {
    alert('請輸入課表名稱')
    return
  }
  if (selectedRoutineExercises.value.length === 0) {
    alert('請至少選擇 1 個動作')
    return
  }

  try {
    const payload = {
      title: newRoutineTitle.value,
      target_split: newRoutineSplit.value,
      exercises: selectedRoutineExercises.value
    }
    if (editingRoutineId.value) {
      await workoutsAPI.updateRoutine(editingRoutineId.value, payload)
    } else {
      await workoutsAPI.createRoutine(payload)
    }
    showCreateRoutineModal.value = false
    editingRoutineId.value = null
    newRoutineTitle.value = ''
    selectedRoutineExercises.value = []
    await fetchRoutines()
  } catch (err) {
    alert('儲存失敗，請稍後重試')
  }
}

function addExerciseToActive(ex) {
  workoutStore.addExerciseToActive(ex)
  router.push('/active-workout')
}

async function fetchWeeklyStats() {
  try {
    const res = await workoutsAPI.getWeeklyComparison()
    weeklyStats.value = res.data
  } catch (err) {
    console.error('Failed to fetch weekly stats:', err)
  }
}

async function handle90dCleanup() {
  if (!confirm('確定要執行 90 天滾動歸檔嗎？超過 3 個月的訓練日誌將會被清理以釋放資料庫空間，但 1RM 歷史最高紀錄將會永久保留。')) return
  try {
    const res = await workoutsAPI.cleanup90d()
    alert(res.data.message || '90 天滾動清理完成！')
    await fetchHistory()
    await fetchWeeklyStats()
  } catch (err) {
    alert('清理失敗，請稍後重試')
  }
}

onMounted(() => {
  fetchRoutines()
  fetchExercises()
  fetchHistory()
  fetchWeeklyStats()
})
</script>
