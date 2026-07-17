document.addEventListener('DOMContentLoaded', function () {
    const collapseButtons = document.querySelectorAll('[data-bs-toggle="collapse"]');
    collapseButtons.forEach(button => {
      button.addEventListener('click', function (e) {
        const targetId = this.getAttribute('data-bs-target');
        const targetCollapse = targetId ? document.querySelector(targetId) : null;
        if (!targetCollapse) return;
        // Comportamiento acordeón: al abrir una sección, cierra las demás.
        // Importante: usar getOrCreateInstance con toggle:false para NO crear
        // instancias nuevas que corrompen el estado (causa de que el 2º clic
        // no colapsara). Bootstrap se encarga del toggle abrir/cerrar.
        if (!targetCollapse.classList.contains('show')) {
          collapseButtons.forEach(otherButton => {
            const otherTargetId = otherButton.getAttribute('data-bs-target');
            const otherCollapse = otherTargetId ? document.querySelector(otherTargetId) : null;
            if (otherCollapse && otherCollapse !== targetCollapse && otherCollapse.classList.contains('show')) {
              bootstrap.Collapse.getOrCreateInstance(otherCollapse, { toggle: false }).hide();
            }
          });
        }
      });
    });
  });

// ─────────────────────────────────────────────────────────────
// Acordeón del sidebar (control explícito, sin depender del
// data-api de Bootstrap, que el Menu de Sneat bloquea con
// stopPropagation). Maneja: abrir, CERRAR al reclic y cerrar
// las demás secciones al abrir una.
// ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  if (typeof bootstrap === 'undefined') return;
  const toggles = document.querySelectorAll('.snav-toggle');

  toggles.forEach(btn => {
    btn.addEventListener('click', function () {
      const sel = this.getAttribute('data-bs-target');
      const target = sel ? document.querySelector(sel) : null;
      if (!target) return;

      const estabaAbierto = target.classList.contains('show');

      // Cerrar las demás secciones abiertas
      toggles.forEach(other => {
        if (other === this) return;
        const osel = other.getAttribute('data-bs-target');
        const ot = osel ? document.querySelector(osel) : null;
        if (ot && ot.classList.contains('show')) {
          bootstrap.Collapse.getOrCreateInstance(ot, { toggle: false }).hide();
          other.setAttribute('aria-expanded', 'false');
        }
      });

      // Alternar la sección actual
      bootstrap.Collapse.getOrCreateInstance(target, { toggle: false }).toggle();
      this.setAttribute('aria-expanded', String(!estabaAbierto));
    });
  });
});
