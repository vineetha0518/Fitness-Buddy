/**
 * Fitness Buddy — Frontend JavaScript
 * =====================================
 * SPA routing, API calls, charts, and UI interactions.
 * IBM Granite-powered AI chat, workout planner, BMI calculator,
 * calorie tracker, and progress dashboard.
 */

'use strict';

/* ============================================================
   STATE
   ============================================================ */
const State = {
  currentSection: 'hero',
  chatHistory:    [],
  allMeals:       {},
  macroChart:     null,
  workoutChart:   null,
  calorieChart:   null,
};

/* ============================================================
   SECTION ROUTING (SPA)
   ============================================================ */
function showSection(name) {
  document.querySelectorAll('.section-panel').forEach(el => el.classList.remove('active'));
  const target = document.getElementById(`section-${name}`);
  if (target) {
    target.classList.add('active');
    State.currentSection = name;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Lazy-load section data on first visit
  const loaders = {
    dashboard:   loadDashboard,
    workout:     loadWarmupCooldown,
    nutrition:   loadMeals,
    progress:    loadProgress,
    profile:     loadProfile,
    planner:     () => loadWeeklyPlan('beginner'),
  };
  if (loaders[name]) loaders[name]();
}

function closeOffcanvas() {
  const el = document.getElementById('mobileNav');
  if (el) bootstrap.Offcanvas.getInstance(el)?.hide();
}

/* ============================================================
   THEME TOGGLE
   ============================================================ */
function initTheme() {
  const saved = localStorage.getItem('fb_theme') || 'light';
  applyTheme(saved);
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-bs-theme', theme);
  const icon = document.getElementById('themeIcon');
  if (icon) {
    icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
  }
  localStorage.setItem('fb_theme', theme);
}

document.getElementById('themeToggle')?.addEventListener('click', () => {
  const current = document.documentElement.getAttribute('data-bs-theme');
  applyTheme(current === 'dark' ? 'light' : 'dark');
});

/* ============================================================
   API HELPERS
   ============================================================ */
async function apiFetch(url, options = {}) {
  try {
    const defaults = {
      headers: { 'Content-Type': 'application/json' },
    };
    const resp = await fetch(url, { ...defaults, ...options });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ error: `HTTP ${resp.status}` }));
      throw new Error(err.error || `HTTP ${resp.status}`);
    }
    return await resp.json();
  } catch (err) {
    console.error(`API error [${url}]:`, err);
    throw err;
  }
}

function post(url, body) {
  return apiFetch(url, { method: 'POST', body: JSON.stringify(body) });
}

function get(url) {
  return apiFetch(url);
}

/* ============================================================
   TOAST NOTIFICATIONS
   ============================================================ */
function showToast(message, type = 'info') {
  const colours = { success: '#22c55e', info: '#6366f1', warning: '#f59e0b', danger: '#ef4444' };
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const id = `toast-${Date.now()}`;
  container.insertAdjacentHTML('beforeend', `
    <div id="${id}" class="toast achievement-toast show align-items-center" role="alert">
      <div class="d-flex align-items-center gap-2 p-3">
        <div style="width:4px;height:40px;background:${colours[type]||colours.info};border-radius:4px;flex-shrink:0;"></div>
        <div class="flex-grow-1 small">${message}</div>
        <button type="button" class="btn-close ms-2" onclick="document.getElementById('${id}').remove()"></button>
      </div>
    </div>
  `);

  setTimeout(() => document.getElementById(id)?.remove(), 5000);
}

/* ============================================================
   DASHBOARD
   ============================================================ */
async function loadDashboard() {
  try {
    const [progress, todayCalories] = await Promise.all([
      get('/api/progress'),
      get('/api/calorie/today'),
    ]);

    // Update stat cards
    setText('dashStreak',  progress.streak);
    setText('dashTotal',   progress.total_workouts);
    setText('dashWeekly',  progress.weekly_workouts);
    setText('dashCalories', progress.weekly_calories_burned);

    // Calorie bar
    const consumed = todayCalories.calories;
    const target   = todayCalories.target;
    const pct      = Math.min(100, Math.round((consumed / target) * 100));
    setText('calConsumed', consumed);
    setText('calTarget',   target);
    setText('calRemaining', Math.max(0, target - consumed));
    setStyle('calProgressBar', 'width', `${pct}%`);

    // Achievements
    renderAchievements('achievementsList', progress.achievements);

    // Recent workouts
    renderRecentWorkouts(progress.recent_logs);

    // Macro chart
    renderMacroChart(todayCalories);

    // Load tip + motivation
    loadDailyTip();
    loadMotivation();

  } catch (err) {
    console.warn('Dashboard load error:', err);
  }
}

