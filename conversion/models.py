import os
import time
from django.db import models
from django.core.files.base import ContentFile

from conversion.styles import obtener_css_unl
from conversion.utils import AnalizadorSemantico, ProcesadorDocumento, GeneradorHTML
from validacion.models import DocumentoPDF


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

    # ==========================================================
    # PATRÓN: TEMPLATE METHOD (El "Director" del Proceso)
    # ==========================================================
    def convertirPDFaHTML(self):
        """
        Este método representa el 'Template Method'. Define la estructura
        fija e inalterable del proceso: 1. Extraer -> 2. Generar -> 3. Guardar.
        """
        inicio = time.time()

        # ==========================================================
        # PATRÓN: STRATEGY (Los "Especialistas" Técnicos)
        # ==========================================================
        # Aquí el sistema selecciona las herramientas (estrategias)
        # necesarias para realizar el trabajo pesado fuera del modelo.
        proc = ProcesadorDocumento()  # Estrategia de extracción física
        analizador = AnalizadorSemantico()  # Estrategia de reglas semánticas
        generador = GeneradorHTML()  # Estrategia de formato de salida

        try:
            # --- PASO 1 DEL TEMPLATE (Delegado a una Strategy) ---
            # Se encarga de la lectura técnica del PDF.
            pdf_data = proc.extraer_toda_la_estructura(
                self.documento_origen.ruta_archivo.path,
                self.documento_origen.id
            )

            # --- PASO 2 DEL TEMPLATE (Delegado a una Strategy) ---
            # Se encarga de la creación del código HTML accesible.
            html_final, conteo = generador.construir_html(
                pdf_data, proc, analizador,
                self.documento_origen.nombre_archivo,
                obtener_css_unl()
            )

            # --- PASO 3 DEL TEMPLATE (Paso fijo del algoritmo) ---
            # Este paso es inalterable y garantiza la persistencia en la DB.
            self._finalizar_guardado(html_final, conteo, inicio)

            return True, "Conversión exitosa"
        except Exception as e:
            # Manejo de errores para asegurar que el flujo no se rompa abruptamente [cite: 73]
            return False, str(e)

    # ==========================================================
    # PASO FINAL DEL TEMPLATE METHOD (Persistencia)
    # ==========================================================
    def _finalizar_guardado(self, html_content, conteo, inicio):
        # Creación del registro con niveles de accesibilidad AA
        res, _ = ArchivoHTML.objects.update_or_create(
            documento_fuente=self.documento_origen,
            defaults={
                'cantidadEtiquetas': conteo,
                'etiquetasSemanticas': "main, article, p, table, tr, td, h1, h2, section, img, figure",
                'lenguajeHTML': "es",
                'nivelAccesibilidad': "AA (Intermedio)"
            }
        )
        nombre_final = f"{os.path.splitext(os.path.basename(self.documento_origen.ruta_archivo.name))[0]}.html"
        res.archivo.save(nombre_final, ContentFile(html_content.encode('utf-8')), save=True)
        self.tiempoEjecucion = time.time() - inicio
        self.save()
        self.documento_origen.estado = 'CONVERTIDO'
        self.documento_origen.save()
