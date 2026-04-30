import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,  // ← único cambio
  headers: {
    'Content-Type': 'application/json',
  },
});

export default {
  async subirPDF(file) {
    const formData = new FormData();
    formData.append('archivo', file);
    const response = await apiClient.post('/validacion/subir/', formData, {
      headers: {'Content-Type': 'multipart/form-data'}
    });
    return response.data;
  },

  async convertirAHTML(docId) {
    const response = await apiClient.post(`/conversion/convertir/${docId}/`);
    return response.data;
  }
};
