/**
 * test.js – IQ test engine
 * Handles: question rendering, timer, answer tracking, submission.
 */

const API_BASE = ''; // Use relative paths

// ── State (in-memory only — lost if tab closed) ──────────────────────
let SESSION_ID   = null;
let QUESTIONS    = [];
let ANSWERS      = {};           // {q_id: chosen_option}
let CURRENT_IDX  = 0;
let TIMER_ID     = null;
let TIME_LEFT    = 1800;         // seconds (overridden by server)
let TOTAL_TIME   = 1800;

// ── DOM refs ─────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

const loadingOverlay     = $('loading-overlay');
const terminatedOverlay  = $('terminated-overlay');
const terminateReason    = $('terminate-reason');
const testContainer      = $('test-container');
const questionText       = $('question-text');
const optionsContainer   = $('options-container');
const questionNum        = $('question-num');
const questionTotal      = $('question-total');
const progressFill       = $('progress-fill');
const timerDisplay       = $('timer-display');
const timerFill          = $('timer-fill');
const btnPrev            = $('btn-prev');
const btnNext            = $('btn-next');
const btnSubmit          = $('btn-submit');
const categoryBadge      = $('category-badge');

const CIRCUMFERENCE = 2 * Math.PI * 36;   // radius 36 on the SVG circle

// ── Timer ─────────────────────────────────────────────────────────────
function startTimer() {
  updateTimerUI();
  TIMER_ID = setInterval(() => {
    TIME_LEFT--;
    updateTimerUI();
    if (TIME_LEFT <= 0) {
      clearInterval(TIMER_ID);
      submitAnswers(true);
    }
  }, 1000);
}

function updateTimerUI() {
  const m = Math.floor(TIME_LEFT / 60).toString().padStart(2, '0');
  const s = (TIME_LEFT % 60).toString().padStart(2, '0');
  timerDisplay.textContent = `${m}:${s}`;

  // SVG ring
  const ratio  = TIME_LEFT / TOTAL_TIME;
  const offset = CIRCUMFERENCE * (1 - ratio);
  timerFill.style.strokeDashoffset = offset;

  // Colour warning
  if (TIME_LEFT <= 300) {
    timerFill.style.stroke = '#ff5470';
    timerDisplay.style.color = '#ff5470';
  } else if (TIME_LEFT <= 600) {
    timerFill.style.stroke = '#ffb547';
  }
}

// ── Question rendering ────────────────────────────────────────────────
function showQuestion(idx) {
  CURRENT_IDX = idx;
  const q = QUESTIONS[idx];

  // Text
  questionText.textContent = q.text;
  categoryBadge.textContent = q.category;
  questionNum.textContent   = idx + 1;
  questionTotal.textContent = QUESTIONS.length;

  // Progress
  progressFill.style.width = `${((idx + 1) / QUESTIONS.length) * 100}%`;

  // Options
  optionsContainer.innerHTML = '';
  Object.entries(q.options).forEach(([key, text]) => {
    const btn = document.createElement('button');
    btn.className  = 'option-btn' + (ANSWERS[q.id] === key ? ' selected' : '');
    btn.dataset.key = key;
    btn.innerHTML = `
      <span class="option-label">${key}</span>
      <span>${text}</span>
    `;
    btn.addEventListener('click', () => selectOption(q.id, key));
    optionsContainer.appendChild(btn);
  });

  // Animate in
  questionText.parentElement.classList.remove('question-card');
  void questionText.parentElement.offsetWidth;
  questionText.parentElement.classList.add('question-card');

  // Nav buttons
  btnPrev.style.visibility   = idx === 0 ? 'hidden' : 'visible';
  btnNext.style.display      = idx < QUESTIONS.length - 1 ? 'inline-flex' : 'none';
  btnSubmit.style.display    = idx === QUESTIONS.length - 1 ? 'inline-flex' : 'none';
}

function selectOption(qId, key) {
  ANSWERS[qId] = key;
  // Refresh highlights
  document.querySelectorAll('.option-btn').forEach(btn => {
    btn.classList.toggle('selected', btn.dataset.key === key);
  });
}

