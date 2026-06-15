/**
 * Sistema de notificaciones (toasts) global para Evolution Control.
 * Reemplaza los alert() nativos por notificaciones no bloqueantes.
 *
 * API pública:
 *   showToast(mensaje, tipo, delay)   -> muestra un toast inmediatamente
 *   flashToast(mensaje, tipo)         -> guarda un toast para mostrarlo tras una redirección
 *
 * tipo: 'success' | 'danger' | 'warning' | 'info'  (por defecto 'info')
 */
(function () {
  'use strict';

  var ICONOS = {
    success: 'bi-check-circle-fill',
    danger:  'bi-x-circle-fill',
    warning: 'bi-exclamation-triangle-fill',
    info:    'bi-info-circle-fill'
  };

  var COLORES = {
    success: '#198754',
    danger:  '#dc3545',
    warning: '#ffc107',
    info:    '#0dcaf0'
  };

  function getContainer() {
    var c = document.getElementById('ec-toast-container');
    if (!c) {
      c = document.createElement('div');
      c.id = 'ec-toast-container';
      c.style.cssText =
        'position:fixed; top:1rem; right:1rem; z-index:11000; ' +
        'display:flex; flex-direction:column; gap:.5rem; max-width:380px;';
      document.body.appendChild(c);
    }
    return c;
  }

  window.showToast = function (mensaje, tipo, delay) {
    tipo = tipo || 'info';
    if (tipo === 'error') tipo = 'danger';          // alias de compatibilidad
    if (typeof delay !== 'number') delay = 4500;
    var icono = ICONOS[tipo] || ICONOS.info;
    var color = COLORES[tipo] || COLORES.info;

    var toast = document.createElement('div');
    toast.setAttribute('role', 'alert');
    toast.style.cssText =
      'background:#fff; border-left:5px solid ' + color + '; ' +
      'border-radius:8px; box-shadow:0 4px 18px rgba(0,0,0,.18); ' +
      'padding:.85rem 1rem; display:flex; align-items:flex-start; gap:.6rem; ' +
      'font-size:.95rem; color:#333; opacity:0; transform:translateX(40px); ' +
      'transition:opacity .25s ease, transform .25s ease;';

    var i = document.createElement('i');
    i.className = 'bi ' + icono;
    i.style.cssText = 'color:' + color + '; font-size:1.2rem; line-height:1.3; flex-shrink:0;';

    var texto = document.createElement('div');
    texto.style.cssText = 'flex:1; line-height:1.35;';
    texto.textContent = mensaje;

    var cerrar = document.createElement('button');
    cerrar.type = 'button';
    cerrar.innerHTML = '&times;';
    cerrar.setAttribute('aria-label', 'Cerrar');
    cerrar.style.cssText =
      'background:none; border:none; font-size:1.3rem; line-height:1; ' +
      'color:#999; cursor:pointer; padding:0 .2rem; flex-shrink:0;';

    toast.appendChild(i);
    toast.appendChild(texto);
    toast.appendChild(cerrar);
    getContainer().appendChild(toast);

    // animar entrada
    requestAnimationFrame(function () {
      toast.style.opacity = '1';
      toast.style.transform = 'translateX(0)';
    });

    var timer = null;
    function remover() {
      if (!toast.parentNode) return;
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(40px)';
      setTimeout(function () {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 250);
    }

    cerrar.addEventListener('click', function () {
      if (timer) clearTimeout(timer);
      remover();
    });

    if (delay > 0) timer = setTimeout(remover, delay);
    return toast;
  };

  /**
   * Guarda un toast en sessionStorage para mostrarlo después de una
   * redirección (window.location.href). Útil tras guardados AJAX exitosos.
   */
  window.flashToast = function (mensaje, tipo) {
    try {
      var pendientes = JSON.parse(sessionStorage.getItem('ec_pending_toasts') || '[]');
      pendientes.push({ mensaje: mensaje, tipo: tipo || 'info' });
      sessionStorage.setItem('ec_pending_toasts', JSON.stringify(pendientes));
    } catch (e) {
      // si sessionStorage falla, mostrar de inmediato como respaldo
      window.showToast(mensaje, tipo);
    }
  };

  /**
   * Red de seguridad: redirige cualquier alert() nativo restante a un toast.
   * Detecta el tipo según el contenido del mensaje.
   * (Los casos de "guardado + redirección" usan flashToast explícitamente.)
   */
  window.alert = function (mensaje) {
    var msg = String(mensaje == null ? '' : mensaje);
    var tipo = 'info';
    if (/error/i.test(msg)) {
      tipo = 'danger';
    } else if (msg.charAt(0) === 'ℹ' || msg.indexOf('ℹ️') === 0) {
      tipo = 'info';
    } else if (/por favor|debe |seleccione|complete|no se pueden|obligatori/i.test(msg)) {
      tipo = 'warning';
    }
    window.showToast(msg.replace(/^ℹ️?\s*/, ''), tipo);
  };

  // Al cargar cualquier página, renderizar toasts pendientes (de redirecciones).
  document.addEventListener('DOMContentLoaded', function () {
    try {
      var pendientes = JSON.parse(sessionStorage.getItem('ec_pending_toasts') || '[]');
      sessionStorage.removeItem('ec_pending_toasts');
      pendientes.forEach(function (t) { window.showToast(t.mensaje, t.tipo); });
    } catch (e) { /* ignorar */ }
  });
})();
