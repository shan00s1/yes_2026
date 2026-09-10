/**
 * NEXUS 2026 - Main Website & Landing Page Interactions
 */

document.addEventListener('DOMContentLoaded', () => {
  initCountdown();
  initScheduleTabs();
  initNavbarScroll();
});

// Countdown Timer to Summit Kickoff (Oct 24, 2026 09:00 AM)
function initCountdown() {
  const cdContainer = document.getElementById('summit-countdown') || document.getElementById('cd-days');
  if (!cdContainer) return;

  const targetDate = new Date('2026-10-24T09:00:00').getTime();

  function update() {
    const now = new Date().getTime();
    const distance = targetDate - now;

    if (distance <= 0) {
      document.getElementById('cd-days').textContent = '00';
      document.getElementById('cd-hours').textContent = '00';
      document.getElementById('cd-mins').textContent = '00';
      document.getElementById('cd-secs').textContent = '00';
      return;
    }

    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
    const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const mins = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    const secs = Math.floor((distance % (1000 * 60)) / 1000);

    const dEl = document.getElementById('cd-days');
    const hEl = document.getElementById('cd-hours');
    const mEl = document.getElementById('cd-mins');
    const sEl = document.getElementById('cd-secs');

    if (dEl) dEl.textContent = String(days).padStart(2, '0');
    if (hEl) hEl.textContent = String(hours).padStart(2, '0');
    if (mEl) mEl.textContent = String(mins).padStart(2, '0');
    if (sEl) sEl.textContent = String(secs).padStart(2, '0');
  }

  update();
  setInterval(update, 1000);
}

// Schedule Tabs Switcher
function initScheduleTabs() {
  const tabBtns = document.querySelectorAll('.schedule-tab-btn');
  const daySchedules = document.querySelectorAll('.day-schedule');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetDay = btn.getAttribute('data-day');

      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      daySchedules.forEach(schedule => {
        if (schedule.getAttribute('data-day') === targetDay) {
          schedule.style.display = 'flex';
        } else {
          schedule.style.display = 'none';
        }
      });
    });
  });
}

// Navbar subtle blur/shadow on scroll
function initNavbarScroll() {
  const nav = document.querySelector('.navbar');
  if (!nav) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 40) {
      nav.style.background = 'rgba(7, 10, 18, 0.95)';
      nav.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.5)';
    } else {
      nav.style.background = 'rgba(7, 10, 18, 0.85)';
      nav.style.boxShadow = 'none';
    }
  });
}
