/* ============================================================
   Ken Ingram Personal Website — main.js
   ============================================================ */

(function () {
  'use strict';

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
      navLinks.classList.toggle('open');
    });
    // Close on link click
    navLinks.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => navLinks.classList.remove('open'));
    });
  }

  /* ── Scroll reveal (IntersectionObserver) ── */
  const reveals = document.querySelectorAll('.timeline-item, .testimonial-card');
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

  /* ── Contact form ── */
  const form = document.getElementById('contactForm');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const btn = form.querySelector('.form-submit');
      const orig = btn.textContent;
      btn.textContent = 'Sent ✓';
      btn.style.background = '#C5973E';
      btn.disabled = true;
      setTimeout(() => {
        btn.textContent = orig;
        btn.style.background = '';
        btn.disabled = false;
        form.reset();
      }, 3500);
    });
  }

  /* ── Smooth active nav highlight ── */
  const sections = document.querySelectorAll('section[id]');
  const navAs    = document.querySelectorAll('.nav-links a');
  const sectionObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          navAs.forEach(a => {
            a.style.color = '';
            if (a.getAttribute('href') === '#' + entry.target.id) {
              // subtle active indicator handled via CSS only to keep it light
            }
          });
        }
      });
    },
    { rootMargin: '-40% 0px -40% 0px' }
  );
  sections.forEach(s => sectionObserver.observe(s));

})();
