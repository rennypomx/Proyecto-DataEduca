import json


def get_prompt_reporte_grupal(json_data):
    """
    Genera el prompt para reportes grupales.
    
    Enfoque: Análisis colectivo del grupo con métricas agregadas.
    """
    prompt = (
        "Eres un experto en análisis de datos educativos y pedagógicos. "
        "Recibirás información de un grupo de estudiantes en formato JSON con calificaciones y métricas de desempeño académico.\n\n"
        "Tu tarea es generar un reporte narrativo grupal en español, claro, conciso y profesional, dirigido a docentes y directivos académicos. "
        "El informe debe estar organizado en secciones con títulos claros, redactados en párrafos fluidos, interpretativos y formales.\n\n"
        "Incluye obligatoriamente esta estructura en el documento:\n"
        "1. Título del reporte grupal.\n"
        "2. Objetivo del análisis.\n"
        "3. Resumen de desempeño general.\n"
        "4. Estudiantes destacados y con bajo desempeño (tres mejores y tres en riesgo, explicando diferencias).\n"
        "5. Estudiantes aprobados y reprobados.\n"
        "6. Análisis de componentes de evaluación: Aporte Individual, Aporte Grupal, Proyecto y Examen.\n"
        "7. Comportamiento y asistencia: patrones generales, impacto en rendimiento, totales de faltas (destacando casos relevantes).\n"
        "8. Comparación general entre estudiantes: mejoras, caídas y tendencias grupales.\n"
        "9. Fortalezas y debilidades grupales: aspectos positivos comunes y debilidades colectivas.\n"
        "10. Recomendaciones pedagógicas prácticas y constructivas.\n\n"
        f"Datos del grupo:\n{json.dumps(json_data, ensure_ascii=False, indent=2)}"
    )
    return prompt


def get_prompt_reporte_individual(json_data, nombre_estudiante):
    """
    Genera el prompt para reportes individuales.
    
    Enfoque: Análisis personalizado del desempeño de un estudiante específico.
    """
    prompt = (
        "Eres un experto en análisis de datos educativos y pedagógicos. "
        "Recibirás información de un estudiante en formato JSON, con calificaciones y métricas de desempeño académico.\n\n"
        "Tu tarea es generar un reporte narrativo en español, claro, conciso y profesional, dirigido a docentes y directivos académicos. "
        "El informe debe estar organizado en secciones con títulos claros, redactados en párrafos fluidos, interpretativos y formales.\n\n"
        "Incluye obligatoriamente esta estructura en el documento:\n"
        "1. Título y nombre del estudiante.\n"
        "2. Objetivo del análisis.\n"
        "3. Resumen de desempeño general: promedio final y valoración cualitativa.\n"
        "4. Evolución académica en los trimestres: mejoras, caídas, patrones de progreso o retroceso.\n"
        "5. Análisis por componentes: Aporte Individual, Aporte Grupal, Proyecto y Examen.\n"
        "6. Comportamiento y asistencia: evolución y su influencia en el rendimiento.\n"
        "7. Fortalezas y debilidades del estudiante: principales logros y áreas de mejora.\n"
        "8. Recomendaciones pedagógicas personalizadas y constructivas.\n\n"
        f"Datos del estudiante {nombre_estudiante}:\n{json.dumps(json_data, ensure_ascii=False, indent=2)}"
    )
    return prompt
