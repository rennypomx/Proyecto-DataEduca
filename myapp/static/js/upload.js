// VERSION: 20251202 - Fix duplicación de uploads
console.log('=== upload.js CARGADO - VERSION 20251202 ===');

// =========================
// UPLOAD – AJAX REAL
// =========================

// Solo inicializar con spa:navigate para evitar duplicación
document.addEventListener("spa:navigate", initUploadPage);

function initUploadPage() {
  const page = document.querySelector('[data-page="upload"]');
  if (!page) return;

  console.log(" initUploadPage activo");

  const form = document.getElementById("upload-form");
  const inputFile = document.getElementById("file");
  const tipo = document.getElementById("tipo-reporte");
  const boxEstudiante = document.getElementById("select-estudiante");
  const selectEstudiante = document.getElementById("estudiante");
  const resultadoBox = document.getElementById("resultado");

  if (!form) {
    console.warn(" No se encontró #upload-form");
    return;
  }

  let archivoSubido = null;
  let estudiantesDisponibles = [];
  let archivoId = null;
  let tipoReporte = null;
  let estudianteSeleccionado = null;

  // Procesar archivo automáticamente cuando se selecciona
  if (inputFile) {
    inputFile.addEventListener("change", () => {
      archivoSubido = inputFile.files[0] || null;
      
      if (archivoSubido) {
        resultadoBox.innerHTML = "<p>Archivo seleccionado. Procesando automáticamente...</p>";
        procesarArchivoYExtraerEstudiantes();
      }
    });
  }

  // Mostrar/ocultar selector estudiante y regenerar JSON cuando cambia el tipo
  if (tipo && boxEstudiante) {
    tipo.addEventListener("change", () => {
      const tipoSeleccionado = tipo.value;
      
      if (tipoSeleccionado === "individual") {
        boxEstudiante.style.display = "block";
      } else {
        boxEstudiante.style.display = "none";
      }

    });
  }

  if (selectEstudiante) {
    selectEstudiante.addEventListener("change", () => {
      estudianteSeleccionado = selectEstudiante.value;
    });
  }
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    
    tipoReporte = tipo.value;
    estudianteSeleccionado = selectEstudiante.value;

    // Validaciones
    if (!archivoSubido) {
      resultadoBox.innerHTML = "<p>❌ Debes seleccionar un archivo Excel.</p>";
      return;
    }

    if (!tipoReporte) {
      resultadoBox.innerHTML = "<p>❌ Debes seleccionar un tipo de reporte.</p>";
      return;
    }

    if (tipoReporte === "individual" && !estudianteSeleccionado) {
      resultadoBox.innerHTML = "<p>❌ Debes seleccionar un estudiante para el reporte individual.</p>";
      return;
    }

    if (!archivoId) {
      resultadoBox.innerHTML = "<p>❌ Error: No se pudo procesar el archivo. Por favor, intenta de nuevo.</p>";
      return;
    }

    // Generar directamente el reporte narrativo con IA usando el archivo ya subido
    generarReporteNarrativo();
  });

  // Procesar archivo y extraer estudiantes (primera carga)
  function procesarArchivoYExtraerEstudiantes() {
    let formData = new FormData();
    formData.append("file", archivoSubido);
    formData.append("tipo", "grupal"); // Por defecto cargamos grupal
    formData.append("estudiante", "");

    resultadoBox.innerHTML = `
      <div style="text-align:center; padding:20px;">
        <h3>⏳ Procesando archivo...</h3>
        <p>Extrayendo datos y lista de estudiantes...</p>
      </div>
    `;

    fetch("/dashboard/upload/", {
      method: "POST",
      body: formData,
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.error) {
          resultadoBox.innerHTML = `<p>❌ Error: ${data.error}</p>`;
          return;
        }

        // Guardar datos
        if (data.estudiantes) {
          estudiantesDisponibles = data.estudiantes;
          archivoId = data.archivo_id;
          console.log("Archivo ID recibido:", archivoId);
        }

        // Actualizar select estudiantes
        if (Array.isArray(data.estudiantes) && data.estudiantes.length > 0) {
          selectEstudiante.innerHTML = '<option value="">Seleccionar...</option>';
          data.estudiantes.forEach((nombre) => {
            const opt = document.createElement("option");
            opt.value = nombre;
            opt.textContent = nombre;
            selectEstudiante.appendChild(opt);
          });
        }

        resultadoBox.innerHTML = `
          <h2 style="color:#4CAF50;">Archivo procesado correctamente</h2>
          <p style="margin:15px 0;">Se encontraron <strong>${data.estudiantes.length}</strong> estudiantes.</p>
          <p>Ahora selecciona el tipo de reporte y haz clic en "Subir y Generar Reporte" para crear el reporte narrativo con IA.</p>`;
      })
      .catch((err) => {
        console.error(err);
        resultadoBox.innerHTML = `
          <div style="padding:20px; background:#ffebee; border-radius:8px;">
            <h3>❌ Error al procesar archivo</h3>
            <p>${err}</p>
          </div>
        `;
      });
  }

  // PASO 2: Generar reporte narrativo con IA usando el archivo ya guardado
  function generarReporteNarrativo() {
    if (!archivoId) {
      resultadoBox.innerHTML = "<p>❌ Error: No se pudo obtener el ID del archivo. Por favor, vuelve a subir el archivo.</p>";
      console.error("archivoId no está definido:", archivoId);
      return;
    }

    console.log("Generando reporte con archivo_id:", archivoId);

    resultadoBox.innerHTML = `
      <div style="text-align:center; padding:20px;">
        <h3>⏳ Generando Reporte narrativo...</h3>
        <p style="color:#666;">Esto puede tardar entre 10-30 segundos.</p>
        <div style="margin-top:20px;">
          <div class="spinner" style="border:4px solid #f3f3f3; border-top:4px solid #3498db; border-radius:50%; width:40px; height:40px; animation:spin 1s linear infinite; margin:0 auto;"></div>
        </div>
      </div>
      <style>
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      </style>
    `;

    let formData = new FormData();
    // NO enviar json_data, que el backend lo genere desde el archivo
    formData.append("tipo", tipoReporte);
    formData.append("estudiante", estudianteSeleccionado);
    formData.append("archivo_id", archivoId);

    fetch("/dashboard/procesar_reporte/", {
      method: "POST",
      body: formData,
    })
      .then((res) => {
        console.log("Respuesta recibida, status:", res.status);
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        console.log("Datos recibidos:", data);
        if (data.error) {
          resultadoBox.innerHTML = `
            <div style="padding:20px; background:#ffebee; border-radius:8px;">
              <h3>❌ Error al generar reporte</h3>
              <p>${data.error}</p>
            </div>
          `;
          return;
        }

        // Mostrar resultado completo
        const tituloJson = tipoReporte === "individual" 
          ? "JSON de reporte individual"
          : "JSON de resumen grupal";

        // Botón "Ver métricas" solo para reportes grupales
        const botonMetricas = tipoReporte === "grupal" 
          ? `<button class="btn-primary" onclick="window.location.href='/dashboard/'" style="background:#015E80;">
               📊 Ver Métricas
             </button>`
          : '';

        resultadoBox.innerHTML = `
          <div style="margin-top:20px; padding:15px; background:#e8f5e9; border-radius:8px; border-left:4px solid #4CAF50;">
            <h3>¡Reporte Generado Exitosamente!</h3>
            <p style="margin:10px 0;">Tu reporte está listo. Puedes descargarlo o previsualizarlo:</p>
            <div style="display:flex; gap:10px; flex-wrap:wrap; margin-top:15px;">
              <button class="btn-success" onclick="descargarPDF('${data.pdf}', '${tipoReporte === 'individual' ? 'reporte_individual' : 'reporte_grupal'}')">
                📥 Descargar PDF
              </button>
              <button class="btn-primary" onclick="previsualizarPDF('${data.pdf}')">Previsualizar PDF
              </button>
              ${botonMetricas}
            </div>
          </div>`;

        resultadoBox.scrollIntoView({ behavior: "smooth", block: "start" });
      })
      .catch((err) => {
        console.error("Error completo:", err);
        resultadoBox.innerHTML = `
          <div style="padding:20px; background:#ffebee; border-radius:8px;">
            <h3>❌ Error inesperado</h3>
            <p><strong>Error:</strong> ${err.message}</p>
            <p style="margin-top:10px; color:#666;">Por favor verifica que:</p>
            <ul style="color:#666;">
              <li>El servidor Django esté corriendo</li>
              <li>Ollama esté corriendo (ejecuta: ollama list)</li>
              <li>El modelo gemma3:12b esté descargado</li>
              <li>Revisa la consola del navegador (F12) y del servidor para más detalles</li>
            </ul>
          </div>
        `;
      });
  }

  // Hacer la función accesible globalmente
  window.generarReporteNarrativo = generarReporteNarrativo;
}

// =========================
// FUNCIONES PARA PDF
// =========================

function descargarPDF(pdfBase64, nombreArchivo) {
  try {
    const byteCharacters = atob(pdfBase64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: "application/pdf" });
    
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `${nombreArchivo}_${new Date().toISOString().split('T')[0]}.pdf`;
    link.click();
    URL.revokeObjectURL(link.href);
  } catch (error) {
    console.error("Error al descargar PDF:", error);
    alert("Error al descargar el PDF");
  }
}

function previsualizarPDF(pdfBase64) {
  try {
    const byteCharacters = atob(pdfBase64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: "application/pdf" });
    
    const previewBox = document.getElementById("preview-box");
    const previewFrame = document.getElementById("preview-frame");
    
    if (previewBox && previewFrame) {
      previewFrame.src = URL.createObjectURL(blob);
      previewBox.style.display = "block";
      previewBox.scrollIntoView({ behavior: "smooth" });
    }
  } catch (error) {
    console.error("Error al previsualizar PDF:", error);
    alert("Error al previsualizar el PDF");
  }
}






