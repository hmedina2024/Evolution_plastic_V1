async function buscadorTable(tableId) {
  let input = document.getElementById("search");
  let busqueda = input.value.trim();
  let url = "/buscando-empleado";

  if (busqueda === "") {
      location.reload(); // Si el campo está vacío, recarga la página para restaurar la tabla original
      return;
  }

  const dataPeticion = { busqueda };
  const headers = {
      "Content-Type": "application/json"
  };

  try {
      const response = await axios.post(url, dataPeticion, { headers });

      if (response.data.fin === 0) {
          $(`#${tableId} tbody`).html(`
          <tr>
              <td colspan="7" style="text-align:center;color: red;font-weight: bold;">
                  No hay resultados para: <strong style="color: #222;">${busqueda}</strong>
              </td>
          </tr>`);
          return;
      }

      let empleados = response.data.data;
      let rows = "";

      empleados.forEach((empleado, index) => {
          rows += `
          <tr>
              <td>${index + 1}</td>
              <td>${empleado.documento}</td>
              <td>${empleado.nombre_empleado}</td>
              <td>${empleado.apellido_empleado}</td>
              <td>${empleado.tipo_empleado}</td>
              <td>${empleado.cargo}</td>
              <td width="10px">
                  <a href="/detalles-empleado/${empleado.id_empleado}" class="btn btn-info btn-sm">
                      <i class="bi bi-eye"></i> Ver detalles
                  </a>
                  <a href="/editar-empleado/${empleado.id_empleado}" class="btn btn-success btn-sm">
                      <i class="bi bi-arrow-clockwise"></i> Actualizar
                  </a>
                  <a href="#" onclick="eliminarEmpleado('${empleado.id_empleado}');" class="btn btn-danger btn-sm">
                      <i class="bi bi-trash3"></i> Eliminar
                  </a>
              </td>
          </tr>`;
      });

      $(`#${tableId} tbody`).html(rows);
      $(".pagination").hide(); // Oculta la paginación cuando se hace una búsqueda

  } catch (error) {
      console.error("Error en la búsqueda: ", error);
  }
}
