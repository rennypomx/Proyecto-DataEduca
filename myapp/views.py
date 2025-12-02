from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
import pandas as pd
import json
import ollama
import httpx
import os
from .models import ArchivoNotas, Estudiante, ReporteGenerado
from .utils.report_generator import (
    generar_pdf,
    generar_reporte_grupal_completo,
    reporte_individual,
    OLLAMA_MODEL
)
from .prompts import get_prompt_reporte_grupal, get_prompt_reporte_individual


# === Página principal (landing pública) ===
def home(request):
    return render(request, "index.html")


# === Registro de usuario ===
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Las contraseñas no coinciden")
            return render(request, "register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya está en uso")
            return render(request, "register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "El correo ya está registrado")
            return render(request, "register.html")

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()
        messages.success(request, "Registro exitoso")
        return redirect("login")

    return render(request, "register.html")


# === Login ===
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect("upload")
        else:
            messages.error(request, "Credenciales incorrectas")

    return render(request, "login.html")


# === Dashboard ===
@login_required
def dashboard(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "Dashboard/partials/metricas.html")
    return render(request, "Dashboard/base.html")


# === Obtener métricas del archivo activo ===
@login_required
def get_metricas(request):
    """
    Devuelve las métricas del archivo activo para las gráficas del dashboard.
    """
    try:
        from .services import MetricsService
        
        # Obtener archivo activo usando el servicio
        archivo = MetricsService.get_or_set_active_file(request.user)
        
        # Calcular métricas usando el servicio
        metricas = MetricsService.calculate_dashboard_metrics(archivo, request.user)
        
        return JsonResponse(metricas)
        
    except Exception as e:
        return JsonResponse({"error": str(e), "sin_datos": True}, status=500)



# === Subida de archivos ===
@csrf_exempt
@login_required
def upload_view(request):
    if request.method == "POST":
        try:
            archivo = request.FILES.get("file")
            tipo = request.POST.get("tipo", "grupal")
            estudiante = request.POST.get("estudiante", "").strip()

            if not archivo:
                return JsonResponse({"error": "No se envió ningún archivo."}, status=400)

            # Guardar archivo en la base de datos
            nuevo_archivo = ArchivoNotas.objects.create(
                usuario=request.user,
                nombre=archivo.name,
                archivo=archivo
            )

            # Leer el Excel
            xls = pd.ExcelFile(nuevo_archivo.archivo.path)
            hojas = {sheet: pd.read_excel(xls, sheet) for sheet in xls.sheet_names}

            # Siempre calculamos resumen grupal (y lo guardamos)
            resumen_grupal = generar_reporte_grupal_completo(hojas)
            nuevo_archivo.resumen_json = resumen_grupal
            nuevo_archivo.save()

            # Extraer nombres de estudiantes (primera hoja)
            hoja_principal = pd.read_excel(xls, xls.sheet_names[0])
            nombres = hoja_principal["APELLIDOS/NOMBRES"].dropna().tolist()

            # Guardar en base de datos
            for nombre in nombres:
                Estudiante.objects.create(archivo=nuevo_archivo, nombre=nombre)

            # Decidir qué JSON devolver al frontend
            if tipo == "individual" and estudiante:
                json_data = reporte_individual(estudiante, hojas)
            else:
                # Por defecto (o si no se seleccionó estudiante) devolvemos el grupal
                json_data = resumen_grupal

            return JsonResponse({
                "message": "Archivo procesado correctamente.",
                "tipo": tipo,
                "archivo_id": nuevo_archivo.id,
                "estudiantes": nombres,
                "json_data": json_data,
            })

        except Exception as e:
            return JsonResponse({"error": f"Ocurrió un error al procesar el archivo: {str(e)}"}, status=500)

    # Renderizado parcial (SPA)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "Dashboard/partials/upload.html")

    return render(request, "Dashboard/base.html")


# === Obtener estudiantes ===
@login_required
def get_estudiantes(request, archivo_id):
    try:
        archivo = ArchivoNotas.objects.get(id=archivo_id, usuario=request.user)
        estudiantes = list(archivo.estudiantes.values_list("nombre", flat=True))
        return JsonResponse({"estudiantes": estudiantes})
    except ArchivoNotas.DoesNotExist:
        return JsonResponse({"error": "Archivo no encontrado"}, status=404)



# === Procesar reporte (IA + PDF) ===
@csrf_exempt
@login_required
def procesar_reporte(request):
    try:
        # Logging para debugging
        print("=" * 50)
        print("DEBUG procesar_reporte - POST data:")
        print(f"json_data presente: {bool(request.POST.get('json_data'))}")
        print(f"tipo: {request.POST.get('tipo')}")
        print(f"estudiante: {request.POST.get('estudiante')}")
        print(f"archivo_id: {request.POST.get('archivo_id')}")
        print("=" * 50)
        
        # Obtener datos del request
        json_data_str = request.POST.get("json_data")
        tipo = request.POST.get("tipo", "grupal")
        estudiante = request.POST.get("estudiante", "")
        archivo_id = request.POST.get("archivo_id")

        if not archivo_id:
            print("ERROR: No se recibió archivo_id")
            return JsonResponse({"error": "No se recibió el ID del archivo"}, status=400)

        # Obtener el archivo
        try:
            archivo = ArchivoNotas.objects.get(id=archivo_id, usuario=request.user)
        except ArchivoNotas.DoesNotExist:
            return JsonResponse({"error": "Archivo no encontrado"}, status=404)

        # Si no se proporciona JSON, generarlo desde el archivo guardado
        if not json_data_str:
            print("INFO: Generando JSON desde archivo guardado")
            
            # Leer el Excel
            xls = pd.ExcelFile(archivo.archivo.path)
            hojas = {sheet: pd.read_excel(xls, sheet) for sheet in xls.sheet_names}
            
            # Generar JSON según el tipo
            if tipo == "individual" and estudiante:
                json_data = reporte_individual(estudiante, hojas)
            else:
                # Usar el resumen guardado o generarlo
                if archivo.resumen_json:
                    json_data = archivo.resumen_json
                else:
                    json_data = generar_reporte_grupal_completo(hojas)
                    archivo.resumen_json = json_data
                    archivo.save()
        else:
            # Parsear el JSON proporcionado
            try:
                json_data = json.loads(json_data_str)
            except json.JSONDecodeError:
                return JsonResponse({"error": "El JSON recibido no es válido"}, status=400)

        # Definir el título del reporte
        if tipo == "individual" and estudiante:
            titulo_reporte = f"Reporte Individual - {estudiante}"
            descripcion = f"Reporte Individual - {estudiante}"
            prompt = get_prompt_reporte_individual(json_data, estudiante)
        else:
            titulo_reporte = "Reporte Grupal"
            descripcion = f"Reporte Grupal - {archivo.nombre}"
            prompt = get_prompt_reporte_grupal(json_data)

        try:
            # Primero verificar que Ollama esté disponible
            ollama.list()
            
            # Generar narrativa con el modelo configurado
            # Configurar cliente con timeout de 30 minutos para modelos grandes
            from ollama import Client
            client = Client(timeout=1800.0)  # 30 minutos de timeout
            
            respuesta = client.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.7}
            )
            narrativa = respuesta["message"]["content"]
        except (httpx.ConnectError, ConnectionError) as e:
            print(f"ERROR de conexión con Ollama: {type(e).__name__}: {str(e)}")
            narrativa = (
                "No se pudo conectar con Ollama para generar la narrativa con IA.\n\n"
                "Por favor, verifica que:\n"
                "1. Ollama esté instalado y ejecutándose\n"
                "2. El servicio de Ollama esté activo\n\n"
                "Puedes iniciar Ollama ejecutando 'ollama serve' en una terminal.\n\n"
                f"Datos del reporte:\n{json.dumps(json_data, ensure_ascii=False, indent=2)}"
            )
        except httpx.ReadTimeout as e:
            print(f"TIMEOUT al generar narrativa: {str(e)}")
            narrativa = (
                "El modelo de IA está tardando demasiado en generar la narrativa.\n\n"
                "Esto puede ocurrir con modelos grandes. Considera:\n"
                "1. Usar un modelo más pequeño (cambia OLLAMA_MODEL en report_generator.py)\n"
                "2. Esperar más tiempo o intentar nuevamente\n\n"
                f"Datos del reporte:\n{json.dumps(json_data, ensure_ascii=False, indent=2)}"
            )
        except Exception as e:
            print(f"ERROR inesperado al generar narrativa: {type(e).__name__}: {str(e)}")
            narrativa = (
                f"Error al generar narrativa con IA: {type(e).__name__}: {str(e)}\n\n"
                f"Datos del reporte:\n{json.dumps(json_data, ensure_ascii=False, indent=2)}"
            )

        # PDF
        pdf_buffer = generar_pdf(titulo_reporte, narrativa)
        pdf_bytes = pdf_buffer.read()

        # Guardar el reporte en la base de datos
        import base64
        from datetime import datetime
        
        # Crear nombre de archivo único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if tipo == "individual" and estudiante:
            pdf_filename = f"reporte_individual_{estudiante.replace(' ', '_')}_{timestamp}.pdf"
        else:
            pdf_filename = f"reporte_grupal_{timestamp}.pdf"

        # Crear el registro del reporte
        reporte = ReporteGenerado.objects.create(
            usuario=request.user,
            archivo=archivo,
            tipo=tipo,
            estudiante=estudiante if tipo == "individual" else None,
            descripcion=descripcion,
            json_data=json_data,
            narrativa=narrativa
        )
        
        # Guardar el archivo PDF
        reporte.pdf_file.save(pdf_filename, ContentFile(pdf_bytes), save=True)

        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        return JsonResponse({
            "ok": True,
            "json": json_data,
            "narrativa": narrativa,
            "pdf": pdf_base64,
            "reporte_id": reporte.id
        })

    except Exception as e:
        print(f"ERROR en procesar_reporte: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)
# === Historial de reportes (SPA parcial) ===
@login_required
def history_view(request):
    reportes = ReporteGenerado.objects.filter(usuario=request.user)
    
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "Dashboard/partials/history.html", {"reportes": reportes})
    return render(request, "Dashboard/base.html", {"reportes": reportes})


