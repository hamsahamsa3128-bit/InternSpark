/**
 * InternSpark - Internships Search & Modal Interactions
 */

document.addEventListener('DOMContentLoaded', () => {
  // Clear filters button
  const clearBtn = document.getElementById('clear-filters-btn');
  if (clearBtn) {
    clearBtn.addEventListener('click', (e) => {
      e.preventDefault();
      window.location.href = clearBtn.dataset.baseUrl || '/internships';
    });
  }

  // Populate Application Modal with internship data
  const applyButtons = document.querySelectorAll('.open-apply-modal-btn');
  const modalInternshipId = document.getElementById('modal-internship-id');
  const modalInternshipTitle = document.getElementById('modal-internship-title');
  const modalInternshipCompany = document.getElementById('modal-internship-company');

  applyButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const iId = btn.dataset.id;
      const title = btn.dataset.title;
      const company = btn.dataset.company;

      if (modalInternshipId) modalInternshipId.value = iId;
      if (modalInternshipTitle) modalInternshipTitle.textContent = title;
      if (modalInternshipCompany) modalInternshipCompany.textContent = company;

      window.openModal('applyModal');
    });
  });
});
