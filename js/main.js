/* ============================================================
   Ken Ingram Personal Website — main.js
   ============================================================ */

(function () {
  'use strict';

  /* ── Tagline — single source of truth, injected into hero + footer ── */
  var TAGLINE_ITEMS = ['AI Enablement', 'Technology Transformation', 'Innovation'];
  var taglineText   = TAGLINE_ITEMS.map(function(s) { return s.toUpperCase(); }).join('\u00A0\u00B7\u00A0');
  document.querySelectorAll('.site-tagline').forEach(function(el) { el.textContent = taglineText; });

  /* ── Sticky nav ── */
  const nav = document.querySelector('.nav');
  function onScroll() {
    nav.classList.toggle('scrolled', window.scrollY > 60);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ── Mobile hamburger ── */
  const hamburger = document.querySelector('.nav-hamburger');
  const navLinks  = document.querySelector('.nav-links');
  if (hamburger && navLinks) {
    hamburger.addEventListener('click', () => {
      const expanded = navLinks.classList.toggle('open');
      hamburger.setAttribute('aria-expanded', expanded);
    });
    // Close on link click
    navLinks.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => navLinks.classList.remove('open'));
    });
  }

  /* ── Scroll reveal (IntersectionObserver) ── */
  const reveals = document.querySelectorAll('.timeline-item');
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15 }
    );
    reveals.forEach(el => observer.observe(el));
  } else {
    // Fallback for older browsers
    reveals.forEach(el => el.classList.add('visible'));
  }

  /* ── Staggered entrance for timeline items ── */
  document.querySelectorAll('.timeline-item').forEach((item, i) => {
    item.style.transitionDelay = `${i * 0.12}s`;
  });

  /* ── Contact form → Google Forms ── */
  // Replace these entry IDs with the real ones from your Google Form.
  // How to find them: open the form, Ctrl+U (View Source), search "entry."
  const GF_URL        = 'https://docs.google.com/forms/d/e/1FAIpQLSc2xtz6sCfgTkT1JLH0V38SHulCt4FrZ5h2VNRlVKLh50P8CQ/formResponse';
  const GF_NAME       = 'entry.1430970630';
  const GF_EMAIL      = 'entry.593472319';
  const GF_SUBJECT    = 'entry.1226788542';
  const GF_MESSAGE    = 'entry.1989302050';

  const form = document.getElementById('contactForm');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const btn  = form.querySelector('.form-submit');
      const data = new FormData();
      data.append(GF_NAME,    form.querySelector('#name').value);
      data.append(GF_EMAIL,   form.querySelector('#email').value);
      data.append(GF_SUBJECT, form.querySelector('#subject').value);
      data.append(GF_MESSAGE, form.querySelector('#message').value);

      btn.textContent = 'Sending…';
      btn.disabled    = true;

      fetch(GF_URL, { method: 'POST', mode: 'no-cors', body: data })
        .then(() => {
          btn.textContent      = 'Sent ✓';
          btn.style.background = 'var(--stone)';
          form.reset();
          setTimeout(() => {
            btn.textContent      = 'Send Message';
            btn.style.background = '';
            btn.disabled         = false;
          }, 3500);
        })
        .catch(() => {
          btn.textContent = 'Send Message';
          btn.disabled    = false;
          alert('Something went wrong — please try emailing directly.');
        });
    });
  }

  /* ── Footer year ── */
  const yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

})();