# === Obtener reportes para API ===
@login_required
def get_reportes(request):
    reportes = ReporteGenerado.objects.filter(usuario=request.user).values(
        'id', 'tipo', 'estudiante', 'descripcion', 'fecha_generacion', 'pdf_file'
    )
    reportes_list = list(reportes)
    for reporte in reportes_list:
        reporte['fecha_generacion'] = reporte['fecha_generacion'].strftime('%d/%m/%Y')
    return JsonResponse({"reportes": reportes_list})


# === Descargar reporte ===
@login_required
def descargar_reporte(request, reporte_id):
    try:
        reporte = ReporteGenerado.objects.get(id=reporte_id, usuario=request.user)
        
        if not reporte.pdf_file:
            return HttpResponse("Archivo no encontrado", status=404)
        
        # Leer el archivo PDF
        pdf_file = reporte.pdf_file.open('rb')
        response = HttpResponse(pdf_file.read(), content_type='application/pdf')
        
        # Generar nombre de archivo para la descarga
        filename = os.path.basename(reporte.pdf_file.name)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        pdf_file.close()
        return response
        
    except ReporteGenerado.DoesNotExist:
        return HttpResponse("Reporte no encontrado", status=404)
    except Exception as e:
        return HttpResponse(f"Error al descargar el archivo: {str(e)}", status=500)