// ── Navigation ────────────────────────────────────────────────────────
function attachNavListeners() {
  btnNext.addEventListener('click', () => {
    if (CURRENT_IDX < QUESTIONS.length - 1) showQuestion(CURRENT_IDX + 1);
  });
  btnPrev.addEventListener('click', () => {
    if (CURRENT_IDX > 0) showQuestion(CURRENT_IDX - 1);
  });
  btnSubmit.addEventListener('click', () => {
    const answered = Object.keys(ANSWERS).length;
    if (answered < QUESTIONS.length) {
      const skipped = QUESTIONS.length - answered;
      if (!confirm(`You have ${skipped} unanswered question(s). Submit anyway?`)) return;
    }
    submitAnswers(false);
  });
}

// ── Submit ────────────────────────────────────────────────────────────
async function submitAnswers(timedOut = false) {
  clearInterval(TIMER_ID);
  AntiCheat.stop();

  if (timedOut) {
    showMessage('⏱️ Time is up!', 'Your answers are being submitted…');
  }

  // Show spinner
  loadingOverlay.classList.remove('hidden');
  loadingOverlay.querySelector('p').textContent = 'Calculating your IQ score…';

  try {
    const res = await fetch(`${API_BASE}/api/test/submit`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ 
        session_id: SESSION_ID, 
        answers: ANSWERS,
        email: localStorage.getItem('user_email')
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Submission failed.');
    }

    const result = await res.json();
    // Store in sessionStorage (same tab only)
    sessionStorage.setItem('iq_result', JSON.stringify(result));
    window.location.href = '/result';
  } catch (err) {
    loadingOverlay.classList.add('hidden');
    alert('Error: ' + err.message);
  }
}

// ── Anti-cheat termination handler ────────────────────────────────────
const TERM_MESSAGES = {
  tab_switch:     'You switched to another tab or window.',
  window_blur:    'The test window lost focus.',
  fullscreen_exit:'You exited fullscreen mode.',
  page_close:     'The test window was closed.',
};

function onTerminated(reason) {
  clearInterval(TIMER_ID);
  testContainer.classList.add('hidden');
  loadingOverlay.classList.add('hidden');
  terminateReason.textContent = TERM_MESSAGES[reason] || 'A rule was violated.';
  terminatedOverlay.classList.remove('hidden');
}

function showMessage(title, body) {
  loadingOverlay.querySelector('h2').textContent   = title;
  loadingOverlay.querySelector('p').textContent    = body;
  loadingOverlay.classList.remove('hidden');
}

// ── Initialise ────────────────────────────────────────────────────────
async function init() {
  loadingOverlay.classList.remove('hidden');
  const spinner      = $('loading-spinner');
  const title        = $('loading-title');
  const msg          = $('loading-msg');
  const startConfirm = $('start-confirm');
  const startBtn     = $('real-start-btn');

  try {
    // 1. Start a new test session (does not require gesture)
    msg.textContent = 'Curating your questions...';
    const res = await fetch(`${API_BASE}/api/test/start`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to start test session.');
    const data = await res.json();

    SESSION_ID  = data.session_id;
    QUESTIONS   = data.questions;
    TIME_LEFT   = data.time_limit;
    TOTAL_TIME  = data.time_limit;

    // 2. Wait for user gesture to enter fullscreen
    spinner.style.display = 'none';
    title.textContent     = 'Test Ready';
    msg.textContent       = 'Click the button below to enter fullscreen and begin your assessment.';
    startConfirm.style.display = 'block';

    startBtn.addEventListener('click', async () => {
      startConfirm.style.display = 'none';
      spinner.style.display = 'block';
      title.textContent     = 'Entering Fullscreen...';

      // 3. Request fullscreen (MUST be in click handler)
      const ok = await AntiCheat.requestFullscreen(document.documentElement);
      if (!ok) {
        alert('Fullscreen is required to take the test. Please enable it and try again.');
        window.location.href = '/';
        return;
      }

      // 4. Set up anti-cheat & start
      AntiCheat.start(SESSION_ID, onTerminated);
      timerFill.style.strokeDasharray = `${CIRCUMFERENCE} ${CIRCUMFERENCE}`;
      timerFill.style.strokeDashoffset = 0;

      loadingOverlay.classList.add('hidden');
      testContainer.classList.remove('hidden');

      attachNavListeners();
      showQuestion(0);
      startTimer();
    });

  } catch (err) {
    alert('Error: ' + err.message + '\nMake sure the backend server is running.');
    window.location.href = '/';
  }
}

document.addEventListener('DOMContentLoaded', init);
