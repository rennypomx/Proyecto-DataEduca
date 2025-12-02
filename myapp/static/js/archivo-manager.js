// ===================================================
// GESTOR DE ARCHIVOS PERSISTENTES
// ===================================================
console.log('=== archivo-manager.js CARGADO - VERSION 20251202 ===');

// Solo inicializar con spa:navigate para evitar duplicación
document.addEventListener("spa:navigate", initArchivoManager);

let archivoActivo = null;
let estudiantesDisponibles = [];

function initArchivoManager() {
  const page = document.querySelector('[data-page="upload"]');
  if (!page) return;

  console.log("📂 Inicializando gestor de archivos");

  // Cargar archivo activo al entrar a la página
  cargarArchivoActivo();

  // Event listeners
  setupEventListeners();
}

function setupEventListeners() {
  const btnVerArchivos = document.getElementById('btn-ver-archivos');
  const btnCambiarArchivo = document.getElementById('btn-cambiar-archivo');
  const btnCerrarLista = document.getElementById('btn-cerrar-lista');
  const formGenerar = document.getElementById('generar-form');
  const tipoReporteGenerar = document.getElementById('tipo-reporte-generar');

  if (btnVerArchivos) {
    btnVerArchivos.addEventListener('click', mostrarListaArchivos);
  }

  if (btnCambiarArchivo) {
    btnCambiarArchivo.addEventListener('click', () => {
      document.getElementById('archivo-actual-box').style.display = 'none';
      document.getElementById('form-generar-box').style.display = 'none';
      document.getElementById('form-upload-box').style.display = 'block';
    });
  }

  if (btnCerrarLista) {
    btnCerrarLista.addEventListener('click', () => {
      document.getElementById('lista-archivos-box').style.display = 'none';
    });
  }

  if (tipoReporteGenerar) {
    tipoReporteGenerar.addEventListener('change', () => {
      const boxEstudiante = document.getElementById('select-estudiante-generar');
      if (tipoReporteGenerar.value === 'individual') {
        boxEstudiante.style.display = 'block';
      } else {
        boxEstudiante.style.display = 'none';
      }
    });
  }

  if (formGenerar) {
    formGenerar.addEventListener('submit', (e) => {
      e.preventDefault();
      generarReporteDesdeArchivoActivo();
    });
  }
}

// Cargar archivo activo del usuario
function cargarArchivoActivo() {
  fetch('/dashboard/get-archivo-activo/')
    .then(res => res.json())
    .then(data => {
      if (data.archivo) {
        archivoActivo = data.archivo;
        estudiantesDisponibles = data.archivo.estudiantes;
        mostrarArchivoActivo();
      } else {
        // No hay archivos, mostrar formulario de subida
        document.getElementById('form-upload-box').style.display = 'block';
      }
    })
    .catch(err => {
      console.error('Error al cargar archivo activo:', err);
      document.getElementById('form-upload-box').style.display = 'block';
    });
}

// Mostrar información del archivo activo
function mostrarArchivoActivo() {
  const box = document.getElementById('archivo-actual-box');
  const formGenerarBox = document.getElementById('form-generar-box');
  const formUploadBox = document.getElementById('form-upload-box');

  document.getElementById('archivo-nombre').textContent = archivoActivo.nombre;
  document.getElementById('archivo-fecha').textContent = archivoActivo.fecha_subida;
  document.getElementById('archivo-num-estudiantes').textContent = estudiantesDisponibles.length;

  // Cargar estudiantes en el select
  const selectEstudiante = document.getElementById('estudiante-generar');
  selectEstudiante.innerHTML = '<option value="">Seleccionar...</option>';
  estudiantesDisponibles.forEach(nombre => {
    const opt = document.createElement('option');
    opt.value = nombre;
    opt.textContent = nombre;
    selectEstudiante.appendChild(opt);
  });

  // Mostrar UI
  box.style.display = 'block';
  formGenerarBox.style.display = 'block';
  formUploadBox.style.display = 'none';
}

// Mostrar lista de todos los archivos
function mostrarListaArchivos() {
  fetch('/dashboard/mis-archivos/')
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById('lista-archivos');
      const box = document.getElementById('lista-archivos-box');

      if (!data.archivos || data.archivos.length === 0) {
        container.innerHTML = '<p>No tienes archivos guardados.</p>';
      } else {
        let html = '';
        data.archivos.forEach(archivo => {
          const esActivo = archivo.activo ? 'activo' : '';
          const badge = archivo.activo ? '<span style="background:#4CAF50; color:white; padding:2px 8px; border-radius:4px; font-size:0.85em;">Activo</span>' : '';
          
          html += `
            <div class="archivo-item ${esActivo}">
              <div class="archivo-item-info">
                <strong>${archivo.nombre}</strong> ${badge}
                <br>
                <small style="color:#666;">
                  Subido: ${archivo.fecha_subida} | 
                  ${archivo.num_estudiantes} estudiantes | 
                  ${archivo.num_reportes} reportes
                </small>
              </div>
              <div class="archivo-item-actions">
                ${!archivo.activo ? `<button class="btn-secondary" onclick="activarArchivo(${archivo.id})">Activar</button>` : ''}
                <button class="btn-secondary" style="background:#f44336;" onclick="eliminarArchivo(${archivo.id}, '${archivo.nombre}')">Eliminar</button>
              </div>
            </div>
          `;
        });
        container.innerHTML = html;
      }

      box.style.display = 'block';
    })
    .catch(err => {
      console.error('Error al listar archivos:', err);
      alert('Error al cargar la lista de archivos');
    });
}

