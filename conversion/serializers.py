from rest_framework import serializers
from .models import ArchivoHTML, ConversorFormato


class ArchivoHTMLSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchivoHTML
        fields = [
            'id',
            'archivo',
            'etiquetasSemanticas',
            'nivelAccesibilidad',
            'cantidadEtiquetas',
            'lenguajeHTML'
        ]


class ConversorFormatoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversorFormato
        fields = [
            'id',
            'formatoDestino',
            'fechaConversion',
            'tiempoEjecucion',
            'documento_origen'
        ]
