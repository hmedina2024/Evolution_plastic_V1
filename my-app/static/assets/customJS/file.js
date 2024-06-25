/**
 *
 * General vista previa de imagen perfil cargada
 */
function readURL(input) {
  if (input.files && input.files[0]) {
    var imageUrl = URL.createObjectURL(input.files[0]);
    $("#imagePreview").css("background-image", "url(" + imageUrl + ")");
    $("#imagePreview").hide();
    $("#imagePreview").fadeIn(650);
  }
}

$("#imageUpload").change(function () {
  readURL(this);
});

/**
 * Formatear Documento
 */
let camposNumericos = document.querySelectorAll("#documento, #cantidad, #telefono");

if (camposNumericos) {
  camposNumericos.forEach(campo => {
    campo.addEventListener("input", (inputEvent) => {
      let valor = inputEvent.target.value.replace(/\D/g, ""); // Eliminar caracteres no numéricos
      valor = parseInt(valor, 10); // Convertir a número entero
      if (isNaN(valor)) {
        valor = 0; // Si no se puede convertir a número, se establece en 0
      }
      // Asignar el valor sin formato al campo de entrada
      inputEvent.target.value = valor.toString();
    });
  });
}


