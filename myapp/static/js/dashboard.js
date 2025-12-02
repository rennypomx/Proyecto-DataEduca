// ======================================================
// SIDEBAR Y LAYOUT
// ======================================================
function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  const body = document.body;

  sidebar.classList.toggle("close");
  body.classList.toggle("sidebar-collapsed");

  const isClosed = sidebar.classList.contains("close");
  localStorage.setItem("sidebarClosed", isClosed ? "true" : "false");

  setTimeout(() => {
    window.dispatchEvent(new Event("resize"));
  }, 310);
}

document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.getElementById("sidebar");
  const body = document.body;
  const isClosed = localStorage.getItem("sidebarClosed") === "true";

  if (isClosed) {
    sidebar.classList.add("close");
    body.classList.add("sidebar-collapsed");
  }
});

// ======================================================
// Utility para destruir gráficos previos de Chart.js
// ======================================================
function destroyIfExists(id) {
  const chartNode = Chart.getChart(id);
  if (chartNode) chartNode.destroy();
}

// ======================================================
// DASHBOARD – Gráficas DINÁMICAS desde archivo activo
// ======================================================
function initCharts() {
  // Obtener canvas
  const chartBar = document.getElementById("chartBarras");
  const chartPie = document.getElementById("chartDona");
  const chartAsistencia = document.getElementById("chartAsistencia");

  if (!chartBar && !chartPie && !chartAsistencia) return;

  // Cargar métricas del archivo activo desde el backend
  fetch('/dashboard/get-metricas/')
    .then(response => response.json())
    .then(metricas => {
      if (metricas.sin_datos) {
        // Mostrar mensaje si no hay datos
        mostrarMensajeSinDatos();
        return;
      }

      // Actualizar cards
      actualizarCards(metricas.cards);

      // Generar gráficas
      generarGraficaBarras(chartBar, metricas.grafica_barras);
      generarGraficaDona(chartPie, metricas.grafica_dona);
      generarGraficaAsistencia(chartAsistencia, metricas.grafica_asistencia);
    })
    .catch(error => {
      console.error('Error al cargar métricas:', error);
      mostrarMensajeSinDatos();
    });
}

function actualizarCards(cards) {
  const cardPromedio = document.getElementById('card-promedio');
  const cardAprobados = document.getElementById('card-aprobados');
  const cardReprobados = document.getElementById('card-reprobados');
  const cardFecha = document.getElementById('card-fecha');

  if (cardPromedio) cardPromedio.textContent = cards.promedio_general;
  if (cardAprobados) cardAprobados.textContent = cards.aprobados;
  if (cardReprobados) cardReprobados.textContent = cards.reprobados;
  if (cardFecha) cardFecha.textContent = cards.ultimo_reporte;
}

function generarGraficaBarras(chartBar, datos) {
  if (!chartBar || !datos.labels || datos.labels.length === 0) return;

  destroyIfExists("chartBarras");

  // Colores dinámicos basados en cantidad de trimestres
  const colores = ["#015E80", "#24AB5A", "#FAA40E", "#E74C3C", "#9B59B6"];
  const backgroundColor = datos.labels.map((_, i) => colores[i % colores.length]);

  new Chart(chartBar.getContext("2d"), {
    type: "bar",
    data: {
      labels: datos.labels,
      datasets: [{
        label: "Promedio General",
        data: datos.valores,
        backgroundColor: backgroundColor,
        borderRadius: 5,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        title: { display: true, text: "Evolución del promedio", color: "#015E80" },
      },
      scales: { y: { beginAtZero: true, max: 10 } },
    },
  });
}

function generarGraficaDona(chartPie, datos) {
  if (!chartPie) return;

  destroyIfExists("chartDona");

  new Chart(chartPie.getContext("2d"), {
    type: "doughnut",
    data: {
      labels: ["Aprobados", "Reprobados"],
      datasets: [{
        data: [datos.aprobados, datos.reprobados],
        backgroundColor: ["#24AB5A", "#FAA40E"],
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: "bottom" },
        title: { display: true, text: "Distribución general del grupo", color: "#015E80" },
      },
    },
  });
}

function generarGraficaAsistencia(chartAsistencia, datos) {
  if (!chartAsistencia || !datos.labels || datos.labels.length === 0) return;

  destroyIfExists("chartAsistencia");

  new Chart(chartAsistencia.getContext("2d"), {
    type: "bar",
    data: {
      labels: datos.labels,
      datasets: [
        {
          label: "Justificadas",
          data: datos.faltas_justificadas,
          backgroundColor: "#24AB5A",
          borderRadius: 5,
        },
        {
          label: "Injustificadas",
          data: datos.faltas_injustificadas,
          backgroundColor: "#E74C3C",
          borderRadius: 5,
        }
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { 
          display: true,
          position: "top"
        },
      },
      scales: { 
        y: { 
          beginAtZero: true,
          title: {
            display: true,
            text: 'Cantidad de Faltas'
          }
        },
        x: {
          title: {
            display: true,
            text: ''
          }
        }
      },
    },
  });
}

function mostrarMensajeSinDatos() {
  const cards = document.querySelector('.cards');
  if (cards) {
    cards.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 40px; background: #fff3cd; border-radius: 8px;">
        <h3 style="color: #856404;">📂 No hay datos disponibles</h3>
        <p style="color: #856404;">Sube un archivo Excel para ver las métricas del grupo.</p>
        <a href="/dashboard/upload/" data-link style="display: inline-block; margin-top: 15px; padding: 10px 20px; background: #015E80; color: white; text-decoration: none; border-radius: 6px;">
          Subir Archivo
        </a>
      </div>
    `;
  }
}

// ======================================================
// UPLOAD PAGE – (OBSOLETO) Mantener por compatibilidad
// ======================================================
function initUploadPage() {
  // Ya NO se usa (upload.js maneja todo)
  // Pero lo dejamos vacío para evitar errores
}

// ======================================================
// FUNCIÓN GENERAL PARA CARGAS SPA
// ======================================================
function initPageContent() {
  const page = document.querySelector("[data-page]")?.dataset.page;

  if (page === "inicio") {
    initCharts();
  }
}

// ======================================================
// INICIALIZACIÓN GLOBAL
// ======================================================
document.addEventListener("DOMContentLoaded", initPageContent);
document.addEventListener("spa:navigate", initPageContent);
