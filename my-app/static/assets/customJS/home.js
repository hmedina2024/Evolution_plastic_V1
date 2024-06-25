const loaderOut = document.querySelector("#loader-out");
function fadeOut(element) {
  let opacity = 1;
  const timer = setInterval(function () {
    if (opacity <= 0.1) {
      clearInterval(timer);
      element.style.display = "none";
    }
    element.style.opacity = opacity;
    opacity -= opacity * 0.1;
  }, 50);
}
fadeOut(loaderOut);

function eliminarEmpleado(id_empleado, foto_empleado) {
  if (confirm("¿Estas seguro que deseas Eliminar el empleado?")) {
    let url = `/borrar-empleado/${id_empleado}/${foto_empleado}`;
    if (url) {
      window.location.href = url;
    }
  }
}

function eliminarProceso(id_proceso) {
  if (confirm("¿Estas seguro que deseas Eliminar el proceso?")) {
    let url = `/borrar-proceso/${id_proceso}`;
    if (url) {
      window.location.href = url;
    }
  }
}

function eliminarCliente(id_cliente , foto_cliente) {
  if (confirm("¿Estas seguro que deseas Eliminar el Cliente?")) {
    let url = `/borrar-cliente/${id_cliente}/${foto_cliente}`;
    if (url) {
      window.location.href = url;
    }
  }
}

function eliminarActividad(id_actividad) {
  if (confirm("¿Estas seguro que deseas Eliminar la actividad?")) {
    let url = `/borrar-actividad/${id_actividad}`;
    if (url) {
      window.location.href = url;
    }
  }
}

function eliminarOperacion(id_operacion) {
  if (confirm("¿Estas seguro que deseas Eliminar la operacion?")) {
    let url = `/borrar-operacion/${id_operacion}`;
    if (url) {
      window.location.href = url;
    }
  }
}

function eliminarJornada(id_jornada) {
  if (confirm("¿Estas seguro que deseas Eliminar la Jornada?")) {
    let url = `/borrar-jornada/${id_jornada}`;
    if (url) {
      window.location.href = url;
    }
  }
}

function eliminarOp(id_op) {
  if (confirm("¿Estas seguro que deseas Eliminar la oop?")) {
    let url = `/borrar-op/${id_op}`;
    if (url) {
      window.location.href = url;
    }
  }
}
