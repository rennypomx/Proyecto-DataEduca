from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"), 
    path("home/", views.home, name="home_alt"), 
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path('dashboard/', views.dashboard, name='inicio'),
    path("dashboard/upload/", views.upload_view, name="upload"),
    path('dashboard/get-estudiantes/<int:archivo_id>/', views.get_estudiantes, name='get_estudiantes'),
    path("dashboard/history/", views.history_view, name="history"),
    path("dashboard/get-reportes/", views.get_reportes, name="get_reportes"),
    path("dashboard/descargar-reporte/<int:reporte_id>/", views.descargar_reporte, name="descargar_reporte"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/procesar_reporte/", views.procesar_reporte, name="procesar_reporte"),
    # Rutas para manejo de archivos
    path("dashboard/get-archivo-activo/", views.get_archivo_activo, name="get_archivo_activo"),
    path("dashboard/mis-archivos/", views.listar_archivos, name="listar_archivos"),
    path("dashboard/activar-archivo/<int:archivo_id>/", views.activar_archivo, name="activar_archivo"),
    path("dashboard/eliminar-archivo/<int:archivo_id>/", views.eliminar_archivo, name="eliminar_archivo"),
    # Ruta para métricas dinámicas
    path("dashboard/get-metricas/", views.get_metricas, name="get_metricas"),
]
