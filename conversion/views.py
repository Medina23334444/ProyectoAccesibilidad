from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
from validacion.models import DocumentoPDF
from .models import ConversorFormato, ArchivoHTML
from .serializers import ArchivoHTMLSerializer
# Importamos tus utilidades criptográficas ABI
from .crypto_utils import cifrar_archivo_temporal, generar_token_sesion, hashear_token


@api_view(['POST'])
def ejecutar_conversion_api(request, doc_id):
    documento = get_object_or_404(DocumentoPDF, id=doc_id)

    # 1. GENERACIÓN DE IDENTIDAD SEGURA (Fase ABI)
    # Generamos un token único de 256 bits para esta sesión
    token_plano = generar_token_sesion()
    # Hasheamos con Argon2id antes de guardar en la DB (Resistencia a GPU)
    token_hash = hashear_token(token_plano)

    # 2. CIFRADO EN REPOSO (NIST SP 800-38D)
    # Leemos el archivo original y lo ciframos con AES-256-GCM antes de procesar
    with documento.archivo.open('rb') as f:
        datos_originales = f.read()
        # Usamos la AES_KEY de tu archivo .env configurada en settings
        datos_cifrados = cifrar_archivo_temporal(datos_originales, settings.AES_KEY)

    # 3. EJECUCIÓN DE CONVERSIÓN
    conversor = ConversorFormato.objects.create(
        documento_origen=documento,
        token_acceso=token_hash  # Guardamos solo el hash
    )

    # Aquí tu método interno debería manejar el flujo cifrado
    exito, mensaje = conversor.convertirPDFaHTML(datos_cifrados)

    if exito:
        resultado = ArchivoHTML.objects.get(documento_fuente=documento)
        serializer = ArchivoHTMLSerializer(resultado)

        datos = serializer.data
        # 4. RESPUESTA SEGURA AL CLIENTE
        # Solo entregamos el token plano UNA VEZ. El cliente debe guardarlo.
        datos['session_token'] = token_plano
        datos['url_archivo'] = resultado.archivo.url
        datos['nivel_accesibilidad'] = resultado.nivelAccesibilidad

        return Response(datos)

    return Response({"error": mensaje}, status=500)