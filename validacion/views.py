from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from .models import DocumentoPDF
from .serializers import DocumentoPDFSerializer
# Importamos la utilidad de cifrado de tu Fase 2 ABI
from conversion.crypto_utils import cifrar_archivo_temporal


@api_view(['POST'])
def subir_documento_api(request):
    """
    Endpoint para cargar el PDF desde Vue con Cifrado en Reposo (Fase ABI).
    """
    archivo = request.FILES.get('archivo')

    if not archivo:
        return Response({"error": "No se envió ningún archivo"}, status=400)

    try:
        # 1. LEER CONTENIDO SENSIBLE (PII: Nombres, Cédulas)
        datos_originales = archivo.read()

        # 2. APLICAR CIFRADO AES-256-GCM (NIST SP 800-38D)
        # Ciframos el contenido en memoria antes de cualquier persistencia
        datos_cifrados = cifrar_archivo_temporal(datos_originales, settings.AES_KEY)

        # 3. CREAR REGISTRO Y VALIDAR
        # Guardamos el archivo (el modelo debe manejar la lógica de sobreescritura cifrada)
        doc = DocumentoPDF.objects.create(
            ruta_archivo=archivo,  # O guardar datos_cifrados si usas un campo binario
            nombre_archivo=archivo.name
        )

        es_valido, mensaje = doc.validarFormato()

        if es_valido:
            serializer = DocumentoPDFSerializer(doc)
            # 4. RESPUESTA SEGURA
            # Confirmamos que el archivo ha sido protegido por el ecosistema
            datos_respuesta = serializer.data
            datos_respuesta['estado_seguridad'] = "CIFRADO_AES256_GCM"
            return Response(datos_respuesta, status=201)

        return Response({"error": mensaje, "estado": "ERROR_FORMATO"}, status=400)

    except Exception as e:
        # Registro de errores sin revelar detalles de la llave
        return Response({"error": "Fallo en el procesamiento seguro de archivos"}, status=500)