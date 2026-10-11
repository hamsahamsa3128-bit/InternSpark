/**
 * InternSpark - Student Profile Enhancements
 */

document.addEventListener('DOMContentLoaded', () => {
  const resumeInput = document.getElementById('resume-upload');
  const fileNotice = document.getElementById('file-chosen-notice');

  if (resumeInput && fileNotice) {
    resumeInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;

      // 5 MB limit check
      const maxBytes = 5 * 1024 * 1024;
      if (file.size > maxBytes) {
        alert("The selected file exceeds 5MB. Please choose a smaller PDF or Word document.");
        resumeInput.value = "";
        fileNotice.textContent = "";
        return;
      }

      // Extension check
      const allowed = ['pdf', 'docx'];
      const ext = file.name.split('.').pop().toLowerCase();
      if (!allowed.includes(ext)) {
        alert("Only PDF (.pdf) and Word (.docx) files are supported for resumes.");
        resumeInput.value = "";
        fileNotice.textContent = "";
        return;
      }

      fileNotice.textContent = `Selected: ${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
    });
  }

  // Quick skill pills adder
  const skillChips = document.querySelectorAll('.skill-suggestion-chip');
  const skillsInput = document.getElementById('skills');

  if (skillsInput && skillChips.length > 0) {
    skillChips.forEach(chip => {
      chip.addEventListener('click', () => {
        const skillName = chip.dataset.skill;
        let current = skillsInput.value.trim();
        let currentList = current ? current.split(',').map(s => s.trim().toLowerCase()) : [];

        if (!currentList.includes(skillName.toLowerCase())) {
          if (current.length > 0 && !current.endsWith(',')) {
            skillsInput.value = current + ', ' + skillName;
          } else if (current.length > 0) {
            skillsInput.value = current + ' ' + skillName;
          } else {
            skillsInput.value = skillName;
          }
          chip.classList.add('selected');
        }
      });
    });
  }
});
