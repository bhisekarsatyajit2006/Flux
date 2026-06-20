/**
 * anticheat.js
 * Anti-cheat enforcement for the IQ test.
 *
 * Rules enforced:
 *  1. Fullscreen is required — test won't start without it.
 *  2. Exiting fullscreen during the test → instant termination.
 *  3. Tab switch (visibilitychange) → instant termination.
 *  4. Window blur (Alt+Tab, click outside) → instant termination.
 *  5. Copy / Cut / Paste are blocked.
 *  6. Right-click context menu is disabled.
 *  7. Common keyboard shortcuts (Ctrl+C, Ctrl+U, F12, etc.) blocked.
 *  8. On page close / beforeunload → session invalidated via sendBeacon.
 */

const AntiCheat = (() => {
  let _sessionId = null;
  let _terminated = false;
  let _onTerminate = null;   // callback
  let _active = false;

  const API_BASE = ''; // Use relative paths

  /* ── Soft termination ── */
  function terminate(reason) {
    if (_terminated || !_active) return;
    _terminated = true;
    _active = false;

    // Invalidate server-side session
    if (_sessionId) {
      const payload = JSON.stringify({ session_id: _sessionId });
      if (navigator.sendBeacon) {
        navigator.sendBeacon(`${API_BASE}/api/test/invalidate`, new Blob([payload], { type: 'application/json' }));
      } else {
        fetch(`${API_BASE}/api/test/invalidate`, {
          method: 'POST', keepalive: true,
          headers: { 'Content-Type': 'application/json' },
          body: payload,
        }).catch(() => {});
      }
    }

    if (_onTerminate) _onTerminate(reason);
  }

  /* ── Event handlers ── */
  function onVisibilityChange() {
    if (document.visibilityState === 'hidden') {
      terminate('tab_switch');
    }
  }

  function onBlur() {
    // small delay to avoid false positives from fullscreen transition
    setTimeout(() => {
      if (!document.fullscreenElement && _active) {
        terminate('window_blur');
      }
    }, 400);
  }

  function onFullscreenChange() {
    if (_active && !document.fullscreenElement) {
      terminate('fullscreen_exit');
    }
  }

  function blockCopy(e) { e.preventDefault(); return false; }

  function blockKeys(e) {
    const blocked = [
      e.ctrlKey && e.key === 'c',    // Copy
      e.ctrlKey && e.key === 'u',    // View source
      e.ctrlKey && e.key === 'p',    // Print
      e.ctrlKey && e.key === 's',    // Save
      e.ctrlKey && e.shiftKey && e.key === 'i', // DevTools
      e.ctrlKey && e.shiftKey && e.key === 'j', // DevTools
      e.key === 'F12',
      e.key === 'PrintScreen',
    ];
    if (blocked.some(Boolean)) { e.preventDefault(); return false; }
  }

  /* ── Public API ── */
  return {
    /**
     * Attach all anti-cheat listeners.
     * @param {string} sessionId  – The active session ID
     * @param {Function} callback – Called with (reason) when test is terminated
     */
    start(sessionId, callback) {
      _sessionId  = sessionId;
      _onTerminate = callback;
      _terminated  = false;
      _active      = true;

      document.addEventListener('visibilitychange',  onVisibilityChange);
      window.addEventListener('blur',                onBlur);
      document.addEventListener('fullscreenchange',  onFullscreenChange);
      document.addEventListener('copy',              blockCopy);
      document.addEventListener('cut',               blockCopy);
      document.addEventListener('paste',             blockCopy);
      document.addEventListener('contextmenu',       blockCopy);
      document.addEventListener('keydown',           blockKeys);
      window.addEventListener('beforeunload',        () => terminate('page_close'));
    },

    stop() {
      _active = false;
      document.removeEventListener('visibilitychange', onVisibilityChange);
      window.removeEventListener('blur',               onBlur);
      document.removeEventListener('fullscreenchange', onFullscreenChange);
      document.removeEventListener('copy',             blockCopy);
      document.removeEventListener('cut',              blockCopy);
      document.removeEventListener('paste',            blockCopy);
      document.removeEventListener('contextmenu',      blockCopy);
      document.removeEventListener('keydown',          blockKeys);
    },

    /** Request fullscreen on an element */
    async requestFullscreen(el) {
      try {
        if (el.requestFullscreen)           await el.requestFullscreen();
        else if (el.webkitRequestFullscreen) await el.webkitRequestFullscreen();
        else if (el.mozRequestFullScreen)    await el.mozRequestFullScreen();
        return true;
      } catch {
        return false;
      }
    },

    get isTerminated() { return _terminated; },
  };
})();

window.AntiCheat = AntiCheat;
