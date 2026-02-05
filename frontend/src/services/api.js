import axios from 'axios';

// Definimos la dirección de tu servidor Django
const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default {
  // Función para el Componente Validación (Subir PDF)
  async subirPDF(file) {
    const formData = new FormData();
    formData.append('archivo', file);
    const response = await apiClient.post('/validacion/subir/', formData, {
      headers: {'Content-Type': 'multipart/form-data'}
    });
    return response.data;
  },

  // Función para el Componente Conversión (Convertir a HTML)
  async convertirAHTML(docId) {
    const response = await apiClient.post(`/conversion/convertir/${docId}/`);
    return response.data;
  }
};
