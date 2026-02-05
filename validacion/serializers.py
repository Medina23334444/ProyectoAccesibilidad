from rest_framework import serializers
from .models import DocumentoPDF


class DocumentoPDFSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentoPDF
        fields = [
            'id',
            'nombre_archivo',
            'ruta_archivo',
            'tamanio',
            'fecha_subida',
            'numeroPaginas',
            'estado'
        ]