// Activar un archivo
window.activarArchivo = function(archivoId) {
  if (!confirm('¿Activar este archivo? Se usará para generar reportes.')) return;

  fetch(`/dashboard/activar-archivo/${archivoId}/`)
    .then(res => res.json())
    .then(data => {
      if (data.message) {
        alert(data.message);
        document.getElementById('lista-archivos-box').style.display = 'none';
        cargarArchivoActivo();
      } else if (data.error) {
        alert('Error: ' + data.error);
      }
    })
    .catch(err => {
      console.error('Error al activar archivo:', err);
      alert('Error al activar el archivo');
    });
};

// Eliminar un archivo
window.eliminarArchivo = function(archivoId, nombre) {
  if (!confirm(`¿Estás seguro de eliminar "${nombre}"? Esta acción no se puede deshacer.`)) return;

  fetch(`/dashboard/eliminar-archivo/${archivoId}/`)
    .then(res => res.json())
    .then(data => {
      if (data.message) {
        alert(data.message);
        mostrarListaArchivos(); // Recargar lista
        
        // Si era el archivo activo, recargar página
        if (archivoActivo && archivoActivo.id === archivoId) {
          location.reload();
        }
      } else if (data.error) {
        alert('Error: ' + data.error);
      }
    })
    .catch(err => {
      console.error('Error al eliminar archivo:', err);
      alert('Error al eliminar el archivo');
    });
};

// Generar reporte desde archivo activo
function generarReporteDesdeArchivoActivo() {
  const tipo = document.getElementById('tipo-reporte-generar').value;
  const estudiante = document.getElementById('estudiante-generar').value;
  const resultadoBox = document.getElementById('resultado');

  if (!tipo) {
    resultadoBox.innerHTML = '<p style="color:#f44336;">❌ Debes seleccionar un tipo de reporte.</p>';
    return;
  }

  if (tipo === 'individual' && !estudiante) {
    resultadoBox.innerHTML = '<p style="color:#f44336;">❌ Debes seleccionar un estudiante.</p>';
    return;
  }

  if (!archivoActivo) {
    resultadoBox.innerHTML = '<p style="color:#f44336;">❌ No hay archivo activo.</p>';
    return;
  }

  resultadoBox.innerHTML = `
    <div style="text-align:center; padding:20px;">
      <h3>⏳ Generando reporte...</h3>
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

  // Obtener JSON desde el backend (ya está guardado en resumen_json)
  fetch(`/dashboard/get-estudiantes/${archivoActivo.id}/`)
    .then(res => res.json())
    .then(data => {
      // Preparar datos para el reporte
      let formData = new FormData();
      formData.append('archivo_id', archivoActivo.id);
      formData.append('tipo', tipo);
      formData.append('estudiante', estudiante);

      // Llamar al endpoint de procesar reporte
      return fetch('/dashboard/procesar_reporte/', {
        method: 'POST',
        body: formData
      });
    })
    .then(res => {
      console.log("Respuesta recibida, status:", res.status);
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      return res.json();
    })
    .then(data => {
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

      // Botón "Ver métricas" solo para reportes grupales
      const botonMetricas = tipo === "grupal" 
        ? `<button class="btn-primary" onclick="window.location.href='/dashboard/'" style="background:#015E80;">
             📊 Ver Métricas
           </button>`
        : '';

      resultadoBox.innerHTML = `
        <div style="margin-top:20px; padding:15px; background:#e8f5e9; border-radius:8px; border-left:4px solid #4CAF50;">
          <h3>¡Reporte Generado Exitosamente!</h3>
          <p style="margin:10px 0;">Tu reporte está listo. Puedes descargarlo o previsualizarlo:</p>
          <div style="display:flex; gap:10px; flex-wrap:wrap; margin-top:15px;">
            <button class="btn-success" onclick="descargarPDF('${data.pdf}', '${tipo === 'individual' ? 'reporte_individual' : 'reporte_grupal'}')">
              📥 Descargar PDF
            </button>
            <button class="btn-primary" onclick="previsualizarPDF('${data.pdf}')">
              Previsualizar PDF
            </button>
            ${botonMetricas}
          </div>
        </div>
      `;

      resultadoBox.scrollIntoView({ behavior: "smooth", block: "start" });
    })
    .catch(err => {
      console.error('Error completo:', err);
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
