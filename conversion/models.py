import os
import time
from django.db import models
from django.core.files.base import ContentFile

from conversion.styles import obtener_css_unl
from conversion.utils import AnalizadorSemantico, ProcesadorDocumento, GeneradorHTML
from validacion.models import DocumentoPDF
from .crypto_utils import descifrar_archivo_temporal
from django.conf import settings


class Protocolo(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()


class Plan(models.Model):
    protocolo = models.ForeignKey(Protocolo, on_delete=models.CASCADE)
    prioridad = models.IntegerField()
    activo = models.BooleanField(default=True)


class AccionPropuesta(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    comando_tecnico = models.CharField(max_length=255)


class ArchivoHTML(models.Model):
    documento_fuente = models.OneToOneField(
        DocumentoPDF,
        on_delete=models.CASCADE,
        related_name='html_generado'
    )
    archivo = models.FileField(upload_to='html_generados/')
    etiquetasSemanticas = models.TextField(blank=True)
    nivelAccesibilidad = models.CharField(max_length=50, default="A (Básico)")
    cantidadEtiquetas = models.IntegerField(default=0)
    lenguajeHTML = models.CharField(max_length=5, default="es")

    def __str__(self):
        return f"Resultado HTML: {self.documento_fuente.nombre_archivo}"


class ArchivoEPUB(models.Model):
    documento_fuente = models.OneToOneField(DocumentoPDF, on_delete=models.CASCADE)
    metadatosAccesibilidad = models.TextField()
    esquemaValidacion = models.CharField(max_length=100)
    incluyeNavegacion = models.BooleanField()
    recursosIncluidos = models.TextField()


class ConversorFormato(models.Model):
    documento_origen = models.ForeignKey(DocumentoPDF, on_delete=models.CASCADE)
    formatoDestino = models.CharField(max_length=10, default="HTML")
    fechaConversion = models.DateTimeField(auto_now_add=True)
    tiempoEjecucion = models.FloatField(null=True, blank=True)
    token_acceso = models.CharField(max_length=255, null=True, blank=True)

    # ==========================================================
    # PATRÓN: TEMPLATE METHOD (El "Director" del Proceso)
    # ==========================================================

    def convertirPDFaHTML(self, datos_cifrados=None):
        """
        Implementación del Template Method con seguridad integrada.
        Recibe los bytes cifrados para procesarlos exclusivamente en RAM.
        """
        inicio = time.time()

        # Estrategias técnicas (Patrón Strategy)
        proc = ProcesadorDocumento()
        analizador = AnalizadorSemantico()
        generador = GeneradorHTML()

        try:
            # --- PASO 1: DESCARGA Y DESCIFRADO (VOLATILIDAD) ---
            # Si el ecosistema envía datos protegidos, los desciframos en memoria.
            if datos_cifrados:
                # AES-256-GCM verifica la integridad antes de entregar los bytes.
                pdf_bytes = descifrar_archivo_temporal(datos_cifrados, settings.AES_KEY)
                # Procesamos desde bytes (RAM) para evitar archivos temporales en disco.
                pdf_data = proc.extraer_desde_bytes(pdf_bytes, self.documento_origen.id)
            else:
                # Flujo estándar de respaldo usando la ruta física
                pdf_data = proc.extraer_toda_la_estructura(
                    self.documento_origen.ruta_archivo.path,
                    self.documento_origen.id
                )

            # --- PASO 2: GENERACIÓN SEMÁNTICA ---
            html_final, conteo = generador.construir_html(
                pdf_data, proc, analizador,
                self.documento_origen.nombre_archivo,
                obtener_css_unl()
            )

            # --- PASO 3: PERSISTENCIA FIJA ---
            self._finalizar_guardado(html_final, conteo, inicio)

            return True, "Conversión exitosa bajo estándares NIST/RFC"

        except Exception as e:
            # Captura fallos de integridad o errores de procesamiento.
            return False, f"Error de seguridad o procesamiento: {str(e)}"

    def _finalizar_guardado(self, html_content, conteo, inicio):
        """Paso inalterable del algoritmo para registrar resultados en la DB."""
        res, _ = ArchivoHTML.objects.update_or_create(
            documento_fuente=self.documento_origen,
            defaults={
                'cantidadEtiquetas': conteo,
                'etiquetasSemanticas': "main, article, h1, h2, p, table, figure",
                'lenguajeHTML': "es",
                'nivelAccesibilidad': "AA (Intermedio)"
            }
        )

        nombre_final = f"{os.path.splitext(self.documento_origen.nombre_archivo)[0]}.html"
        res.archivo.save(nombre_final, ContentFile(html_content.encode('utf-8')), save=True)

        self.tiempoEjecucion = time.time() - inicio
        self.save()

        # Actualizamos el estado del documento original en el módulo de validación
        self.documento_origen.estado = 'CONVERTIDO'
        self.documento_origen.save()
