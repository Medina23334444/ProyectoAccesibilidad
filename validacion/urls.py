from django.urls import path
from . import views

urlpatterns = [
    path('subir/', views.subir_documento_api, name='api_subir_pdf'),
]
