import os
from django.db import models
from pypdf import PdfReader


class EstadoDocumento(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    VALIDADO = 'VALIDADO', 'Validado'
    CONVERTIDO = 'CONVERTIDO', 'Convertido'
    ERROR = 'ERROR', 'Error'


class TipoContenido(models.TextChoices):
    TEXTUAL = 'TEXTUAL', 'Textual'
    MIXTO = 'MIXTO', 'Mixto'
    IMAGEN = 'IMAGEN', 'Imagen (Escaneado)'


class Documento(models.Model):
    nombre_archivo = models.CharField(max_length=255)
    ruta_archivo = models.FileField(upload_to='docs/')
    tamanio = models.FloatField(default=0.0, help_text="Tamaño en KB")
    fecha_subida = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=EstadoDocumento.choices,
        default=EstadoDocumento.PENDIENTE
    )

    class Meta:
        abstract = True


class DocumentoPDF(Documento):
    numeroPaginas = models.IntegerField(default=0)
    tieneEtiquetas = models.BooleanField(default=False)

    tipoContenido = models.CharField(
        max_length=10,
        choices=TipoContenido.choices,
        default=TipoContenido.TEXTUAL
    )

    def validarFormato(self):
        try:
            reader = PdfReader(self.ruta_archivo.path)
            self.numeroPaginas = len(reader.pages)
            self.tamanio = os.path.getsize(self.ruta_archivo.path) / 1024

            if self.numeroPaginas > 0:
                self.estado = EstadoDocumento.VALIDADO

            self.save()
            return True, "PDF Válido"
        except Exception as e:
            self.estado = EstadoDocumento.ERROR
            self.save()
            return False, str(e)

    def __str__(self):
        return self.nombre_archivo


class Observacion(models.Model):
    fechaHora = models.DateTimeField(auto_now_add=True)
    detalleTecnico = models.TextField()
    faseOrigen = models.CharField(max_length=100)
    documento = models.ForeignKey(DocumentoPDF, on_delete=models.CASCADE, related_name='observaciones')


class EsquemaIdentificacion(models.Model):
    nombre = models.CharField(max_length=100)
    formato_regex = models.CharField(max_length=100)
    descripcion = models.TextField()


class ObjetoIdentificable(models.Model):
    documento = models.ForeignKey(DocumentoPDF, on_delete=models.CASCADE, related_name='objetos')
    tipo_elemento = models.CharField(max_length=50)
    posicion_x = models.FloatField()
    posicion_y = models.FloatField()
    pagina = models.IntegerField()


class Identificador(models.Model):
    valor = models.CharField(max_length=255)
    esquema = models.ForeignKey(EsquemaIdentificacion, on_delete=models.CASCADE)
    objeto = models.OneToOneField(ObjetoIdentificable, on_delete=models.CASCADE, related_name='id_oficial')


class ValidadorAccesibilidad(models.Model):
    """
    CLASE CLIENTE - PATRÓN ADAPTER
    Esta clase representa el registro de validaciones de accesibilidad.
    Actúa como el cliente del patrón Adapter al interactuar con diversas
    herramientas externas de forma unificada.
    """
    documento = models.ForeignKey(
        DocumentoPDF,
        on_delete=models.CASCADE,
        related_name='validaciones'
    )

    nombre_herramienta = models.CharField(max_length=50)
    resultado_texto = models.TextField(blank=True)
    fecha_validacion = models.DateTimeField(auto_now_add=True)

    # ==========================================================
    # IMPLEMENTACIÓN DEL PATRÓN ADAPTER
    # ==========================================================
    def ejecutar_analisis(self, adaptador):
        """
        Este método demuestra la utilidad del Adapter.
        No importa qué herramienta externa se use (WAVE, EPUBCheck, etc.),
        el sistema siempre llama al método estandarizado '.validar()'.
        """
        # El adaptador (traductor) convierte la respuesta compleja de la
        # herramienta externa en un diccionario simple que el sistema entiende.
        datos = adaptador.validar(self.documento.ruta_archivo.path)
        # Se registra el nombre de la clase adaptadora (ej. AdaptadorWAVE)
        self.nombre_herramienta = adaptador.__class__.__name__

        # Se almacena el resultado procesado de forma genérica
        self.resultado_texto = f"[{datos['puntuacion']}] {datos['detalle']}"
        self.save()
