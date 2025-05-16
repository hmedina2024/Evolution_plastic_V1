document.addEventListener('DOMContentLoaded', function () {
    const collapseButtons = document.querySelectorAll('[data-bs-toggle="collapse"]');
    collapseButtons.forEach(button => {
      button.addEventListener('click', function (e) {
        const targetId = this.getAttribute('data-bs-target');
        const targetCollapse = document.querySelector(targetId);
        if (!targetCollapse.classList.contains('show')) {
          collapseButtons.forEach(otherButton => {
            const otherTargetId = otherButton.getAttribute('data-bs-target');
            const otherCollapse = document.querySelector(otherTargetId);
            if (otherCollapse && otherCollapse !== targetCollapse && otherCollapse.classList.contains('show')) {
              const bsCollapse = new bootstrap.Collapse(otherCollapse);
              bsCollapse.hide();
            }
          });
        }
      });
    });
  });