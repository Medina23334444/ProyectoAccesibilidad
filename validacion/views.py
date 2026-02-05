from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import DocumentoPDF
from .serializers import DocumentoPDFSerializer


@api_view(['POST'])
def subir_documento_api(request):
    """Endpoint para cargar el PDF desde Vue"""
    archivo = request.FILES.get('archivo')

    if not archivo:
        return Response({"error": "No se envió ningún archivo"}, status=400)

    doc = DocumentoPDF.objects.create(
        ruta_archivo=archivo,
        nombre_archivo=archivo.name
    )
    es_valido, mensaje = doc.validarFormato()

    if es_valido:
        serializer = DocumentoPDFSerializer(doc)
        return Response(serializer.data, status=201)

    return Response({"error": mensaje, "estado": "ERROR"}, status=400)