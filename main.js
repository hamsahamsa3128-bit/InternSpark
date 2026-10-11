/**
 * InternSpark - Core Client-Side Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Menu Toggle
  const mobileToggle = document.querySelector('.mobile-toggle');
  const mobileMenu = document.getElementById('mobile-menu');

  if (mobileToggle && mobileMenu) {
    mobileToggle.addEventListener('click', () => {
      const isExpanded = mobileToggle.getAttribute('aria-expanded') === 'true';
      mobileToggle.setAttribute('aria-expanded', !isExpanded);
      mobileMenu.classList.toggle('active');
    });
  }

  // 2. Alert Dismissal
  const alertCloses = document.querySelectorAll('.alert-close');
  alertCloses.forEach(btn => {
    btn.addEventListener('click', () => {
      const alert = btn.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        alert.style.transition = 'opacity 0.25s ease';
        setTimeout(() => alert.remove(), 250);
      }
    });
  });

  // 3. Modal System
  window.openModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
  };

  window.closeModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
      document.body.style.overflow = '';
    }
  };

  // Close modals when clicking overlay outside dialog
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  });

  // Keyboard accessibility: Escape closes modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.active').forEach(overlay => {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
      });
    }
  });

  // 4. AJAX Bookmark / Save Toggle (graceful enhancement)
  const saveForms = document.querySelectorAll('.ajax-save-form');
  saveForms.forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = form.querySelector('.save-btn');
      const icon = btn ? btn.querySelector('i') : null;
      const countBadge = document.getElementById('nav-saved-count');

      try {
        const formData = new FormData(form);
        const response = await fetch(form.action, {
          method: 'POST',
          body: formData,
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          }
        });

        if (response.ok) {
          const data = await response.json();
          if (data.status === 'ok') {
            if (data.action === 'saved') {
              if (icon) {
                icon.className = 'fa-solid fa-bookmark';
                btn.classList.add('text-primary');
              }
              if (countBadge) {
                countBadge.textContent = parseInt(countBadge.textContent || 0) + 1;
              }
            } else {
              if (icon) {
                icon.className = 'fa-regular fa-bookmark';
                btn.classList.remove('text-primary');
              }
              if (countBadge) {
                const cur = parseInt(countBadge.textContent || 0);
                if (cur > 0) countBadge.textContent = cur - 1;
              }
            }
          }
        } else {
          form.submit(); // fallback to normal submit
        }
      } catch (err) {
        form.submit(); // fallback
      }
    });
  });
});
