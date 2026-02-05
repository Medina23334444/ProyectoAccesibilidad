from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from validacion.models import DocumentoPDF
from .models import ConversorFormato, ArchivoHTML
from .serializers import ArchivoHTMLSerializer


@api_view(['POST'])
def ejecutar_conversion_api(request, doc_id):
    from django.shortcuts import get_object_or_404
    documento = get_object_or_404(DocumentoPDF, id=doc_id)
    conversor = ConversorFormato.objects.create(documento_origen=documento)
    exito, mensaje = conversor.convertirPDFaHTML()

    if exito:
        resultado = ArchivoHTML.objects.get(documento_fuente=documento)
        serializer = ArchivoHTMLSerializer(resultado)

        datos = serializer.data
        datos['url_archivo'] = resultado.archivo.url
        datos['cantidad_etiquetas'] = resultado.cantidadEtiquetas
        datos['nivel_accesibilidad'] = resultado.nivelAccesibilidad

        return Response(datos)

    return Response({"error": mensaje}, status=500)
