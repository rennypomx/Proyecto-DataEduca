from django.contrib import admin
from .models import ArchivoNotas, Estudiante, ReporteGenerado

@admin.register(ArchivoNotas)
class ArchivoNotasAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'usuario', 'fecha_subida')
    list_filter = ('fecha_subida', 'usuario')
    search_fields = ('nombre',)

@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'archivo')
    list_filter = ('archivo',)
    search_fields = ('nombre',)

@admin.register(ReporteGenerado)
class ReporteGeneradoAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'tipo', 'usuario', 'fecha_generacion')
    list_filter = ('tipo', 'fecha_generacion', 'usuario')
    search_fields = ('descripcion', 'estudiante')
    readonly_fields = ('fecha_generacion',)
