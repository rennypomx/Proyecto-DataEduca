// ======================================================
// SPA Router – Maneja navegación sin recargar toda la app
// ======================================================

// === Restaurar estado del sidebar (colapsado/abierto) ===
function restoreSidebar() {
  const sidebar = document.getElementById("sidebar");
  const body = document.body;
  const isClosed = localStorage.getItem("sidebarClosed") === "true";

  if (isClosed) {
    sidebar.classList.add("close");
    body.classList.add("sidebar-collapsed");
  }
}

// ======================================================
// Inicialización principal del router
// ======================================================
document.addEventListener("DOMContentLoaded", () => {
  restoreSidebar();

  const container = document.getElementById("main-content");
  const current = container.getAttribute("data-current-route") || window.location.pathname;

  // Si Django devolvió base.html pero sin el partial cargado, cargarlo manualmente
  if (!container.querySelector("[data-page]")) {
    loadPartial(current, false);
  }

  // Interceptar clics de navegación
  document.querySelectorAll('a[data-link]').forEach(a => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      loadPartial(a.getAttribute('href'), true);
    });
  });

  // Botón atrás/adelante del navegador
  window.addEventListener("popstate", () => {
    loadPartial(window.location.pathname, false);
  });
});

// ======================================================
// Cargar contenido dinámico (partials)
// ======================================================
function loadPartial(url, push = true) {
  const container = document.getElementById("main-content");
  container.innerHTML = '<p style="opacity:.7">⏳ Cargando...</p>';

  fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
    .then(res => {
      if (!res.ok) throw new Error(`Error ${res.status}`);
      return res.text();
    })
    .then(html => {
      container.innerHTML = html;

      // Actualizar URL visible
      if (push) {
        window.history.pushState({}, "", url);
      }

      // Evento global para dashboard.js & upload.js
      document.dispatchEvent(
        new CustomEvent("spa:navigate", { detail: { url } })
      );

      // Ejecutar inicializador auxiliar
      runPageInitializer();

      // Recalcular tamaño (charts, grids, etc.)
      setTimeout(() => window.dispatchEvent(new Event("resize")), 60);
    })
    .catch(err => {
      container.innerHTML = `
        <p style="color:#c00">
          ⚠️ No se pudo cargar el contenido.
        </p>`;
      console.error("SPA Error:", err);
    });
}

// ======================================================
// Inicializador auxiliar centralizado
// ======================================================
function runPageInitializer() {
  // Ya no es necesario llamar manualmente a las funciones init
  // porque cada archivo JS escucha el evento spa:navigate
  // Mantener esta función por si se necesita en el futuro
  const pageEl = document.querySelector('#main-content [data-page]');
  if (!pageEl) return;
  
  // Los módulos se inicializan automáticamente con spa:navigate
}