async function loadDailyTip() {
  try {
    const data = await get('/api/tip');
    const el = document.getElementById('dailyTipContent');
    if (el) el.innerHTML = `<p class="mb-0">${escapeHtml(data.tip)}</p>`;
  } catch {
    const el = document.getElementById('dailyTipContent');
    if (el) el.innerHTML = '<p class="text-muted small">Stay consistent — progress takes time! 💪</p>';
  }
}

async function loadMotivation() {
  const el = document.getElementById('motivationContent');
  if (!el) return;
  el.innerHTML = '<em class="text-muted small">Loading...</em>';
  try {
    const data = await get('/api/motivation');
    el.innerHTML = `<p class="fst-italic mb-0">"${escapeHtml(data.message)}"</p>
      <small class="text-muted mt-2 d-block">🔥 ${data.streak}-day streak</small>`;
  } catch {
    el.innerHTML = '<p class="fst-italic text-muted mb-0">"Every workout brings you one step closer to your goal."</p>';
  }
}

function renderMacroChart(data) {
  const canvas = document.getElementById('macroChart');
  if (!canvas) return;

  if (State.macroChart) State.macroChart.destroy();

  const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
  const textColor = isDark ? '#94a3b8' : '#64748b';

  State.macroChart = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: ['Protein', 'Carbs', 'Fat'],
      datasets: [{
        data: [data.protein || 0, data.carbs || 0, data.fat || 0],
        backgroundColor: ['#6366f1', '#f59e0b', '#ec4899'],
        borderWidth: 0,
        hoverOffset: 6,
      }],
    },
    options: {
      cutout: '68%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: textColor, font: { size: 11 }, padding: 12 },
        },
      },
    },
  });
}