# ========================================
# NUEVAS VISTAS PARA ARCHIVOS PERSISTENTES
# ========================================

# === Obtener archivo activo del usuario ===
@login_required
def get_archivo_activo(request):
    """
    Devuelve el archivo activo del usuario con sus datos procesados.
    Si no hay archivo activo, devuelve el más reciente.
    """
    try:
        # Buscar archivo activo
        archivo = ArchivoNotas.objects.filter(usuario=request.user, activo=True).first()
        
        # Si no hay activo, tomar el más reciente
        if not archivo:
            archivo = ArchivoNotas.objects.filter(usuario=request.user).first()
            if archivo:
                archivo.activo = True
                archivo.save()
        
        if not archivo:
            return JsonResponse({"archivo": None, "message": "No hay archivos cargados"})
        
        # Obtener estudiantes
        estudiantes = list(archivo.estudiantes.values_list("nombre", flat=True))
        
        return JsonResponse({
            "archivo": {
                "id": archivo.id,
                "nombre": archivo.nombre,
                "fecha_subida": archivo.fecha_subida.strftime('%d/%m/%Y'),
                "estudiantes": estudiantes,
                "tiene_datos": archivo.resumen_json is not None
            }
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# === Listar todos los archivos del usuario ===
@login_required
def listar_archivos(request):
    """
    Devuelve todos los archivos del usuario con información básica.
    """
    try:
        archivos = ArchivoNotas.objects.filter(usuario=request.user)
        archivos_list = []
        
        for archivo in archivos:
            archivos_list.append({
                "id": archivo.id,
                "nombre": archivo.nombre,
                "fecha_subida": archivo.fecha_subida.strftime('%d/%m/%Y'),
                "activo": archivo.activo,
                "num_estudiantes": archivo.estudiantes.count(),
                "num_reportes": archivo.reportes.count()
            })
        
        return JsonResponse({"archivos": archivos_list})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# === Activar un archivo específico ===
@login_required
def activar_archivo(request, archivo_id):
    """
    Marca un archivo como activo y desactiva los demás.
    """
    try:
        archivo = ArchivoNotas.objects.get(id=archivo_id, usuario=request.user)
        archivo.activo = True
        archivo.save()  # El método save() del modelo se encarga de desactivar los demás
        
        return JsonResponse({
            "message": f"Archivo '{archivo.nombre}' activado correctamente",
            "archivo_id": archivo.id
        })
    except ArchivoNotas.DoesNotExist:
        return JsonResponse({"error": "Archivo no encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# === Eliminar un archivo ===
@login_required
def eliminar_archivo(request, archivo_id):
    """
    Elimina un archivo y todos sus datos asociados.
    """
    try:
        archivo = ArchivoNotas.objects.get(id=archivo_id, usuario=request.user)
        nombre = archivo.nombre
        
        # Eliminar archivo físico
        if archivo.archivo:
            archivo.archivo.delete()
        
        # Eliminar registro (CASCADE eliminará estudiantes y reportes)
        archivo.delete()
        
        return JsonResponse({"message": f"Archivo '{nombre}' eliminado correctamente"})
    except ArchivoNotas.DoesNotExist:
        return JsonResponse({"error": "Archivo no encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# === Logout ===
def logout_view(request):
    logout(request)
    return redirect("login")
