import re
import ftfy
import unicodedata
import pdfplumber
import os
import html
import io
from django.conf import settings


# ==========================================================
# PATRÓN: STRATEGY (Estrategias de Procesamiento)
# ==========================================================

class ProcesadorDocumento:
    """
    ESTRATEGIA: Extracción y Limpieza de Estructura Física.
    Esta clase encapsula la responsabilidad de interactuar con el PDF
    y extraer su contenido crudo (texto e imágenes).
    """

    @staticmethod
    def limpiar_texto(texto: str) -> str:
        if not texto: return ""
        texto = ftfy.fix_text(str(texto))
        texto = unicodedata.normalize("NFC", texto)
        texto = re.sub(r"\s+", " ", texto)
        return texto.strip()

    def agrupar_en_parrafos(self, palabras):
        """
        Lógica para reconstruir párrafos basándose en la proximidad
        vertical de las líneas de texto.
        """
        if not palabras: return []
        palabras = sorted(palabras, key=lambda w: (w["top"], w["x0"]))

        lineas = []
        linea_actual_texto = []
        y_actual = palabras[0]["top"]

        for w in palabras:
            if abs(w["top"] - y_actual) < 3:
                linea_actual_texto.append(w["text"])
            else:
                lineas.append({"texto": " ".join(linea_actual_texto), "y": y_actual})
                linea_actual_texto = [w["text"]]
                y_actual = w["top"]
        if linea_actual_texto:
            lineas.append({"texto": " ".join(linea_actual_texto), "y": y_actual})

        parrafos_con_pos = []
        parrafo_acumulado = ""
        y_inicio = lineas[0]["y"] if lineas else 0

        for i, linea in enumerate(lineas):
            if i > 0 and (linea["y"] - lineas[i - 1]["y"]) > 16:
                parrafos_con_pos.append({'tipo': 'p', 'contenido': parrafo_acumulado.strip(), 'top': y_inicio})
                parrafo_acumulado = linea["texto"]
                y_inicio = linea["y"]
            else:
                parrafo_acumulado += " " + linea["texto"]

        if parrafo_acumulado:
            parrafos_con_pos.append({'tipo': 'p', 'contenido': parrafo_acumulado.strip(), 'top': y_inicio})
        return parrafos_con_pos

    @staticmethod
    def esta_en_tabla(word, bboxes_tablas):
        """Verifica si una palabra pertenece a las coordenadas de una tabla."""
        x0, top, x1, bottom = word["x0"], word["top"], word["x1"], word["bottom"]
        for (tx0, ttop, tx1, tbottom) in bboxes_tablas:
            if x0 >= tx0 and x1 <= tx1 and top >= ttop and bottom <= tbottom:
                return True
        return False

    @staticmethod
    def extraer_imagenes_pagina(page, doc_id, num_pagina):
        """Extrae imágenes físicas y las almacena en el sistema de archivos de Django."""
        imagenes_extraidas = []
        for i, img in enumerate(page.images):
            bbox = (img["x0"], img["top"], img["x1"], img["bottom"])
            img_obj = page.within_bbox(bbox).to_image(resolution=150)
            nombre_img = f"img_doc{doc_id}_p{num_pagina}_{i}.png"
            ruta_relativa = os.path.join('procesado', 'imagenes', nombre_img)
            ruta_absoluta = os.path.join(settings.MEDIA_ROOT, ruta_relativa)
            os.makedirs(os.path.dirname(ruta_absoluta), exist_ok=True)
            img_obj.save(ruta_absoluta, format="PNG")
            imagenes_extraidas.append({'url': f"{settings.MEDIA_URL}{ruta_relativa}", 'bbox': bbox})
        return imagenes_extraidas

    def extraer_desde_bytes(self, pdf_bytes, doc_id):
        """
        NUEVO MÉTODO ABI: Procesa el PDF desde memoria (RAM).
        Recibe los bytes ya descifrados por AES-256-GCM.
        """
        # Convertimos los bytes en un objeto similar a un archivo en memoria
        flujo_memoria = io.BytesIO(pdf_bytes)

        # Reutilizamos la lógica de extracción pasando el flujo de memoria
        return self._ejecutar_extraccion(flujo_memoria, doc_id)

    def extraer_toda_la_estructura(self, ruta_pdf, doc_id):
        """Mantiene compatibilidad con archivos físicos si fuera necesario."""
        return self._ejecutar_extraccion(ruta_pdf, doc_id)

    def _ejecutar_extraccion(self, origen, doc_id):
        """
        Lógica unificada de extracción que acepta tanto rutas como objetos bytes.
        """
        datos_por_pagina = []
        # pdfplumber puede abrir tanto una ruta (str) como un objeto BytesIO
        with pdfplumber.open(origen) as pdf:
            for i, page in enumerate(pdf.pages):
                elementos = []
                # ... (resto de tu lógica de extracción de imágenes, tablas y texto)
                imgs = self.extraer_imagenes_pagina(page, doc_id, i + 1)
                for im in imgs:
                    elementos.append({'tipo': 'img', 'contenido': im['url'], 'top': im['bbox'][1]})

                tablas = page.find_tables({"snap_tolerance": 3})
                for t in tablas:
                    elementos.append({'tipo': 'tabla', 'contenido': t.extract(), 'top': t.bbox[1]})

                bboxes_excluir = [t.bbox for t in tablas] + [im['bbox'] for im in imgs]
                palabras = page.extract_words(use_text_flow=True)
                solo_texto = [w for w in palabras if not self.esta_en_tabla(w, bboxes_excluir)]
                elementos.extend(self.agrupar_en_parrafos(solo_texto))

                elementos.sort(key=lambda x: x['top'])
                datos_por_pagina.append({'elementos': elementos})
        return datos_por_pagina