function renderRecentWorkouts(logs) {
  const el = document.getElementById('recentWorkoutsTable');
  if (!el) return;

  if (!logs || logs.length === 0) {
    el.innerHTML = '<p class="text-muted small">No workouts logged yet.</p>';
    return;
  }

  const rows = logs.slice().reverse().map(l => `
    <tr>
      <td>${l.date}</td>
      <td class="fw-semibold">${escapeHtml(l.workout_name)}</td>
      <td>${l.duration_min} min</td>
      <td><span class="text-danger fw-semibold">${l.calories_burned} kcal</span></td>
    </tr>
  `).join('');

  el.innerHTML = `
    <div class="table-responsive">
      <table class="fb-table">
        <thead><tr><th>Date</th><th>Workout</th><th>Duration</th><th>Calories</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
}

function renderAchievements(containerId, achievements) {
  const el = document.getElementById(containerId);
  if (!el) return;

  if (!achievements || achievements.length === 0) {
    el.innerHTML = '<p class="text-muted small mb-0">No achievements yet. Keep going! 🏅</p>';
    return;
  }

  el.innerHTML = achievements
    .map(a => `<span class="badge achievement-badge">${escapeHtml(a)}</span>`)
    .join('');
}

/* ============================================================
   WORKOUT PLANNER
   ============================================================ */
async function generateWorkout() {
  const spinner = document.getElementById('workoutSpinner');
  const placeholder = document.getElementById('workoutPlaceholder');
  const resultBox = document.getElementById('workoutResult');
  const content = document.getElementById('workoutResultContent');

  showSpinner(spinner);

  const body = {
    fitness_level:      document.getElementById('wLevel')?.value || 'beginner',
    goal:               document.getElementById('wGoal')?.value || 'weight_loss',
    available_time_min: parseInt(document.getElementById('wTime')?.value || '30'),
    equipment:          document.getElementById('wEquipment')?.value || 'none',
  };

  try {
    const data = await post('/api/workout/recommend', body);

    placeholder.classList.add('d-none');
    resultBox.classList.remove('d-none');

    const plan = data.structured_plan;
    const ai   = data.ai_narrative;

    let html = `
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0">${plan.level} Plan — ${plan.goal}</h5>
        <span class="badge bg-danger">${plan.estimated_calories_burned} kcal est.</span>
      </div>

      <h6 class="text-muted mb-2">🏋️ Exercises</h6>
      <div class="exercise-list mb-3">
    `;

    plan.exercises.forEach(ex => {
      html += `
        <div class="exercise-card">
          <div class="exercise-name">${escapeHtml(ex.name)}</div>
          <div class="exercise-meta">
            <span class="ex-badge">${ex.sets} sets × ${ex.reps}</span>
            <span>Rest: ${ex.rest}</span>
            <span>${ex.muscle_group}</span>
            <span class="text-danger">~${ex.calories_burned * ex.sets} kcal</span>
          </div>
          ${ex.tip ? `<div class="mt-1 small text-muted"><i class="bi bi-lightbulb text-warning me-1"></i>${escapeHtml(ex.tip)}</div>` : ''}
          ${ex.note ? `<div class="mt-1 small" style="color:var(--accent)"><i class="bi bi-info-circle me-1"></i>${escapeHtml(ex.note)}</div>` : ''}
        </div>
      `;
    });

    html += `</div>`;

    if (ai) {
      html += `
        <h6 class="text-muted mb-2">🤖 AI Coach Advice</h6>
        <div class="ai-response-box">${escapeHtml(ai)}</div>
      `;
    }

    html += `
      <div class="mt-3 d-flex gap-2">
        <button class="btn btn-sm btn-success" onclick="openLogModal('${escapeHtml(body.fitness_level).toUpperCase()} Workout', ${body.available_time_min}, ${plan.estimated_calories_burned})">
          <i class="bi bi-check-circle me-1"></i>Log This Workout
        </button>
      </div>
    `;

    content.innerHTML = html;

  } catch (err) {
    showToast(`Failed to generate workout: ${err.message}`, 'danger');
    placeholder.classList.remove('d-none');
    resultBox.classList.add('d-none');
  } finally {
    hideSpinner(spinner);
  }
}

async function loadWarmupCooldown() {
  try {
    const [warmup, cooldown] = await Promise.all([
      get('/api/warmup'),
      get('/api/cooldown'),
    ]);
    renderExerciseList('warmupList', warmup, '#f59e0b');
    renderExerciseList('cooldownList', cooldown, '#06b6d4');
  } catch (err) {
    console.warn('Warmup/cooldown load error:', err);
  }
}

function renderExerciseList(containerId, exercises, color) {
  const el = document.getElementById(containerId);
  if (!el) return;

  el.innerHTML = exercises.map(ex => `
    <div class="d-flex gap-2 align-items-start mb-2">
      <div style="width:4px;min-height:40px;background:${color};border-radius:4px;flex-shrink:0;"></div>
      <div>
        <div class="fw-semibold small">${escapeHtml(ex.name)} <span class="text-muted fw-normal">(${escapeHtml(ex.duration)})</span></div>
        <div class="text-muted" style="font-size:0.78rem;">${escapeHtml(ex.description)}</div>
      </div>
    </div>
  `).join('');
}

/* ============================================================
   NUTRITION
   ============================================================ */
async function loadMeals() {
  if (Object.keys(State.allMeals).length > 0) return;  // cached
  try {
    const data = await get('/api/nutrition/meals');
    State.allMeals = data;
    filterMeals('all');
  } catch (err) {
    console.warn('Meals load error:', err);
  }
}

function filterMeals(category) {
  const grid = document.getElementById('mealsGrid');
  if (!grid) return;

  let meals = [];
  if (category === 'all') {
    ['breakfast', 'lunch', 'dinner', 'snacks'].forEach(cat => {
      (State.allMeals[cat] || []).forEach(m => meals.push({ ...m, category: cat }));
    });
  } else {
    meals = (State.allMeals[category] || []).map(m => ({ ...m, category }));
  }

  grid.innerHTML = meals.map(meal => `
    <div class="col-sm-6 col-lg-4">
      <div class="meal-card" onclick="quickLogMeal(this)" 
           data-name="${escapeHtml(meal.name)}"
           data-cal="${meal.calories}"
           data-protein="${meal.protein_g}"
           data-carbs="${meal.carbs_g}"
           data-fat="${meal.fat_g}">
        <div class="meal-card-header">
          <div class="meal-card-name">${escapeHtml(meal.name)}</div>
          <span class="meal-cal-badge">${meal.calories} kcal</span>
        </div>
        <div class="text-muted small mb-2">${escapeHtml(meal.serving)}</div>
        <div class="meal-macros">
          <span class="macro-pill protein">P: ${meal.protein_g}g</span>
          <span class="macro-pill carbs">C: ${meal.carbs_g}g</span>
          <span class="macro-pill fat">F: ${meal.fat_g}g</span>
          <span class="macro-pill fiber">Fibre: ${meal.fiber_g}g</span>
        </div>
        <div class="mt-2 d-flex flex-wrap gap-1">
          ${(meal.tags || []).slice(0, 3).map(t => `<span class="meal-tag">${escapeHtml(t)}</span>`).join('')}
        </div>
        ${meal.tip ? `<div class="mt-2 text-muted" style="font-size:0.75rem;"><i class="bi bi-lightbulb text-warning me-1"></i>${escapeHtml(meal.tip)}</div>` : ''}
      </div>
    </div>
  `).join('');
}

function quickLogMeal(card) {
  document.getElementById('logMeal').value     = card.dataset.name    || '';
  document.getElementById('logCal').value      = card.dataset.cal     || '';
  document.getElementById('logProtein').value  = card.dataset.protein || '';
  document.getElementById('logCarbs').value    = card.dataset.carbs   || '';
  document.getElementById('logMeal').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  showToast(`Selected: ${card.dataset.name} — click "Log Meal" to save.`, 'info');
}

async function getNutritionPlan() {
  const spinner = document.getElementById('nutSpinner');
  showSpinner(spinner);

  const body = {
    diet:  document.getElementById('nutDiet')?.value || 'vegetarian',
    query: document.getElementById('nutQuery')?.value || '',
  };

  try {
    const data = await post('/api/nutrition/recommend', body);
    const el = document.getElementById('nutritionResult');
    if (el) {
      el.classList.remove('d-none');
      el.querySelector('.ai-response-box').textContent = data.recommendation;
    }
  } catch (err) {
    showToast(`Nutrition plan error: ${err.message}`, 'danger');
  } finally {
    hideSpinner(spinner);
  }
}

async function logCalories() {
  const meal    = document.getElementById('logMeal')?.value.trim();
  const cal     = parseFloat(document.getElementById('logCal')?.value) || 0;
  const protein = parseFloat(document.getElementById('logProtein')?.value) || 0;
  const carbs   = parseFloat(document.getElementById('logCarbs')?.value) || 0;

  if (!meal || cal <= 0) {
    showToast('Please enter a meal name and calories.', 'warning');
    return;
  }

  try {
    const data = await post('/api/calorie/log', { meal, calories: cal, protein, carbs });
    showToast(`✅ ${meal} logged! Total today: ${data.today_totals.calories} kcal`, 'success');
    ['logMeal','logCal','logProtein','logCarbs'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });
    loadTodayCalorieLog();
  } catch (err) {
    showToast(`Log error: ${err.message}`, 'danger');
  }
}

async function loadTodayCalorieLog() {
  try {
    const data = await get('/api/calorie/today');
    const el = document.getElementById('todayCalorieLog');
    if (!el) return;

    if (!data.entries || data.entries.length === 0) {
      el.innerHTML = '<p class="text-muted small mt-2">No meals logged today.</p>';
      return;
    }

    el.innerHTML = `
      <h6 class="mt-3 mb-2">Today's Log</h6>
      <div class="table-responsive">
        <table class="fb-table">
          <thead><tr><th>Meal</th><th>kcal</th><th>Protein</th><th>Carbs</th></tr></thead>
          <tbody>
            ${data.entries.map(e => `
              <tr>
                <td>${escapeHtml(e.meal)}</td>
                <td class="text-danger fw-semibold">${e.calories}</td>
                <td>${e.protein}g</td>
                <td>${e.carbs}g</td>
              </tr>
            `).join('')}
          </tbody>
          <tfoot>
            <tr class="fw-bold">
              <td>Total</td>
              <td class="text-danger">${data.calories}</td>
              <td>${data.protein}g</td>
              <td>${data.carbs}g</td>
            </tr>
          </tfoot>
        </table>
      </div>
    `;
  } catch (err) {
    console.warn('Calorie log error:', err);
  }
}

/* ============================================================
   CALCULATORS
   ============================================================ */
async function calculateBMI() {
  const weight = parseFloat(document.getElementById('bmiWeight')?.value);
  const height = parseFloat(document.getElementById('bmiHeight')?.value);
  const gender = document.getElementById('bmiGender')?.value;

  if (!weight || !height || weight <= 0 || height <= 0) {
    showToast('Please enter valid weight and height.', 'warning');
    return;
  }

  try {
    const data = await post('/api/bmi', { weight_kg: weight, height_cm: height, gender });

    document.getElementById('bmiResult')?.classList.remove('d-none');
    setText('bmiValue', data.bmi);

    const catEl = document.getElementById('bmiCategory');
    if (catEl) {
      catEl.textContent = data.category;
      catEl.className = 'bmi-category-badge';
      if (data.color === 'success') catEl.style.background = 'linear-gradient(135deg,#22c55e,#16a34a)';
      else if (data.color === 'warning') catEl.style.background = 'linear-gradient(135deg,#f59e0b,#d97706)';
      else catEl.style.background = 'linear-gradient(135deg,#ef4444,#dc2626)';
    }

    setText('bmiAdvice', data.advice);

    const iw = data.ideal_weight;
    setText('idealWeight', `${iw.min_kg}–${iw.max_kg} kg`);

    // Position indicator on scale (BMI 16–40 mapped to 0–100%)
    const pct = Math.min(100, Math.max(0, ((data.bmi - 16) / (40 - 16)) * 100));
    setStyle('bmiIndicator', 'left', `${pct}%`);

  } catch (err) {
    showToast(`BMI error: ${err.message}`, 'danger');
  }
}

async function calculateTDEE() {
  const body = {
    weight_kg:      parseFloat(document.getElementById('tdeeWeight')?.value),
    height_cm:      parseFloat(document.getElementById('tdeeHeight')?.value),
    age:            parseInt(document.getElementById('tdeeAge')?.value),
    gender:         document.getElementById('tdeeGender')?.value,
    activity_level: document.getElementById('tdeeActivity')?.value,
    goal:           document.getElementById('tdeeGoal')?.value,
  };

  if (!body.weight_kg || !body.height_cm || !body.age) {
    showToast('Please fill in all fields.', 'warning');
    return;
  }

  try {
    const data = await post('/api/calories', body);

    document.getElementById('tdeeResult')?.classList.remove('d-none');
    setText('tdeeBMR',    `${data.bmr} kcal`);
    setText('tdeeTDEE',   `${data.tdee} kcal`);
    setText('tdeeTarget', `${data.target_calories} kcal/day`);
    setText('tdeeWater',  `${data.water_litres} L`);

    // Macro bars
    const m = data.macros;
    const total = (m.protein_g * 4) + (m.carbohydrate_g * 4) + (m.fat_g * 9);
    const macroEl = document.getElementById('tdeeMarcos');
    if (macroEl) {
      macroEl.innerHTML = [
        { label: 'Protein',      g: m.protein_g,      kcal: m.protein_g * 4,      color: '#6366f1', cls: 'protein' },
        { label: 'Carbohydrates', g: m.carbohydrate_g, kcal: m.carbohydrate_g * 4, color: '#f59e0b', cls: 'carbs' },
        { label: 'Fat',          g: m.fat_g,          kcal: m.fat_g * 9,          color: '#ec4899', cls: 'fat' },
      ].map(({ label, g, kcal, color }) => {
        const pct = total > 0 ? Math.round((kcal / total) * 100) : 0;
        return `
          <div class="macro-row">
            <div class="macro-label">
              <span>${label}</span>
              <span style="color:${color}">${g}g &nbsp;(${pct}%)</span>
            </div>
            <div class="progress fb-progress" style="height:8px;">
              <div class="progress-bar" style="width:${pct}%;background:${color};" role="progressbar"></div>
            </div>
          </div>
        `;
      }).join('');
    }

  } catch (err) {
    showToast(`TDEE error: ${err.message}`, 'danger');
  }
}

/* ============================================================
   WEEKLY PLANNER
   ============================================================ */
async function loadWeeklyPlan(level) {
  try {
    const data = await get(`/api/workout/recommend`);
    // We use static data from workouts.json via a direct fetch
    const resp = await fetch(`/api/workout/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fitness_level: level }),
    });
    const d = await resp.json();
    renderWeeklyPlan(d.structured_plan?.weekly_schedule || {}, level);
  } catch (err) {
    console.warn('Weekly plan error:', err);
  }
}

