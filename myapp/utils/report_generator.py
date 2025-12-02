import pandas as pd
import json
import ollama
from fpdf import FPDF, XPos, YPos
import re
import io
import os
from django.conf import settings

OLLAMA_MODEL = "gemma3:12b"

# =============================
# FUNCIÓN PDF UTF-8 (Se mantiene igual)
# =============================
def generar_pdf(titulo, contenido):
    # ... (Tu código de PDF se mantiene idéntico) ...
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fonts_dir = os.path.join(base_dir, 'static', 'fonts')
    try:
        pdf.add_font("DejaVu", "", os.path.join(fonts_dir, "DejaVuSans.ttf"))
        pdf.add_font("DejaVu", "B", os.path.join(fonts_dir, "DejaVuSans-Bold.ttf"))
        pdf.add_font("DejaVu", "I", os.path.join(fonts_dir, "DejaVuSans-Oblique.ttf"))
        font_family = "DejaVu"
    except Exception as e:
        print(f"⚠️ No se pudieron cargar las fuentes DejaVu: {e}")
        font_family = "Arial"
    pdf.set_font(font_family, "B", 16)
    pdf.cell(0, 12, titulo, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(8)
    contenido = contenido.replace(":-", ":\n-")
    contenido = re.sub(r"^\*\s+", "- ", contenido, flags=re.MULTILINE)
    lines = contenido.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(5)
            continue
        if line.startswith("## "):
            text = line.replace("## ", "")
            pdf.set_font(font_family, "B", 14)
            pdf.multi_cell(190, 10, text=text)
            pdf.ln(2)
            pdf.set_font(font_family, "", 12)
            continue
        if line.startswith("### "):
            text = line.replace("### ", "")
            pdf.set_font(font_family, "I", 12)
            pdf.multi_cell(190, 9, text=text)
            pdf.ln(2)
            pdf.set_font(font_family, "", 12)
            continue
        if line.startswith("- "):
            bullet = "• "
            text = line[2:].strip()
            pdf.set_x(20)
            pdf.set_font(font_family, "", 12)
            pdf.write(8, bullet)
            if "**" in text:
                parts = re.split(r"(\*\*(?:.*?)\*\*)", text)
                for part in parts:
                    if part.startswith("**") and part.endswith("**"):
                        pdf.set_font(font_family, "B", 12)
                        pdf.write(8, part.strip("**"))
                        pdf.set_font(font_family, "", 12)
                    else:
                        pdf.write(8, part)
            else:
                pdf.write(8, text)
            pdf.ln(8)
            continue
        if "**" in line:
            parts = re.split(r"(\*\*(?:.*?)\*\*)", line)
            pdf.set_font(font_family, "", 12)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    pdf.set_font(font_family, "B", 12)
                    pdf.write(8, part.strip("**"))
                    pdf.set_font(font_family, "", 12)
                else:
                    pdf.write(8, part)
            pdf.ln(8)
            continue
        pdf.set_font(font_family, "", 12)
        pdf.multi_cell(190, 8, text=line)
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# =============================
# FUNCIONES AUXILIARES (Se mantienen igual)
# =============================
def analizar_evolucion_detallada(valores):
    if len(valores) < 2:
        return "No hay suficientes datos para analizar evolución."
    if len(valores) == 2:
        if valores[1] > valores[0] + 0.1:
            return "Mejoró en el segundo trimestre."
        elif valores[1] < valores[0] - 0.1:
            return "Empeoró en el segundo trimestre."
        else:
            return "Se mantuvo estable entre ambos trimestres."
    T1, T2, T3 = valores
    if T2 > T1 and T3 > T2:
        return "Mejoró de forma continua en los tres trimestres."
    elif T2 < T1 and T3 < T2:
        return "Empeoró de forma continua a lo largo de los tres trimestres."
    elif T2 > T1 and T3 < T2:
        return "Mejoró en el segundo trimestre pero decayó en el último."
    elif T2 < T1 and T3 > T2:
        return "Empezó con una calificacion, bajo en el segundo trimestre pero mostró recuperación en el último."
    elif abs(T1 - T2) <= 0.1 and abs(T2 - T3) <= 0.1:
        return "Se mantuvo estable durante los tres trimestres."
    else:
        return "Mostró un rendimiento variable con altibajos."

# =============================
# REPORTE GRUPAL (ESTA ES LA PARTE MODIFICADA)
# =============================
def generar_reporte_grupal_completo(hojas):
    reportes = {}
    promedios_trimestres = {}
    componentes_por_trimestre = {}

    # -------------------------------------------------------------------------
    # ### NUEVO CÓDIGO: CÁLCULO ACUMULADO GLOBAL
    # Unificamos todos los trimestres para sacar el promedio real hasta la fecha
    # -------------------------------------------------------------------------
    datos_consolidados = []
    
    for nombre, df in hojas.items():
        # Extraemos solo nombre y nota, renombramos la nota al nombre del trimestre
        temp = df[["APELLIDOS/NOMBRES", "Nota Trimemestre"]].copy()
        temp = temp.set_index("APELLIDOS/NOMBRES")
        temp = temp.rename(columns={"Nota Trimemestre": nombre})
        datos_consolidados.append(temp)

    # Variables globales por defecto
    total_aprobados_acum = 0
    total_reprobados_acum = 0
    lista_reprobados = []

    if datos_consolidados:
        # Unimos las columnas de todos los trimestres alineando por estudiante
        df_global = pd.concat(datos_consolidados, axis=1)
        
        # Calculamos promedio acumulado (ignora celdas vacías automáticamente)
        df_global["Promedio_Acumulado"] = df_global.mean(axis=1)
        
        # Contamos aprobados y reprobados sobre el promedio total
        total_aprobados_acum = int((df_global["Promedio_Acumulado"] >= 7).sum())
        total_reprobados_acum = int((df_global["Promedio_Acumulado"] < 7).sum())
        
        # Obtenemos la lista de nombres de los reprobados
        lista_reprobados = df_global[df_global["Promedio_Acumulado"] < 7].index.tolist()
    # -------------------------------------------------------------------------

    # Iteramos cada trimestre para el reporte individual
    for nombre, df in hojas.items():
        resumen = {}

        resumen["promedio_general"] = round(df["Nota Trimemestre"].mean(), 2)

        top3 = df.nlargest(3, "Nota Trimemestre")[["APELLIDOS/NOMBRES", "Nota Trimemestre"]]
        resumen["Buen rendimiento"] = top3.to_dict(orient="records")

        bottom3 = df.nsmallest(3, "Nota Trimemestre")[["APELLIDOS/NOMBRES", "Nota Trimemestre"]]
        resumen["Bajo rendimiento"] = bottom3.to_dict(orient="records")

        resumen["total_faltas_injustificadas"] = int(df["Falta Injustificada"].fillna(0).sum())
        resumen["total_faltas_justificadas"] = int(df["Falta Justificada"].fillna(0).sum())

        faltas_detalle = df[["APELLIDOS/NOMBRES", "Falta Injustificada", "Falta Justificada"]].fillna(0)
        faltas_detalle = faltas_detalle[
            (faltas_detalle["Falta Injustificada"] > 0) |
            (faltas_detalle["Falta Justificada"] > 0)
        ]
        resumen["faltas_por_estudiante"] = faltas_detalle.to_dict(orient="records")

        mal_comportamiento = df[df["Comportamiento"] == "F"]["APELLIDOS/NOMBRES"].tolist()
        resumen["estudiantes_mal_comportamiento"] = mal_comportamiento
        resumen["total_mal_comportamiento"] = len(mal_comportamiento)

        componentes = ["Aporte Individual", "Aporte Grupal", "Proyecto", "Examen"]
        resumen["componentes_promedio"] = df[componentes].mean().round(2).to_dict()

        reportes[nombre] = resumen
        promedios_trimestres[nombre] = resumen["promedio_general"]
        componentes_por_trimestre[nombre] = resumen["componentes_promedio"]

    # Análisis de evolución
    orden_trimestres = list(hojas.keys())
    evolucion = {}

    valores_prom = [promedios_trimestres[t] for t in orden_trimestres if t in promedios_trimestres]
    if len(valores_prom) >= 2:
        evolucion["promedio_general"] = analizar_evolucion_detallada(valores_prom)

    for comp in ["Aporte Individual", "Aporte Grupal", "Proyecto", "Examen"]:
        valores = [componentes_por_trimestre[t][comp] for t in orden_trimestres if t in componentes_por_trimestre]
        if len(valores) >= 2:
            evolucion[comp] = analizar_evolucion_detallada(valores)

    # Fortalezas/debilidades globales
    componentes_global = {comp: [] for comp in ["Aporte Individual", "Aporte Grupal", "Proyecto", "Examen"]}
    for t in componentes_por_trimestre:
        for comp, val in componentes_por_trimestre[t].items():
            componentes_global[comp].append(val)

    fortalezas, debilidades = [], []
    for comp, valores in componentes_global.items():
        if valores:
            promedio = sum(valores) / len(valores)
            if promedio >= 8.5:
                fortalezas.append(comp)
            elif promedio <= 6.5:
                debilidades.append(comp)

    return {
        # ### NUEVO: Agregamos la sección global al principio del reporte
        "estatus_academico_acumulado": {
            "total_aprobados": total_aprobados_acum,
            "total_reprobados": total_reprobados_acum,
            "estudiantes_en_riesgo": lista_reprobados # Lista de nombres
        },
        "reportes_trimestrales": reportes,
        "analisis_evolucion_grupal": evolucion,
        "fortalezas_debilidades_grupales": {
            "fortalezas": fortalezas,
            "debilidades": debilidades
        }
    }

# =============================
# REPORTE INDIVIDUAL (Se mantiene igual)
# =============================
def reporte_individual(nombre_estudiante, hojas):
    reporte = {
        "nombre": nombre_estudiante,
        "trimestres": {},
        "analisis_evolucion": {},
        "fortalezas_debilidades": {}
    }

    # Guardar datos por trimestre
    for trimestre, df in hojas.items():
        fila = df[df["APELLIDOS/NOMBRES"] == nombre_estudiante]

        if fila.empty:
            reporte["trimestres"][trimestre] = "No se encontraron datos"
            continue

        fila = fila.iloc[0]

        reporte["trimestres"][trimestre] = {
            "nota_final": float(fila["Nota Trimemestre"]),
            "cualitativa": fila["Cualitativa"],
            "componentes": {
                "aporte_individual": float(fila["Aporte Individual"]),
                "aporte_grupal": float(fila["Aporte Grupal"]),
                "proyecto": float(fila["Proyecto"]),
                "examen": float(fila["Examen"])
            },
            "faltas": {
                "injustificadas": int(fila["Falta Injustificada"]) if not pd.isna(fila["Falta Injustificada"]) else 0,
                "justificadas": int(fila["Falta Justificada"]) if not pd.isna(fila["Falta Justificada"]) else 0
            },
            "comportamiento": fila["Comportamiento"]
        }

    # ANÁLISIS DE EVOLUCIÓN DETALLADA
    orden_trimestres = list(hojas.keys())

    # Evolución de nota final
    notas = [
        reporte["trimestres"][t]["nota_final"]
        for t in orden_trimestres
        if isinstance(reporte["trimestres"][t], dict)
    ]

    if len(notas) >= 2:
        reporte["analisis_evolucion"]["nota_final"] = analizar_evolucion_detallada(notas)

    # Evolución de componentes
    componentes_valores = {
        comp: [] for comp in ["aporte_individual", "aporte_grupal", "proyecto", "examen"]
    }

    for t in orden_trimestres:
        if isinstance(reporte["trimestres"][t], dict):
            for comp, val in reporte["trimestres"][t]["componentes"].items():
                componentes_valores[comp].append(val)

    for comp, valores in componentes_valores.items():
        if len(valores) >= 2:
            reporte["analisis_evolucion"][comp] = analizar_evolucion_detallada(valores)

    # FORTALEZAS Y DEBILIDADES
    fortalezas = []
    debilidades = []

    for comp, valores in componentes_valores.items():
        if valores:
            promedio = sum(valores) / len(valores)
            if promedio >= 8.5:
                fortalezas.append(comp)
            elif promedio <= 6.5:
                debilidades.append(comp)

    reporte["fortalezas_debilidades"] = {
        "fortalezas": fortalezas,
        "debilidades": debilidades
    }

    return reporte