class AnalizadorSemantico:
    """
    ESTRATEGIA: Análisis de Jerarquía y Semántica.
    Encapsula las reglas para diferenciar títulos de párrafos comunes,
    permitiendo cambiar los criterios sin afectar la extracción.
    """

    @staticmethod
    def es_titulo_seccion(texto: str) -> bool:
        claves = ["objetivo", "metodología", "resultados", "conclusiones", "introducción", "desarrollo"]
        t = texto.lower()
        return any(t.startswith(c) for c in claves)

    @staticmethod
    def parece_subtitulo(texto: str) -> bool:
        if len(texto) < 60 and not texto.endswith("."):
            mayus = sum(1 for c in texto if c.isupper())
            return mayus > len(texto) * 0.3
        return False


class GeneradorHTML:
    """
    ESTRATEGIA: Construcción de Formato de Salida.
    Encapsula la creación del código HTML accesible (WCAG), asegurando
    la correcta aplicación de etiquetas semánticas.
    """

    @staticmethod
    def construir_html(pdf_data, proc, analizador, nombre_doc, css_unl):
        conteo = 0
        html_res = css_unl
        html_res += f"<body><main><h1>{html.escape(nombre_doc)}</h1>"
        for i, pagina in enumerate(pdf_data):
            html_res += f"<article class='pdf-page'><h2>Página {i + 1}</h2>"
            for el in pagina['elementos']:
                if el['tipo'] == 'img':
                    html_res += f"<figure><img src='{el['contenido']}' alt='Imagen p{i + 1}'></figure>"
                elif el['tipo'] == 'tabla':
                    html_res += "<div class='table-wrapper'><table>"
                    for fila in el['contenido']:
                        html_res += "<tr>" + "".join([f"<td>{html.escape(str(c) or '')}</td>" for c in fila]) + "</tr>"
                    html_res += "</table></div>"
                elif el['tipo'] == 'p':
                    texto = proc.limpiar_texto(el['contenido'])
                    if len(texto) < 3: continue
                    tag = "h2" if analizador.es_titulo_seccion(texto) else (
                        "h3" if analizador.parece_subtitulo(texto) else "p")
                    html_res += f"<{tag}>{html.escape(texto)}</{tag}>"
                conteo += 1
            html_res += "</article>"
        html_res += "</main></body></html>"
        return html_res, conteo
