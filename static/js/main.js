// Arifa Women's Academy - JavaScript Core
// Dark/Light Mode, Bento interactions, Attendance helpers

function initCoreApp() {
  initTheme();
  initMobileNav();
  initAttendanceToggles();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initCoreApp);
} else {
  initCoreApp();
}

// Theme Management
function initTheme() {
  let savedTheme = 'light';
  try {
    savedTheme = localStorage.getItem('arifa_theme');
    if (!savedTheme) {
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        savedTheme = 'dark';
      } else {
        savedTheme = 'light';
      }
    }
  } catch (e) {
    savedTheme = 'light';
  }

  document.documentElement.setAttribute('data-theme', savedTheme);
  if (typeof updateThemeIcon === 'function') {
    updateThemeIcon(savedTheme);
  }
}

function updateThemeIcon(theme) {
  const themeBtn = document.getElementById('theme-toggle-btn');
  if (!themeBtn) return;
  if (theme === 'dark') {
    themeBtn.title = 'Switch to Light Mode';
    themeBtn.setAttribute('aria-label', 'Switch to Light Mode');
    themeBtn.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="5"></circle>
        <line x1="12" y1="1" x2="12" y2="3"></line>
        <line x1="12" y1="21" x2="12" y2="23"></line>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
        <line x1="1" y1="12" x2="3" y2="12"></line>
        <line x1="21" y1="12" x2="23" y2="12"></line>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
      </svg>`;
  } else {
    themeBtn.title = 'Switch to Dark Mode';
    themeBtn.setAttribute('aria-label', 'Switch to Dark Mode');
    themeBtn.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
      </svg>`;
  }
}

// Mobile Menu Navigation
function initMobileNav() {
  const toggleBtn = document.getElementById('mobile-menu-toggle');
  const drawer = document.getElementById('mobile-drawer');
  const backdrop = document.getElementById('mobile-backdrop');
  const closeBtn = document.getElementById('mobile-close-btn');

  if (toggleBtn && drawer && backdrop) {
    toggleBtn.addEventListener('click', () => {
      drawer.classList.add('open');
      backdrop.classList.add('open');
    });

    const closeMenu = () => {
      drawer.classList.remove('open');
      backdrop.classList.remove('open');
    };

    if (closeBtn) closeBtn.addEventListener('click', closeMenu);
    backdrop.addEventListener('click', closeMenu);
  }
}

// Attendance Sheet Interaction Helpers
function initAttendanceToggles() {
  // Individual Student Status Pill Clicks
  document.querySelectorAll('.attendance-toggle-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      const parent = this.closest('.attendance-toggle-group');
      const studentId = parent.dataset.studentId;
      const targetStatus = this.dataset.status;
      const hiddenInput = document.getElementById(`status_input_${studentId}`);

      // Reset active classes
      parent.querySelectorAll('.attendance-toggle-btn').forEach(b => {
        b.classList.remove('active-p', 'active-a', 'active-l');
      });

      // Apply active style
      if (targetStatus === 'PRESENT') this.classList.add('active-p');
      if (targetStatus === 'ABSENT') this.classList.add('active-a');
      if (targetStatus === 'LATE') this.classList.add('active-l');

      if (hiddenInput) {
        hiddenInput.value = targetStatus;
      }
      updateAttendanceSummaryCounters();
    });
  });

  // Bulk Quick Actions: Mark All Present
  const markAllPresentBtn = document.getElementById('btn-mark-all-present');
  if (markAllPresentBtn) {
    markAllPresentBtn.addEventListener('click', () => {
      document.querySelectorAll('.attendance-toggle-group').forEach(group => {
        const studentId = group.dataset.studentId;
        const hiddenInput = document.getElementById(`status_input_${studentId}`);
        group.querySelectorAll('.attendance-toggle-btn').forEach(b => b.classList.remove('active-p', 'active-a', 'active-l'));
        const pBtn = group.querySelector('[data-status="PRESENT"]');
        if (pBtn) pBtn.classList.add('active-p');
        if (hiddenInput) hiddenInput.value = 'PRESENT';
      });
      updateAttendanceSummaryCounters();
    });
  }

  // Bulk Quick Actions: Mark All Absent
  const markAllAbsentBtn = document.getElementById('btn-mark-all-absent');
  if (markAllAbsentBtn) {
    markAllAbsentBtn.addEventListener('click', () => {
      document.querySelectorAll('.attendance-toggle-group').forEach(group => {
        const studentId = group.dataset.studentId;
        const hiddenInput = document.getElementById(`status_input_${studentId}`);
        group.querySelectorAll('.attendance-toggle-btn').forEach(b => b.classList.remove('active-p', 'active-a', 'active-l'));
        const aBtn = group.querySelector('[data-status="ABSENT"]');
        if (aBtn) aBtn.classList.add('active-a');
        if (hiddenInput) hiddenInput.value = 'ABSENT';
      });
      updateAttendanceSummaryCounters();
    });
  }
}

function updateAttendanceSummaryCounters() {
  const inputs = document.querySelectorAll('.attendance-status-hidden');
  let p = 0, a = 0, l = 0;
  inputs.forEach(inp => {
    if (inp.value === 'PRESENT') p++;
    else if (inp.value === 'ABSENT') a++;
    else if (inp.value === 'LATE') l++;
  });

  const countP = document.getElementById('count-present');
  const countA = document.getElementById('count-absent');
  const countL = document.getElementById('count-late');

  if (countP) countP.textContent = p;
  if (countA) countA.textContent = a;
  if (countL) countL.textContent = l;
}
