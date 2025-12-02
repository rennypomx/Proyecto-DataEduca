from django.db import models
from django.contrib.auth.models import User

class ArchivoNotas(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    archivo = models.FileField(upload_to='uploads/')
    fecha_subida = models.DateTimeField(auto_now_add=True)
    resumen_json = models.JSONField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fecha_subida']

    def __str__(self):
        return self.nombre
    
    def save(self, *args, **kwargs):
        # Si este archivo se marca como activo, desactivar los demás del usuario
        if self.activo:
            ArchivoNotas.objects.filter(usuario=self.usuario).exclude(pk=self.pk).update(activo=False)
        super().save(*args, **kwargs)


class Estudiante(models.Model):
    archivo = models.ForeignKey(ArchivoNotas, on_delete=models.CASCADE, related_name='estudiantes')
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre


class ReporteGenerado(models.Model):
    TIPO_CHOICES = [
        ('grupal', 'Grupal'),
        ('individual', 'Individual'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    archivo = models.ForeignKey(ArchivoNotas, on_delete=models.CASCADE, related_name='reportes')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    estudiante = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.CharField(max_length=500)
    pdf_file = models.FileField(upload_to='reportes/')
    json_data = models.JSONField()
    narrativa = models.TextField()
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_generacion']

    def __str__(self):
        return f"{self.descripcion} - {self.fecha_generacion.strftime('%d/%m/%Y')}"