function renderWeeklyPlan(schedule, level) {
  const grid = document.getElementById('weeklyPlanGrid');
  if (!grid) return;

  const days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
  const today = new Date().toLocaleDateString('en-US', { weekday: 'long' });

  grid.innerHTML = days.map(day => {
    const workout = schedule[day] || 'Rest Day';
    const isToday = day === today;
    const isRest  = workout.toLowerCase().includes('rest');
    return `
      <div class="col-sm-6 col-lg-3">
        <div class="day-card ${isToday ? 'today-card' : ''}">
          <div class="day-label">${day} ${isToday ? '• TODAY' : ''}</div>
          <div class="day-workout">
            <i class="bi ${isRest ? 'bi-moon-stars text-info' : 'bi-lightning-charge text-warning'} me-1"></i>
            ${escapeHtml(workout)}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

async function getDailyPlan(dayType = 'workout') {
  const card   = document.getElementById('dailyPlanCard');
  const result = document.getElementById('dailyPlanResult');
  if (!card || !result) return;

  result.innerHTML = '<div class="skeleton-line"></div><div class="skeleton-line w-75"></div>';
  card.classList.remove('d-none');

  try {
    const data = await post('/api/daily-plan', { day_type: dayType });
    result.innerHTML = `<div class="ai-response-box">${escapeHtml(data.plan)}</div>`;
  } catch (err) {
    result.innerHTML = `<p class="text-danger small">${err.message}</p>`;
  }
}

/* ============================================================
   PROGRESS
   ============================================================ */
async function loadProgress() {
  try {
    const data = await get('/api/progress');

    renderAchievements('fullAchievementsList', data.achievements);

    // Workout chart
    renderProgressCharts(data.recent_logs);

    // History table
    const el = document.getElementById('historyTable');
    if (el && data.recent_logs && data.recent_logs.length > 0) {
      const rows = data.recent_logs.slice().reverse().map(l => `
        <tr>
          <td>${l.date}</td>
          <td class="fw-semibold">${escapeHtml(l.workout_name)}</td>
          <td>${l.duration_min} min</td>
          <td><span class="text-danger fw-semibold">${l.calories_burned} kcal</span></td>
          <td class="text-muted small">${escapeHtml(l.notes || '—')}</td>
        </tr>
      `).join('');
      el.innerHTML = `
        <table class="fb-table">
          <thead><tr><th>Date</th><th>Workout</th><th>Duration</th><th>Calories</th><th>Notes</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>`;
    } else if (el) {
      el.innerHTML = '<p class="text-muted small">No workouts logged yet.</p>';
    }

  } catch (err) {
    console.warn('Progress load error:', err);
  }
}

function renderProgressCharts(logs) {
  const days = getLast7Days();

  const workoutCounts = days.map(d =>
    (logs || []).filter(l => l.date === d).length
  );
  const caloriesBurned = days.map(d =>
    (logs || []).filter(l => l.date === d).reduce((s, l) => s + (l.calories_burned || 0), 0)
  );

  const labels = days.map(d => new Date(d).toLocaleDateString('en-IN', { weekday: 'short' }));
  const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
  const textColor = isDark ? '#94a3b8' : '#64748b';

  const chartDefaults = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: textColor }, grid: { display: false } },
      y: { ticks: { color: textColor }, grid: { color: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }, beginAtZero: true },
    },
  };

  const wCanvas = document.getElementById('workoutChart');
  if (wCanvas) {
    if (State.workoutChart) State.workoutChart.destroy();
    State.workoutChart = new Chart(wCanvas, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          data: workoutCounts,
          backgroundColor: 'rgba(99,102,241,0.7)',
          borderRadius: 8,
        }],
      },
      options: chartDefaults,
    });
  }

  const cCanvas = document.getElementById('caloriesBurnedChart');
  if (cCanvas) {
    if (State.calorieChart) State.calorieChart.destroy();
    State.calorieChart = new Chart(cCanvas, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          data: caloriesBurned,
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239,68,68,0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 5,
          pointBackgroundColor: '#ef4444',
        }],
      },
      options: chartDefaults,
    });
  }
}

/* ============================================================
   CHAT
   ============================================================ */
async function sendMessage() {
  const input   = document.getElementById('chatInput');
  const message = input?.value.trim();
  if (!message) return;

  appendMessage('user', message);
  input.value = '';
  autoResizeTextarea(input);

  showTypingIndicator(true);

  try {
    const data = await post('/api/chat', { message });
    showTypingIndicator(false);
    appendMessage('bot', data.response);
  } catch (err) {
    showTypingIndicator(false);
    appendMessage('bot', `⚠️ Error: ${err.message}`);
  }
}

function sendQuickPrompt(prompt) {
  const input = document.getElementById('chatInput');
  if (input) input.value = prompt;
  sendMessage();
}

function appendMessage(role, text) {
  const container = document.getElementById('chatMessages');
  if (!container) return;

  const isBot   = role === 'bot';
  const time    = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
  const avatarIcon = isBot ? 'bi-robot' : 'bi-person-fill';

  const el = document.createElement('div');
  el.className = `message ${isBot ? 'bot-message' : 'user-message'}`;
  el.innerHTML = `
    <div class="message-avatar"><i class="bi ${avatarIcon}"></i></div>
    <div class="message-content">
      <div class="message-bubble">${formatMessageText(text)}</div>
      <small class="message-time text-muted">${time}</small>
    </div>
  `;

  container.appendChild(el);
  container.scrollTop = container.scrollHeight;
}

function formatMessageText(text) {
  // Convert markdown-like formatting to HTML
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^• (.+)/gm, '<li>$1</li>')
    .replace(/^- (.+)/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, '<ul class="mb-2">$&</ul>')
    .replace(/\n/g, '<br>');
}

function showTypingIndicator(show) {
  const el = document.getElementById('typingIndicator');
  if (!el) return;
  if (show) {
    el.classList.remove('d-none');
    document.getElementById('chatMessages')?.scrollTo({ top: 99999, behavior: 'smooth' });
  } else {
    el.classList.add('d-none');
  }
}

async function clearChat() {
  await post('/api/chat/clear', {}).catch(() => {});
  State.chatHistory = [];
  const container = document.getElementById('chatMessages');
  if (container) {
    container.innerHTML = `
      <div class="message bot-message">
        <div class="message-avatar"><i class="bi bi-robot"></i></div>
        <div class="message-content">
          <div class="message-bubble">
            <p>Chat cleared! 👋 I'm FitBot — ready to help with your fitness goals. What would you like to work on?</p>
          </div>
          <small class="message-time text-muted">Just now</small>
        </div>
      </div>`;
  }
}

// Auto-expand textarea
document.getElementById('chatInput')?.addEventListener('keydown', function (e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

document.getElementById('chatInput')?.addEventListener('input', function () {
  autoResizeTextarea(this);
});

function autoResizeTextarea(el) {
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

/* ============================================================
   WORKOUT LOG MODAL
   ============================================================ */
function openLogModal(name = '', duration = 30, calories = 200) {
  document.getElementById('logWorkoutName').value = name;
  document.getElementById('logDuration').value    = duration;
  document.getElementById('logCalBurned').value   = calories;
  new bootstrap.Modal(document.getElementById('logWorkoutModal')).show();
}

async function logWorkout() {
  const name     = document.getElementById('logWorkoutName')?.value.trim();
  const duration = parseInt(document.getElementById('logDuration')?.value)    || 30;
  const calories = parseInt(document.getElementById('logCalBurned')?.value)   || 0;
  const notes    = document.getElementById('logNotes')?.value.trim()          || '';

  if (!name) { showToast('Please enter a workout name.', 'warning'); return; }

  try {
    const data = await post('/api/workout/log', {
      workout_name: name, duration_min: duration, calories_burned: calories, notes,
    });

    bootstrap.Modal.getInstance(document.getElementById('logWorkoutModal'))?.hide();
    showToast(`✅ Workout logged! Streak: ${data.streak} days 🔥`, 'success');

    if (data.new_achievements && data.new_achievements.length > 0) {
      data.new_achievements.forEach(a => {
        setTimeout(() => showToast(`🏆 Achievement unlocked: ${a}`, 'warning'), 800);
      });
    }

    // Refresh dashboard if visible
    if (State.currentSection === 'dashboard') loadDashboard();

  } catch (err) {
    showToast(`Log error: ${err.message}`, 'danger');
  }
}

/* ============================================================
   PROFILE
   ============================================================ */
async function loadProfile() {
  try {
    const [profile, progress] = await Promise.all([
      get('/api/profile'),
      get('/api/progress'),
    ]);

    const fieldMap = {
      pName: profile.name, pAge: profile.age, pGender: profile.gender,
      pWeight: profile.weight_kg, pHeight: profile.height_cm,
      pLevel: profile.fitness_level, pGoal: profile.goal,
      pDiet: profile.diet, pTime: profile.available_time_min,
      pEquipment: profile.equipment,
    };

    Object.entries(fieldMap).forEach(([id, val]) => {
      const el = document.getElementById(id);
      if (el && val !== undefined) el.value = val;
    });

    setText('profileName',     profile.name || 'Fitness Enthusiast');
    setText('profileSubtitle', `${profile.fitness_level || 'Beginner'} • ${(profile.goal || 'General Fitness').replace('_',' ')}`);
    setText('profileStreak',   progress.streak);
    setText('profileTotal',    progress.total_workouts);

  } catch (err) {
    console.warn('Profile load error:', err);
  }
}

async function saveProfile() {
  const spinner = document.getElementById('profileSpinner');
  showSpinner(spinner);

  const body = {
    name:               document.getElementById('pName')?.value.trim(),
    age:                parseInt(document.getElementById('pAge')?.value),
    gender:             document.getElementById('pGender')?.value,
    weight_kg:          parseFloat(document.getElementById('pWeight')?.value),
    height_cm:          parseFloat(document.getElementById('pHeight')?.value),
    fitness_level:      document.getElementById('pLevel')?.value,
    goal:               document.getElementById('pGoal')?.value,
    diet:               document.getElementById('pDiet')?.value,
    available_time_min: parseInt(document.getElementById('pTime')?.value),
    equipment:          document.getElementById('pEquipment')?.value,
  };

  try {
    await post('/api/profile', body);
    showToast('✅ Profile saved successfully!', 'success');
    setText('profileName',     body.name || 'Fitness Enthusiast');
    setText('profileSubtitle', `${body.fitness_level} • ${body.goal.replace('_',' ')}`);
  } catch (err) {
    showToast(`Save error: ${err.message}`, 'danger');
  } finally {
    hideSpinner(spinner);
  }
}

/* ============================================================
   UTILITIES
   ============================================================ */
function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function setStyle(id, prop, value) {
  const el = document.getElementById(id);
  if (el) el.style[prop] = value;
}

function showSpinner(el) { el?.classList.remove('d-none'); }
function hideSpinner(el) { el?.classList.add('d-none'); }

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function getLast7Days() {
  const days = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    days.push(d.toISOString().split('T')[0]);
  }
  return days;
}

/* ============================================================
   INIT
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {
  initTheme();

  // Seed stats from Flask session data
  if (window.FB_DATA) {
    setText('dashStreak',  window.FB_DATA.streak);
    setText('dashTotal',   window.FB_DATA.totalWorkouts);
    setText('profileStreak', window.FB_DATA.streak);
    setText('profileTotal',  window.FB_DATA.totalWorkouts);
    renderAchievements('achievementsList', window.FB_DATA.achievements);
  }

  // Show hero on load
  showSection('hero');

  // Auto-load calorie log on nutrition tab
  document.addEventListener('click', e => {
    if (e.target?.closest('[onclick*="nutrition"]')) {
      setTimeout(loadTodayCalorieLog, 300);
    }
  });
});
