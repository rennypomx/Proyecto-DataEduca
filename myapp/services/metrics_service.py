"""
Servicio de cálculo de métricas para el dashboard.
Extrae la lógica de cálculo de métricas de las vistas para mejorar testabilidad.
"""

from ..models import ArchivoNotas, ReporteGenerado


class MetricsService:
    """
    Servicio para calcular métricas del dashboard.
    """
    
    @staticmethod
    def get_or_set_active_file(user):
        """
        Obtiene el archivo activo del usuario.
        Si no hay archivo activo, activa el más reciente.
        
        Args:
            user: Usuario de Django
            
        Returns:
            ArchivoNotas o None si no hay archivos
        """
        # Buscar archivo activo
        archivo = ArchivoNotas.objects.filter(usuario=user, activo=True).first()
        
        if not archivo:
            # Si no hay activo, tomar el más reciente
            archivo = ArchivoNotas.objects.filter(usuario=user).first()
            if archivo:
                archivo.activo = True
                archivo.save()
        
        return archivo
    
    @staticmethod
    def calculate_dashboard_metrics(archivo, user):
        """
        Calcula todas las métricas del dashboard para un archivo.
        
        Args:
            archivo: Instancia de ArchivoNotas con resumen_json
            user: Usuario de Django (para buscar reportes)
            
        Returns:
            dict: Diccionario con todas las métricas para el dashboard
        """
        if not archivo or not archivo.resumen_json:
            return {
                "sin_datos": True,
                "message": "No hay archivo activo con datos procesados"
            }
        
        # Extraer datos del resumen_json
        resumen = archivo.resumen_json
        reportes_trim = resumen.get("reportes_trimestrales", {})
        
        # Calcular métricas para las cards
        cards_data = MetricsService._calculate_card_metrics(reportes_trim, resumen, user)
        
        # Preparar datos para gráficas
        metricas = {
            "sin_datos": False,
            "cards": cards_data,
            "grafica_barras": MetricsService._prepare_bar_chart_data(reportes_trim),
            "grafica_dona": MetricsService._prepare_donut_chart_data(cards_data),
            "grafica_asistencia": MetricsService._prepare_attendance_chart_data(reportes_trim)
        }
        
        return metricas
    
    @staticmethod
    def _calculate_card_metrics(reportes_trim, resumen, user):
        """
        Calcula métricas para las tarjetas del dashboard.
        
        Args:
            reportes_trim: Diccionario de reportes trimestrales
            resumen: Resumen completo del JSON
            user: Usuario de Django
            
        Returns:
            dict: Métricas para cards (promedio, aprobados, reprobados, último reporte)
        """
        if reportes_trim:
            trimestres = list(reportes_trim.keys())
            
            # 1. Calcular promedio general de todos los trimestres
            promedios_trimestrales = [reportes_trim[t]["promedio_general"] for t in trimestres]
            promedio_general = sum(promedios_trimestrales) / len(promedios_trimestrales) if promedios_trimestrales else 0
            
            # 2. Obtener aprobados/reprobados del estatus acumulado
            estatus_acum = resumen.get("estatus_academico_acumulado", {})
            aprobados = estatus_acum.get("total_aprobados", 0)
            reprobados = estatus_acum.get("total_reprobados", 0)
        else:
            promedio_general = 0
            aprobados = 0
            reprobados = 0
        
        # Obtener fecha del último reporte grupal generado
        ultimo_reporte_grupal = ReporteGenerado.objects.filter(
            usuario=user,
            tipo='grupal'
        ).order_by('-fecha_generacion').first()
        
        fecha_ultimo_reporte = ultimo_reporte_grupal.fecha_generacion.strftime('%d/%m/%Y') if ultimo_reporte_grupal else 'Sin reportes'
        
        return {
            "promedio_general": round(promedio_general, 1),
            "aprobados": aprobados,
            "reprobados": reprobados,
            "ultimo_reporte": fecha_ultimo_reporte
        }
    
    @staticmethod
    def _prepare_bar_chart_data(reportes_trim):
        """
        Prepara datos para gráfica de barras de promedios por trimestre.
        
        Args:
            reportes_trim: Diccionario de reportes trimestrales
            
        Returns:
            dict: Datos para gráfica de barras
        """
        return {
            "labels": list(reportes_trim.keys()),
            "valores": [reportes_trim[t]["promedio_general"] for t in reportes_trim.keys()]
        }
    
    @staticmethod
    def _prepare_donut_chart_data(cards_data):
        """
        Prepara datos para gráfica de dona de aprobados/reprobados.
        
        Args:
            cards_data: Datos de las cards (contiene aprobados y reprobados)
            
        Returns:
            dict: Datos para gráfica de dona
        """
        return {
            "aprobados": cards_data["aprobados"],
            "reprobados": cards_data["reprobados"]
        }
    
    @staticmethod
    def _prepare_attendance_chart_data(reportes_trim):
        """
        Prepara datos para gráfica de asistencia por trimestre.
        
        Args:
            reportes_trim: Diccionario de reportes trimestrales
            
        Returns:
            dict: Datos para gráfica de asistencia
        """
        trimestres = list(reportes_trim.keys())
        
        if not trimestres:
            return {
                "labels": [],
                "faltas_justificadas": [],
                "faltas_injustificadas": []
            }
        
        labels_trimestres = []
        faltas_just = []
        faltas_injust = []
        
        for trimestre in trimestres:
            trim_data = reportes_trim[trimestre]
            labels_trimestres.append(trimestre)
            faltas_just.append(trim_data.get("total_faltas_justificadas", 0))
            faltas_injust.append(trim_data.get("total_faltas_injustificadas", 0))
        
        return {
            "labels": labels_trimestres,
            "faltas_justificadas": faltas_just,
            "faltas_injustificadas": faltas_injust
        }
