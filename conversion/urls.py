from django.urls import path
from . import views

urlpatterns = [
    path('convertir/<int:doc_id>/', views.ejecutar_conversion_api, name='api_convertir'),
]